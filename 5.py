from langchain_openai import ChatOpenAI
from pathlib import Path
import json
import re

def clean_output(raw: str) -> str:
    return re.sub(r"^```(?:json|ass)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()

input_transcription = json.load(open("data/input_transcription_with_energy.json", encoding="utf-8"))
prompt2_static = Path("prompts/chunking_prompt.txt").read_text(encoding="utf-8")
all_frames = json.load(open("data/all_frames.json", encoding="utf-8"))

max_words = max(len(frame.get("words", [])) for frame in all_frames)

chunk_prompt = (
    f"You're given transcription with energy data:\n"
    f"Max words per caption chunk should not exceed {max_words}.\n\n"
    f"{json.dumps(input_transcription)}\n\n"
    + prompt2_static
)

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
response = llm.invoke(chunk_prompt)
chunks = clean_output(response.content)

Path("output").mkdir(exist_ok=True)
Path("output/chunks.json").write_text(chunks, encoding="utf-8")
print(" Saved: chunks.json")
