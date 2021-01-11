import math
import sys
import mido
from mido.ports import MultiPort
import time
import threading
from threading import Thread
import dspFormat as dspfloats
from dspspi import DSP
import subprocess

def my_excepthook(type, value, traceback):
	print('Unhandled error:', type, value)

sys.excepthook = my_excepthook

print_messages = (len(sys.argv) > 1)

#process = subprocess.run(["dsptoolkit", "install-profile", "testprofile.xml"])
#print("returncode:", process.returncode)
#bytearray = dspfloats.to824(float x)

loadlock = threading.Lock()
mhan = True

monophonic = False

#setup global variables and constants
clockmsg = "clock"
note_on = "note_on"
note_off = "note_off"
control_change = "control_change"
type_osc = "midi_osc"
type_oscm = "midi_oscm"
type_oscf = "midi_oscf"
type_midi_knob = "midi_knob"
type_midi_pad = "midi_pad"
type_sample_rate = "sampleRate"
type_filtf_multi = "filtFMulti"
type_front_edge = "front_edge"
type_back_edge = "back_edge"
type_both_edges = "both_edges"
type_piano_key = "piano_key"
type_on_off = "on_off"
format_523 = "523"
format_824 = "824"
format_320 = "320"
#LAUNCHKEY MINI Scene Down Control Num
next_program = 105
#LAUNCHKEY MINI Scene Up Control Num
prev_program = 104
key_chan = 0
pad_chan = 9
#LAUNCHKEY MINI pad note order
pad_notes = [40, 41, 42, 43, 48, 49, 50, 51, 36, 37, 38, 39, 44, 45, 46, 47]
pad_counter = 0
midi_pads = []
max_pads = 16
control1 = 21
max_knobs = 8
knob_counter = 0
knob_nums = []
midi_knobs = []
running = True
loadingDSP = True
profile_files = []
cur_program = 0
num_programs = 0
oscs = []
oscms = []
oscfs = []
noteFreqs = []
notesIn824 = []
filtIn824 = []
map128_1to0_824 = []
releasetime = 0.05
sample_rate = 48000
filtFMulti = 12
note_range = 150
dsp_one = dspfloats.to824(1)
dsp_zero = dspfloats.to824(0)
dsp = DSP()

print("knobs:")
for i in range(max_knobs):
	cnum = control1+i
	print(cnum)
	knob_nums.append(cnum)

for i in range(note_range):
	f = 440 * math.pow(2, (i-69)/12)
	noteFreqs.append(f)

for i in range(128):
	map128_1to0_824.append(dspfloats.to824(i/127))

def mapFMultiTo824(m):
	vals = []
	for i in range(note_range):
		dspf = dspfloats.to824(noteFreqs[i] * m / (sample_rate * 0.5))
		vals.append(dspf)
	return vals

def map_knob_to_320(min, max):
	vals = []
	r = float(max - min)
	for i in range(128):
		f = min + r*(float(i)/128.9)
		vals.append(dspfloats.to320(f))
	return vals

def map_knob_to_824(min, max):
	vals = []
	r = float(max - min)
	for i in range(128):
		f = min + r*(float(i)/128.0)
		vals.append(dspfloats.to824(f))
	return vals

def map_on_off_to_824(min, max):
	vals = [dspfloats.to824(min)]
	for i in range(127):
		vals.append(dspfloats.to824(max))
	return vals

def map_knob_to_824(min, max):
	vals = []
	r = float(max - min)
	for i in range(128):
		f = min + r*(float(i)/128.0)
		vals.append(dspfloats.to824(f))
	return vals

def map_on_off_to_824(min, max):
	vals = [dspfloats.to824(min)]
	for i in range(127):
		vals.append(dspfloats.to824(max))
	return vals

