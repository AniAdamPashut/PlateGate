import imutils
import cv2
import easyocr


def get_license_plate_from_image(imagename):
    image = cv2.imread(imagename)
    # resize the image
    image = imutils.resize(image, width=500)

    # grayscale the image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # smooth the image
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    # gets the edges from the grayscaled image
    edged = cv2.Canny(gray, 170, 200)

    # find the contours
    cnts, new = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
    number_plate_count = None

    count = 0
    name = 0

    for i in cnts:
        perimeter = cv2.arcLength(i, True)
        approx = cv2.approxPolyDP(i, 0.02 * perimeter, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(i)
            crp_image = image[y:y + h, x:x + w]
            name += 1
            cv2.imwrite(str(name) + '.png', crp_image)
            break
    if name < 1:
        return False
    cropped = cv2.imread(f'{name}.png')
    reader = easyocr.Reader(['en'])
    result = reader.readtext(cropped)
    if not result:
        return False
    return result[0][1]


def get_digits(string: str):
    if not string:
        return ''
    return ''.join(list(filter(lambda x: x.isdigit(), string)))


def recognize_from_image(image):
    return get_digits(get_license_plate_from_image(image))
