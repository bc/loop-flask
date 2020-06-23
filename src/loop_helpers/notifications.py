import requests


def get_telegram_token(loop_token: str):
    # TODO make non-hardcoded. will only ping brian via bot.
    return "911638276:AAEe7XkH3B_YNg1mpfRZsjt0jm7QX3nZaCg"
import os

def get_notification_phonenumber(loop_token:str):
    target_filepath = "%s_contactinfo.txt"%loop_token
    if os.path.exists(target_filepath):
        raise Exception("No contactinfo found")
    else:
        pass
        #todo lookup
    return("+13108007011")

def get_telegram_chat_id(loop_token):
    # TODO make non-hardcoded. will only ping brian via bot.
    return 97634578


def push_telegram_notification(loop_token, message):
    telegram_token = get_telegram_token(loop_token)
    telegram_chat_id = get_telegram_chat_id(loop_token)
    url = "https://api.telegram.org/bot%s/sendMessage" % telegram_token
    payload = 'chat_id=%s&text=%s' % (telegram_chat_id, message)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.json()["ok"]:
            return True
        else:
            return False
    except:
        return False


def text_update(loop_token: str, msg: str):
    target_number = get_notification_phonenumber(loop_token)
    url = "https://api.twilio.com/2010-04-01/Accounts/ACc213f0b60986d196fa19d7e6a1b4fa17/Messages.json"

    payload = 'To=%s&From=+12052892818&Body=%s' % (target_number, msg)
    headers = {
        'Authorization': 'Basic QUNjMjEzZjBiNjA5ODZkMTk2ZmExOWQ3ZTZhMWI0ZmExNzpiNGIzZTkxNzgyM2NkODJhNWFiMTNjNDg4NDc4ZmU3NQ==',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return (response.text.encode('utf8'))
