from source import Recognize

PLATE_NUMBER = '6930113'

plate_number = Recognize.recognize_from_image('../source/pego.jpg')
print("START TEST")
print("-"*30)
print(f"{{plate_number == PLATE_NUMBER}}")
print("-"*30)
print("END TEST")

assert plate_number == PLATE_NUMBER
