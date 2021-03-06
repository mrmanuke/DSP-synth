def to523x(paramDec):
	param223 = int(paramDec * (1 << 23))
	param227 = param223 + (1 << 27)
	hex = param227.to_bytes(4, byteorder='big', signed=True)
	px = [hex[0] ^ 0x08, hex[1], hex[2], hex[3]]
	return px

def to523(paramDec):
	param223 = int(paramDec * (1 << 23))
	param227 = param223 + (1 << 27)
	hex3 = param227 & 0b11111111
	hex2 = (param227 >> 8) & 0b11111111
	hex1 = (param227 >> 16) & 0b11111111
	hex0 = (param227 >> 24) & 0b11111111
	hex0 = hex0 ^ 0x08
	px = [hex0, hex1, hex2, hex3]
	return px

def hexTo523(paramHex):
	return to523(int(paramHex, 16))

def to824(paramDec):
	param224 = int(paramDec * (1 << 24))
	param231 = param224 + (1 << 31)
	hex3 = param231 & 0b11111111
	hex2 = (param231 >> 8) & 0b11111111
	hex1 = (param231 >> 16) & 0b11111111
	hex0 = (param231 >> 24) & 0b11111111
	hex0 = hex0 ^ 0x80
	px = [hex0, hex1, hex2, hex3]
	return px

def to320(paramInt):
	paramInt = int(paramInt)
	hex3 = paramInt & 0b11111111
	hex2 = (paramInt >> 8) & 0b11111111
	hex1 = (paramInt >> 16) & 0b11111111
	hex0 = (paramInt >> 24) & 0b11111111
	px = [hex0, hex1, hex2, hex3]
	return px

def hexTo824(paramHex):
	return to824(int(paramHex, 16))

def toAddress(addr):
	addrInt = int(addr)
	hex1 = addrInt & 0b11111111
	hex0 = (addrInt >> 8) & 0b11111111
	ax = [hex0, hex1]
	return ax

def hexToAddress(addrHex):
	return toAddress(int(addrHex, 16))
