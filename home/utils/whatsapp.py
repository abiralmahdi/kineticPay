# home/utils/whatsapp.py

import requests


def send_whatsapp_message(phone, message):

    print("WHATSAPP FUNCTION CALLED")
    print("PHONE:", phone)
    print("MESSAGE:", message)

    try:

        response = requests.post(
            "http://127.0.0.1:3001/send-message",
            json={
                "phone": phone,
                "message": message
            },
            timeout=15
        )

        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

        return response.json()

    except Exception as e:

        print("WHATSAPP ERROR:", str(e))
        return None