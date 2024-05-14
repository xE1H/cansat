import struct
import ubinascii

structure = {
    "time": {
        # Time in ms since start of day
        "type": "unsigned int",
        "size": 4,
        "multiplier": 1
    },
    "bat_v": {
        "type": "unsigned short",
        "size": 2,
        "multiplier": 1000
    },

    "lat": {
        "type": "int",
        "size": 4,
        # Scale down to 7 decimal places, should be enough
        "multiplier": 10 ** 6
    },
    "lon": {
        "type": "int",
        "size": 4,
        "multiplier": 10 ** 6
    },
    "gps_sats": {
        "type": "unsigned char",
        "size": 1,
        "multiplier": 1
    },

    "gps_hdop": {
        "type": "unsigned short",
        "size": 2,
        "multiplier": 10
    },
    "gps_alt": {
        "type": "unsigned short",
        "size": 2,
        "multiplier": 10
    },

    "gsm_signal": {
        "type": "unsigned char",
        "size": 1,
        "multiplier": 100
    },

    "baro_bmp": {
        "type": "unsigned int",
        "size": 4,
        "multiplier": 10000
    },
    "baro_bme": {
        "type": "unsigned int",
        "size": 4,
        "multiplier": 10000
    },
    "baro_ms5611": {
        "type": "unsigned int",
        "size": 4,
        "multiplier": 10000
    },

    "temp_bmp": {
        "type": "short",
        "size": 4,
        "multiplier": 100
    },
    "temp_mpu": {
        "type": "short",
        "size": 4,
        "multiplier": 100
    },
    "temp_bme": {
        "type": "short",
        "size": 4,
        "multiplier": 100
    },
    "temp_ms5611": {
        "type": "short",
        "size": 4,
        "multiplier": 100
    },

    "hum_bme": {
        "type": "short",
        "size": 4,
        "multiplier": 100
    },

    "acc_x": {
        "type": "int",
        "size": 4,
        "multiplier": 1000
    },
    "acc_y": {
        "type": "int",
        "size": 4,
        "multiplier": 1000
    },
    "acc_z": {
        "type": "int",
        "size": 4,
        "multiplier": 1000
    },

    "gyro_x": {
        "type": "int",
        "size": 4,
        "multiplier": 1000
    },
    "gyro_y": {
        "type": "int",
        "size": 4,
        "multiplier": 1000
    },
    "gyro_z": {
        "type": "int",
        "size": 4,
        "multiplier": 1000
    },
    "mag_x": {
        "type": "int",
        "size": 4,
        "multiplier": 1
    },
    "mag_y": {
        "type": "int",
        "size": 4,
        "multiplier": 1
    },
    "mag_z": {
        "type": "int",
        "size": 4,
        "multiplier": 1
    },

    "ahrs_x": {
        "type": "int",
        "size": 4,
        "multiplier": 1000
    },
    "ahrs_y": {
        "type": "int",
        "size": 4,
        "multiplier": 1000
    },
    "ahrs_z": {
        "type": "int",
        "size": 4,
        "multiplier": 1000
    },

    "ens_tvoc": {
        "type": "unsigned short",
        "size": 2,
        "multiplier": 1
    },
    "ens_eco2": {
        "type": "unsigned short",
        "size": 2,
        "multiplier": 1
    },

    "als": {
        "type": "unsigned short",
        "size": 2,
        "multiplier": 1
    },

    "vspd": {
        "type": "int",
        "size": 4,
        "multiplier": 1000
    }
}

sequencing = [
    "time",
    "bat_v",
    "lat",
    "lon",
    "gps_sats",
    "gps_hdop",
    "gps_alt",
    "gsm_signal",
    "baro_bmp",
    "baro_bme",
    "baro_ms5611",
    "temp_bmp",
    "temp_mpu",
    "temp_bme",
    "temp_ms5611",
    "hum_bme",
    "acc_x",
    "acc_y",
    "acc_z",
    "gyro_x",
    "gyro_y",
    "gyro_z",
    "mag_x",
    "mag_y",
    "mag_z",
    "ahrs_x",
    "ahrs_y",
    "ahrs_z",
    "ens_tvoc",
    "ens_eco2",
    "als",
    "vspd"
]

types = {
    "int": "i",
    "unsigned int": "I",
    "short": "h",
    "unsigned short": "H",
    "unsigned char": "B"
}

size = sum([structure[i]["size"] for i in structure])  # 44 bytes == 352 bits\

for i in structure:
    structure[i]["value"] = 0


def set_value(value, key):
    structure[key]["value"] = value


def set_values(values):
    for key in values:
        set_value(values[key], key)


dataminmax = {
    "int": {
        "min": -2147483648,
        "max": 2147483647
    },
    "unsigned int": {
        "min": 0,
        "max": 4294967295
    },
    "short": {
        "min": -32768,
        "max": 32767
    },
    "unsigned short": {
        "min": 0,
        "max": 65535
    },
    "unsigned char": {
        "min": 0,
        "max": 255
    }
}


def pack(dbg=False):
    # fmt = ">" + "".join([types[structure[i]["type"]] for i in structure])
    # Pack using sequiencing
    fmt = ">" + "".join([types[structure[i]["type"]] for i in sequencing])

    dt = []
    for i in sequencing:
        val = structure[i]["value"] * structure[i]["multiplier"]
        # print(i, "=", val, end="; ")
        dt.append(int(val))

    # print()
    # Check for int/short overflow
    for i in sequencing:
        if structure[i].get("value", 0) * structure[i]["multiplier"] < dataminmax[structure[i]["type"]]["min"] or \
                structure[i].get("value", 0) * structure[i]["multiplier"] > dataminmax[structure[i]["type"]]["max"]:
            raise Exception(
                f"Overflow {i} {structure[i].get('value', 0)} {structure[i]['multiplier']} {structure[i].get('value', 0) * structure[i]['multiplier']} {dataminmax[structure[i]['type']]['min']} {dataminmax[structure[i]['type']]['max']}")
        # print("Overflow", i, structure[i].get("value", 0), structure[i]["multiplier"], structure[i].get("value", 0) * structure[i]["multiplier"], dataminmax[structure[i]["type"]]["min"],
        #      dataminmax[structure[i]["type"]]["max"])

    s = struct.pack(fmt, *dt)
    # B64
    b = ubinascii.b2a_base64(s).decode("utf-8")
    return b


def unpack(data):
    # Return a dictionary with the values
    fmt = ">" + "".join([types[structure[i]["type"]] for i in structure])
    ub = ubinascii.a2b_base64(data)
    unpacked = struct.unpack(fmt, ub)

    return {list(structure.keys())[i]: unpacked[i] / list(structure.values())[i]["multiplier"] for i in
            range(len(structure))}
