from PyQt5 import QtWidgets
import commands as cmd
from cmd_page import CommandPage


class LaserPage(CommandPage):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(8, 8)
        self.table.setHorizontalHeaderLabels(['Lane', 'Req Enable', 'Req Bias', 'Req Power',
                                              'Req APC', 'Actual state', 'Measured', 'Last received'])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(25)
        self.table.setMinimumHeight(235)
        layout.addWidget(self.table)
        controls = QtWidgets.QGroupBox('Laser settings')
        grid = QtWidgets.QGridLayout(controls)
        self.lane = QtWidgets.QComboBox()
        self.lane.addItems([str(i) for i in range(1, 9)] + ['all'])
        grid.addWidget(QtWidgets.QLabel('Lane'), 0, 0)
        grid.addWidget(self.lane, 0, 1)
        self.values = {}
        for row, (field, title) in enumerate([('enable', 'Enable (0/1)'), ('bias', 'Bias (µA)'),
                                              ('power', 'Power (µW)'), ('apc', 'APC (0/1)')], 1):
            value = QtWidgets.QSpinBox()
            value.setRange(*cmd.LASER_SETTINGS[field].value_range)
            self.values[field] = value
            button = self.button('Send ' + field, cmd.LASER_SETTINGS[field],
                                 lane=self.lane.currentText, value=value.value)
            grid.addWidget(QtWidgets.QLabel(title), row, 0)
            grid.addWidget(value, row, 1)
            grid.addWidget(button, row, 2)
        layout.addWidget(controls)
        queries = QtWidgets.QHBoxLayout()
        queries.addWidget(self.button('Read selected lane', cmd.GET_LASER_STATUS, lane=self.lane.currentText))
        queries.addWidget(self.button('Read all lanes', cmd.GET_LASER_STATUS, lane='all'))
        layout.addLayout(queries)
