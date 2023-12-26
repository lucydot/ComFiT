import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import comfit as cf
import matplotlib.pyplot as plt
import numpy as np

pfc = cf.PhaseFieldCrystal2DSquare(21, 21)
eta = pfc.calc_amplitudes_with_dislocation_dipole(
dislocation_type=1,
x1=pfc.xmax/3,   y1=pfc.ymax/2,
x2=2*pfc.xmax/3, y2=pfc.ymax/2)
pfc.conf_PFC_from_amplitudes(eta)
pfc.evolve_PFC(100)
#eta = pfc.calc_demodulate_PFC()
# pfc.plot_field(pfc.psi)
#pfc.plot_field(np.abs(eta[2]),cmap_symmetric=False)
# alpha = pfc.calc_dislocation_density()
Dnodes = pfc.calc_dislocation_nodes()
print(Dnodes)
print(pfc.a)
# pfc.plot_field(alpha[0],colormap='bluewhitered')
pfc.plot_field(pfc.psi,colorbar=False)
pfc.plot_dislocation_nodes(Dnodes)
#print(eta[1])
plt.show()