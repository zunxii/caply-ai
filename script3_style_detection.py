import os
import base64
import json
from pathlib import Path
import re
from tqdm import tqdm
from dotenv import load_dotenv
import openai

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
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
    hex_color = hex_color.replace("#", "")
    if len(hex_color) != 6:
        return "&HFFFFFF"
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
    return Path("prompts/frame_style_prompt.txt").read_text(encoding="utf-8")

def analyze_frames(folder: str, output_path: str, max_frames: int = 85):
    files = sorted([
        f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png"))
    ], key=extract_frame_number)[:max_frames]

    print(f"🎨 Processing {len(files)} frames in '{folder}'")
    all_data = []

    for filename in tqdm(files, desc="Analyzing Frames"):
        image_path = os.path.join(folder, filename)
        image_b64 = image_to_base64(image_path)

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a subtitle caption visual style extractor."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": generate_prompt()},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=1000
            )

            raw = response.choices[0].message.content
            cleaned = clean_json_text(raw)
            words = json.loads(cleaned).get("words", [])
            normalized = [normalize_word(word) for word in words]

            all_data.append({"frame": filename, "words": normalized})

        except Exception as e:
            print(f" Error on {filename}: {e}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2)

    print(f" Frame style data saved to: {output_path}")