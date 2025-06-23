import cv2
import os

# Input video file
video_path = 'ref_video.mp4'

# Output folder for frames
output_folder = 'frames_output'
os.makedirs(output_folder, exist_ok=True)

# Load the video
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
frame_interval = int(fps / 2)

frame_num = 0
saved_frame_num = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    if frame_num % frame_interval == 0:
        frame_path = os.path.join(output_folder, f'frame_{saved_frame_num:05d}.jpg')
        cv2.imwrite(frame_path, frame)
        saved_frame_num += 1

    frame_num += 1

cap.release()
print(f"Extracted {saved_frame_num} frames to '{output_folder}'")
