import _thread
import os

import machine

import datapacker
from hardware import lora_e220, micropyGPS, bmp280, bme280, ms5611, sim800l, lora_e220_constants
from hardware.imu import MPU6050

######## GENERAL SETUP  #########

rtc = machine.RTC()
# sd = machine.SDCard(slot=2, miso=18, mosi=21, sck=8, cs=9, freq=2_000_000)
#
# os.mount(sd, "/sd")
#
# print(os.listdir("/sd"))

########## I2C SETUP ############
i2c_main = machine.SoftI2C(scl=machine.Pin(11), sda=machine.Pin(12))
print([i for i in i2c_main.scan()])  # ['0x68' -- 6500, '0x76' -- bmp, '0x77' -- ms5611]

i2c_secondary = machine.SoftI2C(scl=machine.Pin(3), sda=machine.Pin(5))  # todo
print([i for i in i2c_secondary.scan()])  # ['0x76' -- bme280]

###########  GSM SETUP   ############
gsm = sim800l.Modem(  # todo
    uart=machine.UART(2, tx=machine.Pin(17), rx=machine.Pin(16))
)

gsm.initialize()
gsm.connect('internet.tele2.lt')


def gsm_loop():
    while True:
        print(gsm.get_ip_addr())
        print(gsm.get_info())
        print(gsm.get_signal_strength())

        gsm.http_request("https://sat.xe1h.xyz/sat/gsm", "POST", datapacker.pack(), "text/plain")
        utime.sleep_ms(20)


########### SENSOR SETUP ############
mpu = MPU6050(i2c_main, device_addr=0)
bmp = bmp280.BMP280(i2c_main)
ms5611 = ms5611.MS5611(i2c_main)  # todo

bme = bme280.BME280(i2c_secondary)

########### RADIO SETUP  ############
radio = lora_e220.LoRaE220('400T22D', machine.UART(1, tx=machine.Pin(33), rx=machine.Pin(34)))

radio_configuration = lora_e220.Configuration("400T22D")

radio_configuration.CHAN = 24
radio_configuration.TRANSMISSION_MODE.enableRSSI = lora_e220_constants.RssiEnableByte.RSSI_ENABLED

radio.set_configuration(radio_configuration)

_, configuration = radio.get_configuration()

lora_e220.print_configuration(configuration)

radio.begin()


def radio_loop():
    while True:
        dp = datapacker.pack()
        code = radio.send_transparent_message(dp)
        utime.sleep_ms(20)


###########  GPS SETUP   ############

gps = machine.UART(0, baudrate=9600, tx=machine.Pin(37), rx=machine.Pin(38))
gps_parser = micropyGPS.MicropyGPS(local_offset=3, location_formatting="dd")  # offset for UTC+3, decimal degrees


def gps_loop():
    while True:
        gps_data = {}
        if gps.any():
            line = gps.readline()

            for c in line:
                gps_parser.update(chr(c))

            gps_data["lat"] = gps_parser.latitude[0]
            gps_data["lon"] = gps_parser.longitude[0]

            seconds = gps_parser.timestamp[2]
            # Seconds is a float, convert to seconds int and microseconds int
            microseconds = int((seconds - int(seconds)) * 1000000)
            seconds = int(seconds)

            current_dt = (gps_parser.date[2], gps_parser.date[1], gps_parser.date[0], gps_parser.timestamp[0],
                          gps_parser.timestamp[1], seconds, microseconds)

            # Set the RTC time to the GPS time
            rtc.datetime(current_dt)

            gps_data["gps_sats"] = gps_parser.satellites_in_use

            datapacker.set_values(gps_data)


# Run radio loop in a separate thread to not block the main loop,
# use main loop only for sampling sensors and saving onboard
_thread.start_new_thread(radio_loop, ())
_thread.start_new_thread(gsm_loop, ())
_thread.start_new_thread(gps_loop, ())

while True:
    accel = mpu.accel.xyz
    gyro = mpu.gyro.xyz
    bme_temp, bme_pressure, bme_hum = bme.values
    ms5611_temp, ms5611_pressure = ms5611.measurements

    # millis since start of day
    # rtc.datetime() returns a tuple with the following format:
    # (year, month, day[, hour[, minute[, second[, microsecond)

    millis = int(
        rtc.datetime()[3] * 3600000 + rtc.datetime()[4] * 60000 + rtc.datetime()[5] * 1000 + rtc.datetime()[6] // 1000)

    d = {
        "time": millis,

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
    with open("data.txt", "a") as f:
        f.write(datapacker.pack() + "\n")
