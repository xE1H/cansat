from hardware import sim800l
from log import Logger

import utime

GSM_APN = 'internet.tele2.lt'

DOWNSTREAM_IP = '130.61.136.101'
DOWNSTREAM_PORT = 8019


class GSM:
    def __init__(self, uart, datapacker):
        self.uart = uart
        self.datapacker = datapacker
        self.log = Logger('GSM')
        uart.write(b"\x1a")
        uart.read()
        self.modem = sim800l.Modem(uart=self.uart)

        self.modem.initialize()
        self.log.log('Modem initialized', 'green')
        self.modem.connect(GSM_APN)
        self.log.log('Modem connected to APN', 'green')

    def set_signal_strength(self):
        self.datapacker.set_value(self.modem.get_signal_strength(), "gsm_signal")

    def get_ip_addr(self):
        return self.modem.get_ip_addr()

    def send_data(self, data):
        ip = self.get_ip_addr()
        if ip:
            self.modem.send_tcp(data)
        else:
            # Not connected, wait
            utime.sleep_ms(1000)
            self.log.log('Not connected to GSM network', 'red')

    def open(self):
        self.modem.open_tcp(DOWNSTREAM_IP, DOWNSTREAM_PORT)

    def close(self):
        self.modem.close_tcp()

    def loop(self):
        utime.sleep_ms(10000)  # Wait for modem to be ready
        self.log.log('Starting GSM loop', 'blue')
        self.open()
        while True:
            try:
                self.set_signal_strength()
                self.send_data(self.datapacker.pack())
            except Exception as e:
                self.log.log(f'Got exception while sending data: {e}', 'red')
                self.uart.read()  # Clear the buffer
                # Close and open the connection, in case the connection is lost for
                # some reason this should recover it 99% of the time if signal is still there
                self.close()
                self.open()
                utime.sleep_ms(1000)
