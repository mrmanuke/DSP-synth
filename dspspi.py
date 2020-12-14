import spidev

class DSP:
	address = [0]

	def __init__(self):
		self.spi = spidev.SpiDev()
		#spi speed of 250MHz / 2^7 
		self.spi.max_speed_hz = 1953125
		self.spi.mode = 0b11

	def write(subaddr, databytes):
		self.spi.xfer(address + subaddr + databytes)
		return
