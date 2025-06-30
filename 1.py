import subprocess
import requests
import time
import json
from io import BytesIO
import io
from typing import Generator
import numpy as np
import soundfile as sf
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("ASSEMBLYAI_API_KEY")

def mp4_to_mp3_bytes(input_path: str) -> bytes:
    command = [
        'ffmpeg',
        '-i', input_path,
        '-f', 'mp3',
        '-acodec', 'libmp3lame',
        '-vn',
        'pipe:1'
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr.decode()}")
    return result.stdout

def read_in_chunks(data: bytes, chunk_size: int = 5242880) -> Generator[bytes, None, None]:
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def upload_to_assemblyai(audio_bytes: bytes) -> str:
    headers = {
        "authorization": api_key,
        "transfer-encoding": "chunked"
    }
    response = requests.post(
        "https://api.assemblyai.com/v2/upload",
        headers=headers,
        data=read_in_chunks(audio_bytes),
        stream=True
    )
    response.raise_for_status()
    return response.json()['upload_url']

def transcribe_audio_url(audio_url: str) -> list:
    headers = {
        "authorization": api_key,
        "content-type": "application/json"
    }
    response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json={"audio_url": audio_url, "auto_chapters": False, "iab_categories": False}
    )
    transcript_id = response.json()['id']

    while True:
        polling = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
        status = polling.json()['status']
        if status == 'completed':
            return polling.json()['words']
        elif status == 'error':
            raise Exception(f"Transcription failed: {polling.json()['error']}")
        time.sleep(2)

def energy_data(audio: bytes, transcription: list) -> list:
    audio_data, sample_rate = sf.read(io.BytesIO(audio))
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)

    for word in transcription:
        start_sec = word["start"] / 1000.0
        end_sec = word["end"] / 1000.0

        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)

        word_audio = audio_data[start_sample:end_sample]
        energy = float(np.sqrt(np.mean(word_audio**2))) if len(word_audio) > 0 else 0.0
        word["energy"] = energy

    return transcription

def save_to_json(data: list, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_video(video_path: str, output_filename: str):
    audio_bytes = mp4_to_mp3_bytes(video_path)
    audio_url = upload_to_assemblyai(audio_bytes)
    words = transcribe_audio_url(audio_url)
    enhanced = energy_data(audio_bytes, words)
    save_to_json(enhanced, os.path.join("data", output_filename))

def main():
    print(" Processing reference reel...")
    process_video("videos/reference1.mp4", "ref_transcription_with_energy.json")

    print(" Processing input reel...")
    process_video("videos/video.mp4", "input_transcription_with_energy.json")

    print(" Done. Only 2 files saved in /data")

if __name__ == "__main__":
    main()
