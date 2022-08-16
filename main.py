from asyncio import TimeoutError
from random import randint
from interactions import Client, Button, ButtonStyle, ComponentContext, CommandContext, option
from interactions.ext.wait_for import setup

from readyup_domain import ReadyUpModel
from readyup_ui import ReadyUpViewModel
from readyup_constants import BIG_NUMBER, ButtonId, ButtonIdStr, DISCORD_TOKEN, SERVER_ID
from readyup_usecases import *

ready_up_model = ReadyUpModel()
ready_up_view_model = ReadyUpViewModel()

# View
client = Client(
    token=DISCORD_TOKEN,
    default_scope=SERVER_ID
)

setup(client)

@client.command(name="ready_up", description="ready up polling bot")
@option(str, name="event_name", description="name of the event (default=\"\")", required=False)
@option(str, name="time_frame", description="what time frame are setting (default=\"\")", required=False)
@option(int, name="duration", description="how long in seconds this request will stay active before timing out (default=60 seconds)", required=False)
@option(int, name="number_to_wait_for", description="how many need to be ready? (default=3)", required = False)
async def ready_up_command(command_context : CommandContext, event_name : str = "", time_frame : str = "", duration : int = 60, number_to_wait_for : int = 3):
    global ready_up_model, ready_up_view_model

    # if there is a previously open ready up poll, close it.
    if ready_up_model.active_context is not None:
        print("previous context was still active -- closing now")
        close_previous_context_use_case = CloseActiveContextUseCase(ready_up_model)
        ready_up_model = await close_previous_context_use_case()

    # reset all data to the default 
    ready_up_model.clear()

    # initialize ready up model
    ready_up_model.active_context = command_context
    ready_up_model.event_name = event_name
    ready_up_model.time_frame = time_frame
    ready_up_model.num_ready_for_success = number_to_wait_for
    ready_up_model.timeout_in_seconds = duration

    ready_button = Button(
        style=ButtonStyle(ButtonStyle.SUCCESS),
        custom_id=ButtonIdStr.READY.value + str(randint(0, BIG_NUMBER)), # each button requires a unique id, so appending some random number is necessary
        label="Ready"
    )

    not_ready_button = Button(
        style=ButtonStyle(ButtonStyle.DANGER),
        custom_id=ButtonIdStr.NOT_READY.value + str(randint(0, BIG_NUMBER)), # each button requires a unique id, so appending some random number is necessary
        label="Not Ready"
    )
    
    # invalidate the view model
    model_to_view_model_use_case = ModelToViewModelUseCase(ready_up_model, ready_up_view_model)
    ready_up_view_model = model_to_view_model_use_case()

    # invalidate the view
    get_command_message_use_case = GetCommandMessageUseCase(ready_up_view_model)
    await command_context.defer()
    await command_context.send(get_command_message_use_case(), components=[ready_button, not_ready_button])

    # create the buttons - once this await returns, it means one of the buttons was clicked
    is_ready_up_finished_use_case = IsReadyUpFinishedUseCase(ready_up_model)
    while(not is_ready_up_finished_use_case()):

        print("not finished processing user buttons")

        try: 
            # when this returns it means the button was clicked, the context returned is the context of the button that was clicked
            button_context : ComponentContext = await client.wait_for_component(components=[ready_button, not_ready_button], timeout=ready_up_model.timeout_in_seconds)

            print(f"button context defer {button_context.id}")
            await button_context.defer(ephemeral=True)

            # parse the button id that was clicked            
            custom_id_to_button_id_use_case =  ButtonCustomIdToButtonIdUseCase(button_context.custom_id)
            button_id = custom_id_to_button_id_use_case()

            # switch based on the button id to figure out which button was clicked
            reply_message = ""
            update_model_use_case = NoOpReadyUpModelUpdateUseCase(ready_up_model)
            match (button_id):
                case ButtonId.READY:
                    update_model_use_case = SetMemberAsReadyUseCase(ready_up_model, button_context)
                    reply_message = "you are ready!"
                case ButtonId.NOT_READY:
                    update_model_use_case = SetMemberAsNotReadyUseCase(ready_up_model, button_context)
                    reply_message = "you are not ready"
                case _:
                    # there is no reason for us to hit this, so we need to figure out why it was hit
                    reply_message = "something went wrong!"
                    print("error: button id was invalid")
            await button_context.send(reply_message)

            # invalidate the model
            ready_up_model = update_model_use_case()

            # display the message to the user who pressed the button
            print("sending reply")

            # invalidate the view model
            model_to_view_model_use_case = ModelToViewModelUseCase(ready_up_model, ready_up_view_model)
            ready_up_view_model = model_to_view_model_use_case()

            # invalidate the view
            get_command_message_use_case = GetCommandMessageUseCase(ready_up_view_model)
            await command_context.edit(get_command_message_use_case())

        except TimeoutError:
            print("not enough people readied up, and we timed out")
            break
        finally:
            is_ready_up_finished_use_case = IsReadyUpFinishedUseCase(ready_up_model) 

    # if command context is still active close out and show results
    if ready_up_model.active_context is command_context:
        print("current command context is still active -- closing now")

        # edit the initial call to action message to display as 'closed', and remove the interaction buttons
        close_active_context_use_case = CloseActiveContextUseCase(ready_up_model)
        await close_active_context_use_case()
            
        # invalidate the view model
        model_to_view_model_use_case = ModelToViewModelUseCase(ready_up_model, ready_up_view_model)
        ready_up_view_model = model_to_view_model_use_case()

        # invalidate the view
        get_command_message_use_case = GetCommandMessageUseCase(ready_up_view_model)
        await command_context.edit(get_command_message_use_case())

        # send a ping out to everyone who readied up to notify them of the results
        get_final_results_message_use_case = GetFinalResultMessageUseCase(ready_up_model)
        await command_context.send(get_final_results_message_use_case())

    # else someone else alaready closed the poll
    else:
        print("poll was already closed")

client.start()