class MidiKnob:
	def __init__(self, id, daddr, min, max, format):
		if daddr is None or min is None or max is None or format is None:
			self.argError = True
			return
		self.argError = False
		self.num = id
		self.addr = daddr
		self.minOut = float(min)
		self.maxOut = float(max)
		if format is not None:
			if format == format_523:
				self.vals = map_knob_to_523(self.minOut, self.maxOut)
			elif format == format_824:
				self.vals = map_knob_to_824(self.minOut, self.maxOut)
			elif format == format_320:
				self.vals = map_knob_to_320(self.minOut, self.maxOut)
			else:
				self.vals = map_knob_to_824(self.minOut, self.maxOut)
		else:
			print("error, knob must be assigned a number format")
			#disable knob
			self.num = -1

	def change_value(self, v):
		#print("knob write", v)
		#v is knob value in range 0 to 127
		dsp.write(self.addr, self.vals[v])

#MidiPad example: min = 1, max = 1, ptype = back_edge; the pad will send a 1 each time it's pressed and released
#example: ptype = on_off; the pad will send max every time it's pressed and min every time it's released
class MidiPad:
	def __init__(self, id, daddr, min, max, format, ptype):
		if daddr is None or min is None or max is None or format is None or ptype is None:
			self.argError = True
			return
		self.argError = False
		self.note = id
		self.addr = daddr
		self.minOut = min
		self.maxOut = max
		self.padType = ptype
		if ptype == type_back_edge:
			#send value to DSP only when pad is released
			self.back = True
		elif ptype == type_front_edge:
			#send value to DSP only when pad is pressed
			self.front = True
		elif ptype == type_on_off:
			#send only max to DSP for note_on and min for note_off
			self.back = True
			self.front = True
		else:
			#send value to DSP on both edges
			self.back = True
			self.front = False
		if format is not None:
			if format == format_523:
				if ptype == type_on_off:
					self.vals = map_on_off_to_523(self.minOut, self.maxOut)
				else:
					self.vals = map_knob_to_523(self.minOut, self.maxOut)
			elif format == format_824:
				if ptype == type_on_off:
					self.vals = map_on_off_to_824(self.minOut, self.maxOut)
				else:
					self.vals = map_knob_to_824(self.minOut, self.maxOut)
			else:
				if ptype == type_on_off:
					self.vals = map_on_off_to_824(self.minOut, self.maxOut)
				else:
					self.vals = map_knob_to_824(self.minOut, self.maxOut)
		else:
			print("error, pad must be assigned a number format")
			#disable knob
			self.note = -1

	def note_on(self, msg):
		if msg.velocity == 0:
			self.note_off(msg)
			return
		if self.front:
			dsp.write(self.addr, self.vals[msg.velocity])

	def note_off(self, msg):
		if self.back:
			dsp.write(self.addr, self.vals[msg.velocity])

def setSampleRate(sr):
	sample_rate = float(sr)
	notesIn824.clear()
	filtIn824.clear()
	for i in range(0, note_range):
		dspf = noteFreqs[i]/(sample_rate * 0.5)
		n824 = dspfloats.to824(dspf)
		notesIn824.append(n824)

def mapFiltFTo824(m):
	vals = []
	for i in range(0, note_range):
		filtf = 2*math.sin(math.pi * noteFreqs[i] * m / sample_rate)
		f824 = dspfloats.to824(filtf)
		vals.append(f824)
	return vals

class OscF:
	def __init__(self, freqAddr, m, eid):
		if freqAddr is None or m is None:
			self.argError = True
			return
		self.fAddr = freqAddr
		self.fmulti = m
		self.oscID = eid
		self.filtFIn824 = mapFiltFTo824(m)
		self.argError = False

	def setF(self, note):
		dsp.write(self.fAddr, self.filtFIn824[note])

class OscM:
	def __init__(self, freqAddr, m, eid):
		if freqAddr is None or m is None:
			self.argError = True
			return
		self.fAddr = freqAddr
		self.fMulti = m
		self.oscID = eid
		self.fIn824 = mapFMultiTo824(m)
		self.argError = False

	def setF(self, note):
		dsp.write(self.fAddr, self.fIn824[note])

