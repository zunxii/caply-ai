import json

# === Load styled chunk data ===
with open("styled_output.json", "r", encoding="utf-8") as f:
    styled_chunks = json.load(f)

# === Load original transcription with timestamps ===
with open("data/input_transcription_with_energy.json", "r", encoding="utf-8") as f:
    transcript_words = json.load(f)

# Flatten and normalize the transcription text for matching
transcript_queue = transcript_words.copy()
current_index = 0

for chunk in styled_chunks:
    chunk_words = chunk["words"]
    for word in chunk_words:
        target_word = word["word"].strip().lower()

        # Match each word in order
        while current_index < len(transcript_queue):
            transcript_word = transcript_queue[current_index]
            current_index += 1

            trans_text = transcript_word["text"].strip().lower()

            # Match ignoring trailing punctuation like ".", ",", "?" etc.
            if trans_text.rstrip(".,?!") == target_word.rstrip(".,?!"):
                word["start"] = transcript_word["start"]
                word["end"] = transcript_word["end"]
                break
        else:
            raise ValueError(f"Could not find match for word '{target_word}'")

    # Update chunk start and end
    chunk["start"] = chunk_words[0]["start"]
    chunk["end"] = chunk_words[-1]["end"]

# === Save output ===
with open("styled_chunks_with_timestamps.json", "w", encoding="utf-8") as f:
    json.dump(styled_chunks, f, indent=2)

print("✅ Timestamps mapped successfully to styled chunks.")
