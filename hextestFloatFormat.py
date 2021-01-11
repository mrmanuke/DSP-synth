import dspFormat as dspfloats
import sys

x = int(sys.argv[1], 16)
print("convert", x, "to 5.23:")
result = dspfloats.to523(x)
for i in range(0, len(result)):
	print("byte", i, ": ", hex(result[i]))

print("convert", x, "to 8.24")
result = dspfloats.to824(x)
for i in range(0, len(result)):
	print("byte", i, ": ", hex(result[i]))
