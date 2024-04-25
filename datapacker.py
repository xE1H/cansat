import struct
import ubinascii

structure = {
    "time": {
        # Time in ms since start of day
        "type": "unsigned int",
        "size": 4,
        "multiplier": 1
    },

    "lat": {
        "type": "int",
        "size": 4,
        # Scale down to 7 decimal places, should be enough
        "multiplier": 10 ** 7
    },
    "lon": {
        "type": "int",
        "size": 4,
        "multiplier": 10 ** 7
    },
    "gps_sats": {
        "type": "unsigned short",
        "size": 2,
        "multiplier": 1
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


}

types = {
    "int": "i",
    "unsigned int": "I",
    "short": "h",
    "unsigned short": "H"
}

size = sum([structure[i]["size"] for i in structure])  # 44 bytes == 352 bits\

for i in structure:
    structure[i]["value"] = 0

def set_value(value, key):
    structure[key]["value"] = value * structure[key]["multiplier"]


def set_values(values):
    for key in values:
        set_value(values[key], key)


def pack(dbg = False):
    fmt = ">" + "".join([types[structure[i]["type"]] for i in structure])

    dt = []
    for i in structure:
        if dbg:
            print(i, structure[i]["value"], structure[i].get("value", 0) * structure[i]["multiplier"])
        dt.append(int(structure[i].get("value", 0) * structure[i]["multiplier"]))

    s = struct.pack(fmt, *dt)
    # B64
    return ubinascii.b2a_base64(s).decode("utf-8")


def unpack(data):
    # Return a dictionary with the values
    fmt = ">" + "".join([types[structure[i]["type"]] for i in structure])
    ub = ubinascii.a2b_base64(data)
    unpacked = struct.unpack(fmt, data)

    return {list(structure.keys())[i]: unpacked[i] / list(structure.values())[i]["multiplier"] for i in
            range(len(structure))}
