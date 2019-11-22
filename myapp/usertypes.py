import enum
import typing
from PyQt5.QtCore import QUrl


Url = typing.TypeVar('Url', str, QUrl)

LoadEvent = enum.Enum(
    "LoadEvent", ["FINISHED", "STARTED", "BEFORE_LOAD"]
)
