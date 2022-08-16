class ReadyUpViewModel:
    def __init__(self) -> None:
        self.call_to_action : str = ""
        self.status : str = ""

    def clear(self) -> None:
        self.call_to_action : str = ""
        self.status : str = ""