from source import validator


print("START TEST")
print("-"*30)

mails = [
    'someone@gmail.com',
    'john.doe.1@yahoo.com',
    'david@davitech.io'
]
for mail in mails:
    assert validator.validate_email(mail)

passwords = [
    ('asdpj1p2SDkn$', True),
    ('password', False),
    ('123%aA', False)
]

for password, expected_result in passwords:
    assert validator.validate_password(password) == expected_result

ids = [
    ('215616830', True),
    ('27938216', True),
    ('123456789', False)
]

for id, expected_result in ids:
    assert validator.validate_id(id) == expected_result

names = [
    ('123', False),
    ('Ben', True),
    ('fn29', False),
    ('fas asd', False)
]

for name, expected_result in names:
    assert validator.validate_name(name) == expected_result

print("-"*30)
print("END TEST")
