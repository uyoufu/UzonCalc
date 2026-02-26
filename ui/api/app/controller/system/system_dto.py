from app.controller.dto_base import BaseDTO


class DesktopAutoLoginResDTO(BaseDTO):
	enabled: bool
	username: str
	password: str
