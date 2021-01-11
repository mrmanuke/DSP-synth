import dspFormat as dspfloats
from dspspi import DSP
import sys
import math
import time

ahex = 0x0083
ohex = 0x007c
dsp_one = dspfloats.to824(1)
dsp_zero = dspfloats.to824(0)

if len(sys.argv) < 2:
	sys.exit("note value between 0 and 100 must be specified as first argument")
note = float(sys.argv[1])
if note < 0 or note > 100:
	sys.exit("note must be in range 0 to 100")
sleeptime = 1
if len(sys.argv) > 2:
	sleeptime = float(sys.argv[2])
dsp = DSP()
sample_rate = 48000
addr = dspfloats.toAddress(ahex)
oaddr = dspfloats.toAddress(ohex)
f = 440 * math.pow(2, (note-69)/12)
dspf = f/(sample_rate * 0.5)
n523 = dspfloats.to824(dspf)
dsp.write(addr, n523)
dsp.write(oaddr, dsp_one)
time.sleep(sleeptime)
dsp.write(oaddr, dsp_zero)
dsp.close()
