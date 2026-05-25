import os
from cerebras.cloud.sdk import Cerebras

api_key = "csk-mc4ce8w4kv9kvm3hy8hxydwjd5e5yr9fdj8pkmcvcyp35xdw"
client = Cerebras(api_key=api_key)

prompt = """Return ONLY a JSON array with 2 objects:
[
  {"id": 1, "status": "Replied", "area": "Billing"},
  {"id": 2, "status": "Escalated", "area": "General"}
]"""

print("Testing Cerebras API with simple JSON request...")
try:
    response = client.chat.completions.create(
        model="qwen-3-235b-a22b-instruct-2507",
        messages=[{"role": "user", "content": prompt}],
    )
    
    print("Response type:", type(response))
    print("Response choices:", response.choices)
    print("\nRaw content:")
    print(repr(response.choices[0].message.content))
    print("\nFormatted content:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
