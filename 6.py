import json
from pathlib import Path
import hashlib

frames = json.load(open("data/all_frames.json", encoding="utf-8"))

style_templates = []
template_lookup = {}
frame_style_map = {}

def style_hash(style_dict):
    """Generate a unique hash based on style properties."""
    relevant = {
        k: style_dict[k]
        for k in ["fontname", "fontsize", "primary_colour", "bold", "italic", "outline", "shadow"]
    }
    return hashlib.md5(json.dumps(relevant, sort_keys=True).encode()).hexdigest()

style_index = 1
for frame in frames:
    fname = frame["frame"]
    frame_num = int(Path(fname).stem.split("_")[1])
    frame_time_ms = frame_num * (1000 // 2)

    styles = []
    positions = []

    for word in frame["words"]:
        x, y = word.get("relative_position", [0, 0])
        style_key = {
            "fontname": word.get("fontname", ""),
            "fontsize": word.get("fontsize", 0),
            "primary_colour": word.get("primary_colour", ""),
            "bold": word.get("bold", 0),
            "italic": word.get("italic", 0),
            "outline": word.get("outline", 0),
            "shadow": word.get("shadow", 0),
            "x": x,
            "y": y
        }

        h = style_hash(style_key)
        if h not in template_lookup:
            style_name = f"Style_{style_index}"
            style_index += 1
            template = {
                "name": style_name,
                "fontname": style_key["fontname"],
                "fontsize": int(style_key["fontsize"]),
                "primary_colour": style_key["primary_colour"],
                "bold": int(style_key["bold"]),
                "italic": int(style_key["italic"]),
                "outline": int(style_key["outline"]),
                "shadow": int(style_key["shadow"]),
                "relative_position": [x, y]
            }
            template_lookup[h] = style_name
            style_templates.append(template)

        styles.append(template_lookup[h])
        positions.append([x, y])

    frame_style_map[fname] = {
        "time_ms": frame_time_ms,
        "styles": styles,
        "positions": positions
    }

Path("output").mkdir(exist_ok=True)
Path("output/templates.json").write_text(json.dumps(style_templates, indent=2), encoding="utf-8")
Path("output/style_sequence_by_frame.json").write_text(json.dumps(frame_style_map, indent=2), encoding="utf-8")

print("Done:")
print("  → output/templates.json (all unique styles)")
print("  → output/style_sequence_by_frame.json (per-frame styles + positions + time)")
