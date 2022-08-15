from enum import Enum
from typing import Callable

import os
from dotenv import load_dotenv
import asyncio

from interactions import Client, Member, Button, ButtonStyle, ComponentContext, CommandContext, option
from interactions.ext.wait_for import setup


class ButtonId(Enum):
    INVALID = 0
    READY = 1
    NOT_READY = 2

class ButtonIdToCustomIdUseCase:
    def __init__(self, in_button_id : ButtonId):
        self.button_id = in_button_id

    def __call__(self) -> str:
        match (self.button_id):
            case ButtonId.READY:
                return "ready"
            case ButtonId.NOT_READY:
                return "not_ready"
            case _:
                return "invalid"

class CustomIdToButtonIdUseCase:
    def __init__(self, in_custom_id : str):
        self.custom_id = in_custom_id

    def __call__(self) -> ButtonId:
        match (self.custom_id):
            case "ready":
                return ButtonId.READY
            case "not_ready":
                return ButtonId.NOT_READY
            case _:
                return ButtonId.INVALID

class ReadyUpReply(Enum):
    INVALID = 0
    AUTHOR_ONLY = 1
    READY_MEMBERS = 2
    UNREADY_MEMBERS = 3

# MVVM
class ReadyUpModel:
    def __init__(self) -> None:
        self.event_name : str = ""
        self.time_name : str = ""
        self.num_ready_for_success : int = 3
        self.num_not_ready_for_failure : int = 1
        self.timeout_in_seconds = 60
        self.ready_members : dict = dict() # dict<Member, CommandContext | ButtonContext>
        self.not_ready_members : set = set() # set<Member>
        self.previous_context : None | CommandContext = None

    def clear(self) -> None:
        self.event_name : str = ""
        self.time_frame : str = ""
        self.num_ready_for_success : int = 3
        self.num_not_ready_for_failure : int = 1
        self.timeout_in_seconds = 60
        self.ready_members.clear()
        self.not_ready_members.clear()
        # previous_context purposefully is not cleared

class GetInteractionReplyUseCase:
    def __init__(self, in_model : ReadyUpModel) -> None:
        self.model = in_model
    
    def __call__(self) -> str:
        get_ready_members_names = StringifyMembersToNamesUseCase(self.model.ready_members)
        get_ready_members_plural = GetPluralUseCase(self.model.ready_members)
        get_not_ready_members_names = StringifyMembersToNamesUseCase(self.model.not_ready_members)
        get_not_ready_members_plural = GetPluralUseCase(self.model.not_ready_members)

        out_str : str = ""

        if len(self.model.ready_members) > 0:
            out_str += f"{ get_ready_members_names() } { get_ready_members_plural() } ready"
        if len(self.model.not_ready_members) > 0:
            out_str += f"\n{ get_not_ready_members_names() } { get_not_ready_members_plural() } not ready"

        return out_str

# Use Cases
class NoOpReadyUpModelUpdateUseCase:
    def __init__(self, inout_ready_up_model : ReadyUpModel) -> None:
        self.ready_up_model = inout_ready_up_model
        
    def __call__(self) -> ReadyUpModel:
        return self.ready_up_model

class SetMemberAsReadyUseCase:
    def __init__(self, inout_ready_up_model : ReadyUpModel, in_context : ComponentContext | CommandContext) -> None:
        self.ready_up_model = inout_ready_up_model
        self.member = in_context.author
        self.context = in_context

    def __call__(self) -> ReadyUpModel:
        self.ready_up_model.ready_members[self.member] = self.context

        try:
            self.ready_up_model.not_ready_members.remove(self.member)
        except:
            pass

        return self.ready_up_model

class SetMemberAsNotReadyUseCase:
    def __init__(self, inout_ready_up_model : ReadyUpModel, in_context : ComponentContext) -> None:
        self.ready_up_model = inout_ready_up_model
        self.member = in_context.author
        self.context = in_context

    def __call__(self) -> ReadyUpModel:

            self.ready_up_model.not_ready_members.add(self.member)

            try:
                self.ready_up_model.ready_members.pop(self.member)
            except:
                pass
              
            return self.ready_up_model

class CloseReadyUpContextUseCase:
    def __init__(self, in_context : CommandContext | None) -> None:
        self.context = in_context
    
    async def __call__(self) -> None:
        if self.context is not None:
            new_content = self.context.message.content + " (Closed)"
            await self.context.edit(components=[], content=new_content)

class ClosePreviousContextUseCase:
    def __init__(self, inout_model : ReadyUpModel) -> None:
        self.model = inout_model

    async def __call__(self) -> ReadyUpModel:
        close_ready_up_context_use_case = CloseReadyUpContextUseCase(self.model.previous_context)
        await close_ready_up_context_use_case()
        self.model.previous_context = None
        return self.model

