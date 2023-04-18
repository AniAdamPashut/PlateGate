import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Mailing import Mailer
from dotenv import dotenv_values

CONFIG = dotenv_values('../.env')


def window():
    m = Mailer('smtp.gmail.com', False)
    m.enter_credentials(CONFIG['MAIL_ADDR'], CONFIG['MAIL_PASS'])
    m.mailto(['minebenking@gmail.com'], 'Test', 'test')
    app = QApplication(sys.argv)
    w = QWidget()
    b = QLabel(w)
    b.setText("Welcome to PlateGate!")
    b.setAlignment(Qt.AlignHCenter)
    w.setGeometry(100, 100, 600, 400)
    w.setWindowTitle("PlateGate")
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    window()
