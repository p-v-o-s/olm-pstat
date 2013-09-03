import numpy as np
import pylab
import serial, yaml
from StringIO import StringIO
from potentiostat import Potentiostat

PORT     = "/dev/ttyUSB0"
BAUDRATE = 115200

if __name__ == "__main__":
    pstat = Potentiostat(port     = PORT,
                         baudrate = BAUDRATE,
                         debug    = True)
    R1 = [1.0]
    fig1 = pylab.figure()
    ax1_1 = fig1.add_subplot(211)
    ax1_2 = fig1.add_subplot(212)
    fig1.suptitle("Potentiostatic Control of R2 = 1kOhm Load,\n with varying R1 (CE to WE)")
    ax1_1.set_xlabel("Voltage WE (vs. RE) [V]")
    ax1_1.set_ylabel("Voltage CTRL [V]")
    ax1_1.set_xlim(-1.6,1.6)
    ax1_2.set_xlabel("Voltage WE (vs. RE) [V]")
    ax1_2.set_ylabel("Current WE [mA]")
    ax1_2.set_xlim(-1.6,1.6)
    for r1 in R1:
        print "Change resistor R1 to %0.2f kOhm" % r1
        raw_input()
        pstat.reset()
        D = pstat.do_voltage_sweep(v_start   = 0.0,
                                   v_end     = 1.0,
                                   v_rate    = 0.25,
                                   samp_rate = 10.0,
                                   cycles    = 3,
                                  )
        V_CTRL   = D[:,0]
        V_WEtoRE = D[:,1]
        I_WE     = D[:,2] * 1000.0 #convert to mAmps
        #plot voltage RE vs. input V_CE
        ax1_1.plot(V_WEtoRE,V_CTRL,'.-', label = "%0.2f kOhm" % r1)
        #plot voltage RE vs. input V_CE
        ax1_2.plot(V_WEtoRE,I_WE,'.-', label = "%0.2f kOhm" % r1)
    ax1_1.legend(loc="lower right", prop={'size':8})
    pylab.savefig("data/out.pdf")
    pylab.savefig("data/out.png")
    pylab.show()
