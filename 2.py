import cv2
import numpy as np
import easyocr
import re
import os
import shutil
from difflib import SequenceMatcher
import language_tool_python

# === CONFIG ===
video_path = 'ref_video.mp4'
output_folder = 'filtered_frames'
os.makedirs(output_folder, exist_ok=True)


# === OCR CLASS ===
class OCRWithEnhancements:
    def __init__(self, conf_thresh=0.4, similarity_thresh=0.85):
        self.reader = easyocr.Reader(['en'], gpu=False)
        self.conf_thresh = conf_thresh
        self.tool = language_tool_python.LanguageTool('en-US')
        self.similarity_thresh = similarity_thresh
        self.last_text = ""

    def enhance_image(self, image):
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        merged = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

        enhanced = enhanced.astype(np.float32) / 255.0
        enhanced = np.power(enhanced, 1.2)
        enhanced = np.clip(enhanced * 255, 0, 255).astype(np.uint8)

        sharpened = cv2.filter2D(enhanced, -1, np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]))
        return sharpened

    def clean(self, text):
        text = text.replace("\n", " ")
        text = re.sub(r'[^a-zA-Z0-9\s.,!?;:"\'()-]', '', text)
        return re.sub(r'\s{2,}', ' ', text).strip()

    def group_and_space(self, results):
        lines = {}
        for (bbox, text, conf) in results:
            if conf < self.conf_thresh:
                continue
            (tl, tr, br, bl) = bbox
            y = int((tl[1] + br[1]) / 2)
            x1 = int(min(tl[0], bl[0]))
            x2 = int(max(tr[0], br[0]))
            if y not in lines:
                lines[y] = []
            lines[y].append((x1, x2, self.clean(text)))

        final = []
        for y in sorted(lines):
            line = sorted(lines[y], key=lambda t: t[0])
            spaced_line = ""
            prev_right = None
            for x1, x2, word in line:
                if prev_right and x1 - prev_right > 10:
                    spaced_line += " "
                spaced_line += word
                prev_right = x2
            final.append(spaced_line.strip())
        return " ".join(final).strip()

    def is_valid_english(self, sentence):
        matches = self.tool.check(sentence)
        errors = [m for m in matches if m.ruleIssueType == 'grammar' and m.message]
        return len(errors) < 3  # allow up to 2 minor grammar issues

    def is_similar_to_last(self, text):
        similarity = SequenceMatcher(None, text.lower(), self.last_text.lower()).ratio()
        return similarity >= self.similarity_thresh

    def detect_text(self, image):
        enhanced = self.enhance_image(image)
        results = self.reader.readtext(enhanced)

        if not results:
            return ""

        text = self.group_and_space(results)

        if not self.is_valid_english(text):
            return ""

        if self.is_similar_to_last(text):
            return ""

        self.last_text = text
        return text


# === PROCESS VIDEO ===
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
frame_interval = int(fps / 2)

frame_num = 0
saved_count = 0
ocr = OCRWithEnhancements()

print("📽️ Scanning video and saving filtered frames...\n")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    if frame_num % frame_interval == 0:
        text = ocr.detect_text(frame)
        if text:
            frame_path = os.path.join(output_folder, f'frame_{saved_count:05d}.jpg')
            cv2.imwrite(frame_path, frame)
            print(f"✅ Frame {saved_count:05d}: {text}")
            saved_count += 1

    frame_num += 1

cap.release()

print(f"\n🎯 Done. {saved_count} filtered frames saved to: '{output_folder}'")
