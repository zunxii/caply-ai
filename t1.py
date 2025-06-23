import cv2
import numpy as np
import easyocr
import re
import os
import shutil

class EasyOCRTextDetector:
    def __init__(self, confidence_threshold: float = 0.4):  # lowered threshold
        self.confidence_threshold = confidence_threshold
        self.reader = easyocr.Reader(['en'], gpu=False)

    def is_meaningful(self, text: str) -> bool:
        cleaned = re.sub(r'[^\w\s.,!?;:"\'()-]', '', text)
        words = cleaned.split()
        return any(len(w) > 1 or w.isalnum() for w in words)

    def clean_text(self, text: str) -> str:
        text = text.replace('\n', ' ')
        text = re.sub(r'[^a-zA-Z0-9\s.,!?;:"\'()-]', '', text)
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        # Convert to LAB and apply CLAHE
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # Gamma correction
        enhanced = enhanced.astype(np.float32) / 255.0
        gamma = 1.2
        enhanced = np.power(enhanced, gamma)
        enhanced = np.clip(enhanced * 255, 0, 255).astype(np.uint8)

        # Sharpening and dilation
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)

        # Dilation to thicken faint text
        dilated = cv2.dilate(sharpened, np.ones((1, 1), np.uint8), iterations=1)

        return dilated

    def detect_text(self, image: np.ndarray) -> str:
        enhanced = self.enhance_image(image)
        results = self.reader.readtext(enhanced)

        if not results:
            return ""

        # Group lines by y-center proximity
        lines = {}
        line_tolerance = 12

        for (bbox, text, conf) in results:
            if conf < self.confidence_threshold:
                continue

            clean = self.clean_text(text)
            if not self.is_meaningful(clean):
                continue

            (tl, tr, br, bl) = bbox
            y_center = int((tl[1] + br[1]) / 2)
            x_left = int(min(tl[0], bl[0]))
            x_right = int(max(tr[0], br[0]))

            inserted = False
            for line_y in lines:
                if abs(line_y - y_center) <= line_tolerance:
                    lines[line_y].append((x_left, x_right, clean))
                    inserted = True
                    break

            if not inserted:
                lines[y_center] = [(x_left, x_right, clean)]

        # Sort lines and words
        final_lines = []
        for y in sorted(lines.keys()):
            line = lines[y]
            line.sort(key=lambda x: x[0])  # sort by x_left

            spaced_line = ""
            prev_right = None

            for x_left, x_right, word in line:
                if prev_right is not None:
                    gap = x_left - prev_right
                    avg_char_width = max((x_right - x_left) / max(len(word), 1), 1)
                    if gap > avg_char_width * 0.4:
                        spaced_line += " "
                spaced_line += word
                prev_right = x_right

            final_lines.append(spaced_line.strip())

        return ' '.join(final_lines).strip()


# ✅ Folders
input_folder = "frames_output"
output_folder = "filtered_frames"
os.makedirs(output_folder, exist_ok=True)

# ✅ Detector instance
detector = EasyOCRTextDetector()

# ✅ Scan and filter frames
frame_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.png'))])
print(f"🔍 Scanning {len(frame_files)} frames...\n")

count = 0
for filename in frame_files:
    path = os.path.join(input_folder, filename)
    image = cv2.imread(path)

    if image is None:
        print(f"❌ Skipped (can't read): {filename}")
        continue

    text = detector.detect_text(image)
    if text:
        count += 1
        print(f"✅ {filename}: {text}")
        shutil.copy(path, os.path.join(output_folder, filename))

print(f"\n🎯 Done. {count} frames saved to '{output_folder}'")
