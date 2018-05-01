import cv2
import numpy as np
import pytesseract
import imutils
from imutils.perspective import four_point_transform
from Utils.log import log


def preprocess(path):
    # Open the image from a path
    im = cv2.imread(path)
    # imread returns None if path is incorrect
    if im is None:
        return None

    copy = im.copy()

    # Resize image
    image = imutils.resize(copy, height=1000)
    # Convert image to greyscale
    im_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Normalize image histogram
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl1 = clahe.apply(im_gray)

    # Blur out high-frequency noise
    blur = cv2.GaussianBlur(cl1, (5, 5), 0)
    # Determine automatic threshold values
    sigma = 0.33
    v = np.median(blur)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    # Canny edge detection
    edge = cv2.Canny(image, lower, upper, L2gradient=True)

    return edge


def trim_image(image):
    _, contours, _ = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    display_boundaries = []

    for c in contours:
        # Approximate the contour
        perimeter = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * perimeter, True)
        # Check if we have a square
        if len(approx) == 4:
            display_boundaries.append(approx)

    cropped = None
    # If we found a convincing square in the image
    # Then we crop because we assume it's the screen
    if len(display_boundaries) >= 1:
        cropped = four_point_transform(image, display_boundaries[0].reshape(4, 2))

    return cropped


def reinforce_contours(image):
    image, contours, hierarchy = cv2.findContours(image.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    reinforced = cv2.drawContours(image, contours, -1, (255, 255, 255), thickness=-1, lineType=cv2.LINE_AA)
    return reinforced


def text_from_image(path_to_image):
    img = preprocess(path_to_image)
    if img is None:
        log.error("image pre-processing for OCR failed")

    crop = trim_image(img)
    if crop is None:
        log.error("trim image for OCR failed")

    ret = reinforce_contours(crop)
    # TODO post-process text from OCR (character replace, etc.)
    text = pytesseract.image_to_string(ret, lang='eng', boxes=False, config='--psm 6')
    return text
