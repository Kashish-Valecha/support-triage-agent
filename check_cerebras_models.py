import os
from cerebras.cloud.sdk import Cerebras

api_key = "csk-mc4ce8w4kv9kvm3hy8hxydwjd5e5yr9fdj8pkmcvcyp35xdw"
client = Cerebras(api_key=api_key)

# Try to list available models
try:
    models = client.models.list()
    print("Available models:")
    print(f"Type: {type(models)}")
    print(f"Content: {models}")
    if isinstance(models, (list, tuple)):
        for i, model in enumerate(models):
            print(f"  [{i}] {model}")
except Exception as e:
    print(f"Error listing models: {e}")
    
    # Try a test request with a generic model name
    print("\nTrying alternative model names...")
    test_models = [
        "llama-3.3-70b",
        "llama-3.1-70b",
        "llama-3-70b",
        "llama3-70b",
        "llama-70b",
        "gpt-4",
        "claude",
    ]
    
    for model_name in test_models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello"}],
            )
            print(f"✓ Model '{model_name}' works!")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg or "not found" in error_msg:
                print(f"✗ Model '{model_name}' - not found")
            else:
                print(f"✗ Model '{model_name}' - error: {error_msg[:80]}")
