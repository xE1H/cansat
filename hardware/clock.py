import machine


class Clock(machine.RTC):
    def __init__(self):
        super().__init__()

    def millis(self):
        dt = self.datetime()
        return int(
            dt[-4] * 3600000 + dt[-3] * 60000 + dt[-2] * 1000 + dt[-1] // 1000)
