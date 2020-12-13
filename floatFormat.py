def to523(paramDec):
	param223 = int(paramDec * (1 << 23))
	param227 = param223 + (1 << 27)
	hex = param227.to_bytes(4, byteorder='big', signed=True)
	px = [hex[0] ^ 0x08, hex[1], hex[2], hex[3]]
	return px

def to523x(paramDec):
	param223 = int(paramDec * (1 << 23))
	param227 = param223 + (1 << 27)
	hex3 = param227 & 0b11111111
	hex2 = (param227 >> 8) & 0b11111111
	hex1 = (param227 >> 16) & 0b11111111
	hex0 = (param227 >> 24) & 0b11111111
	hex0 = hex0 ^ 0x08
	px = [hex0, hex1, hex2, hex3]
	return px

def to824(paramDec):
	param223 = int(paramDec * (1 << 24))
	param231 = param223 + (1 << 31)
	hex = param231.to_bytes(4, byteorder='big', signed=True)
	px = [hex[0] ^ 0x08, hex[1], hex[2], hex[3]]
	return px

def to824x(paramDec):
	param223 = int(paramDec * (1 << 24))
	param227 = param223 + (1 << 31)
	hex3 = param227 & 0b11111111
	hex2 = (param227 >> 8) & 0b11111111
	hex1 = (param227 >> 16) & 0b11111111
	hex0 = (param227 >> 24) & 0b11111111
	hex0 = hex0 ^ 0x80
	px = [hex0, hex1, hex2, hex3]
	return px
