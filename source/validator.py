import re


def validate_id(id_number: str):
    try:
        int(id_number)
    except ValueError:
        raise ValueError("Please insert a string made up from digits")
    if not id_number:
        return False
    if len(id_number) > 9:
        return False
    if len(id_number) < 9:
        id_number = "00000000" + id_number
        id_number = id_number[-9:]
        print(id_number)
    validator = "121212121"
    array = []
    for id_num, validating_num in zip(id_number, validator):
        num = int(id_num) * int(validating_num)
        if num > 10:
            num = num % 10 + num // 10
        array.append(num)
    id_sum = sum(array)
    return id_sum % 10 == 0


def validate_name(name: str):
    return name.isalpha()


def validate_email(email: str):
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    return re.fullmatch(regex, email)