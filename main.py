#!/usr/bin/env python3
"""ELSFP UART bench console. Never sends settings automatically."""
import sys
import time
from datetime import datetime
import serial
from serial.tools import list_ports
from PyQt5 import QtCore, QtWidgets
from protocol import ConsoleState, Pending
from laser_page import LaserPage
from msm_page import MsmPage
from system_page import SystemPage

class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ELSFP UART Tool — 8 Lane')
        self.resize(1120, 780)
        self.port = None
        self.pending = None
        self.buffer = bytearray()
        self.state = ConsoleState()
        self.deadline = 0
        self.tx_buttons = []
        self.setting_buttons = []
        self.query_until = 0
        root = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(root)
        self.setCentralWidget(root)
        link = QtWidgets.QHBoxLayout()
        self.ports = QtWidgets.QComboBox(); self.ports.setEditable(True)
        refresh = QtWidgets.QPushButton('Refresh ports'); refresh.clicked.connect(self.refresh_ports)
        self.baud = QtWidgets.QComboBox(); self.baud.addItems(['115200', '9600', '57600', '230400'])
        self.connect_button = QtWidgets.QPushButton('Connect'); self.connect_button.clicked.connect(self.toggle)
        for widget in (QtWidgets.QLabel('Port'), self.ports, refresh, QtWidgets.QLabel('Baud'), self.baud, self.connect_button): link.addWidget(widget)
        layout.addLayout(link)
        self.status = QtWidgets.QLabel('Disconnected'); layout.addWidget(self.status)
        self.tabs = QtWidgets.QTabWidget()
        self.laser_page = LaserPage()
        self.msm_page = MsmPage()
        self.system_page = SystemPage()
        for title, page in [('Laser', self.laser_page), ('MSM', self.msm_page), ('System', self.system_page)]:
            self.tabs.addTab(page, title)
            page.command.connect(self.send)
            self.tx_buttons.extend(page.tx_buttons)
            self.setting_buttons.extend(page.setting_buttons)
        self.table = self.laser_page.table
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.addWidget(self.tabs)
        layout.addWidget(self.splitter, 1)
        self.log = QtWidgets.QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMaximumBlockCount(5000)
        self.splitter.addWidget(self.log)
        self.splitter.setSizes([540, 180])
        actions = QtWidgets.QHBoxLayout()
        clear = QtWidgets.QPushButton('Clear log'); clear.clicked.connect(self.log.clear)
        save = QtWidgets.QPushButton('Save log'); save.clicked.connect(self.save_log)
        actions.addWidget(clear); actions.addWidget(save); layout.addLayout(actions)
        self.timer = QtCore.QTimer(self); self.timer.timeout.connect(self.poll); self.timer.start(20)
        self.refresh_ports(); self.reset_table(); self.update_buttons()

    def refresh_ports(self):
        current = self.ports.currentText(); self.ports.clear()
        self.ports.addItems([p.device for p in list_ports.comports()])
        if current: self.ports.setCurrentText(current)

    def reset_table(self):
        for row in range(8):
            for col in range(8): self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(row + 1) if col == 0 else '—'))

    def append(self, direction, text):
        self.log.appendPlainText(f'{datetime.now():%H:%M:%S.%f}'[:-3] + f' {direction} {text}')

    def update_buttons(self):
        ready = self.port is not None and time.monotonic() >= self.query_until
        for button in self.tx_buttons:
            button.setEnabled(ready and (self.pending is None or button not in self.setting_buttons))
        self.ports.setEnabled(self.port is None); self.baud.setEnabled(self.port is None)

    def toggle(self):
        if self.port:
            self.disconnect('Disconnected')
            return
        try:
            self.port = serial.Serial(self.ports.currentText().strip(), int(self.baud.currentText()), timeout=0, write_timeout=0.2, rtscts=False, dsrdtr=False, xonxoff=False)
            self.buffer.clear(); self.pending = None; self.state = ConsoleState(); self.reset_table()
            self.msm_page.reset(); self.system_page.reset(); self.query_until = 0
            self.connect_button.setText('Disconnect'); self.status.setText('Connected')
            self.append('INFO', 'Connected')
        except (serial.SerialException, ValueError, OSError) as exc:
            self.port = None; self.status.setText(str(exc))
        self.update_buttons()

    def disconnect(self, reason):
        if self.port:
            try: self.port.close()
            except (serial.SerialException, OSError): pass
        self.port = None; self.pending = None; self.buffer.clear()
        self.state.lane = None
        self.reset_table(); self.msm_page.reset(); self.system_page.reset()
        self.connect_button.setText('Connect'); self.status.setText(reason); self.append('INFO', reason); self.update_buttons()

    def send(self, command, opcode=None):
        if not self.port or (opcode is not None and self.pending) or time.monotonic() < self.query_until: return
        try:
            # No raw/manual commands: enforce the firmware's 64-byte line limit.
            data = command.encode('ascii')
            if len(data) > 64: raise ValueError('Command exceeds 64 bytes')
            if opcode is not None:
                self.pending = Pending(opcode); self.deadline = time.monotonic() + 6
                self.status.setText('Waiting: ' + command)
            else:
                self.query_until = time.monotonic() + 1.5
                self.status.setText('Sent: ' + command)
            self.state.lane = None
            payload = data + b'\r\n'
            if self.port.write(payload) != len(payload): raise OSError('Partial write; command state unknown')
            self.append('TX', command)
        except (serial.SerialException, OSError, ValueError) as exc:
            self.disconnect('TX error: ' + str(exc))
        self.update_buttons()

    def poll(self):
        if not self.port: return
        try:
            data = self.port.read(min(self.port.in_waiting, 4096))
            if data:
                self.buffer.extend(data)
                while b'\n' in self.buffer:
                    raw, _, rest = self.buffer.partition(b'\n'); self.buffer = bytearray(rest)
                    self.on_line(raw.rstrip(b'\r').decode('ascii', errors='replace'))
                if len(self.buffer) > 8192:
                    self.append('RX', '[overlong/incomplete line discarded]'); self.buffer.clear(); self.state.lane = None
            if self.pending and time.monotonic() >= self.deadline:
                # Release the UI only; the firmware request may still execute.
                self.pending = None
                message = 'Timeout (6 s): result unknown'
                self.status.setText(message)
                self.append('INFO', message)
            self.update_buttons()
        except (serial.SerialException, OSError) as exc:
            self.disconnect('RX error: ' + str(exc))

    def on_line(self, line):
        self.append('RX', line)
        self.msm_page.receive(line)
        self.system_page.receive(line)
        row = self.state.parse(line)
        if row is not None:
            values = self.state.rows[row]
            for col, key in enumerate(['enable', 'bias', 'power', 'apc', 'actual', 'measured'], 1):
                self.table.item(row, col).setText(values.get(key, '—'))
            self.table.item(row, 7).setText(datetime.now().strftime('%H:%M:%S'))
        if self.pending:
            outcome = self.pending.consume(line)
            if outcome is not None:
                self.status.setText(outcome)
                self.pending = None
                # Let firmware finish its following lane-mask log line.
                self.query_until = time.monotonic() + 0.2

    def save_log(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save visible log', 'elsfp_uart.log', 'Log (*.log);;Text (*.txt)')
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f: f.write(self.log.toPlainText() + '\n')
            except OSError as exc: QtWidgets.QMessageBox.warning(self, 'Save failed', str(exc))

    def closeEvent(self, event):
        self.disconnect('Closed'); event.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Window(); window.show()
    sys.exit(app.exec_())
