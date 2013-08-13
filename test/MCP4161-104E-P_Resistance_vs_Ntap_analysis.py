from pylab import *

D = loadtxt("MCP4161-104E-P_Resistance_vs_Ntap.csv",delimiter=",")
X = D[:,0]
Y = D[:,1]

p = polyfit(X,Y,1)

X_fit = arange(257)
Y_fit = X_fit*p[0] + p[1]

plot(X,Y,'b.')
plot(X_fit,Y_fit, 'k-')
title("Calibration of MCP4161-104E/P\n8bit 100k Digital Potentiomenter")
xlabel("Tap Number, N")
ylabel(r"Resistance $R_{W0\rightarrow B0}$ [k$\Omega$]")
text(10,80,"$Y = %0.4f X + %0.4f$" % (p[0],p[1]))
savefig("MCP4161-104E-P_Resistance_vs_Ntap.png")
