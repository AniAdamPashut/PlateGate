import re


def validate_id(id_number: str):
    bikoret = id_number[-1]
    id_number = id_number[:-1]
    try:
        int(id_number)
    except ValueError:
        raise ValueError("Please insert a string made up from digits")
    if not id_number:
        return False
    if len(id_number) > 8:
        return False
    if len(id_number) < 8:
        id_number = "00000000" + id_number
        id_number = id_number[-8:]
        print(id_number)
    validator = "12121212"
    array = []
    for id_num, validating_num in zip(id_number, validator):
        num = int(id_num) * int(validating_num)
        if num > 9:
            num = num % 10 + num // 10
        array.append(num)
    id_sum = sum(array)
    bikoret_validate = (10 - id_sum % 10) % 10
    return bikoret_validate == int(bikoret)


def validate_name(name: str):
    return name.isalpha()


def validate_email(email: str):
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    return bool(re.fullmatch(regex, email))


def validate_password(password: str) -> bool:
    regex = re.compile(r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$")
    return bool(re.fullmatch(regex, password))
