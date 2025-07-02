import json
from datetime import timedelta

# === Load caption chunks ===
with open("styled_output_with_templates.json", "r") as f:
    caption_chunks = json.load(f)

# === Load styles from demo_data.json ===
with open("demo_data.json", "r") as f:
    raw_styles = json.load(f)

# Create style lookup dictionary from demo_data.json
styles = {style["name"].lower(): style for style in raw_styles}

# === Convert milliseconds to ASS time format ===
def ms_to_ass_time(ms):
    t = timedelta(milliseconds=ms)
    return f"{int(t.total_seconds() // 3600)}:{int((t.total_seconds() % 3600) // 60):02}:{int(t.total_seconds() % 60):02}.{int(t.microseconds / 10000):02}"

# === ASS Header ===
ass_header = """[Script Info]
Title: Styled Subtitles
ScriptType: v4.00+
Collisions: Normal
PlayResY: 720
PlayResX: 1280
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, Bold, Italic, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""

# === Generate [V4+ Styles] from demo_data.json ===
style_lines = []
for s in raw_styles:
    style_lines.append(
        f"Style: {s['name']},{s['fontname']},{s['fontsize']},{s['primary_colour']},{s['bold']},{s['italic']},{s['outline']},{s['shadow']},2,10,10,10,1"
    )

# === ASS [Events] Header ===
event_header = """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# === Generate Dialogue Lines ===
events = []

for chunk in caption_chunks:
    words = chunk["words"]
    chunked_words = [words[i:i + 4] for i in range(0, len(words), 4)]  # max 4 words per line

    for subchunk in chunked_words:
        start_time = ms_to_ass_time(subchunk[0]["start"])
        end_time = ms_to_ass_time(subchunk[-1]["end"])
        text_parts = []

        for word in subchunk:
            style_name = word["style"].lower()
            s = styles[style_name]  # Guaranteed to be present

            styled_word = (
                "{\\fn" + s["fontname"] +
                f"\\fs{s['fontsize']}\\c{ s['primary_colour'] }" +
                ("\\b1" if s["bold"] == -1 else "") +
                f"\\shad{s['shadow']}}}" + word["word"]
            )

            text_parts.append(styled_word)

        dialogue = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{' '.join(text_parts)}"
        events.append(dialogue)

# === Write to ASS file ===
with open("output_subtitles.ass", "w", encoding="utf-8") as f:
    f.write("\n".join([ass_header, *style_lines, event_header, *events]))

print("✅ Subtitle file created: output_subtitles.ass")
