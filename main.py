import _thread

import machine
import utime

import datapacker
import log
from communication import radio433, gsm
from modules import onboard_logger, gps, ahrs
from hardware import bmp280, bme280, ms5611, battery, clock

log = log.Logger()
log.log('Logging started', 'blue')
clock = clock.Clock()
led = machine.Pin(15, machine.Pin.OUT)
battery = battery.Battery()
log.log('RTC and battery initialized', 'green')

onboard_logger = onboard_logger.OnboardLogger(datapacker)

if battery.voltage() < 3:
    log.log('Battery voltage low, expecting USB power', 'blue')
    log.log('Not clearing onboard log', 'red')
else:
    onboard_logger.clear_log()

log.log('Waiting for sensors to be ready', 'blue')
utime.sleep_ms(10000)
log.log('Starting setup', 'green')
i2c_main = machine.I2C(0, scl=machine.Pin(11), sda=machine.Pin(12))
log.log(f'Got following I2C devices on primary bus: {", ".join([str(hex(i)) for i in i2c_main.scan()])}', 'blue')

i2c_secondary = machine.I2C(1, scl=machine.Pin(5), sda=machine.Pin(3))
log.log(f'Got following I2C devices on secondary bus: {", ".join([str(hex(i)) for i in i2c_secondary.scan()])}', 'blue')

gsm_uart = machine.UART(0, tx=machine.Pin(17), rx=machine.Pin(16))
gsm = gsm.GSM(gsm_uart, datapacker)

ahrs = ahrs.AHRS(i2c_main, clock)

bmp = bmp280.BMP280(i2c_main, addr=0x77)
ms5611 = ms5611.MS5611(i2c_secondary)

bme = bme280.BME280(i2c=i2c_secondary, mode=4)

log.log('Sensors initialized', 'green')
radio_uart = machine.UART(1, baudrate=9600, tx=machine.Pin(33), rx=machine.Pin(34))
radio433 = radio433.Radio433(radio_uart, datapacker)

log.log('Switch UART to tx for radio and rx for GPS', 'blue')
radio_uart = machine.UART(1, baudrate=9600, tx=machine.Pin(33), rx=machine.Pin(38))
gps = gps.GPS(radio_uart, datapacker)

# Run radio loop in a separate thread to not block the main loop,
# use main loop only for sampling sensors and saving onboard
_thread.start_new_thread(radio433.loop, ())
_thread.start_new_thread(gsm.loop, ())
_thread.start_new_thread(gps.loop, ())
_thread.start_new_thread(onboard_logger.loop, ())
_thread.start_new_thread(ahrs.loop, ())

log.log('Starting sensor loop', 'blue')
while True:
    try:
        if led.value() == 0:
            led.value(1)
        else:
            led.value(0)

        accel = ahrs.accel
        gyro = ahrs.gyro
        mag = ahrs.mag

        bme_temp, bme_pressure, bme_hum = bme.values
        ms5611_temp, ms5611_pressure = ms5611.measurements

        millis = clock.millis()

        d = {
            "time": millis,
            "bat_v": battery.voltage(),

            "temp_bmp": bmp.temperature,
            "temp_mpu": ahrs.temp,
            "temp_bme": bme_temp,
            "temp_ms5611": ms5611_temp,

            "hum_bme": bme_hum,

            "baro_bmp": bmp.pressure,
            "baro_bme": bme_pressure,
            "baro_ms5611": ms5611_pressure,

            "acc_x": accel[0],
            "acc_y": accel[1],
            "acc_z": accel[2],

            "gyro_x": gyro[0],
            "gyro_y": gyro[1],
            "gyro_z": gyro[2],

            "mag_x": mag[0],
            "mag_y": mag[1],
            "mag_z": mag[2]
        }

        datapacker.set_values(d)

        utime.sleep_ms(2)
    except Exception as e:
        log.log(f'Got exception while reading data: {e}', 'red')
