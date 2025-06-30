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
OUTPUT = "data/all_frames.json"
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
        "You're an expert subtitle style extractor.\n\n"
        "🧠 YOUR TASK:\n"
        "From this image, analyze all **captioned words** on screen.\n"
        "Each captioned word may differ in style. Extract every word **individually** with full styling.\n\n"
        "===============================\n"
        "📝 RETURN JSON in this exact format:\n"
        "{\n"
        "  \"words\": [\n"
        "    {\n"
        "      \"text\": \"Hello\",               // The exact visible text, preserve case\n"
        "      \"font\": \"Montserrat Thin Italic\", // Include full font name including weight/style (e.g. Thin, Bold, SemiBold Italic)\n"
        "      \"font_size\": 58,               // Font size as number only (no px)\n"
        "      \"color\": \"#FEE440\",           // Primary font fill color in HEX (e.g. #FFFFFF)\n"
        "      \"bold\": true,                  // True if bold or heavy\n"
        "      \"italic\": true,                // True if italic, slanted, script, cursive\n"
        "      \"outline\": 2,                  // Stroke thickness if visible (0 if none)\n"
        "      \"shadow\": 1,                   // Shadow strength (0 if no shadow)\n"
        "      \"relative_position\": [1, 2]    // Position on screen: [line_number, word_order_in_line]\n"
        "    },\n"
        "    ... more words ...\n"
        "  ]\n"
        "}\n\n"
        "===============================\n"
        "🎯 STRICT STYLE DETECTION RULES:\n"
        "- ✅ Font must include family + weight + style if distinguishable (e.g., 'Poppins Bold Italic', 'Montserrat Thin')\n"
        "- ✅ Italic, slanted, script, or cursive fonts → set `italic: true`\n"
        "- ✅ Bold or heavy appearance → set `bold: true`\n"
        "- ✅ Outline: count visible outer stroke size\n"
        "- ✅ Shadow: any soft blur/drop shadow present (0 if none)\n"
        "- ✅ Position: use [line number (1=top), word number in line]\n"
        "- ✅ Font size: relative optical size if not pixel readable\n\n"
        "===============================\n"
        "📦 OUTPUT FORMAT:\n"
        "- Return **raw JSON** only.\n"
        "- No markdown, no prose, no explanation.\n"
        "- Format must be valid JSON parsable by Python.\n\n"
        "⚠️ VERY IMPORTANT: Only include visible, styled subtitle words from the image. Do not return background text, watermark, or logos."
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
