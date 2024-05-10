import utime

from hardware import lora_e220, lora_e220_constants
from log import Logger


class Radio433:
    def __init__(self, uart, datapacker):
        self.uart = uart
        self.datapacker = datapacker
        self.log = Logger('Radio')

        self.radio = lora_e220.LoRaE220('400T22D', self.uart, m1_pin=35, m0_pin=39)

        radio_configuration = lora_e220.Configuration("400T22D")
        radio_configuration.CHAN = 42
        radio_configuration.TRANSMISSION_MODE.enableRSSI = lora_e220_constants.RssiEnableByte.RSSI_ENABLED

        self.radio.set_configuration(radio_configuration)
        self.radio.begin()
        self.log.log( 'Radio initialized', 'green')

    def send(self, data):
        try:
            dp = data + "@"
            self.uart.write(dp.encode("utf-8"))
            utime.sleep_ms(750)
        except Exception as e:
            self.log.log(f'Got exception while sending data: {e}', 'red')
            utime.sleep_ms(1000)

    def loop(self):
        self.log.log('Starting radio loop', 'blue')
        while True:
            self.send(self.datapacker.pack().replace("\n", ""))
            utime.sleep_ms(750)
