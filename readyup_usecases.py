from readyup_constants import ButtonId
from readyup_domain import ReadyUpModel
from interactions import CommandContext, ComponentContext, Member

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
        print(f"parsing id: {self.custom_id}")
        match (self.custom_id):
            case "ready":
                return ButtonId.READY
            case "not_ready":
                return ButtonId.NOT_READY
            case _:
                return ButtonId.INVALID

class GetInteractionReplyUseCase:
    def __init__(self, in_model : ReadyUpModel) -> None:
        self.model = in_model
    
    def __call__(self) -> str:
        get_ready_members_names = StringifyMembersToNamesUseCase(self.model.ready_members)
        get_ready_members_plural = GetPluralUseCase(self.model.ready_members)
        get_not_ready_members_names = StringifyMembersToNamesUseCase(self.model.not_ready_members)
        get_not_ready_members_plural = GetPluralUseCase(self.model.not_ready_members)

        out_str : str = "Status: "

        if len(self.model.ready_members) > 0:
            out_str += f"{ get_ready_members_names() } { get_ready_members_plural() } ready"
        if len(self.model.not_ready_members) > 0:
            out_str += f"\n{ get_not_ready_members_names() } { get_not_ready_members_plural() } not ready"

        return out_str

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
        if self.context is not None and self.context.message is not None:
            try:
                new_content = self.context.message.content + " (Closed)"
                await self.context.edit(components=[], content=new_content)
            except:
                print("error trying to close ready up context")

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
    # in_stringify_callable : is a function that converts an element in the container to a string
    def __init__(self, in_elements : set, in_stringify_callable):
        self.elements = in_elements
        self.in_stringify_callable = in_stringify_callable
    
    def __call__(self) -> str:
        out_str : str = ""

        i = 0
        count = len(self.elements)

        if (count > 0): # prefix before concat
            out_str += "**"

        for element in self.elements:
            out_str += self.in_stringify_callable(element)

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
            get_not_ready_members_as_names_string = StringifyMembersToNamesUseCase(self.model.not_ready_members)
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
