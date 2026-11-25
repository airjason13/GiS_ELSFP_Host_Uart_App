"""Small parser for the current ELSFP text console (no Qt dependency)."""
import re

class ConsoleState:
    def __init__(self):
        self.lane = None
        self.rows = [{} for _ in range(8)]

    def parse(self, line):
        header = re.search(r'\[CMD\] Laser Lane ([1-8]) requested', line)
        if header:
            self.lane = int(header[1]) - 1
            self.rows[self.lane] = {}
            return self.lane
        if line.startswith('[CMD]') and 'Laser: not published' not in line:
            self.lane = None
        if self.lane is None:
            return None
        row = self.rows[self.lane]
        value = re.fullmatch(r'\s*(enable|bias|power|apc)=(.+)', line)
        if value:
            row[value[1]] = value[2]
        elif 'actual status: not published' in line:
            row['actual'] = 'Not published'
        elif line.strip().startswith('actual enabled='):
            row['actual'] = line.strip().removeprefix('actual ')
        elif 'Laser: not published' in line:
            row['measured'] = 'Not published'
        elif line.strip().startswith('measured bias='):
            row['measured'] = line.strip().removeprefix('measured ')
        else:
            return None
        return self.lane

class Pending:
    def __init__(self, opcode):
        self.opcode = opcode
        self.request_id = None

    def consume(self, line):
        accepted = re.search(r'\[CMD\] accepted id=(0x[\dA-Fa-f]+) op=(0x[\dA-Fa-f]+)', line)
        if accepted and int(accepted[2], 16) == self.opcode:
            self.request_id = int(accepted[1], 16)
        result = re.search(r'\[CMD\] result id=(0x[\dA-Fa-f]+) op=(0x[\dA-Fa-f]+) status=(-?\d+) (.*)', line)
        if result and self.request_id is not None and int(result[1], 16) == self.request_id and int(result[2], 16) == self.opcode:
            return result[4]
        if any(x in line for x in ('[CMD] busy:', '[CMD] request not queued', '[CMD] invalid', '[CMD] request IDs exhausted')):
            return line
        return None
