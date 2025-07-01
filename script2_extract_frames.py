import cv2
import os

def extract_frames(video_path: str, output_folder: str, target_fps: int = 2):
    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        raise ValueError("Unable to determine video FPS.")

    frame_interval = int(fps / target_fps)
    frame_num = 0
    saved_count = 0

    print(f"📸 Extracting frames from: {video_path}")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % frame_interval == 0:
            frame_path = os.path.join(output_folder, f'frame_{saved_count:05d}.jpg')
            cv2.imwrite(frame_path, frame)
            saved_count += 1

        frame_num += 1

    cap.release()
    print(f" Saved {saved_count} frames to: {output_folder}")