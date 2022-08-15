import asyncio

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

    # clear the ready up model
    close_previous_context_use_case = ClosePreviousContextUseCase(ready_up_model)
    ready_up_model = await close_previous_context_use_case()
    ready_up_model.clear()
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

    get_call_to_action_message_use_case = GetCallToActionMessageUseCase(ready_up_model)
    await command_context.defer()

    test = get_call_to_action_message_use_case()
    print (test)

    await command_context.send(get_call_to_action_message_use_case(), components=[ready_button, not_ready_button])

    is_ready_up_finished_use_case = IsReadyUpFinishedUseCase(ready_up_model)
    while(not is_ready_up_finished_use_case()):
        try: 
            button_context : ComponentContext = await client.wait_for_component(components=[ready_button, not_ready_button], timeout=ready_up_model.timeout_in_seconds)

            custom_id_to_button_id_use_case = CustomIdToButtonIdUseCase(button_context.custom_id)
            button_id = custom_id_to_button_id_use_case()

            update_model_use_case = NoOpReadyUpModelUpdateUseCase(ready_up_model)
            match (button_id):
                case ButtonId.READY:
                    update_model_use_case = SetMemberAsReadyUseCase(ready_up_model, button_context)
                case ButtonId.NOT_READY:
                    update_model_use_case = SetMemberAsNotReadyUseCase(ready_up_model, button_context)
                case _:
                    print("button id invalid")

            ready_up_model = update_model_use_case()
            get_interaction_reply_use_case = GetInteractionReplyUseCase(ready_up_model)

            await button_context.defer(ephemeral=True)
            await button_context.send(get_interaction_reply_use_case())
        except asyncio.TimeoutError:
            break
        finally:
            is_ready_up_finished_use_case = IsReadyUpFinishedUseCase(ready_up_model) 

    close_command_context_use_case = CloseReadyUpContextUseCase(command_context)
    await close_command_context_use_case()

    get_final_result_message_use_case = GetFinalResultMessageUseCase(ready_up_model)
    await command_context.send(get_final_result_message_use_case())

client.start()