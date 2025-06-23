import cv2
import pytesseract
import numpy as np

# ✅ Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ✅ Input image path
image_path = "frames_output/frame_00001.jpg"  # Change this if needed

def is_caption_frame(image):
    image = cv2.resize(image, (1280, 720))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Optional: increase contrast
    contrast = cv2.convertScaleAbs(gray, alpha=1.8, beta=0)

    # Optional: basic thresholding (sometimes better than adaptive)
    _, thresh = cv2.threshold(contrast, 150, 255, cv2.THRESH_BINARY)

    # OCR with details
    data = pytesseract.image_to_data(
        thresh, config='--oem 3 --psm 6',
        output_type=pytesseract.Output.DICT
    )

    valid_word_count = 0
    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        try:
            conf = int(data['conf'][i])
        except:
            conf = -1

        if (
            conf >= 50 and
            len(word) >= 2 and
            any(c.isalpha() for c in word)
        ):
            valid_word_count += 1

    return valid_word_count >= 1

# 🔍 Load and check the image
image = cv2.imread(image_path)
if image is None:
    print("❌ Could not read image.")
else:
    if is_caption_frame(image):
        print("✅ Caption detected.")
    else:
        print("❌ No visible caption.")
