import json
from pathlib import Path

def get_frame_text(frame):
    return " ".join(word["text"] for word in frame["words"]).strip()

def filter_duplicate_frames(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        all_frames = json.load(f)

    filtered_frames = []
    i = 0

    while i < len(all_frames):
        current = all_frames[i]
        current_text = get_frame_text(current)

        if i + 1 < len(all_frames):
            next_text = get_frame_text(all_frames[i + 1])
            if current_text and current_text in next_text:
                i += 1
                continue

        filtered_frames.append(current)
        i += 1

    Path(output_path).parent.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filtered_frames, f, indent=2, ensure_ascii=False)

    print(f" Filtered frames saved: {output_path}")
    print(f" Original: {len(all_frames)} → Filtered: {len(filtered_frames)}")
