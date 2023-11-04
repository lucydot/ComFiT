import comfit as cf

import comfit as cf
import numpy as np
import matplotlib.pyplot as plt


bec = cf.BEC(2,xRes=101,yRes=101)
bec.set_initial_condition_disordered()
bec.evolve_relax_BEC(200)

# rho = bec.calc_vortex_density_singular()
#
# bec.plot_field(rho)
# plt.show()

fig,axs = plt.subplots(nrows=1,ncols=2)

nodes = bec.calc_vortex_nodes()
bec.plot_vortices(nodes,axs[0])
bec.plot_angle_field(np.angle(bec.psi),ax=axs[1])

plt.show()
