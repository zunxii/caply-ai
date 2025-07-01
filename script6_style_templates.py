import json
from pathlib import Path
import hashlib
import numpy as np

def style_hash(style_dict):
    relevant = {
        k: style_dict[k] for k in ["fontname", "fontsize", "primary_colour", "bold", "italic", "outline", "shadow"]
    }
    return hashlib.md5(json.dumps(relevant, sort_keys=True).encode()).hexdigest()

def normalize_font_sizes(frames):
    sizes = []
    for frame in frames:
        for word in frame["words"]:
            size = word.get("fontsize", 0)
            if isinstance(size, (int, float)) and size > 0:
                sizes.append(size)

    if not sizes:
        return {}

    # Use percentiles to split into 5 levels
    thresholds = np.percentile(sizes, [20, 40, 60, 80])
    size_map = {}

    def map_size(original):
        if original <= thresholds[0]:
            return 24  # xs
        elif original <= thresholds[1]:
            return 28  # s
        elif original <= thresholds[2]:
            return 32  # m
        elif original <= thresholds[3]:
            return 40  # l
        else:
            return 48  # xl

    for size in set(sizes):
        size_map[size] = map_size(size)

    return size_map

def extract_styles(frames_path: str, template_output: str, map_output: str):
    frames = json.load(open(frames_path, encoding="utf-8"))

    size_map = normalize_font_sizes(frames)

    style_templates = []
    template_lookup = {}
    frame_style_map = {}
    style_index = 1

    for frame in frames:
        fname = frame["frame"]
        frame_num = int(Path(fname).stem.split("_")[1])
        frame_time_ms = frame_num * (1000 // 2)

        styles = []
        positions = []

        for word in frame["words"]:
            x, y = word.get("relative_position", [0, 0])
            raw_size = word.get("fontsize", 0)
            normalized_size = size_map.get(raw_size, 32)  # default to 'm' size if missing

            style_key = {
                "fontname": word.get("fontname", ""),
                "fontsize": normalized_size,
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
                    "fontsize": style_key["fontsize"],
                    "primary_colour": style_key["primary_colour"],
                    "bold": style_key["bold"],
                    "italic": style_key["italic"],
                    "outline": style_key["outline"],
                    "shadow": style_key["shadow"],
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

    Path(template_output).write_text(json.dumps(style_templates, indent=2), encoding="utf-8")
    Path(map_output).write_text(json.dumps(frame_style_map, indent=2), encoding="utf-8")

    print("✅ Saved style templates and mapping with normalized font sizes.")
