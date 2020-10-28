import os
import sys
import webbrowser

import pyperclip
import rumps

from uuid import UUID
import time
import rumps

global app, token, mytoken_menuitem
mytoken_menuitem = "TOKEN_ITEM"

@rumps.timer(10)
def refresh_update(sender):
    app.title = str(time.time())
    # print('TODO post CPU update')

def validate_uuid4(uuid_string):
    """
    https://gist.github.com/ShawnMilo/7777304
    Validate that a UUID string is in
    fact a valid uuid4.

    Happily, the uuid module does the actual
    checking for us.

    It is vital that the 'version' kwarg be passed
    to the UUID() call, otherwise any 32-character
    hex string is considered valid.
    """

    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        # If it's a value error, then the string
        # is not a valid hex code for a UUID.
        return False

    # If the uuid_string is a valid hex code,
    # but an invalid uuid4,
    # the UUID.__init__ will convert it to a
    # valid uuid4. This is bad for validation purposes.

    return val.hex == uuid_string


def ask_for_token():
    clipboard_element = pyperclip.paste()
    # has token
    newwindow = rumps.Window(message='Right click to paste your token below', default_text=str(clipboard_element),
                             title='SpookyLoop 5000', ok="Submit Token", cancel="Cancel", dimensions=(320, 160))
    outcome = newwindow.run()
    try:
        return str(UUID(outcome.text, version=4))
    except:
        return None


@rumps.clicked('Print Something')
def print_something(_):
    rumps.alert(message='something', ok='YES!', cancel='NO!')

@rumps.clicked(mytoken_menuitem)
def mytoken_menuitem_function(_):
    webbrowser.open('http://142.93.117.219:5000/webclient?token=%s' % token, new=2)


@rumps.clicked('On/Off Test')
def on_off_test(_):
    print_button = app.menu['Print Something']
    if print_button.callback is None:
        print_button.set_callback(print_something)
    else:
        print_button.set_callback(None)


@rumps.clicked('Clean Quit')
def clean_up_before_quit(_):
    print('TODO notify server of disconnect')
    rumps.quit_application()


if __name__ == "__main__":
    rumps.debug_mode(True)
    app = rumps.App('SpookyLoop', menu=[mytoken_menuitem, 'Print Something', 'On/Off Test', 'Clean Quit'], quit_button=None)
    token = ask_for_token()
    token_menuitem_val = app.menu[mytoken_menuitem]
    token_menuitem_val.title = "Token: " + token[0:5] + "..."
    if token is not None:
        # TODO check if the token is valid by sending a sample CPU val
        rumps.alert(title=None, message='It worked!')
        app.run()
    else:
        rumps.alert(title=None, message='Bad token')
        sys.exit(0)