class Osc:
	def __init__(self, freqAddr, filtfAddr, adsrAddr, velAddr, eid):
		if freqAddr is None or adsrAddr is None or velAddr is None:
			self.argError = True
			return
		self.argError = False
		#addresses must be in list of bytes
		self.fAddr = freqAddr
		self.aAddr = adsrAddr
		self.vAddr = velAddr
		self.filtAddr = filtfAddr
		self.hasFilt = (filtfAddr != 0)
		self.n = 60
		self.id = eid
		self.offtime = 0
		self.on = False
		self.oscms = []
		self.oscfs = []

	def addOscM(self, om):
		self.oscms.append(om)

	def addOscF(self, oq):
		self.oscfs.append(oq)

	def turnOn(self, note, velocity):
		self.on = True
		self.n = note
		for om in self.oscms:
			om.setF(note)
		for oq in self.oscfs:
			oq.setF(note)
		#if self.hasFilt:
		#	dsp.write(self.filtAddr, filtIn824[note])
		#write frequency to faddr
		dsp.write(self.fAddr, notesIn824[note])
		#write velocity (range 0 to 127) to vaddr
		dsp.write(self.vAddr, map128_1to0_824[velocity])
		#print(velocity, "vol:", map128_1to0_824[velocity])
		#write "1" to adsr
		dsp.write(self.aAddr, dsp_one)

	def turnOff(self):
		#write "0" to adsr
		dsp.write(self.aAddr, dsp_zero)
		#set offtime for when this osc will be available again
		self.offtime = time.clock_gettime(time.CLOCK_MONOTONIC) + releasetime
		self.on = False

def get_osc(note):
	if monophonic:
		return oscs[0]
	#returns osc object or None if all oscs are in use
	gt = time.clock_gettime(time.CLOCK_MONOTONIC)
	for osc in oscs:
		if not osc.on and osc.offtime < gt:
			return osc
	return None

def turn_off_note(note):
	for osc in oscs:
		if osc.n == note:
			osc.turnOff()

def create_synth_element(edata):
	global pad_counter
	global knob_counter
	global flitFMulti
	#slashsplit = xml.text.split('/')
	#eAddr = dspfloats.toAddress(slashsplit[0])
	etype = edata[0].split(':')
	if etype[0] == type_sample_rate:
		setSampleRate(etype[1])
		return
	if etype[0] == type_filtf_multi:
		return
	eAddr = dspfloats.toAddress(edata[1].split(':')[1])
	aAddr = 0
	vAddr = 0
	fAddr = 0
	minVal = 0
	maxVal = 0
	numFormat = '824'
	eid = 0
	padType = 0
	for d in edata:
		s = d.split(':')
		if s[0] == 'addr':
			if s[1] != '':
				eAddr = dspfloats.toAddress(s[1])
		elif s[0] == 'aAddr':
			if s[1] != '':
				aAddr = dspfloats.toAddress(s[1])
		elif s[0] == 'vAddr':
			if s[1] != '':
				vAddr = dspfloats.toAddress(s[1])
		elif s[0] == 'fAddr':
			if s[1] != '':
				fAddr = dspfloats.toAddress(s[1])
		elif s[0] == 'min':
			minVal = s[1]
		elif s[0] == 'max':
			maxVal = s[1]
		elif s[0] == 'format':
			numFormat = s[1]
		elif s[0] == 'midi_id':
			eid = s[1]
		elif s[0] == 'padType':
			padType = s[1]
	if etype[0] == type_osc:
		osc = Osc(eAddr, fAddr, aAddr, vAddr, eid)
		if osc.argError:
			print("arguments for osc", eAddr, "were not supplied correctly")
			return
		oscs.append(osc)
		return
	if etype[0] == type_oscm:
		fmultiplier = float(minVal + "." + maxVal)
		print("fmulti:" + str(fmultiplier))
		oscm = OscM(eAddr, fmultiplier, eid)
		if oscm.argError:
			print("arguments for oscm", eAddr, "were not supplied correctly")
			return
		oscms.append(oscm)
		return
	if etype[0] == type_oscf:
		fmultiplier = float(minVal + "." + maxVal)
		oscf = OscF(eAddr, fmultiplier, eid)
		if oscf.argError:
			print("arguments for oscf", eAddr, "were not supplied correctly")
			return
		oscfs.append(oscf)
		return
	if etype[0] == type_midi_knob:
		if knob_counter >= max_knobs:
			print("failed to assign knob", eAddr, "because knob num limit has been reached")
			return
		print("knob counter", knob_counter, "assign knob for control", knob_nums[knob_counter])
		knob = MidiKnob(knob_nums[knob_counter], eAddr, minVal, maxVal, numFormat)
		if knob.argError:
			print("arguments for knob", eAddr, "were not supplied correctly")
			return
		knob_counter = knob_counter + 1
		midi_knobs.append(knob)
		return
	if etype[0] == type_midi_pad:
		if pad_counter >= max_pads:
			print("failed to assign pad", eAddr, "because pad num limit has been reached")
		pad = MidiPad(pad_notes[pad_counter], eAddr, minVal, maxVal, numFormat, padType)
		if pad.argError:
			print("arguments for pad", eAddr, "were not supplied correctly")
			return
		pad_counter = pad_counter + 1
		midi_pads.append(pad)
		return

