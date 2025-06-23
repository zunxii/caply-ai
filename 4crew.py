from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from pathlib import Path
import json
import re
import textwrap

# === Utility: Convert ms to .ass time format ===
def ms_to_ass_time(ms: int) -> str:
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    cs = (ms % 1000) // 10  # hundredths of a second
    return f"{h}:{m:02}:{s:02}.{cs:02}"

# === Load input data ===
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
    goal="Extract reusable subtitle style templates from a reference video.",
    backstory="A cinematic subtitle designer who reverse-engineers subtitle visual styles into modular, reusable templates.",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

chunker_agent = Agent(
    role="Transcription Chunker",
    goal="Chunk transcriptions into subtitle-sized blocks using pause, energy dips, and reference density.",
    backstory="An expert at identifying subtitle grouping based on natural pauses and energy shifts.",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

style_assigner = Agent(
    role="Template Assigner and ASS Generator",
    goal="Assign templates to chunks and convert them into valid .ass subtitle format.",
    backstory="A subtitle rendering engine that understands cinematic layout and applies style templates to create professional subtitle files.",
    llm=llm,
    verbose=True,
    allow_delegation=False
)

# === Prompt Preparation with full JSON safely truncated ===
def truncate_json(data, max_chars=12000):
    full = json.dumps(data)
    if len(full) <= max_chars:
        return full
    return full[:max_chars]

# === Tasks ===

extract_templates_task = Task(
    name="extract_templates",
    description=(
        "You are analyzing subtitle frame style data and transcription with energy values.\n\n"
        f"Frames JSON:\n{truncate_json(all_frames)}\n\n"
        f"Reference Transcription:\n{truncate_json(ref_transcription)}\n\n"
        "Instructions:\n"
        "1. Align transcription words with frames based on timestamp.\n"
        "2. Identify 5–6 style templates with:\n"
        "- template_name, usage_condition, sentence_relation, mood, usage_frequency, exact_word_count,\n"
        "- style_structure: [{fontname, fontsize, color, bold, italic, shadow, relative_position}]\n"
        "- sample_frames\n"
        "Output: ONLY valid JSON array — no markdown or extra text."
    ),
    expected_output="JSON array of reusable style templates.",
    agent=style_template_extractor
)

chunk_task = Task(
    name="chunk_transcription",
    description=(
        f"You are given full transcription:\n{truncate_json(input_transcription)}\n\n"
        "Chunk it based on:\n"
        "- Pauses >120ms, energy dips, and average density in reference (3–5 words per chunk).\n"
        "- Avoid unnatural phrase breaks.\n\n"
        "Each chunk should include:\n"
        "- chunk_text, start_time, end_time, words[], mood, sentence_relation\n"
        "Return: Clean JSON array only."
    ),
    expected_output="List of clean subtitle chunks in JSON.",
    agent=chunker_agent
)

assign_styles_task = Task(
    name="assign_templates",
    description=(
        "You are a subtitle engine that renders .ass files.\n"
        "Input:\n- Style templates\n- Chunks with mood, relation, timings\n\n"
        "Instructions:\n"
        "1. Assign best matching template based on word_count, mood, sentence_relation\n"
        "2. Use all templates at least once and proportionally to frequency\n"
        "3. Generate valid .ass file content with:\n"
        "[Script Info], [V4+ Styles], [Events] sections\n"
        "- Use PlayResX=1920, PlayResY=1080\n"
        "- Format Dialogue line per chunk with timing in H:MM:SS.cs\n\n"
        "Return: ONLY raw .ass file content. No JSON, no comments, no markdown."
    ),
    expected_output="Valid .ass subtitle file content.",
    agent=style_assigner
)

# === Crew Setup ===
crew = Crew(
    agents=[style_template_extractor, chunker_agent, style_assigner],
    tasks=[extract_templates_task, chunk_task, assign_styles_task],
    verbose=True,
    return_intermediate_steps=True
)

# === Run ===
results = crew.kickoff()
task_outputs = results.tasks_output

# === Save directory ===
Path("output").mkdir(exist_ok=True)

# === Output Cleanup Function ===
def clean_output(raw: str) -> str:
    return re.sub(r"^```(?:json|ass)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

# === Save files ===
with open("output/templates.json", "w", encoding="utf-8") as f:
    f.write(clean_output(task_outputs[0].raw))

with open("output/chunks.json", "w", encoding="utf-8") as f:
    f.write(clean_output(task_outputs[1].raw))

with open("output/styled_output.ass", "w", encoding="utf-8") as f:
    f.write(clean_output(task_outputs[2].raw))

print("✅ All files saved to /output:\n- templates.json\n- chunks.json\n- styled_output.ass")
