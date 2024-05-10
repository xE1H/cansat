import log
from hardware import micropyGPS
import utime


class GPS:
    def __init__(self, uart, datapacker):
        self.uart = uart
        self.log = log.Logger("GPS")
        self.datapacker = datapacker
        self.parser = micropyGPS.MicropyGPS(local_offset=3,
                                            location_formatting="dd")  # offset for UTC+3, decimal degrees

        self.log.log('GPS initialized', 'green')

    def parse(self):
        gps_data = {}
        if self.uart.any():
            line = self.uart.readline()

            for c in line:
                self.parser.update(chr(c))
            # print("got", line)

            gps_data["lat"] = self.parser.latitude[0]
            gps_data["lon"] = self.parser.longitude[0]
            gps_data["gps_sats"] = self.parser.satellites_in_use
            gps_data["gps_hdop"] = self.parser.hdop
            gps_data["gps_alt"] = self.parser.altitude

            self.datapacker.set_values(gps_data)

    def loop(self):
        self.log.log('Starting GPS loop', 'blue')
        while True:
            try:
                self.parse()
                utime.sleep_ms(20)
            except Exception as e:
                self.log.log('GPS', f'Got exception while reading data: {e}', 'red')
                utime.sleep_ms(1000)
            utime.sleep_ms(10)
