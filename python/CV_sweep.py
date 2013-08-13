import numpy as np
import pylab
import serial, yaml
from StringIO import StringIO

PORT = "/dev/ttyUSB2"
BAUDRATE = 9600

ser = serial.Serial(PORT, baudrate=BAUDRATE)

def do_sweep():
    ser.write('CV_SWEEP?\n')
    buff = []
    while True:
        line = ser.readline().strip('\r\n')
        print line
        buff.append(line)
        if line.startswith("#END"):
            break
    data = "\n".join(buff)
    data = np.genfromtxt(StringIO(data), delimiter=",",comments='#')
    return data
    
    
if __name__ == "__main__":
    R1 = [0.0,0.25,0.50,0.75,1.0,1.25,1.50,1.75,2.00]
    fig1 = pylab.figure()
    ax1_1 = fig1.add_subplot(211)
    ax1_2 = fig1.add_subplot(212)
    fig1.suptitle("Potentiostatic Control of R2 = 1kOhm Load,\n with varying R1 (CE to WE)")
    ax1_1.set_xlabel("Voltage CE [V]")
    ax1_1.set_ylabel("Voltage RE [V]")
    ax1_2.set_xlabel("Voltage CE [V]")
    ax1_2.set_ylabel("Current WE [mA]")
    for r1 in R1:
        print "Change resistor R1 to %0.2f kOhm" % r1
        raw_input()
        D = do_sweep()
        V_CE = D[:,0]
        V_RE = D[:,1]
        I_WE = D[:,2] * 1000.0 #convert to mAmps
        #plot voltage RE vs. input V_CE
        ax1_1.plot(V_CE,V_RE,'.-', label = "%0.2f kOhm" % r1)
        #plot voltage RE vs. input V_CE
        ax1_2.plot(V_CE,I_WE,'.-', label = "%0.2f kOhm" % r1)
    ax1_1.legend(loc="lower right", prop={'size':8})
    pylab.savefig("data/out.pdf")
    pylab.savefig("data/out.png")
    pylab.show()
