from langchain_openai import ChatOpenAI
from pathlib import Path
import json
import re

def clean_output(raw: str) -> str:
    return re.sub(r"^```(?:json|ass)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

def chunk_transcription(transcription_path: str, all_frames_path: str, output_path: str):
    transcription = json.load(open(transcription_path, encoding="utf-8"))
    all_frames = json.load(open(all_frames_path, encoding="utf-8"))
    prompt_static = Path("prompts/chunking_prompt.txt").read_text(encoding="utf-8")

    max_words = max(len(f.get("words", [])) for f in all_frames)
    chunk_prompt = (
        f"You're given transcription with energy data:\n"
        f"Max words per caption chunk should not exceed {max_words}.\n\n"
        f"{json.dumps(transcription)}\n\n"
        + prompt_static
    )

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    response = llm.invoke(chunk_prompt)
    chunks = clean_output(response.content)

    Path(output_path).parent.mkdir(exist_ok=True)
    Path(output_path).write_text(chunks, encoding="utf-8")
    print(f" Saved: {output_path}")
