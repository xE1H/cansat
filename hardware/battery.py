import machine


class Battery:
    def __init__(self):
        self.battery = machine.ADC(machine.Pin(7), atten=machine.ADC.ATTN_11DB)
        self._last_vals = []

    def raw_voltage(self):
        # Battery voltage in V
        return self.battery.read_uv() / 1000000 * 4

    def voltage(self):
        # Take average of last 50 readings
        vals = self._last_vals
        if len(vals) < 50:
            vals.append(self.raw_voltage())
        else:
            vals.pop(0)
            vals.append(self.raw_voltage())

        return sum(vals) / len(vals)
