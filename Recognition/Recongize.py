import imutils
import cv2
import easyocr
from GovAPI.fetch import GovApiFetcher
# Read the image
image = cv2.imread('otto.jpg')

# resize the image
image = imutils.resize(image, width=500)

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

gray = cv2.bilateralFilter(gray, 11, 17, 17)

edged = cv2.Canny(gray, 170, 200)


cnts, new = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
copied = image.copy()
cv2.drawContours(copied, cnts, -1, (0, 255, 0), 3)

cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
NumberPlateCount = None


image2 = image.copy()
cv2.drawContours(image2, cnts, -1, (0, 255, 0), 3)

count = 0
name = 1

for i in cnts:
    perimeter = cv2.arcLength(i, True)
    approx = cv2.approxPolyDP(i, 0.02*perimeter, True)
    if len(approx) == 4:
        NumberPlateCount = approx
        x, y, w, h = cv2.boundingRect(i)
        crp_image = image[y:y+h, x:x+w]
        cv2.imwrite(str(name)+'.png', crp_image)
        name += 1
        break

cv2.drawContours(image, [NumberPlateCount], -1, (0, 255, 0), 3)
cv2.imwrite('Drawed.jpg', image)
crp_image_name = '1.png'
crpped = cv2.imread(crp_image_name)


reader = easyocr.Reader(['en'])
result = reader.readtext(crpped)
print(result)

result = result[0]


def get_digits(string: str):
    return ''.join(char for char in string if char.isdigit())


num = get_digits(result[1])
print(num)
vehicle = GovApiFetcher.get_vehicle_by_plate_number(num)

print(vehicle.plate_number)
print(vehicle.sug_rechev)
print(vehicle.active)
print(vehicle.totaled)
print(vehicle.shnat_yitsur)


vehicle.add_to_database('215616830')