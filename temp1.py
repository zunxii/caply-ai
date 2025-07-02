import json
import re
from openai import OpenAI

# Load your transcription JSON (adjust the path if needed)
with open("data/input_transcription_with_energy.json", "r") as f:
    transcription_data = json.load(f)

# Flatten transcription into plain text
transcript_text = " ".join([segment["text"] for segment in transcription_data])

# Initialize OpenAI client with your API key
client = OpenAI(api_key="your-key")

# Define the system prompt (refined and strict)
system_prompt = """
You are an AI assistant that transforms transcribed video data into stylized caption chunks for vertical short-form videos (Instagram Reels, TikToks, YouTube Shorts).

Each input is a list of word-level transcription objects with the following **EXACT** structure:
- `text`: the spoken word
- `start`: word start time in milliseconds
- `end`: word end time in milliseconds
- `energy`: vocal energy of the speaker during the word (float)

---

🎯 YOUR GOAL:

Output a JSON list of caption chunks. Each chunk must follow this format exactly:

[
  {
    "dialog": "<concatenated string of words>",
    "start": <start time of first word (copy from input transcription)>,
    "end": <end time of last word (copy from input transcription)>,
    "words": [
      {
        "word": "<word text, same as input>",
        "priority_value": <float between 0.00 and 1.00>,
        "style_order": <integer ≥ 1>,
      },
      ...
    ]
  },
  ...
]

---

🛑 ABSOLUTELY NON-NEGOTIABLE RULES:

1. **Preserve word order**:
   - The `words` field must maintain the exact sequence from the input.
   - Do not omit or alter any word.
   - Do not invent punctuation.

2. **Chunking rules**:
   - Each chunk should contain **2 to 4 consecutive words** (5 if required).
   - Start a new chunk if:
     • A pause > 120ms between two words
     • Sharp energy drop (from ≥ 0.6 to ≤ 0.3)
     • Punctuation like `. , ? !` is found
     • Clear clause/sentence or meaning shift

3. **Styling rules**:
   - Assign a `priority_value` (0.00–1.00) to each word.
   - Assign a `style_order` (1 = highest importance).
   - Filler/low-impact words must have low priority and higher style_order (like 3 or 4).
   - You must assign fewer words to `style_order = 1` than to `style_order = 2` in each chunk.

---

🔥 STYLING LOGIC (APPLY CAREFULLY):

You MUST compute a `priority_value` and `style_order` for **every word** based on the following criteria:

✅ `priority_value` (range: 0.00 to 1.00):
- 0.8 to 1.0 → Strong emphasis (high-energy, emotionally charged, or meaningful words)
- 0.5 to 0.79 → Moderate importance (nouns, verbs, adjectives with moderate energy)
- 0.2 to 0.49 → Filler or connector words (“with”, “just”, “and”, etc.)
- 0.0 to 0.19 → Very low-impact words (“a”, “the”, “in”)

✅ `style_order`:
- **1** → Top-tier emphasis (highest energy + impact)
- **2** → Supporting important words (medium energy or emotional relevance)
- **3** → Default text (common, less important)
- **4+** → Filler, connectors, low energy (use this to visually de-emphasize)


🚫 DO NOT:
- Rearrange or skip words
- Return markdown, explanations, or any other formatting
- Add or infer words not present in the input

---

✅ YOUR OUTPUT MUST:
- Be a single valid JSON array
- Use the input word list **as-is** and **in-order**
- Retain all input timestamps **verbatim**
- Reflect real energy-based and pause-based boundaries

You are not allowed to make any assumptions. Copy timestamps exactly. Be deterministic, accurate, and structured. Return only the JSON output.
"""

# Create the chat completion
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcript_text}
    ],
    temperature=0.4
)

# Extract response content
output_text = response.choices[0].message.content

# Try to parse JSON
try:
    # First attempt: direct parse
    styled_chunks = json.loads(output_text)
except json.JSONDecodeError:
    print(" JSON decode failed — attempting cleanup...")

    # --- Cleaning Filter ---
    cleaned_output = output_text.strip()

    # Remove Markdown code block markers like ```json or ```
    cleaned_output = re.sub(r"^```(?:json)?", "", cleaned_output, flags=re.MULTILINE)
    cleaned_output = re.sub(r"```$", "", cleaned_output, flags=re.MULTILINE)

    # Remove trailing commas before ] or }
    cleaned_output = re.sub(r",(\s*[}\]])", r"\1", cleaned_output)

    # Remove extra whitespace or invisible characters
    cleaned_output = cleaned_output.replace('\u200b', '').strip()

    try:
        styled_chunks = json.loads(cleaned_output)
        print(" Cleaned and parsed JSON successfully.")
    except json.JSONDecodeError as e:
        print(" Still failed after cleanup:")
        print(cleaned_output[:500])  # print the start of malformed output for inspection
        raise e  # re-raise for visibility

#  Save to file if everything worked
with open("styled_output.json", "w", encoding="utf-8") as outfile:
    json.dump(styled_chunks, outfile, indent=2, ensure_ascii=False)

print(" Output saved to styled_output.json")