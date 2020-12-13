import floatFormat as dspfloats
import sys

x = float(sys.argv[1])
print("convert", x, "to 5.23:")
result = dspfloats.to523(x)
for i in range(0, len(result)):
	print("byte", i, ": ", result[i])

print("convert", x, "to 5.23x")
result = dspfloats.to523x(x)
for i in range(0, len(result)):
	print("byte", i, ": ", result[i])

print("convert", x, "to 8.24x")
result = dspfloats.to824x(x)
for i in range(0, len(result)):
	print("byte", i, ": ", result[i])
