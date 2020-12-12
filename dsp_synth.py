import sys
import mido
import time
import threading
import xml.etree.ElementTree as ET

#setup global variables and constants
clockmsg = "clock"
running = True
loadingDSP = True
profile_xml_files = []
oscs = []

def handle_message(message):
        if message.type.find(clockmsg) == -1:
                print(message.note)
                msg = message.note
                msb = msg >> 8
                lsb = msg & 0xFF
	#if message is button to load DSP program then set loadingDSP to True and start load_DSP_thread

def port_poling_thread(port):
        while running:
                msg = port.poll()
                if !loadingDSP and msg is not None:
                        handle_message(msg)

def load_DSP_thread(pnum):
	tree = ET.parse(profiles[0])
	root = tree.getroot()
	print("root.tag:", root.tag)
	#clear osc array and reset number of oscs
	#read parameters that can be set by midi and assign midi knob
	for child in root:
        	print("child.tag:", child.tag)
        	if child.tag == "beometa":
                	for beo in child:
                        	slashsplit = beo.text.split('/')
                        	print("type:", beo.get('type'), "; text =", beo.text, "(", hex(int(slashsplit[0])), ")")
	loadingDSP = False

def get_osc(note):
	for osc in oscs:
		print(osc.off)

#load up list of profile xml files
proftree = ET.parse('dsp_profile_list.xml')
profroot = proftree.getroot()
print("profroot.tag:", profroot.tag)

for child in profroot:
	print("pchild.tag:", child.tag)
	if child.tag == "file":
		print("file:", child.text)
		profile_xml_files.append(child.text)

print (mido.get_input_names())

#port = mido.open_input("Digital Piano:Digital Piano MIDI 1")
port = mido.open_input("Launchkey Mini:Launchkey Mini MIDI 1")
#sleep required after opening port and before poling port to clear out pending messages
time.sleep(1)
msg = port.poll()
if msg is None:
        print("xx")
while msg is not None:
        msg = port.poll()
        #print("x", msg)
mthread = threading.Thread(target=port_poling_thread, args=(port,))
mthread.start()
sinp = input("Hit Enter to stop")
print(sinp)
running = False
mthread.join()
port.callback = None
port.close()
