import _thread
import utime

import machine

import datapacker
import log

from hardware import lora_e220, micropyGPS, bmp280, bme280, ms5611, sim800l, lora_e220_constants, battery
from hardware.imu import MPU6050

######## GENERAL SETUP  #########
log = log.Logger()
log.log('MAIN', 'Logging started', 'blue')

rtc = machine.RTC()
battery = battery.Battery()

log.log('MAIN', 'RTC and battery initialized', 'green')

if battery.voltage() < 3:
    log.log('MAIN', 'Battery voltage low, expecting USB power', 'red')
    log.log('MAIN', 'Not clearing onboard log', 'red')
else:
    f = open("/onboard.log", "w").close()


def onboard_log_loop():
    while True:
        utime.sleep_ms(950)
        try:
            with open("/onboard.log", "a") as f:
                f.write(datapacker.pack())
        except OSError as e:
            log.log('ONBOARD', f'Got exception while writing data to onboard log: {e}', 'red')


log.log('ONBOARD', 'Onboard log initialized', 'green')

log.log('MAIN', 'Waiting for sensors to be ready', 'blue')
utime.sleep_ms(10000)
log.log('MAIN', 'Starting setup', 'green')

########## I2C SETUP ############
i2c_main = machine.SoftI2C(scl=machine.Pin(11), sda=machine.Pin(12))
# ['0x69' -- 6500, '0x76' -- bmp]
log.log('I2C Main', f'Got following I2C devices: {", ".join([str(hex(i)) for i in i2c_main.scan()])}', 'blue')

i2c_secondary = machine.SoftI2C(scl=machine.Pin(3), sda=machine.Pin(5))  # todo
# ['0x76' -- bme280, '0x77' -- ms5611]
log.log('I2C Secondary', f'Got following I2C devices: {", ".join([str(hex(i)) for i in i2c_secondary.scan()])}', 'blue')

###########  GSM SETUP   ############
gsm_uart = machine.UART(0, tx=machine.Pin(17), rx=machine.Pin(16))
gsm = sim800l.Modem(  # todo
    uart=gsm_uart
)
gsm.initialize()
log.log('GSM', 'GSM modem initialized', 'green')
gsm.connect('internet.tele2.lt')
log.log('GSM', 'GSM modem connected to APN', 'green')

first_gsm_request = True
should_close = False


def gsm_loop():
    global first_gsm_request, should_close
    utime.sleep_ms(10000)  # Do not overwhelm the modem with requests
    while True:
        try:
            ip = gsm.get_ip_addr()
            datapacker.set_value(gsm.get_signal_strength(), "gsm_signal")
            if ip:
                packed_data = datapacker.pack()
                packed_data = packed_data.replace("\n", "").replace("+", "%2B").replace("=", "%3D").replace("/", "%2F")

                gsm.http_request(f"http://130.61.136.101:8018/sat/gsm?data={packed_data}", "POST", "d",
                                 should_close=should_close, should_open=first_gsm_request)
                first_gsm_request = False
                should_close = False
                utime.sleep_ms(50)
            else:
                # Not connected, wait
                utime.sleep_ms(1000)
                log.log('GSM', 'Not connected to GSM network', 'red')
        except Exception as e:
            log.log('GSM', f'Got exception while sending data: {e}', 'red')
            gsm_uart.read()  # Clear the buffer
            should_close = True
            first_gsm_request = True
            utime.sleep_ms(1000)


########### SENSOR SETUP ############
mpu = MPU6050(i2c_main, device_addr=1)
bmp = bmp280.BMP280(i2c_main, addr=0x77)
ms5611 = ms5611.MS5611(i2c_secondary)

bme = bme280.BME280(i2c=i2c_secondary, mode=4)

log.log('Sensors', 'Sensors initialized', 'green')

########### RADIO SETUP  ############
radio_uart = machine.UART(1, baudrate=9600, tx=machine.Pin(33), rx=machine.Pin(34))

