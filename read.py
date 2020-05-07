import time
import board
from busio  import I2C
import adafruit_bme680

i2c = I2C(board.SCL, board.SDA)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c,debug=False)

bme680.sea_level_pressure = 1013.25


for i in range(10):
	print("\nTemperature: %0.1f C" % bme680.temperature)

	print("\nGas: %d ohm" % bme680.gas)

	print("\nHumidity: %0.1f %%" % bme680.humidity)

	print("\nPressure: %0.3f hPa" % bme680.pressure)

	print("\nAltitude = %0.2f meters" % bme680.altitude)

	time.sleep(2)

