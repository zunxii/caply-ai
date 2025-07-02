import json
def apply_template_styles(data, total_styles=3, threshold=0.15, default_style="style3"):
    """
    Applies styling based on style_order and priority_value differences in each chunk.
    
    Parameters:
    - data: list of chunks (your processed transcription)
    - total_styles: number of style types defined in template
    - threshold: minimum difference in priority_value to trigger style assignment
    - default_style: style to use when chunk is uniform
    """
    i = 0
    for chunk in data:
        words = chunk["words"]
        dialog = chunk["dialog"]
        priority_values = [w["priority_value"] for w in words]
        
        max_p = max(priority_values)
        min_p = min(priority_values)
        delta = max_p - min_p
        if delta > threshold:
            i = i+1
            for word in words:
                if 1 <= word["style_order"] <= total_styles - 1:
                    word["style"] = f"style{word['style_order']}"
                else:
                    word["style"] = default_style
        else:
            print(dialog)
            for word in words:
                word["style"] = default_style
    print(i)
    return data

with open("styled_chunks_with_timestamps.json", "r", encoding="utf-8") as f:
    styled_chunks = json.load(f)

# Apply your style template logic
styled_chunks_with_style = apply_template_styles(
    styled_chunks,
    total_styles=4,        # define 3 styles (style1, style2, style3), style4 as default
    threshold=0.15,        # tweak this based on how expressive chunks are
    default_style="style4" # fallback if uniform
)

# Save updated version with styles
with open("styled_output_with_templates.json", "w", encoding="utf-8") as f:
    json.dump(styled_chunks_with_style, f, indent=2, ensure_ascii=False)

print("✅ Styles applied and saved to styled_output_with_templates.json")