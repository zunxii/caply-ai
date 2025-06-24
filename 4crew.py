from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from pathlib import Path
import json
import re

# === Utility ===
def ms_to_ass_time(ms: int) -> str:
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    cs = (ms % 1000) // 10
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def truncate_json(data, max_chars=12000):
    full = json.dumps(data)
    return full if len(full) <= max_chars else full[:max_chars]

def clean_output(raw: str) -> str:
    return re.sub(r"^```(?:json|ass)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

# === Load Data ===
with open("data/all_frames.json", "r", encoding="utf-8") as f:
    all_frames = json.load(f)

with open("data/ref_transcription_with_energy.json", "r", encoding="utf-8") as f:
    ref_transcription = json.load(f)

with open("data/input_transcription_with_energy.json", "r", encoding="utf-8") as f:
    input_transcription = json.load(f)

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# === Agents ===
style_template_extractor = Agent(
    role="Style Template Extractor",
    goal="Extract rich, detailed subtitle style templates from a reference video.",
    backstory="A subtitle stylist who decodes recurring visual design patterns across a video and labels them into reusable, mood-aware templates.",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

chunker_agent = Agent(
    role="Reel Subtitle Chunking Expert",
    goal="Divide transcription into naturally expressive, reel-optimized caption chunks.",
    backstory="An expert in subtitle pacing for vertical video formats who chunks based on audio energy, emotion, semantics, punctuation, and rhythm.",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

style_assigner = Agent(
    role="ASS Formatter and Template Styler",
    goal="Assign styles to chunks and render valid .ASS subtitles with inline word-level formatting.",
    backstory="A subtitle compositor that builds professional-quality captions using assigned word styles per chunk, ensuring cinematic flow.",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# === TASKS ===

extract_templates_task = Task(
    name="extract_templates",
    description=(
        f"Analyze:\n"
        f"- Frame-wise subtitle styles from: {truncate_json(all_frames)}\n"
        f"- Matching transcription entries: {truncate_json(ref_transcription)}\n\n"
        
        "Your job is to extract **subtitle style templates**. A template defines the word-level layout and appearance of a stylized subtitle from visually identical frames.\n\n"
        
        "====================================\n"
        "🎨 STYLE MATCHING RULES (STRICT)\n"
        "====================================\n"
        "Only group frames together as a single template if:\n"
        "✔️ Every word in the frame matches EXACTLY in:\n"
        "   - fontname, fontsize, bold, italic, outline, shadow\n"
        "   - primary_colour (convert RGB to &HBBGGRR)\n"
        "   - relative_position (must be same for each word in sequence)\n"
        "✔️ Word **count and order** is identical\n"
        "✔️ All style attributes align 1-to-1 per word\n"
        "🚫 DO NOT group frames based on partial visual similarity or approximation\n\n"

        "====================================\n"
        "🔍 FOR EACH TEMPLATE RETURN:\n"
        "====================================\n"
        "- template_name: short, expressive (e.g. 'bold-yellow-hype-3w')\n"
        "- exact_word_count: integer\n"
        "- usage_frequency: count of frames using it\n"
        "- mood: label the emotion or intensity (e.g. 'calm', 'assertive', 'urgent')\n"
        "- sentence_relation: ideal part of sentence (intro, CTA, emphasis, question, etc.)\n"
        "- usage_condition: deeply specific; e.g. 'when emphasizing call-to-action with rising intonation and high energy ending'\n"
        "- style_structure: one style object per word with full metadata:\n"
        "  • fontname, fontsize, bold, italic, outline, shadow, relative_position, primary_colour\n"
        "- default_layout: describe the layout visually (e.g. 'center-aligned, 2-line stacked with italic highlight last')\n"
        "- sample_frames: list of 3–5 frame IDs from the dataset used in this group\n\n"
        "Return full JSON array of templates only."
    ),
    expected_output="Detailed reusable subtitle style templates.",
    agent=style_template_extractor
)

chunk_task = Task(
    name="chunk_transcription",
    description=(
        f"You're given transcription with energy data:\n{truncate_json(input_transcription)}\n\n"
        "Each word has:\n"
        "- text\n- start (ms)\n- end (ms)\n- energy (float between 0–1)\n\n"

        "====================================\n"
        "🎬 REEL-CENTRIC SUBTITLE CHUNKING\n"
        "====================================\n"
        "Create expressive chunks for **short-form vertical videos** (Instagram, Reels, TikTok). These subtitles must feel natural, rhythmic, and emotionally responsive. \n\n"
        "KEY RULES:\n"
        "• Preferred chunk size: 2–4 words (max 5)\n"
        "• NEVER isolate a single word unless for strong effect\n"
        "• Chunks must reflect speaking rhythm, emotional inflection, and visual pacing\n\n"
        "BREAK CHUNKS WHEN:\n"
        "✔️ Pause > 120ms (hard rule), OR even smaller (e.g. 10ms) if there’s visible energy shift\n"
        "✔️ Significant energy dip/drop between words (e.g. 0.6 → 0.2)\n"
        "✔️ Punctuation: '.', '?', '!', ','\n"
        "✔️ Semantic change — new clause, emphasized point, call-to-action\n"
        "✔️ Word importance: isolate strong verbs/adjectives for effect\n"
        "✔️ Emotional impact: rising tone, urgency, suspense, curiosity\n\n"
        "NOTE:\n"
        "- Use start_time of **first word**, end_time of **last word**\n"
        "- Combine energy, semantic, and timing logic — don’t rely on just one\n\n"
        "====================================\n"
        "🧾 FOR EACH CHUNK RETURN:\n"
        "====================================\n"
        "- chunk_text\n"
        "- start_time (ms)\n"
        "- end_time (ms)\n"
        "- words: list of word texts\n"
        "- mood: infer from context and energy (e.g. 'curious', 'intense', 'playful')\n"
        "- sentence_relation: 'start', 'middle', 'end', or 'standalone'\n\n"
        "Return a clean JSON array of chunks only. No markdown or prose."
    ),
    expected_output="High-quality, expressive chunks optimized for reel display.",
    agent=chunker_agent
)

assign_styles_task = Task(
    name="assign_templates",
    description=(
        "You're given:\n"
        "- A set of subtitle style templates (word-level styles and metadata)\n"
        "- Subtitle chunks (with text, timing, mood, and role)\n\n"
        "====================================\n"
        "🎯 OBJECTIVE: STYLED .ASS GENERATION\n"
        "====================================\n"
        "1. Match each chunk with the best template:\n"
        "   - Match exact word count\n"
        "   - Mood compatibility (template.mood ≈ chunk.mood)\n"
        "   - sentence_relation compatibility\n"
        "   - usage_condition fit\n"
        "2. Apply inline styling to **each word**, not entire chunk\n"
        "3. All subtitles must be **center-aligned** and styled precisely\n"
        "4. Every template must be used at least once\n\n"
        "====================================\n"
        "🧾 ASS OUTPUT FILE FORMAT\n"
        "====================================\n"
        "[Script Info]\n"
        "  Title: Styled Subtitle Output\n"
        "  PlayResX: 1920\n"
        "  PlayResY: 1080\n"
        "  WrapStyle: 2\n"
        "  ScaledBorderAndShadow: yes\n"
        "  Collisions: Normal\n\n"
        "[V4+ Styles]\n"
        "  Format line\n"
        "  One entry per unique word style (across all templates)\n\n"
        "[Events]\n"
        "  Format line\n"
        "  One dialogue line per chunk:\n"
        "  Dialogue: 0,start,end,Style,,0,0,0,,{\\style1}word1 {\\style2}word2 ...\n\n"
        "Use precise `ms_to_ass_time(ms)` formatting for time.\n"
        "Return full .ASS content only (no markdown)."
    ),
    expected_output="Final .ass file with proper styles per word and accurate timings.",
    agent=style_assigner
)

# === Crew Setup ===
crew = Crew(
    agents=[style_template_extractor, chunker_agent, style_assigner],
    tasks=[extract_templates_task, chunk_task, assign_styles_task],
    verbose=True,
    return_intermediate_steps=True
)

# === Run Pipeline ===
results = crew.kickoff()
task_outputs = results.tasks_output

# === Save Output ===
Path("output").mkdir(exist_ok=True)

with open("output/templates.json", "w", encoding="utf-8") as f:
    f.write(clean_output(task_outputs[0].raw))

with open("output/chunks.json", "w", encoding="utf-8") as f:
    f.write(clean_output(task_outputs[1].raw))

with open("output/styled_output.ass", "w", encoding="utf-8") as f:
    f.write(clean_output(task_outputs[2].raw))

print("✅ All files saved: templates.json, chunks.json, styled_output.ass")
