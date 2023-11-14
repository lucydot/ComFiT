import numpy as np
import matplotlib.pyplot as plt
from comfit.core.base_system import BaseSystem


class BEC(BaseSystem):
    def __init__(self, dimension, **kwargs):
        """
        Initializes a system to simulate a Bose-Einstein Condensate using the Gross-Pitaevskii equation.

        Parameters:
        - dimension : int
            The dimension of the system.
        - x_resolution : int
            The resolution along the x-axis.
        - kwargs : dict, optional
            Optional keyword arguments to set additional parameters.

        Returns:
        - BEC object
            The system object representing the BEC simulation.

        Example:
        bec = BEC(3, 100, dissipation_factor=0.5)
        Creates a BEC system with 3 dimensions and an x-resolution of 100. The dissipation factor is set to 0.5.
        """

        # First initialize the BaseSystem class
        super().__init__(dimension, **kwargs)

        # Type of the system
        self.psi = None
        self.psi_f = None
        self.type = 'BEC'

        # Default simulation parameters
        self.gamma = 0.1 if 'gamma' not in kwargs else kwargs['gamma']    # Dissipation (gamma)
        self.V_ext = 0  # External potential

        # If there are additional arguments provided, set them as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    # Initial conditions
    def set_initial_condition_disordered(self, noise_strength=0.01):
        """
        Sets disordered initial condition for the BEC with some thermal flcutiations

        :param noise_strength:
        :return:
        """

        if self.dim==1:
            self.psi = np.random.rand(self.xRes) - 0.5 + \
                       1j * np.random.rand(self.xRes) - 0.5j

        elif self.dim==2:
            self.psi = np.random.rand(self.xRes, self.yRes)-0.5 + \
                       1j*np.random.rand(self.xRes, self.yRes)-0.5j

        elif self.dim==3:
            self.psi = np.random.rand(self.xRes, self.yRes,self.zRes) - 0.5 + \
                       1j * np.random.rand(self.xRes, self.yRes,self.zRes) - 0.5j
        else:
            raise Exception("Code for this dimension has not yet been implemented.")

        self.psi = noise_strength*self.psi
        self.psi_f = np.fft.fftn(self.psi)

    def set_harmonic_potential(self,R_tf):
        """
        Set the external potential to a harmonic trap with R_tf being the Thomas-Fermi radius
        Args:
                R_tf (float): The Thomas-Fermi radius
        returns:
                A harmonic potential
        """
        trapping_strength = 1 / (R_tf ** 2)
        if self.dim ==1:
            return  trapping_strength*(self.x -self.xmid )**2
        if self.dim == 2:
            return trapping_strength*(((self.x-self.xmid)**2).reshape(self.xRes, 1)
                                         +((self.y-self.ymid)**2).reshape(1, self.yRes) )
        if self.dim == 3:
            return trapping_strength * (((self.x - self.xmid) ** 2).reshape(self.xRes, 1,1)
                                           + ((self.y - self.ymid) ** 2).reshape(1, self.yRes,1)
                                           +((self.z - self.zmid) ** 2).reshape(1, 1,self.zRes) )

    def set_initial_condition_Thomas_Fermi(self):
        """
        Finds the Thomas_Fermi ground state.
        Must be precided by an energy relaxation to find the true ground state

        Returns: sets the value of self.psi and self.psi_f
        """
        self.psi = np.emath.sqrt(1-self.V_ext)
        self.psi[self.V_ext > 1] = 0
        self.psi_f = np.fft.fftn(self.psi)

    def set_spatialy_varying_gamma(self,d=7, wx=0,wy=0,wz=0):
        '''
        This function sets self.gamma so that it has a low value in the bulk and a large value near the edges.
         Args
             d (float): length of the interface between the low gamma and high gamma regions
            wx (float): distance fom center to the frame in x-direction
            wy (float):    -- " --                         y-direction
            wz (float):     -- " --                         z-direction
        return: self.gamma
        '''
        if self.dim == 2:
            X,Y =  np.meshgrid(self.x, self.y, indexing='ij')
            gammax = self.gamma +1/2 * (2 + np.tanh((X-self.xmid-wx)/d) - np.tanh((X-self.xmid+wx)/d) )
            gammay = self.gamma + 1 / 2 * (2 + np.tanh((Y-self.ymid - wy) / d) - np.tanh((Y-self.ymid + wy) / d))
            self.gamma = np.real(np.maximum(gammax,gammay))
        elif self.dim == 3:
            X, Y, Z = np.meshgrid(self.x, self.y,self.z, indexing='ij')
            gammax = self.gamma + 1 / 2 * (2 + np.tanh((X-self.xmid - wx) / d) - np.tanh((X-self.xmid + wx) / d))
            gammay = self.gamma + 1 / 2 * (2 + np.tanh((Y-self.ymid - wy) / d) - np.tanh((Y-self.ymid + wy) / d))
            gammaz = self.gamma + 1 / 2 * (2 + np.tanh((Z-self.zmid - wz) / d) - np.tanh((Z-self.zmid + wz) / d))
            self.gamma = np.real(np.maximum(gammax, gammay,gammaz))
        else:
            raise Exception("This feature is not yet available for the given dimension.")


    def calc_gaussian_stirring_potential(self,size,strength,position):
        """
        Function for calculate a gaussian potential
        Args:
            size (float) size of the stirrer
            strength (float) strength of the stirrer, i.e how large the potential is at the stirrers position
            position (array) the position of the stirrer
        returns:
            (numpy.ndarray) a gaussian potential
        """

        if self.dim ==1:
            return strength*np.exp( -(self.x -position[0])**2/size**2 )

        elif self.dim == 2:
            return strength*np.exp(-(((self.x-position[0])**2).reshape(self.xRes, 1)
                                         + ((self.y-position[1])**2).reshape(1, self.yRes)) /(size**2) )
        elif self.dim == 3:
            return strength* np.exp(-(((self.x - position[0]) ** 2).reshape(self.xRes, 1,1)
                                           + ((self.y - position[1]) ** 2).reshape(1, self.yRes,1)
                                           +((self.z - position[2]) ** 2).reshape(1, 1,self.zRes))/(size**2 ))

    #Time evolution
    def evolve_dGPE(self,number_of_steps):
        '''
               Evolver that uses the EDT2RK loop for the dGPE, assuming a time-independent potential
                   Args:
                       number_of_steps (int) the number of time steps that we are evolving the equation
                   returns:
                       Updates the self.psi and self.psi_f
               '''
        k2 = self.calc_k2()
        omega_f =   (1j + self.gamma) * (1 - 1 / 2 * k2)
        integrating_factors_f = self.calc_evolution_integrating_factors_ETD2RK(omega_f)

        for n in range(number_of_steps):
            self.psi, self.psi_f = self.evolve_ETD2RK_loop(integrating_factors_f,self.calc_nonlinear_evolution_term_f,
                                                           self.psi, self.psi_f)

    def evolve_dGPE_ETD4RK(self,number_of_steps):
        '''
        Evolver that uses the EDT4RK loop for the dGPE, assuming a time-independent potential
            Args:
                number_of_steps (int) the number of time steps that we are evolving the equation
            returns:
                Updates the self.psi and self.psi_f
        '''
        k2 = self.calc_k2()
        omega_f = (1j + self.gamma) * (1 - 1 / 2 * k2)
        integrating_factors_f = self.calc_evolution_integrating_factors_ETDRK4(omega_f)
        for n in range(number_of_steps):
            self.psi, self.psi_f = self.evolve_ETDRK4_loop(integrating_factors_f, self.calc_nonlinear_evolution_term_f,
                                                           self.psi, self.psi_f)




    def evolve_time_dependent(self,number_of_steps,V_t):
        '''
        Evolver that uses the EDT2RK loop for the dGPE, assuming a time-dependent potential
            Args:
                number_of_steps (int) the number of time steps that we are evolving the equation
                V_t (function(float)) the time dependent potential
            returns:
                Updates the self.psi and self.psi_f
        '''
        if not(hasattr(self,'t')):
            self.t = 0
        k2 = self.calc_k2()

        omega_f = (1j + self.gamma) * (1 - 1 / 2 * k2)
        integrating_factors_f = self.calc_evolution_integrating_factors_ETD2RK(omega_f)
        for n in range(number_of_steps):
            self.psi, self.psi_f = self.evolve_ETD2RK_loop_timedep(integrating_factors_f,self.calc_nonlinear_evolution_term_timedep_f,
                                                                    V_t, self.psi, self.psi_f)

    def evolve_time_dependent_ETDRK4(self,number_of_steps,V_t):
        '''
        Evolver that uses the EDT4RK loop for the dGPE, assuming a time-dependent potential
            Args:
                number_of_steps (int) the number of time steps that we are evolving the equation
                V_t (function(float)) the time dependent potential
            returns:
                Updates the self.psi and self.psi_f
        '''
        if not (hasattr(self, 't')):
            self.t = 0
        k2 = self.calc_k2()
        omega_f = (1j + self.gamma) * (1 - 1 / 2 * k2)
        integrating_factors_f = self.calc_evolution_integrating_factors_ETDRK4(omega_f)
        for n in range(number_of_steps):
            self.psi, self.psi_f = self.evolve_ETDRK4_loop_timedep(integrating_factors_f,
                                                                   self.calc_nonlinear_evolution_term_timedep_f,
                                                                   V_t, self.psi, self.psi_f)

    def evolve_relax_BEC(self,number_of_steps):
        '''
        Evolver that uses the EDT4RK loop for the dGPE in imaginary time to relax the equation
            Args:
                number_of_steps (int) the number of time steps that we are evolving the equation
            returns:
                Updates the self.psi and self.psi_f
        '''
        gamma0 = self.gamma

        self.gamma=1-1j

        self.evolve_dGPE_ETD4RK(number_of_steps)

        self.gamma=gamma0

    def evolve_comoving_dGPE(self, number_of_steps, velx):
        '''
        Evolver that uses the EDT4RK loop for the dGPE in the comoving frame.
        This evolver assume that the stiring is in the x-direction and that gamma is spatialy dependent
            Args:
                number_of_steps (int) the number of time steps that we are evolving the equation
                velx (float) velocity in x direction
            returns:
                Updates the fields self.psi and self.psi_f
                '''
        k2 = self.calc_k2()

        omega_f = (1j) * (1 - 1 / 2 * k2) + velx * self.dif[0]

        integrating_factors_f = self.calc_evolution_integrating_factors_ETDRK4(omega_f)

        for n in range(number_of_steps):
            self.psi, self.psi_f = self.evolve_ETDRK4_loop(integrating_factors_f, self.calc_nonlinear_evolution_term_comoving_f,
                                                           self.psi, self.psi_f)


            #Calculation functions


    def calc_nonlinear_evolution_term_f(self,psi):
        """
        Calculates the non-linear evolution term of the dGPE
        Args:
             psi (numpy.ndarray): the wavefunction at a given time.
        returns:
            (numpy.ndarray): the non-linear evolution term
        """
        psi2 = np.abs(psi)**2
        return np.fft.fftn((1j+self.gamma)*(-self.V_ext-psi2)*psi)

    def calc_nonlinear_evolution_term_timedep_f(self,psi,V_t):
        """
        Calculates the non-linear evolution term of the dGPE when the potential is time dependent
        Args:
            psi (numpy.ndarray): the wavefunction at a given time.
            V_t (function): the time-dependent potential
        Returns:
             (numpy.ndarray): the non-linear evolution term
        """
        self.V_ext = V_t(self.t)
        psi2 = np.abs(psi) ** 2
        return np.fft.fftn((1j + self.gamma) * (-self.V_ext - psi2) * psi)

    def calc_nonlinear_evolution_term_comoving_f(self,psi):
        """
               Calculates the non-linear evolution term of the dGPE when gamma is not a constant.
               Relevant for example in the comoving frame when we have a dissipative frame around the edge.
               Args:
                   psi (numpy.ndarray): the wavefunction at a given time.
               Returns:
                    (numpy.ndarray): the non-linear evolution term
               """
        psi2 = np.abs(psi)**2
        term1 = np.fft.fftn(-(1j+self.gamma)*(self.V_ext+psi2)*psi)
        term2 = np.fft.fftn(self.gamma*psi)
        term3 = 0.5*np.fft.fftn(self.gamma*np.fft.ifftn(-self.calc_k2()*np.fft.fftn(psi)))
        return (term1 + term2 + term3)

    def calc_vortex_density(self):
        return self.calc_defect_density([np.real(self.psi),np.imag(self.psi)])

    def calc_vortex_density_singular(self):
        return self.calc_defect_density([np.real(self.psi),np.imag(self.psi)])




    def calc_vortex_nodes(self):
        """
        Calculate the positions and charges of vortex nodes based on the defect density.
        Returns:
            list: A list of dictionaries representing the vortex nodes. Each dictionary contains the following keys:
                  - 'position_index': The position index of the vortex node in the defect density array.
                  - 'charge': The charge of the vortex node.
                  - 'position': The position of the vortex node as a list [x, y].
        """

        charge_tolerance = 0.2

        #Calculate defect density
        rho = self.calc_vortex_density()

        #Calculate the point where defect density is largest
        rho_max_index = np.unravel_index(np.argmax(np.abs(rho)),rho.shape)

        #Integrate the defect density around this point (i.e. in a ball around)
        charge,ball = self.calc_integrate_field(rho,index=rho_max_index,radius=1)

        #self.plot_field(rho)
        #plt.show()

        vortex_nodes = []

        X, Y = np.meshgrid(self.x, self.y, indexing='ij')


        while abs(charge)>charge_tolerance:
            vortex = {}
            vortex['position_index'] = rho_max_index
            vortex['charge'] = np.sign(charge)*np.ceil(np.abs(charge))
            x = np.sum(ball*abs(rho)*X)/np.sum(ball*abs(rho))
            y = np.sum(ball*abs(rho)*Y)/np.sum(ball*abs(rho))
            vortex['position'] = [x,y]

            vortex_nodes.append(vortex)

            rho[ball]=0
            rho_max_index = np.unravel_index(np.argmax(np.abs(rho)), rho.shape)

            charge, ball = self.calc_integrate_field(rho, index=rho_max_index, radius=1)



        return vortex_nodes


    #Plot functions
    def plot_vortices(self,vortex_nodes,ax=None):

        if ax == None:
            ax = plt.gcf().add_subplot(111)

        x_coords_pos = []
        y_coords_pos = []

        x_coords_neg = []
        y_coords_neg = []

        for vortex in vortex_nodes:

            if vortex['charge'] > 0:
                x_coords_pos.append(vortex['position'][0])
                y_coords_pos.append(vortex['position'][1])
            else:
                x_coords_neg.append(vortex['position'][0])
                y_coords_neg.append(vortex['position'][1])

        print(x_coords_pos,y_coords_pos)
        print(x_coords_neg,y_coords_neg)
        ax.scatter(x_coords_pos,y_coords_pos, marker='+',color='red')
        ax.scatter(x_coords_neg,y_coords_neg, marker='*',color='blue')
        ax.set_aspect('equal')

        

