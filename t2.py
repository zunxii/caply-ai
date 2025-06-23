import cv2
import pytesseract
import numpy as np

# ✅ Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def has_caption_text(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return "No"

    image = cv2.resize(image, (1280, 720))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Sharpen image
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, sharpen_kernel)

    # Threshold
    thresh = cv2.adaptiveThreshold(
        sharpened, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # OCR with bounding boxes
    data = pytesseract.image_to_data(thresh, config='--oem 3 --psm 6', output_type=pytesseract.Output.DICT)

    valid_word_count = 0
    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        conf = int(data['conf'][i]) if data['conf'][i].isdigit() else -1
        width = int(data['width'][i])
        height = int(data['height'][i])

        if (
            conf >= 60 and
            len(word) >= 4 and
            any(c.isalpha() for c in word) and
            width > 40 and height > 10
        ):
            valid_word_count += 1

    # ✅ Only if enough real words with good confidence
    if valid_word_count >= 1:
        return "Yes"
    else:
        return "No"

# Example usage
image_path = "frames_output/frame_00001.jpg"
has_caption_text(image_path)
