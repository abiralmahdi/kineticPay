import requests

url = "http://192.168.68.72:8000/api/sms-webhook/"

payload = {
    "api_key": "7dfb81be-1526-4bb2-8a9e-a201f7bd35eb",
    "sender": "bkash",
    "message": (
        "Cash In Tk. 1500 received from 01769025257. "
        "Fee Tk. 0.00. Balance Tk. 12,450.00. "
        "TrxID AAA111BBC at 10/06/2026 07:45PM."
    )
}

response = requests.post(
    url,
    json=payload
)

print("Status Code:", response.status_code)
print("Response:")
print(response.text)