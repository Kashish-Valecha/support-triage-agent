import os
import json
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
hf_token = os.getenv('HF_TOKEN')

SYSTEM_PROMPT = """You are a support triage agent.
Respond with JSON only."""

prompt = f'{SYSTEM_PROMPT}\n\nTICKET: How do I reset my password in Claude?\n\nContext: Password reset docs here.\n\nRespond with JSON object only.'

print("Testing Gemma chat_completion API...")

try:
    client = InferenceClient(token=hf_token)
    
    response = client.chat_completion(
        model='google/gemma-2-2b-it',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=150,
        temperature=0.3,
    )
    
    response_text = response['choices'][0]['message']['content']
    print('\n✓ API Response received!')
    print(f'Response (first 250 chars): {response_text[:250]}')
    
    # Try to parse JSON
    if '{' in response_text:
        json_start = response_text.index('{')
        json_str = response_text[json_start:]
        if '}' in json_str:
            json_end = json_str.rindex('}') + 1
            json_str = json_str[:json_end]
            parsed = json.loads(json_str)
            print('\n✓ JSON parsed successfully!')
            print(f'Status: {parsed.get("status")}')
            print(f'Product Area: {parsed.get("product_area")}')
    else:
        print('Note: No JSON found in response')
        
except Exception as e:
    import traceback
    print(f'\n✗ ERROR: {type(e).__name__}: {e}')
    traceback.print_exc()
