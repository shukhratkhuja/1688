import openai
import json
import time
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Kalitlar ro'yxati: bu keylar modelga yuborilmaydi
EXCLUDED_KEYS = {"image_urls", "image_paths", "large_images"}

def remove_excluded_keys(data):
    if isinstance(data, dict):
        return {
            k: remove_excluded_keys(v)
            for k, v in data.items()
            if k not in EXCLUDED_KEYS
        }
    elif isinstance(data, list):
        return [remove_excluded_keys(item) for item in data]
    else:
        return data

def build_prompt(entry):
    filtered_entry = remove_excluded_keys(entry)
    return f"""
You are a professional e-commerce translator.

Translate the following product data from Chinese to English.

Instructions:
- Translate both keys and values in the JSON.
- Use proper e-commerce terminology.
- Keep the structure exactly the same.
- Do not add or remove fields.
- Return valid JSON.

Input:
{json.dumps(filtered_entry, ensure_ascii=False, indent=2)}
"""

def translate_entry(entry):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {"role": "system", "content": "You are a professional e-commerce translator."},
                {"role": "user", "content": build_prompt(entry)}
            ]
        )
        translated = response['choices'][0]['message']['content']
        return json.loads(translated)
    except Exception as e:
        print("❌ Error:", e)
        return None

def main():
    with open("input.json", "r", encoding="utf-8") as infile:
        data = json.load(infile)

    results = []
    for i, item in enumerate(data):
        print(f"🔄 Translating item {i+1}/{len(data)}")
        translated = translate_entry(item)
        if translated:
            # originaldan image_urls ni qaytadan qo‘shamiz
            for key in EXCLUDED_KEYS:
                if key in item:
                    translated[key] = item[key]
            results.append(translated)
        time.sleep(1.5)

    with open("output.json", "w", encoding="utf-8") as outfile:
        json.dump(results, outfile, ensure_ascii=False, indent=2)

    print("✅ All entries translated and saved to output.json")

if __name__ == "__main__":
    main()



"""
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer openai_api_key" \
  -d '{
    "model": "gpt-4o-mini",
    "store": true,
    "messages": [
      {"role": "user", "content": "write a haiku about ai"}
    ]
  }'


"""