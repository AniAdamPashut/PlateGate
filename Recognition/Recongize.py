import pytesseract
import cv2

# Read the image
img = cv2.imread('image.png')

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Apply thresholding to the image
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]


# Perform OCR using pytesseract
text = pytesseract.image_to_string(thresh, config='--psm 6', lang='eng')

# Extract only numbers from the text
number = ''.join(filter(str.isdigit, text))

print('Car plate number:', number)
