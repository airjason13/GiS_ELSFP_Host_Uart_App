from PyQt5 import QtCore, QtWidgets


class CommandPage(QtWidgets.QWidget):
    command = QtCore.pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.tx_buttons = []
        self.setting_buttons = []

    def button(self, label, command, **parameters):
        button = QtWidgets.QPushButton(label)
        def send_command():
            # Read widget values when clicked, not when the page is constructed.
            values = {key: value() if callable(value) else value
                      for key, value in parameters.items()}
            self.command.emit(command.build(**values), command.opcode)

        button.clicked.connect(send_command)
        self.tx_buttons.append(button)
        if command.opcode is not None:
            self.setting_buttons.append(button)
        return button
