from PyQt5 import QtCore, QtWidgets
import commands as cmd
from cmd_page import CommandPage


class SystemPage(CommandPage):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self.version = {}
        form = QtWidgets.QFormLayout()
        for field in ('Firmware Version', 'Build ID', 'Build Time'):
            self.version[field] = QtWidgets.QLabel('—')
            self.version[field].setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            form.addRow(field, self.version[field])
        layout.addLayout(form)
        for title, command in [('Read version', cmd.GET_SYSTEM_VERSION), ('Task / Stack status', cmd.GET_SYSTEM_STATUS),
                               ('ELSFP status', cmd.GET_ELSFP_STATUS), ('Help', cmd.HELP)]:
            layout.addWidget(self.button(title, command))
        layout.addStretch()

    def receive(self, line):
        for field, label in self.version.items():
            prefix = '[CMD] ' + field + ': '
            if prefix in line:
                label.setText(line.split(prefix, 1)[1].strip())

    def reset(self):
        for label in self.version.values():
            label.setText('—')
