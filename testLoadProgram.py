import loadProgram as loader

class DSP:
	def xfer(self, w):
		print(w)

txDat = './tx.dat'
nbDat = './nb.dat'
dsp = DSP()

loader.writeFromDat(dsp, txDat, nbDat)
