from enum import Enum, unique

@unique
class FramesCategory(Enum):
    CONSTANT_DROWSINESS_FRAME_COUNT_LEVEL = [1, 2, 3]
    CONSTANT_NO_DROWSINESS_FRAME_COUNT = 2

@unique
class PwmLevels(Enum):
    MAX_LEVEL_PWM = 4
    MAX_DUTY_CYCLE_PWM = 100