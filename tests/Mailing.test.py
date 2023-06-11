from source import Mailing
import dotenv

CONFIG = dotenv.dotenv_values('../source/.env')
mailer = Mailing.Mailer('smtp.gmail.com', False)
mailer.enter_credentials(CONFIG['MAIL_ADDR'], CONFIG['MAIL_PASS'])

print("START TEST")
print("-"*30)
mailer.mailto(['minebenking@gmail.com'], 'Test', 'TEST')
print("-"*30)
print("END TEST")

