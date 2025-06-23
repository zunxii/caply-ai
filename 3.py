import os
import openai
import base64
import json
import re
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

FOLDER = "frames"
OUTPUT = "all_frames.json"
MODEL = "gpt-4o"
MAX_FRAMES = 85

client = openai.Client(api_key=API_KEY)

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def extract_frame_number(filename):
    match = re.search(r"(\d+)", filename)
    return int(match.group(1)) if match else 0

def clean_json_text(raw):
    return re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE)

def hex_to_ass_color(hex_color):
    """Convert #RRGGBB or RRGGBB to &HBBGGRR"""
    hex_color = hex_color.replace("#", "")
    if len(hex_color) != 6:
        return "&HFFFFFF"  # Default fallback
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return f"&H{b}{g}{r}".upper()

def normalize_word(word_obj):
    return {
        "text": word_obj.get("text", ""),
        "fontname": word_obj.get("font", "Poppins"),
        "fontsize": int(word_obj.get("font_size", 48)),
        "primary_colour": hex_to_ass_color(word_obj.get("color", "#FFFFFF")),
        "bold": -1 if str(word_obj.get("bold", False)).lower() in ["true", "-1", "1"] else 0,
        "italic": -1 if str(word_obj.get("italic", False)).lower() in ["true", "-1", "1"] else 0,
        "outline": int(word_obj.get("outline", 1)),
        "shadow": int(word_obj.get("shadow", 0)),
        "relative_position": word_obj.get("relative_position", [1, 1]),
    }

def generate_prompt():
    return (
        "You're a subtitle caption analyzer. From this image, extract all styled words as JSON.\n"
        "Each word should follow this strict format:\n"
        "{\n"
        '  "text": "Hello",\n'
        '  "font": "Poppins Bold",\n'
        '  "font_size": 58,\n'
        '  "color": "#FEE440",\n'
        '  "bold": true,\n'
        '  "italic": false,\n'
        '  "outline": 2,\n'
        '  "shadow": 1,\n'
        '  "relative_position": [1, 2]  // line 1, second word\n'
        "}\n\n"
        "Return a JSON object: { words: [...] }. NO explanations or markdown formatting."
    )

def process_frames():
    frame_files = sorted([
        f for f in os.listdir(FOLDER)
        if f.lower().endswith((".jpg", ".png"))
    ], key=extract_frame_number)[:MAX_FRAMES]

    print(f"📂 Found {len(frame_files)} frames in `{FOLDER}`")

    all_data = []

    for filename in tqdm(frame_files, desc="🔍 Analyzing Frames"):
        image_path = os.path.join(FOLDER, filename)
        image_b64 = image_to_base64(image_path)

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a subtitle caption visual style extractor."
                    },
                    {
                        "role": "user",
                        "content": [
                            { "type": "text", "text": generate_prompt() },
                            {
                                "type": "image_url",
                                "image_url": { "url": f"data:image/jpeg;base64,{image_b64}" }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=1000
            )

            raw = response.choices[0].message.content
            cleaned = clean_json_text(raw)
            json_data = json.loads(cleaned)

            words = json_data.get("words", [])
            normalized_words = [normalize_word(word) for word in words]

            all_data.append({
                "frame": filename,
                "words": normalized_words
            })

        except Exception as e:
            print(f" Error in {filename}: {e}")

    with open(OUTPUT, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f" Saved all frame data to `{OUTPUT}`")

if __name__ == "__main__":
    process_frames()
