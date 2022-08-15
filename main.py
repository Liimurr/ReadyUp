from asyncio import TimeoutError
from interactions import Client, Button, ButtonStyle, ComponentContext, CommandContext, option
from interactions.ext.wait_for import setup

from readyup_domain import ReadyUpModel
from readyup_constants import ButtonId, ButtonIdStr, DISCORD_TOKEN, SERVER_ID
from readyup_usecases import *

ready_up_model = ReadyUpModel()

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
    global ready_up_model

    # if there is a previously open ready up poll, close it.
    close_previous_context_use_case = ClosePreviousContextUseCase(ready_up_model)
    ready_up_model = await close_previous_context_use_case()

    # reset all data to the default 
    ready_up_model.clear()

    # get command arguments
    ready_up_model.event_name = event_name
    ready_up_model.time_frame = time_frame
    ready_up_model.num_ready_for_success = number_to_wait_for
    ready_up_model.timeout_in_seconds = duration

    ready_button = Button(
        style=ButtonStyle(ButtonStyle.SUCCESS),
        custom_id=ButtonIdStr.READY.value,
        label="Ready"
    )

    not_ready_button = Button(
        style=ButtonStyle(ButtonStyle.DANGER),
        custom_id=ButtonIdStr.NOT_READY.value,
        label="Not Ready"
    )
    
    # get the initial message string to show everyone
    get_call_to_action_message_use_case = GetCallToActionMessageUseCase(ready_up_model)

    # defer allows us to send follow up messages after the initial message
    await command_context.defer()

    # tell discord to display the initial message
    await command_context.send(get_call_to_action_message_use_case(), components=[ready_button, not_ready_button])

    is_ready_up_finished_use_case = IsReadyUpFinishedUseCase(ready_up_model)
    while(not is_ready_up_finished_use_case()):
        try: 
            # create the buttons - once this await returns, it means one of the buttons was clicked
            button_context : ComponentContext = await client.wait_for_component(components=[ready_button, not_ready_button], timeout=ready_up_model.timeout_in_seconds)

            # switch based on the button id to figure out which button was clicked
            custom_id_to_button_id_use_case = CustomIdToButtonIdUseCase(button_context.custom_id)
            button_id = custom_id_to_button_id_use_case()
            update_model_use_case = NoOpReadyUpModelUpdateUseCase(ready_up_model)
            match (button_id):
                case ButtonId.READY:
                    update_model_use_case = SetMemberAsReadyUseCase(ready_up_model, button_context)
                case ButtonId.NOT_READY:
                    update_model_use_case = SetMemberAsNotReadyUseCase(ready_up_model, button_context)
                case _:
                    # there is no reason for us to hit this, so we need to figure out why it was hit
                    print("button id invalid -- something went wrong")

            # update our internal if a discord user readied up or decided they were not ready
            ready_up_model = update_model_use_case()

            # get a new display message for the user who pressed the button
            get_interaction_reply_use_case = GetInteractionReplyUseCase(ready_up_model)

            # display the message to the user who pressed the button
            await button_context.defer(ephemeral=True)
            await button_context.send(get_interaction_reply_use_case())

        except TimeoutError:
            print("not enough people readied up, and we timed out")
            break
        finally:
            is_ready_up_finished_use_case = IsReadyUpFinishedUseCase(ready_up_model) 

    # edit the initial call to action message to display as 'closed', and remove the interaction buttons
    close_command_context_use_case = CloseReadyUpContextUseCase(command_context)
    await close_command_context_use_case()

    # send a message to ping everyone who readied up displaying the result of the poll
    get_final_result_message_use_case = GetFinalResultMessageUseCase(ready_up_model)
    await command_context.send(get_final_result_message_use_case())

client.start()