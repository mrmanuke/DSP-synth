import math
import sys
import mido
import time
import threading
import xml.etree.ElementTree as ET
import dspFormat as dspfloats
import DSP from dspspi
#bytearray = dspfloats.to523(float x)
#import module that writes over SPI

#setup global variables and constants
clockmsg = "clock"
note_on = "note_on"
note_off = "note_off"
control_change = "control_change"
type_osc = "osc"
type_midi_knob = "midi_knob"
format_523 = "523"
format_824 = "824"
#LAUNCHKEY MINI Scene Down Control Num
next_program = 105
#LAUNCHKEY MINI Scene Up Control Num
prev_program = 104
key_chan = 0
pad_chan = 1
control1 = 21
max_knobs = 8
knob_counter = 0
knob_nums = []
midi_knobs = []
running = True
loadingDSP = True
profile_xml_files = []
oscs = []
noteFreqs = []
notesIn523 = []
map128_1to0_523 = []
releasetime = 0.1
sample_rate = 48000
note_range = 150
dsp_one = dspfloats.to523(1)
dsp_zero = dspfloats.to523(0)
dsp = DSP()

for i in range(max_knobs):
	knob_nums.append(int(control1+i))

for i in range(note_range):
	f = 440 * math.pow(2, (i-69)/12)
	noteFreqs.append(f)

for i in range(128):
	map128_1to0_523.append(dspfloats.to523(i))

def map_knob_to_523(min, max):
	vals = []
	r = float(max - min)
	for i in range(128):
		f = min + r*(float(i)/128.0)
		vals.append(dspfloats.to523(f))
	return vals

def map_knob_to_824(min, max):
	vals = []
	r = float(max - min)
	for i in range(128):
		f = min + r*(float(i)/128.0)
		vals.append(dspfloats.to824(f))
	return vals

class MidiKnob:
	def __init__(self, id, daddr, min, max, format):
		self.num = id
		self.addr = daddr
		self.minOut = float(min)
		self.maxOut = float(max)
		if format is not None:
			if format == format_523:
				self.vals = map_knob_to_523(self.minOut, self.maxOut)
			elif format == format_824:
				self.vals = map_knob_to_824(self.minOut, self.maxOut)
			else:
				self.vals = map_knob_to_523(self.minOut, self.maxOut)

	def change_value(v):
		#v is knob value in range 0 to 127
		dsp.write(self.addr, self.vals[v])

def setSampleRate(sr):
	sample_rate = sr
	notesIn523.clear()
	for i in range(0, note_range):
		dspf = noteFreqs[i]/(sample_rate * 0.5)
		n523 = dspfloats.to523(dspf)
		notesIn523.append(n523)

class Osc:
	def __init__(self, freqAddr, adsrAddr, velAddr):
		#addresses must be in list of bytes
		self.fAddr = freqAddr
		self.aAddr = adsrAddr
		sell.vAddr = velAddr
		self.n = 60
		self.offtime = 0
		self.on = False

	def turnOn(note, velocity)
		self.on = True
		self.n = note
		#write frequency to faddr
		dsp.write(self.fAddr, notesIn523[note])
		#write velocity (range 0 to 127) to vaddr
		dsp.write(self.vAddr, map128_1to0_523[velocity])
		#write "1" to adsr
		dsp.write(self.aAddr, dsp_one)

	def turnOff()
		#write "0" to adsr
		dsp.write(self.aAddr, dsp_zero)
		#set offtime for when this osc will be available again
		self.offtime = time.clock_gettime(time.CLOCK_MONOTONIC) + releasetime
		self.on = False

def get_osc(note):
	#returns osc object or None if all oscs are in use
	gt = time.clock_gettime(time.CLOCK_MONOTONIC)
	for osc in oscs:
		if not osc.on and osc.offtime < gt:
			return osc
	return None

def turn_off_note(note):
	for osc in oscs:
		if osc.n == message.note:
			osc.turnOff()
def create_synth_element(etype, xml):
	slashsplit = beo.text.split('/')
	eAddr = dspfloats.toAddress(slashsplit[0])
	if etype == type_osc:
		aAddr = dspfloats.toAddress(xml.get('aAddr'))
		vAddr = dspfloats.toAddress(xml.get('vAddr'))
		# Osc(freqAddr, adsrAddr, velAddr)
		osc = Osc(eAddr, aAddr, vAddr)
		oscs.append(osc)
		return
	if etype == type_midi_knob:
		if knob_counter >= max_knobs:
			print("failed to assign knob", eAddr, "because knob num limit has been reached")
			return
		minVal = xml.get('min')
		maxVal = xml.get('max')
		knob = MidiKnob(knob_counter, eAddr, minVal, maxVal)
		knob_counter = knob_counter + 1
		midi_knobs.append(knob)
		return

def load_DSP_thread(pnum):
	tree = ET.parse(profiles[pnum])
	root = tree.getroot()
	print("root.tag:", root.tag)
	#clear osc array and reset number of oscs
	oscs.clear()
	midi_knobs.clear()
	knob_counter = 0
	#read parameters that can be set by midi and assign midi knob
	#read sample rate and call setSampleRate()
	for child in root:
		print("child.tag:", child.tag)
		if child.tag == "beometa":
			for beo in child:
				#if osc then make new osc, etc
				synthElem = beo.get('synth')
				if synthElem is not None:
					create_synth_element(synthElem, beo)
				#slashsplit = beo.text.split('/')
				#print("type:", beo.get('type'), "; text =", beo.text, "(", hex(int(slashsplit[0])), ")")

	loadingDSP = False

def load_next_program():
	if len(profile_xml_files) < 2:
		return

def load_prev_program():
	if len(profile_xml_files) < 2:
		return

def handle_message(message):
	if message.type == clockmsg:
		return
	if message.type == note_off:
		turn_off_note(message.note)
		return
	if message.type == note_on:
		if message.velocity == 0:
			turn_off_note(message.note)
			return
		o = get_osc(message.note)
		if o is None:
			return
		o.turnOn(n, message.velocity)
		return
	if message.type == control_change:
		if message.control == next_program and value == 0:
			load_next_program()
			return
		if message.control == prev_program and value == 0:
			load_prev_program()
			return
		for k in midi_knobs:
			if k.num == message.control:
				k.change_value(message.value)
		return
	#if message is button to load DSP program then set loadingDSP to True and start load_DSP_thread

def port_poling_thread(port):
	while running:
	msg = port.poll()
	if !loadingDSP and msg is not None:
		handle_message(msg)

#load up list of profile xml files
proftree = ET.parse('dsp_profile_list.xml')
profroot = proftree.getroot()
print("profroot.tag:", profroot.tag)

for child in profroot:
	print("pchild.tag:", child.tag)
	if child.tag == "file":
		print("file:", child.text)
		profile_xml_files.append(child.text)

midi_inputs = mido.get_input_names()
print (midi_inputs)

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
	#print("x", msg)
mthread = threading.Thread(target=port_poling_thread, args=(port,))
mthred.daemon = True
mthread.start()
sinp = input("Hit Enter to stop")
print(sinp)
running = False
while True:
	mthread.join(600)
	if not mthread.isAlive();
		break;
port.callback = None
for i in range(len(inports)):
	inports[i].close()