radio = lora_e220.LoRaE220('400T22D', radio_uart, m1_pin=35, m0_pin=39)

radio_configuration = lora_e220.Configuration("400T22D")
radio_configuration.CHAN = 42
radio_configuration.TRANSMISSION_MODE.enableRSSI = lora_e220_constants.RssiEnableByte.RSSI_ENABLED

code = radio.set_configuration(radio_configuration)
radio.begin()
log.log('Radio', 'Radio initialized', 'green')


def radio_loop():
    while True:
        try:
            dp = datapacker.pack().replace("\n", "") + "@"
            radio_uart.write(dp.encode("utf-8"))
            utime.sleep_ms(750)
        except Exception as e:
            log.log('Radio', f'Got exception while sending data: {e}', 'red')
            utime.sleep_ms(1000)


###########  GPS SETUP   ############
log.log('MAIN', 'Switch UART to tx for radio and rx for GPS', 'blue')
radio_uart = machine.UART(1, baudrate=9600, tx=machine.Pin(33), rx=machine.Pin(38))
# Use TX for radio, but RX for GPS, so we can use the same uart for both. No more uart pins needed.
gps = radio_uart
gps_parser = micropyGPS.MicropyGPS(local_offset=3, location_formatting="dd")  # offset for UTC+3, decimal degrees
log.log('GPS', 'GPS initialized', 'green')


def gps_loop():
    while True:
        try:
            gps_data = {}
            if gps.any():
                line = gps.readline()

                for c in line:
                    gps_parser.update(chr(c))

                gps_data["lat"] = gps_parser.latitude[0]
                gps_data["lon"] = gps_parser.longitude[0]
                gps_data["gps_sats"] = gps_parser.satellites_in_use
                gps_data["gps_hdop"] = gps_parser.hdop
                gps_data["gps_alt"] = gps_parser.altitude

                datapacker.set_values(gps_data)

            utime.sleep_ms(20)
        except Exception as e:
            log.log('GPS', f'Got exception while reading data: {e}', 'red')
            utime.sleep_ms(1000)
        utime.sleep_ms(10)


# Run radio loop in a separate thread to not block the main loop,
# use main loop only for sampling sensors and saving onboard
_thread.start_new_thread(radio_loop, ())
_thread.start_new_thread(gsm_loop, ())
_thread.start_new_thread(gps_loop, ())
_thread.start_new_thread(onboard_log_loop, ())
log.log('MAIN', 'Started radio, GPS, GSM and data logger loop', 'green')

led = machine.Pin(15, machine.Pin.OUT)

log.log('MAIN', 'Starting sensor loop', 'blue')
while True:
    try:
        if led.value() == 0:
            led.value(1)
        else:
            led.value(0)

        accel = mpu.accel.xyz
        gyro = mpu.gyro.xyz
        bme_temp, bme_pressure, bme_hum = bme.values
        ms5611_temp, ms5611_pressure = ms5611.measurements

        # rtc.datetime() returns a tuple with the following format:
        # (year, month, day[, hour[, minute[, second[, microsecond)

        millis = int(
            rtc.datetime()[-4] * 3600000 + rtc.datetime()[-3] * 60000 + rtc.datetime()[-2] * 1000 + rtc.datetime()[
                -1] // 1000)

        d = {
            "time": millis,
            "bat_v": battery.voltage(),

            "temp_bmp": bmp.temperature,
            "temp_mpu": mpu.temperature,
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
            "gyro_z": gyro[2]
        }

        datapacker.set_values(d)

        # Save data to the SD card
        try:
            pass
            # with open(f"sd/data-{millis}", "a") as f:
            #     f.write(datapacker.pack(True))
        except OSError as e:
            datapacker.pack(False)

        utime.sleep_ms(20)
    except Exception as e:
        log.log('SENSORS', f'Got exception while reading data: {e}', 'red')
