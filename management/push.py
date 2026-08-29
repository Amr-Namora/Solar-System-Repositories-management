import requests

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

def send_push_notification(tokens, title, body, data=None):
    if not tokens:
        return
    messages = [{
        "to": token,
        "sound": "default",
        "title": title,
        "body": body,
        "data": data or {},
    } for token in tokens]

    try:
        resp = requests.post(
            EXPO_PUSH_URL,
            json=messages,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=10,
        )
        print("Expo push response:", resp.status_code, resp.text)  # remove later, useful while testing
    except requests.RequestException as e:
        print("Push notification failed:", e)