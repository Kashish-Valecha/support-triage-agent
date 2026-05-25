import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
hf_token = os.getenv('HF_TOKEN')

client = InferenceClient(token=hf_token)
print("Testing HuggingFace chat_completion API...")

response = client.chat_completion(
    model='HuggingFaceH4/zephyr-7b-beta',
    messages=[{'role': 'user', 'content': 'What is 2+2? Respond with just the number.'}],
    max_tokens=50,
    temperature=0.3
)

print('✓ API works!')
print('Response:', response['choices'][0]['message']['content'])
