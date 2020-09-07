import json
import numpy as np

import cv2
import pytesseract
import imutils
import requests

from app.parse_info import parse

LicenseCode = 'B92F6B02-4FBA-464C-895A-07F88963BD8A'
UserName =  'sunedition'
RequestUrl = "http://www.ocrwebservice.com/restservices/processDocument?gettext=true"

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def find_rectangle(image):
    rectangle_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 5))
    square_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (27, 27))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rectangle_kernel)
    gradX = cv2.Sobel(blackhat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
    gradX = np.absolute(gradX)
    (minVal, maxVal) = (np.min(gradX), np.max(gradX))
    gradX = (255 * ((gradX - minVal) / (maxVal - minVal))).astype("uint8")
    gradX = cv2.morphologyEx(gradX, cv2.MORPH_CLOSE, rectangle_kernel)
    thresh = cv2.threshold(gradX, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, square_kernel)
    thresh = cv2.erode(thresh, None, iterations=4)
    p = int(image.shape[1] * 0.05)
    thresh[:, 0:p] = 0
    thresh[:, image.shape[1] - p:] = 0
    return thresh

def find_contours(image, thresh):
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        crWidth = w / float(image.shape[1])
        if ar > 5 and crWidth > 0.75:
            pX = int((x + w) * 0.03)
            pY = int((y + h) * 0.03)
            (x, y) = (x - pX, y - pY)
            (w, h) = (w + (pX * 2), h + (pY * 2))
            roi = image[y:y + h, x:x + w].copy()
            return roi

def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
    """Return a sharpened version of the image, using an unsharp mask."""
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = float(amount + 1) * image - float(amount) * blurred
    sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
    sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
    sharpened = sharpened.round().astype(np.uint8)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened

def detect_read(image):
    image = np.array(image)
    if image.shape[0] > image.shape[1]:
        image = imutils.resize(image, width=600)
    else:
        image = imutils.resize(image, height=600) 
    rotation_dict = {}
    for i in range(4):
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        thresh = find_rectangle(image)
        roi = find_contours(image, thresh)
        try:
            sharpened_image = unsharp_mask(roi)
            rotation_dict[i] = sharpened_image
        except:
            continue
    digits_dict = {}
    for key, value in rotation_dict.items():
        text = pytesseract.image_to_string(value, lang='eng')
        digits = 0
        for c in text:
            if c.isdigit():
                digits += 1
        digits_dict[digits] = value
    cv2.imwrite('./roi.jpg', digits_dict[max(list(digits_dict.keys()))])
    response = requests.post(RequestUrl, data=open('./roi.jpg', 'rb'), auth=(UserName, LicenseCode))
    jobj = json.loads(response.content)
    text = jobj["OCRText"][0][0]
    # text = pytesseract.image_to_string(digits_dict[max(list(digits_dict.keys()))])
    try:
        json_object = parse(text)
    except:
        json_object = {'Error': 'Unable to recognize structure in text!'}
    if 'Error' not in json_object:
        return json_object
    else:
        json_object = {**json_object, 
                    'Possible Solution': 'Try to upload image with better resolution (min 800x600).'}
    return json.dumps(json_object)