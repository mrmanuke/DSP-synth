import spidev

class DSP:
	def __init__(self):
		self.address = [0]
		self.spi = spidev.SpiDev()
		self.spi.open(0, 0)
		#spi speed of 250MHz / 2^7 
		self.spi.max_speed_hz = 1953125
		self.spi.mode = 0b11

	def write(self, subaddr, databytes):
		self.spi.xfer(self.address + subaddr + databytes)
		return

	def close(self):
		self.spi.close()
		return

	def xfer(self, databytes):
		#databytes is a list that includes address
		self.spi.xfer(databytes)
		return
