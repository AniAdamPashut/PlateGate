import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


def window():
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
