from interactions import CommandContext

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