import os
from pathlib import Path
import json

from script1_transcription import process_video
from script2_extract_frames import extract_frames
from script3_style_detection import analyze_frames
from script4_filter_frames import filter_duplicate_frames
from script5_chunk_transcription import chunk_transcription
from script6_style_templates import extract_styles
from script7_generate_ass import generate_ass_file

REFERENCE_VIDEO = "videos/reference2.mp4"
INPUT_VIDEO = "videos/video1.mp4"
DATA_DIR = "data"
FRAMES_DIR = "frames"
OUTPUT_DIR = "output"

REF_JSON = os.path.join(DATA_DIR, "ref_transcription_with_energy.json")
INPUT_JSON = os.path.join(DATA_DIR, "input_transcription_with_energy.json")
ALL_FRAMES_JSON = os.path.join(DATA_DIR, "all_frames.json")
FILTERED_FRAMES_JSON = os.path.join(OUTPUT_DIR, "filtered_all_frames.json")
CHUNKS_JSON = os.path.join(OUTPUT_DIR, "chunks.json")
TEMPLATES_JSON = os.path.join(OUTPUT_DIR, "templates.json")
STYLE_SEQ_JSON = os.path.join(OUTPUT_DIR, "style_sequence_by_frame.json")
ASS_OUTPUT = os.path.join(OUTPUT_DIR, "styled_output.ass")
LOG_OUTPUT = os.path.join(OUTPUT_DIR, "logs.txt")

# print("\n[1/7] Transcribing reference and input videos with energy...")
# process_video(REFERENCE_VIDEO, REF_JSON)
# process_video(INPUT_VIDEO, INPUT_JSON)

# print("\n[2/7] Extracting frames from reference video...")
# extract_frames(REFERENCE_VIDEO, FRAMES_DIR, target_fps=2)

# print("\n[3/7] Analyzing frames for subtitle style detection...")
# analyze_frames(FRAMES_DIR, ALL_FRAMES_JSON, max_frames=85)

# print("\n[4/7] Filtering duplicate frames...")
# filter_duplicate_frames(ALL_FRAMES_JSON, FILTERED_FRAMES_JSON)

# print("\n[5/7] Chunking transcription...")
# chunk_transcription(INPUT_JSON, ALL_FRAMES_JSON, CHUNKS_JSON)

print("\n[6/7] Extracting styles and mapping sequences...")
extract_styles(ALL_FRAMES_JSON, TEMPLATES_JSON, STYLE_SEQ_JSON)

print("\n[7/7] Generating final .ASS subtitle file...")
generate_ass_file(CHUNKS_JSON, STYLE_SEQ_JSON, TEMPLATES_JSON, ASS_OUTPUT, LOG_OUTPUT)

print("\n Pipeline complete! Outputs saved in:")
print(f"  → {REF_JSON}, {INPUT_JSON}")
print(f"  → Frames: {FRAMES_DIR}/")
print(f"  → {ALL_FRAMES_JSON}, {FILTERED_FRAMES_JSON}")
print(f"  → {CHUNKS_JSON}, {TEMPLATES_JSON}, {STYLE_SEQ_JSON}")
print(f"  → {ASS_OUTPUT}, {LOG_OUTPUT}")
