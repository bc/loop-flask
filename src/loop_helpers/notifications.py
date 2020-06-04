import requests

def get_telegram_token(loop_token: str):
    # TODO make non-hardcoded. will only ping brian via bot.
    return "911638276:AAEe7XkH3B_YNg1mpfRZsjt0jm7QX3nZaCg"


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