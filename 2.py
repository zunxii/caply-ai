import cv2
import os

video_path = "videos/reference1.mp4"
output_folder = "frames"
target_fps = 2

os.makedirs(output_folder, exist_ok=True)

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
frame_interval = int(fps / target_fps)

frame_num = 0
saved_count = 0

print("Scanning video and saving frames...\n")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    if frame_num % frame_interval == 0:
        frame_path = os.path.join(output_folder, f'frame_{saved_count:05d}.jpg')
        cv2.imwrite(frame_path, frame)
        print(f" Frame {saved_count:05d} saved")
        saved_count += 1

    frame_num += 1

cap.release()
print(f"\n Done. {saved_count} frames saved to: '{output_folder}'")
