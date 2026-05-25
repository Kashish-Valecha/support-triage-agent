import google.generativeai as genai
import json
import csv
from pathlib import Path

# Load one batch of tickets
tickets = []
with open('support_tickets/support_tickets.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i < 3:  # Just first 3 tickets for debugging
            tickets.append(row)

genai.configure(api_key='AIzaSyBmqQgvTHbGPuKpPwNghsb1688O64DN2B8')
model = genai.GenerativeModel('gemini-2.5-flash')

# Simple prompt for testing
prompt = """You are a support triage agent. For each ticket below, respond with a JSON array.

TICKET #1:
Subject: Screen doesn't load
Company: HackerRank
Issue: The platform screen isn't rendering

TICKET #2:
Subject: Feature request
Company: Claude
Issue: Can we add dark mode?

TICKET #3:
Subject: Payment issue
Company: Visa
Issue: Card charged twice

Please respond with ONLY a JSON array (no markdown, no extra text) with one object per ticket:
[
  {"ticket_num": 1, "status": "Replied or Escalated", "product_area": "short name"},
  ...
]"""

print("Sending request to Gemini API...")
response = model.generate_content(prompt)
print(f"Raw response:\n{response.text}\n")
print(f"Response length: {len(response.text)}")

# Try to strip and parse
response_text = response.text.strip()
print(f"\nAfter strip:\n{response_text[:500]}\n")

if response_text.startswith("```"):
    response_text = response_text.split("```")[1]
    if response_text.startswith("json"):
        response_text = response_text[4:].strip()
    print(f"\nAfter markdown removal:\n{response_text[:500]}\n")

# Try to parse
try:
    data = json.loads(response_text)
    print(f"✓ Successfully parsed as JSON")
    print(f"Type: {type(data)}")
    print(f"Content: {data}")
except json.JSONDecodeError as e:
    print(f"✗ JSON parsing failed: {e}")
    # Try to find the issue
    lines = response_text.split('\n')
    for i, line in enumerate(lines[:10]):
        print(f"Line {i}: {repr(line)}")
