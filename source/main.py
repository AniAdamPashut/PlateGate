from dotenv import dotenv_values
from source.Recongnize import Recognizer
import cv2


CONFIG = dotenv_values('.env')


def window():
    number = Recognizer.recognize_from_image(cv2.imread())
    print(number)


if __name__ == '__main__':
    window()
