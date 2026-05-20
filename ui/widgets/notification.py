from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer

class Notification(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("background: red; color: white; padding: 10px;")
        self.hide()

    def show_message(self, text):
        self.setText(text)
        self.show()
        QTimer.singleShot(3000, self.hide)