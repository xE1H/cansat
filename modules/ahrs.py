# AHRS using MPU6050 and magnetometer
import math
import utime

from algorithms.madgwickahrs import MadgwickAHRS
from algorithms.quaternion import Quaternion
from hardware.hmc5883l import HMC5883L
from hardware.imu import MPU6050

from algorithms.umatrix import matrix


class AHRS:
    def __init__(self, i2c, clock):
        self.mpu = MPU6050(i2c, device_addr=1, gyro_calibration=(1.797567, 0.06129264, 0.4031449),
                           accel_calibration=(5.30599 * (10 ** -5), -0.02539356, -0.02039746))

        self.accel = [0, 0, 0]
        self.gyro = [0, 0, 0]
        self.mag = [0, 0, 0]
        self.pos = (0, 0, 0)
        self.temp = 0

        self.clock = clock

        self.compass = HMC5883L(i2c)

        startqt = Quaternion(0.7071068, 0, 0, -0.7071068)

        self.madgwick = MadgwickAHRS()

    def update(self, t):
        self.gyro = self.mpu.gyro.xyz  # in deg/s, convert to rad/s
        self.accel = self.mpu.accel.xyz
        self.temp = self.mpu.temperature

        self.mag = self.get_mag()
        # self.madgwick.update(matrix([[a * math.pi / 180 for a in self.gyro]]),
        #                      matrix([[a for a in self.mpu.accel.xyz]]),
        #                      matrix([[a] for a in self.mag]), t)
        #
        # self.pos = self.position()

        # self.madgwick.update_imu(matrix([[a * math.pi / 180 for a in self.gyro]]), matrix([list(self.accel)]), t)

    def position(self):
        try:
            x, y, z = self.madgwick.quaternion.to_euler_angles()
            return x * 180.0 / math.pi, y * 180.0 / math.pi, z * 180.0 / math.pi
        except:
            return 0, 0, 0

    def loop(self):
        self.last_update = self.clock.millis()
        while True:
            self.update(self.clock.millis() - self.last_update)
            self.last_update = self.clock.millis()
            utime.sleep_ms(1)

    def get_mag(self):
        f = self.compass.read()

        return f[1], -f[0], f[2]
