import dspFormat as dspfloats
from dspspi import DSP
import sys
import math

if len(sys.argv) < 2:
	sys.exit("note value between 0 and 100 must be specified as first argument")
note = float(sys.argv[1])
if note < 0 or note > 100:
	sys.exit("note must be in range 0 to 100")
#dsp = DSP()
sample_rate = 48000
ahex = 0
addr = dspfloats.toAddress(ahex)
f = 440 * math.pow(2, (note-69)/12)
dspf = f/(sample_rate * 0.5)
n523 = dspfloats.to523(dspf)
#dsp.write(addr, n523)
