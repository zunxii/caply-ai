import json
from pathlib import Path

with open("data/all_frames.json", "r", encoding="utf-8") as f:
    all_frames = json.load(f)

def get_frame_text(frame):
    return " ".join(word["text"] for word in frame["words"]).strip()

filtered_frames = []
i = 0

while i < len(all_frames):
    current_frame = all_frames[i]
    current_text = get_frame_text(current_frame)

    if i + 1 < len(all_frames):
        next_frame = all_frames[i + 1]
        next_text = get_frame_text(next_frame)

        if current_text and current_text in next_text:
            i += 1
            continue

    filtered_frames.append(current_frame)
    i += 1

output_path = Path("output/filtered_all_frames.json")
output_path.parent.mkdir(exist_ok=True)
output_path.write_text(json.dumps(filtered_frames, indent=2, ensure_ascii=False), encoding="utf-8")

print(f" Filtered frames saved to: {output_path}")
print(f" Original: {len(all_frames)} frames → Filtered: {len(filtered_frames)} frames")
