from .extras import printMessage


def printHello():
    print("Hello from test.py")


def beforeLoad(channel, page):
    print("beforeLoad event fired")


def activate():
    print("plugin test activated")
    printHello()
    printMessage()


def deactivate():
    print("plugin deactivated")
