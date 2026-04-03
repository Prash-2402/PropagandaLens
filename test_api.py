import urllib.request
import json
import sys

url = "https://propagandalens.onrender.com/analyze"
data = json.dumps({"text": "This is a simple test."}).encode("utf-8")
headers = {"Content-Type": "application/json"}

try:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        print("STATUS CODE:", response.status)
        print("RESPONSE:", response.read().decode('utf-8')[:500])
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code)
    print("ERROR BODY:", e.read().decode('utf-8'))
except Exception as e:
    print("ERROR:", str(e))
