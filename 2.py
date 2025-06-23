import os
import cv2
import pytesseract

# Input and output folders
input_dir = "frames_output"
output_dir = "frame_filtered"
os.makedirs(output_dir, exist_ok=True)

# Set tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

saved_count = 0
skipped_count = 0

for filename in os.listdir(input_dir):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        filepath = os.path.join(input_dir, filename)
        image = cv2.imread(filepath)

        if image is None:
            print(f"⚠️ Skipped {filename} (could not read image)")
            continue

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # ✅ Apply Gaussian Blur to smooth the background
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # ✅ Adaptive Threshold to make text pop
        processed = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # OCR
        text = pytesseract.image_to_string(processed, config='--psm 6').strip()

        if text:
            save_path = os.path.join(output_dir, filename)
            cv2.imwrite(save_path, image)
            print(f"✅ Kept: {filename}")
            saved_count += 1
        else:
            print(f"❌ Discarded: {filename} → No text found.")
            skipped_count += 1

print(f"\n🎉 Done. Saved {saved_count} frames. Skipped {skipped_count}.")
