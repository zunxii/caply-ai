import json
from pathlib import Path

def ms_to_ass_time(ms):
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    cs = (ms % 1000) // 10
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def generate_ass_file(chunks_path: str, style_seq_path: str, templates_path: str, output_path: str, log_path: str):
    chunks = json.load(open(chunks_path, encoding="utf-8"))
    style_seq = json.load(open(style_seq_path, encoding="utf-8"))
    templates = json.load(open(templates_path, encoding="utf-8"))

    template_lookup = {t["name"]: t for t in templates}

    def find_matching_frame(avg_time, word_count):
        closest_frame = None
        closest_diff = float("inf")
        for frame_name, data in style_seq.items():
            if len(data["styles"]) != word_count:
                continue
            frame_time = data.get("time_ms", None)
            if frame_time is None:
                continue
            diff = abs(frame_time - avg_time)
            if diff < closest_diff:
                closest_diff = diff
                closest_frame = (frame_name, data)
        return closest_frame

    ass_lines = []
    log_lines = []

    for chunk in chunks:
        start = chunk["start_time"]
        end = chunk["end_time"]
        words = chunk["words"]
        avg_time = (start + end) // 2

        matched = find_matching_frame(avg_time, len(words))
        if not matched:
            print(f"⚠️ Skipping chunk: {chunk['chunk_text']}")
            continue

        frame_name, data = matched
        frame_styles = data["styles"]
        frame_positions = data["positions"]

        ass_text = ""
        last_row = None
        log_entry = f"Chunk: \"{chunk['chunk_text']}\"\nFrame: {frame_name} @ {data['time_ms']} ms\n"

        for word, style_name, pos in zip(words, frame_styles, frame_positions):
            row = pos[0]
            if last_row is not None and row != last_row:
                ass_text += r"\N"

            t = template_lookup[style_name]
            override = f"{{\\fn{t['fontname']}\\fs{t['fontsize']}\\c{t['primary_colour']}"
            if t['bold'] == -1:
                override += "\\b1"
            if t['italic'] == -1:
                override += "\\i1"
            if t['shadow'] > 0:
                override += f"\\shad{t['shadow']}"
            override += "}"

            ass_text += override + word + " "
            last_row = row
            log_entry += f"  - {word}: {style_name}\n"

        ass_text = ass_text.strip()
        ass_line = f"Dialogue: 0,{ms_to_ass_time(start)},{ms_to_ass_time(end)},Default,,0,0,0,,{ass_text}"
        ass_lines.append(ass_line)
        log_lines.append(log_entry + "\n")

    ass_header = """[Script Info]
Title: Styled Subtitles
ScriptType: v4.00+
Collisions: Normal
PlayResY: 720
PlayResX: 1280
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, Bold, Italic, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,24,&HFFFFFF,-1,0,0,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    Path(output_path).write_text(ass_header + "\n" + "\n".join(ass_lines), encoding="utf-8")
    Path(log_path).write_text("\n".join(log_lines), encoding="utf-8")

    print(f" .ASS saved: {output_path}")
    print(f" Logs saved: {log_path}")
