import google.generativeai as genai

genai.configure(api_key='AIzaSyBmqQgvTHbGPuKpPwNghsb1688O64DN2B8')
model = genai.GenerativeModel('gemini-2.5-flash')

print("Testing simple API call...")
response = model.generate_content("Respond with JSON: {\"test\": \"value\"}")
print(f"Response object type: {type(response)}")
print(f"Response.text: '{response.text}'")
print(f"Response.text length: {len(response.text)}")
print(f"Response.text is empty: {not response.text or not response.text.strip()}")

if hasattr(response, 'finish_reason'):
    print(f"finish_reason: {response.finish_reason}")

if hasattr(response, 'prompt_feedback'):
    print(f"prompt_feedback: {response.prompt_feedback}")

# Try with safety settings
print("\nTesting with relaxed safety settings...")
response2 = model.generate_content(
    "Respond with JSON object with 10 support ticket triages",
    safety_settings=[
        {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_NONE'},
        {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_NONE'},
        {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_NONE'},
        {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_NONE'},
    ]
)
print(f"Response2.text length: {len(response2.text)}")
print(f"Response2: {response2.text[:200]}")