def getOscByID(id):
	for o in oscs:
		if o.id == id:
			return o
	return None

def load_DSP_thread(pnum):
	global loadingDSP
	global knob_counter
	global monophonic
	oscs.clear()
	oscms.clear()
	oscfs.clear()
	midi_knobs.clear()
	knob_counter = 0
	f = open(profile_files[pnum])
	lines = f.readlines()
	r = len(lines)
	l = 0
	b = 0
	numb = 0
	inProgram = False
	xferdata = [0]
	while l < r:
		line = lines[l]
		if inProgram:
			while b > 0:
				nums = line.split(',')
				for n in nums:
					b = b - 1
					xferdata.append(int(n) & 0b11111111)
				l = l + 1
				if l < r:
					line = lines[l]
			if len(xferdata) > 1:
				#print(xferdata)
				#write xferdata to dsp here
				if numb == 4 and xferdata[1] + xferdata[2] == 0:
					time.sleep(0.1)
					#print("delay")
				else:
					dsp.xfer(xferdata)
					#print(xferdata)
				xferdata = [0]
			if l < r:
				numb = int(line)
				b = numb
				l = l + 1
			continue
		elif line.find('<beometa>') > -1:
			l = l+1
			continue
		elif line.find('<program>') > -1:
			l = l+1
			inProgram = True
			continue

		#handle synth elements
		edata = line.split(',')
		create_synth_element(edata)
		l = l+1
	for oq in oscfs:
		osc = getOscByID(oq.oscID)
		osc.addOscF(oq)
	for om in oscms:
		osc = getOscByID(om.oscID)
		if osc is not None:
			osc.addOscM(om)
	monophonic = len(oscs) < 2
	loadingDSP = False

def xload_DSP_thread(pnum):
	#TODO:load control parameters in separate thread from loading DSP program?
	global loadingDSP
	tree = ET.parse(profile_files[pnum])
	root = tree.getroot()
	#print("root.tag:", root.tag)
	#clear osc array and reset number of oscs
	oscs.clear()
	midi_knobs.clear()
	knob_counter = 0
	#read parameters (knobs, oscs, ...) that can be set by midi and create control elements
	#read sample rate and call setSampleRate()
	for child in root:
		#print("child.tag:", child.tag)
		if child.tag == "beometa":
			for beo in child:
				#if osc then make new osc, etc
				synthElem = beo.get('synth')
				if synthElem is not None:
					create_synth_element(synthElem, beo)
				typeElem = beo.get('type')
				if typeElem is not None:
					if typeElem == type_sample_rate:
						setSampleRate(beo.text)
				#slashsplit = beo.text.split('/')
				#print("type:", beo.get('type'), "; text =", beo.text, "(", hex(int(slashsplit[0])), ")")
	#call shell script to load program to DSP
	print("loading DSP program. This takes a while")
	process = subprocess.run(["dsptoolkit", "install-profile", profile_files[pnum]])
	print(profile_files[pnum] ,"loaded, returncode:", process.returncode)
	loadingDSP = False

def load_dsp_program(pnum):
	global loadingDSP
	global cur_program
	cur_program = pnum
	print("load dsp")
	loadingDSP = True
	dthread = threading.Thread(target=load_DSP_thread, args=(pnum,))
	dthread.daemon = True
	dthread.start()

