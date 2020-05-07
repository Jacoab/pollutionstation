import pigpio  # aptitude install python3-pigpio
import time
import struct
import sys
import crcmod  # aptitude install python3-crcmod
import os
import signal
from subprocess import call

import pprint


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class SPS30:
    LOGFILE = '/run/sensors/sps30/last'

    PIGPIO_HOST = '127.0.0.1'
    I2C_SLAVE = 0x69
    I2C_BUS = 1

    DEBUG = False

    def __init__(self):
        deviceOnI2C = call("i2cdetect -y 1 0x69 0x69|grep '\--' -q", shell=True)  # grep exits 0 if match found
        if deviceOnI2C:
            print("I2Cdetect found SPS30")
        else:
            print("SPS30 (0x69) not found on I2C bus")
            exit(1)

        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        self.pi = pigpio.pi(self.PIGPIO_HOST)
        if not self.pi.connected:
            eprint("no connection to pigpio daemon at " + self.PIGPIO_HOST + ".")
            exit(1)
        else:
            if self.DEBUG:
                print("connection to pigpio daemon successful")

        try:
            self.pi.i2c_close(0)
        except:
            tupl = sys.exc_info()
            if tupl[1] and str(tupl[1]) != "'unknown handle'":
                eprint("Unknown error: ", tupl)

        # try:
        self.h = self.pi.i2c_open(self.I2C_BUS, self.I2C_SLAVE)
        # except:
        #  eprint("i2c open failed")
        #  exit(1)

        # def i2cOpen():
        #  global h
        #  try:
        #    h = pi.i2c_open(I2C_BUS, I2C_SLAVE)
        #  except:
        #    eprint("i2c open failed")
        #    exit(1)

        self.f_crc8 = crcmod.mkCrcFun(0x131, 0xFF, False, 0x00)


    def exit_gracefully(self, a, b):
        print("exit")
        self.stopMeasurement()
        os.path.isfile(self.LOGFILE) and os.access(self.LOGFILE, os.W_OK) and os.remove(self.LOGFILE)
        self.pi.i2c_close(self.h)
        exit(0)

    def calcCRC(self, TwoBdataArray):
        byteData = ''.join(chr(x) for x in TwoBdataArray)
        return self.f_crc8(byteData.encode())

    # print(hex(calcCRC([0xBE,0xEF])))

    def readNBytes(self, n):
        try:
            (count, data) = self.pi.i2c_read_device(self.h, n)
        except:
            eprint("error: i2c_read failed")
            exit(1)

        if count == n:
            return data
        else:
            eprint("error: read bytes didnt return " + str(n) + "B")
            return False

    # takes an array of bytes (integer-array)
    def i2cWrite(self, data):
        try:
            self.pi.i2c_write_device(self.h, data)
        except Exception as e:
            pprint.pprint(e)
            eprint("error in i2c_write:", e.__doc__ + ":", e.value)
            return -1
        return True

    def readFromAddr(self, LowB, HighB, nBytes):
        for amount_tries in range(3):
            ret = self.i2cWrite([LowB, HighB])
            if ret != True:
                eprint("readFromAddr: write try unsuccessful, next")
                continue
            data = self.readNBytes(nBytes)
            if data:
                return data
            eprint("error in readFromAddr: " + hex(LowB) + hex(HighB) + " " + str(nBytes) + "B did return Nothing")
        eprint("readFromAddr: write tries(3) exceeded")
        return False

    def readArticleCode(self):
        data = self.readFromAddr(0xD0, 0x25, 47)
        if data == False:
            eprint('readArticleCode failed')
            return False

        acode = ''
        crcs = ''
        for i in range(47):
            currentByte = data[i]
            if currentByte == 0:
                break
            if (i % 3) != 2:
                acode += chr(currentByte) + '|'
            else:
                crcs += str(currentByte) + '.'
        print('Article code: "' + acode + '"')
        return True

    def readSerialNr(self):
        data = self.readFromAddr(0xD0, 0x33, 47)
        if data == False:
            eprint('readSerialNr failed')
            return False

        snr = ''
        for i in range(47):
            if (i % 3) != 2:
                currentByte = data[i]
                if currentByte == 0:
                    break
                if i != 0:
                    snr += '-'
                snr += chr(currentByte)
        print('Serial number: ' + snr)
        return True

    def readCleaningInterval(self):
        data = self.readFromAddr(0x80, 0x04, 6)
        if data and len(data):
            interval = SPS30.calcInteger(data)
            print('cleaning interval:', str(interval), 's')

    def startMeasurement(self):
        ret = -1
        for i in range(3):
            ret = self.i2cWrite([0x00, 0x10, 0x03, 0x00, self.calcCRC([0x03, 0x00])])
            if ret == True:
                return True
            eprint('startMeasurement unsuccessful, next try')
            self.bigReset()
        eprint('startMeasurement unsuccessful, giving up')
        return False

    def stopMeasurement(self):
        self.i2cWrite([0x01, 0x04])

    def reset(self):
        if self.DEBUG:
            print("reset called")
        for i in range(5):
            ret = self.i2cWrite([0xd3, 0x04])
            if self.DEBUG:
                print("reset sent")
            if ret == True:
                if self.DEBUG:
                    print("reset ok")
                return True
            eprint('reset unsuccessful, next try in', str(0.2 * i) + 's')
            time.sleep(0.2 * i)
        eprint('reset unsuccessful')
        return False


    def readDataReady(self):
        data = self.readFromAddr(0x02, 0x02, 3)
        if data == False:
            eprint("readDataReady: command unsuccessful")
            return -1
        if data and data[1]:
            if self.DEBUG:
                print("✓")
            return 1
        else:
            if self.DEBUG:
                print('.', end='')
            return 0

    def calcInteger(sixBArray):
        integer = sixBArray[4] + (sixBArray[3] << 8) + (sixBArray[1] << 16) + (sixBArray[0] << 24)
        return integer

    def calcFloat(sixBArray):
        struct_float = struct.pack('>BBBB', sixBArray[0], sixBArray[1], sixBArray[3], sixBArray[4])
        float_values = struct.unpack('>f', struct_float)
        first = float_values[0]
        return first

    #
    # EDIT THIS BUSINESS
    #
    def printPrometheus(self, data):
        pm10 = SPS30.calcFloat(data[18:24])
        if pm10 == 0:
            eprint("pm10 == 0; ignoring values")
            return

        output_string = 'particulate_matter_ppcm3_size = 0.5,  Value in μg/m3: {0:.3f}\n'.format(SPS30.calcFloat(data[24:30]))
        output_string += 'particulate_matter_ppcm3_size = 1.0,  Value in μg/m3: {0:.3f}\n'.format(SPS30.calcFloat(data[30:36]))
        output_string += 'particulate_matter_ppcm3_size = 2.5,  Value in μg/m3: {0:.3f}\n'.format(SPS30.calcFloat(data[36:42]))
        output_string += 'particulate_matter_ppcm3_size = 4.0,  Value in μg/m3: {0:.3f}\n'.format(SPS30.calcFloat(data[42:48]))
        output_string += 'particulate_matter_ppcm3_size = 10.0, Value in μg/m3: {0:.3f}\n'.format(SPS30.calcFloat(data[48:54]))
        output_string += 'particulate_matter_ugpm3_size = 1.0,  Value in 1/cm3: {0:.3f}\n'.format(SPS30.calcFloat(data))
        output_string += 'particulate_matter_ugpm3_size = 2.5,  Value in 1/cm3: {0:.3f}\n'.format(SPS30.calcFloat(data[6:12]))
        output_string += 'particulate_matter_ugpm3_size = 4.0,  Value in 1/cm3: {0:.3f}\n'.format(SPS30.calcFloat(data[12:18]))
        output_string += 'particulate_matter_ugpm3_size = 10.0, Value in 1/cm3: {0:.3f}\n'.format(pm10)
        output_string += 'Average Particle Size In μg: {0:.3f}\n'.format(SPS30.calcFloat(data[54:60]))
        print(output_string)
        logfilehandle = open(self.LOGFILE, "w", 1)
        logfilehandle.write(output_string)
        logfilehandle.close()

    def printHuman(self, data):
        print("pm0.5 count: %f" % SPS30.calcFloat(data[24:30]))
        print("pm1   count: {0:.3f} ug: {1:.3f}".format(SPS30.calcFloat(data[30:36]), SPS30.calcFloat(data)))
        print("pm2.5 count: {0:.3f} ug: {1:.3f}".format(SPS30.calcFloat(data[36:42]), SPS30.calcFloat(data[6:12])))
        print("pm4   count: {0:.3f} ug: {1:.3f}".format(SPS30.calcFloat(data[42:48]), SPS30.calcFloat(data[12:18])))
        print("pm10  count: {0:.3f} ug: {1:.3f}".format(SPS30.calcFloat(data[48:54]), SPS30.calcFloat(data[18:24])))
        print("pm_typ: %f" % SPS30.calcFloat(data[54:60]))

    def getDataDict(self, data):
        return {
            'pm0p5': SPS30.calcFloat(data[24:30]),
            'pm1p0': SPS30.calcFloat(data[30:36]),
            'pm2p5': SPS30.calcFloat(data[36:42]),
            'pm4p0': SPS30.calcFloat(data[42:48]),
            'pm10p0': SPS30.calcFloat(data[48:54]),
            'nc1p0': SPS30.calcFloat(data),
            'nc2p5': SPS30.calcFloat(data[6:12]),
            'nc4p0': SPS30.calcFloat(data[12:18]),
            'nc10p0': SPS30.calcFloat(data[18:24]),
            'avg_size': SPS30.calcFloat(data[54:60])
        }

    def readPMValues(self):
        data = self.readFromAddr(0x03, 0x00, 59)
        if self.DEBUG:
            self.printHuman(data)

        return self.getDataDict(data)

    def initialize(self):
        self.startMeasurement() or exit(1)
        time.sleep(0.9)

    def bigReset(self):
        #global h
        if self.DEBUG:
            print("bigReset.")
        eprint('resetting...', end='')
        self.pi.i2c_close(self.h)
        time.sleep(0.5)
        self.h = self.pi.i2c_open(self.I2C_BUS, self.I2C_SLAVE)
        time.sleep(0.5)
        self.reset()
        time.sleep(0.1)  # note: needed after reset

'''
if __name__ == "__main__":
    sps30 = SPS30()

    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        sps30.exit_gracefully(False, False)

    call(["mkdir", "-p", "/run/sensors/sps30"])

    sps30.readArticleCode() or exit(1)

    sps30.reset()
    time.sleep(0.1)  # note: needed after reset

    sps30.readSerialNr()
    sps30.readCleaningInterval()

    sps30.initialize()

    while True:
        ret = sps30.readDataReady()
        if ret == -1:
            eprint('resetting...', end='')
            sps30.bigReset()
            sps30.initialize()
            continue

        if ret == 0:
            time.sleep(0.1)
            continue

        sps30.readPMValues()
        time.sleep(0.9)
'''