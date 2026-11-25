"""UART command definitions. Keep wire syntax and opcodes in this module."""
from dataclasses import dataclass
from enum import IntEnum


class AppOpcode(IntEnum):
    """Keep names and values synchronized with firmware AppOpcode_t."""
    APP_CMD_MSM_PUBLISH = 0x7002
    APP_CMD_MSM_RESET = 0x7003
    APP_CMD_MSM_LOWPOWER = 0x7004
    APP_CMD_MSM_FAULT = 0x7005
    APP_CMD_MSM_DONE = 0x7006
    APP_CMD_MSM_SET_STATE = 0x7007
    APP_CMD_LASER_ENABLE = 0x7010
    APP_CMD_LASER_BIAS = 0x7011
    APP_CMD_LASER_POWER = 0x7012
    APP_CMD_LASER_APC = 0x7013


MSM_STATES = ('Resetting', 'Reset', 'MgmtInit', 'ModuleLowPwr',
              'ModulePwrUp', 'ModuleReady', 'ModulePwrDn', 'ModuleFault')


@dataclass(frozen=True)
class Command:
    template: str
    opcode: AppOpcode | None = None
    value_range: tuple[int, int] | None = None

    def build(self, **params):
        """Validate UI input and return the command without its line ending."""
        if '{lane}' in self.template:
            if str(params.get('lane')) not in tuple(map(str, range(1, 9))) + ('all',):
                raise ValueError('Lane must be 1..8 or all')
        if self.value_range is not None:
            value = params.get('value')
            low, high = self.value_range
            if not isinstance(value, int) or not low <= value <= high:
                raise ValueError(f'Value must be {low}..{high}')
        return self.template.format(**params)


# System queries
GET_SYSTEM_VERSION = Command('get system version')
GET_SYSTEM_STATUS = Command('get system status')
GET_ELSFP_STATUS = Command('get elsfp status')
HELP = Command('help')

# Laser queries and settings: field -> wire format, result opcode, value range.
GET_LASER_STATUS = Command('get laser {lane} status')
LASER_SETTINGS = {
    'enable': Command('set laser {lane} enable {value}', AppOpcode.APP_CMD_LASER_ENABLE, (0, 1)),
    'bias':   Command('set laser {lane} bias {value}',   AppOpcode.APP_CMD_LASER_BIAS, (0, 2147483647)),
    'power':  Command('set laser {lane} power {value}',  AppOpcode.APP_CMD_LASER_POWER, (0, 2147483647)),
    'apc':    Command('set laser {lane} apc {value}',    AppOpcode.APP_CMD_LASER_APC, (0, 1)),
}

# MSM test controls
GET_MSM_STATUS = Command('get msm status')
SET_MSM_STATE = Command('set msm state {value}', AppOpcode.APP_CMD_MSM_SET_STATE, (0, len(MSM_STATES) - 1))
MSM_INPUTS = {
    'reset':    Command('set msm reset {value}',    AppOpcode.APP_CMD_MSM_RESET, (0, 1)),
    'lowpower': Command('set msm lowpower {value}', AppOpcode.APP_CMD_MSM_LOWPOWER, (0, 1)),
    'fault':    Command('set msm fault {value}',    AppOpcode.APP_CMD_MSM_FAULT, (0, 1)),
}
MSM_DONE = Command('set msm done 1', AppOpcode.APP_CMD_MSM_DONE)
