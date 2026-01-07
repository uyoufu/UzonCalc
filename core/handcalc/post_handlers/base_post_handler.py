class BasePostHandler:

    def handle(self, data: str) -> str:
        raise NotImplementedError()
