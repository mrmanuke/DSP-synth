import time

def writeFromDat(dsp, txDat, nbDat):
	txf = open(txDat)
	nb = open(nbDat)
	bdata = nb.readlines()
	tx = txf.readlines()
	c = 0
	for line in bdata:
		b = int(line.split(',')[0])
		a = tx[c].split(',')
		w = [0, int(a[0], 16), int(a[1], 16)]
		b = b-2
		while b > 0:
			c = c + 1
			tdata = tx[c].split(',')
			r = len(tdata) - 1
			for d in range(r):
				b = b - 1
				w.append(int(tdata[d], 16))
		if w[1] + w[2] == 0:
			time.sleep(0.1)
			#print("delay")
		else:
			dsp.xfer(w)
			#print(w)
		c = c + 1
