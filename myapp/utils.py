import os
import re
import fnmatch
from typing import TypeVar, Callable

T = TypeVar('T')


class Signal:
    def __init__(self, *args):
        self.__subscribers = []

    def emit(self, *args, **kwargs):
        for subs in self.__subscribers:
            subs(*args, **kwargs)

    def connect(self, func: Callable[[T], None]):
        self.__subscribers.append(func)

    def disconnect(self, func: Callable[[T], None]):
        try:
            self.__subscribers.remove(func)
        except ValueError:
            print('Warning: function %s not removed '
                  'from signal %s' % (func, self))


def findFiles(pattern, path, regex=False):
    matches = []
    for root, dirs, files in os.walk(path):
        for basename in files:
            if not regex:
                if fnmatch.fnmatch(basename, pattern):
                    filename = os.path.join(root, basename)
                    matches.append(filename)
            else:
                if len(re.findall(pattern, basename)) > 0:
                    filename = os.path.join(root, basename)
                    matches.append(filename)

    return matches