def load_next_program():
	global cur_program
	if num_programs < 2:
		return
	cur_program = (cur_program+1)%num_programs
	load_dsp_program(cur_program)

def load_prev_program():
	global cur_program
	if num_programs < 2:
		return
	cur_program = (cur_program+num_programs-1)%num_programs
	load_dsp_program(cur_program)

def handle_message(message):
	if message.type == clockmsg:
		return
	if print_messages:
		print(message)
	if message.type == note_off:
		if message.channel == pad_chan:
			for pad in midi_pads:
				if pad.note == message.note:
					pad.note_off(message)
			return
		turn_off_note(message.note)
		return
	if message.type == note_on:
		if message.channel == pad_chan:
			for pad in midi_pads:
				if pad.note == message.note:
					pad.note_on(message)
			return
		if message.velocity == 0:
			turn_off_note(message.note)
			return
		o = get_osc(message.note)
		if o is None:
			return
		o.turnOn(message.note, message.velocity)
		return
	if message.type == control_change:
		#print(message)
		if message.control == next_program and message.value == 0:
			load_next_program()
			return
		if message.control == prev_program and message.value == 0:
			load_prev_program()
			return
		for k in midi_knobs:
			#print("k", k, ", control", message.control)
			if k.num == message.control:
				k.change_value(message.value)
		return
	#if message is button to load DSP program then set loadingDSP to True and start load_DSP_thread

def port_poling_thread(port):
	while running:
		global loadingDSP
		msg = port.poll()
		if not loadingDSP and msg is not None:
			handle_message(msg)
			continue
		if msg is not None and msg.type != clockmsg:
			print(loadingDSP, "x", msg)

class PropagatingThread(Thread):
	def run(self):
		self.exc = None
		try:
			if hasattr(self, '*Thread__target'):
				self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
			else:
				self.ret = self._target(*self._args, **self._kwargs)
		except BaseException as e:
			self.exc = e

	def join(self, tmout):
		super(PropagatingThread, self).join(tmout)
		if self.exc:
			raise self.exc
		return self.ret

def tryInt(i):
	try:
		s = int(i)
		return s
	except ValueError:
		return -1

def list_dsp_programs():
	for p in profile_files:
		print(p)

#load up list of profile xml files
#proftree = ET.parse('dsp_profile_list.xml')
#profroot = proftree.getroot()
#print("profroot.tag:", profroot.tag)

#for child in profroot:
#	print("pchild.tag:", child.tag)
#	if child.tag == "file":
#		print("file:", child.text)
#		profile_files.append(child.text)
#		num_programs = num_programs + 1

datlist = open('dat_profile_list.txt')
datlines = datlist.readlines()
for dl in datlines:
	profile_files.append(dl.strip('\n'))
	num_programs = num_programs + 1

if num_programs > 0:
	list_dsp_programs()
	load_dsp_program(0)
else:
	print("no dsp programs were provided")

midi_inputs = mido.get_input_names()
print (midi_inputs)
inports = []

for i in range(len(midi_inputs)):
	inports.append(mido.open_input(midi_inputs[i]))

port = MultiPort(inports)
#sleep required after opening port and before poling port to clear out pending message
time.sleep(1)
#load first DSP profile
#clear out pending messages from midi port
msg = port.poll()
if msg is None:
	print("xx")
while msg is not None:
	msg = port.poll()
	print("x", msg)
mthread = PropagatingThread(target=port_poling_thread, args=(port,))
mthread.daemon = True
mthread.start()
sinp = "a"
while len(sinp) > 0:
	sinp = input("")
	#print(sinp, running)
	sin = tryInt(sinp)
	if sin > -1 and sin < num_programs:
		load_dsp_program(sin)
	else:
		list_dsp_programs()
#print("loadlock", loadlock.locked())
running = False
for o in oscs:
	if o.on:
		o.turnOff()
dsp.close()
while True:
	mthread.join(600)
	if not mthread.isAlive():
		break
port.callback = None
for i in range(len(inports)):
	inports[i].close()
