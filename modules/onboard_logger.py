import utime

import log


class OnboardLogger:
    # Onboard logging
    # Logs data to a file on the MCU
    def __init__(self, datapacker):
        self.log = log.Logger('Onboard')
        self.datapacker = datapacker

        self.log.log('Onboard logging initialized', 'green')

    def clear_log(self):
        open('onboard.log', 'w').close()

    def log_write(self, message):
        with open('onboard.log', 'a') as f:
            f.write(f'{message}')

    def loop(self):
        self.log.log('Starting onboard logging loop', 'blue')
        while True:
            utime.sleep_ms(950)
            try:
                self.log_write(self.datapacker.pack())
            except Exception as e:
                self.log.log(f'Error while logging: {e}', 'red')
