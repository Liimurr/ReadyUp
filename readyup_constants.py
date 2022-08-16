
from os import getenv
from dotenv import load_dotenv
from enum import Enum

class ButtonId(Enum):
    INVALID = 0
    READY = 1
    NOT_READY = 2

class ButtonIdStr(Enum):
    INVALID = "invalid"
    READY = "ready"
    NOT_READY = "not_ready"

load_dotenv()

DISCORD_TOKEN = getenv('DISCORD_TOKEN')
SERVER_ID = getenv('SERVER_ID')

SMALL_NUMBER = 1.e-8
KINDA_SMALL_NUMBER = 1.e-4
BIG_NUMBER = 3.4e+38