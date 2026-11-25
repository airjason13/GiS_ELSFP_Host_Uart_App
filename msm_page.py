import re
from PyQt5 import QtWidgets
import commands as cmd
from cmd_page import CommandPage


class MsmPage(CommandPage):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self.observed = QtWidgets.QLabel('Current state: —')
        layout.addWidget(self.observed)
        layout.addWidget(self.button('Read MSM status', cmd.GET_MSM_STATUS))
        group = QtWidgets.QGroupBox('MSM test control')
        grid = QtWidgets.QGridLayout(group)
        self.state = QtWidgets.QComboBox()
        for number, name in enumerate(cmd.MSM_STATES):
            self.state.addItem(f'{number} — {name}', number)
        grid.addWidget(QtWidgets.QLabel('Select state'), 0, 0)
        grid.addWidget(self.state, 0, 1)
        grid.addWidget(self.button('Set state', cmd.SET_MSM_STATE, value=self.state.currentData), 0, 2)
        self.inputs = {}
        for row, field in enumerate(('reset', 'lowpower', 'fault'), 1):
            value = QtWidgets.QComboBox()

            for number in range(2):
                value.addItem(str(number), number)
            self.inputs[field] = value
            grid.addWidget(QtWidgets.QLabel(field.capitalize()), row, 0)
            grid.addWidget(value, row, 1)
            grid.addWidget(self.button('Set ' + field, cmd.MSM_INPUTS[field], value=value.currentData), row, 2)
        grid.addWidget(self.button('Complete current operation', cmd.MSM_DONE), 4, 0, 1, 3)
        layout.addWidget(group)
        layout.addStretch()

    def receive(self, line):
        # Only display queried state, never treat the selected target as actual state.
        match = re.search(r'\[CMD\] MSM=(\w+) seq=(\d+) power=(\d+)', line)
        if match:
            self.observed.setText(f'Current state: {match[1]}   |   Sequence: {match[2]}   |   Power: {match[3]}')
        elif '[CMD] module: not published' in line:
            self.observed.setText('Current state: not published')

    def reset(self):
        self.observed.setText('Current state: —')
