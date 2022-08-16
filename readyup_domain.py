from interactions import CommandContext

class ReadyUpModel:
    def __init__(self) -> None:

        self.event_name : str = ""
        self.num_ready_for_success : int = 3
        self.num_not_ready_for_failure : int = 1
        self.timeout_in_seconds : float = 900 # 15 minutes

        # transient
        self.ready_members : dict = dict() # dict<Member, CommandContext | ButtonContext>
        self.not_ready_members : set = set() # set<Member>
        self.active_context : None | CommandContext = None

    def clear(self) -> None:

        self.event_name : str = ""
        self.call_to_action : str = ""
        self.num_ready_for_success : int = 3
        self.num_not_ready_for_failure : int = 1
        self.timeout_in_seconds : float = 900 # 15 minutes

        # transient
        self.ready_members.clear()
        self.not_ready_members.clear()
        self.active_context : None | CommandContext = None