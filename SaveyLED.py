# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap

class SaveyLED(QtWidgets.QLabel):
    def version():
        return __FILE__ + " v. 001"

    def __init__(self):
        QtWidgets.QLabel.__init__(self)

        self.pix_led_green = QPixmap("PIC/LED_green_ts.png")
        self.pix_led_red = QPixmap("PIC/LED_red_ts.png")

        self.setPixmap(self.pix_led_red)

        self.effect = QtWidgets.QGraphicsOpacityEffect(opacity=1.0)
        self.setGraphicsEffect(self.effect)
        self.animation = QtCore.QPropertyAnimation(self.effect, b'opacity')
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setDuration(1500)
        self.animation.finished.connect(self.checkAnimation)

        #self.clicked.connect(self.startAnimation)
        self.startAnimation

    def startAnimation(self):
        self.animation.stop()
        self.animation.setDirection(self.animation.Forward)
        self.animation.start()

    def checkAnimation(self):
        if not self.animation.currentValue():
            self.animation.setDirection(self.animation.Backward)
        else:
            self.animation.setDirection(self.animation.Forward)
        self.animation.start()
