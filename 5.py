import subprocess

ass_file = "output/styled_output.ass"
input_video = "videos/video.mp4"
output_video = "final11.mp4"

cmd = [
    "ffmpeg",
    "-i", input_video,
    "-vf", f"ass={ass_file}",
    "-c:a", "copy",
    output_video
]

subprocess.run(cmd, check=True)
print(" Captions applied and saved to:", output_video)
