import os

def write_ass_file(dialogues, styles, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, Bold, Italic, Alignment, MarginL, MarginR, MarginV, Outline, Shadow, BorderStyle, Encoding
"""

    style_lines = ""
    for style in styles:
        s = style['style']
        style_lines += (
            f"Style: {style['template_name']},{s.get('fontname', 'Arial')},{s.get('fontsize', 48)},"
            f"{s.get('color', '&H00FFFFFF')},0,0,{s.get('alignment', 2)},"
            f"10,10,30,1,0,1,1\n"
        )

    events_header = """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = ""
    for d in dialogues:
        start = ms_to_ass_time(d['start'])
        end = ms_to_ass_time(d['end'])
        text = d['text'].replace("\n", "\\N")
        style = d['style']
        dialogue_lines += f"Dialogue: 0,{start},{end},{style},,0,0,0,,{text}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header + style_lines + events_header + dialogue_lines)

def ms_to_ass_time(ms):
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    cs = (ms % 1000) // 10
    return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"
