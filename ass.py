import subprocess

ass_file = "output_subtitles.ass"
input_video = "videos/mb_1_plain.mp4"
output_video = "final_mb.mp4"

cmd = [
    "ffmpeg",
    "-i", input_video,
    "-vf", f"ass={ass_file}",
    "-c:a", "copy",
    output_video
]

subprocess.run(cmd, check=True)
print(" Captions applied and saved to:", output_video)