class CustomIdToModelUpdateActionUseCase:
    def __init__(self, inout_ready_up_model : ReadyUpModel, in_member : Member, in_custom_id : str):
        self.custom_id = in_custom_id
        self.member = in_member
        self.ready_up_model = inout_ready_up_model,
    
    def __call__(self):
        match (self.custom_id):
            case "ready":
                return SetMemberAsReadyUseCase(self.ready_up_model, self.member)
            case "not_ready":
                return SetMemberAsNotReadyUseCase(self.ready_up_model, self.member)
            case _:
                return NoOpReadyUpModelUpdateUseCase(self.ready_up_model)

class IsReadyUpSuccessfulUseCase:
    def __init__(self, in_ready_up_model : ReadyUpModel):
        self.ready_up_model = in_ready_up_model

    def __call__(self) -> bool:
        return len(self.ready_up_model.ready_members) >= self.ready_up_model.num_ready_for_success

class IsReadyUpFailedUseCase:
    def __init__(self, in_ready_up_model : ReadyUpModel):
        self.ready_up_model = in_ready_up_model

    def __call__(self) -> bool:
        return len(self.ready_up_model.not_ready_members) >= self.ready_up_model.num_not_ready_for_failure

class IsReadyUpFinishedUseCase:
    def __init__(self, in_ready_up_model : ReadyUpModel):
        self.ready_up_model = in_ready_up_model

    def __call__(self) -> bool:
        is_ready_up_successful_use_case = IsReadyUpSuccessfulUseCase(self.ready_up_model)
        is_ready_up_failed_use_case = IsReadyUpFailedUseCase(self.ready_up_model)
        return is_ready_up_successful_use_case() or is_ready_up_failed_use_case()

class StringifySetUseCase:
    def __init__(self, in_elements : set, in_stringify_function : Callable):
        self.elements = in_elements
        self.stringify_function = in_stringify_function
    
    def __call__(self) -> str:
        out_str : str = ""

        i = 0
        count = len(self.elements)

        if (count > 0): # prefix before concat
            out_str += "**"

        for element in self.elements:
            out_str += self.stringify_function(element)

            if (i == count-1): # last
                out_str += "** "
            elif (i == count-2): # second to last
                out_str += "** and **"
            else:
                out_str += "**, **"
            
            i += 1

        return out_str

class StringifyMembersToMentionsUseCase:
    def __init__(self, in_members : set):
        self.members = in_members

    def __call__(self) -> str:
        stringify_to_mentions = StringifySetUseCase(self.members, lambda member : member.mention)
        out_str = stringify_to_mentions()
        return out_str

class StringifyMembersToNamesUseCase:
    def __init__(self, in_members : set):
        self.members = in_members

    def __call__(self) -> str:
        stringify_to_names = StringifySetUseCase(self.members, lambda member : member.name)
        out_str = stringify_to_names()
        return out_str

class GetPluralUseCase:
    def __init__(self, in_container):
        self.container = in_container
    
    def __call__(self) -> str:
        length = len(self.container)
        outstr : str = ""
        if length > 1:
            outstr = "are"
        else:
            outstr = "is"
        return outstr

class GetFinalResultMessageUseCase:
    def __init__(self, in_model : ReadyUpModel):
        self.model = in_model
    
    def __call__(self) -> str:
        is_ready_up_successful_use_case = IsReadyUpSuccessfulUseCase(self.model)
        is_ready_up_failed_use_case = IsReadyUpFailedUseCase(self.model)
        get_ready_members_as_mentions_string = StringifyMembersToMentionsUseCase(self.model.ready_members)
        get_not_ready_members_plural = GetPluralUseCase(self.model.not_ready_members)
        if is_ready_up_successful_use_case():
            return f"{get_ready_members_as_mentions_string()}\neveryone is ready!"
        elif is_ready_up_failed_use_case():
            get_not_ready_members_as_names_string = StringifyMembersToNamesUseCase(ready_up_model.not_ready_members)
            return f"{get_ready_members_as_mentions_string()}\n{get_not_ready_members_as_names_string()} {get_not_ready_members_plural()} not ready"
        else:
            return f"{get_ready_members_as_mentions_string()}\nnot enough members readied up"

class GetCallToActionMessageUseCase:
    def __init__(self, in_model : ReadyUpModel):
        self.model = in_model

    def __call__(self) -> str:
        event_name_concat = "are you ready"
        if (self.model.event_name and not self.model.event_name.isspace()):
            event_name_concat += f" for {self.model.event_name}"
        time_frame_concat = ""
        if (self.model.time_frame and not self.model.time_frame.isspace()):
            time_frame_concat = " " + self.model.time_frame

        return f"{event_name_concat}{time_frame_concat}?"

# Constants
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SERVER_ID = os.getenv('SERVER_ID')
get_ready_button_id = ButtonIdToCustomIdUseCase(ButtonId.READY)
get_not_ready_button_id = ButtonIdToCustomIdUseCase(ButtonId.NOT_READY)

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
        custom_id=get_ready_button_id(),
        label="Ready"
    )

    not_ready_button = Button(
        style= ButtonStyle(ButtonStyle.DANGER),
        custom_id=get_not_ready_button_id(),
        label="Not Ready"
    )

    get_call_to_action_message_use_case = GetCallToActionMessageUseCase(ready_up_model)
    await command_context.defer()
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
    # edit the original message and remove the button(s)

client.start()