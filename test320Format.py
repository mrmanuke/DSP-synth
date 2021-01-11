import dspFormat as dspfloats
import sys

x = int(sys.argv[1])
print("convert", x, "to 32.0:")
result = dspfloats.to320(x)
for i in range(0, len(result)):
	print("byte", i, ": ", hex(result[i]))

