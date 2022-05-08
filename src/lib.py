"""
Bending of Bernoulli beams project (numerical analysis) library of functions.
=============================================================================
 Last reviewed:  05.2022
=============================================================================
"""

import numpy as np
import matplotlib.pyplot as plt

def get_phi(grid, i):
    """
    Computes the functions that form the ansatz space Vh, where Vh is a space 
    of pecewise cubic polynomials.
    
    Input
    ----------
    grid: {array}
        Vector with gridpoints.
    i: {int}
        Index of the considered node in the grid.

    Returns
    -------
    phi: {function}
        Basis functions
        
    """
        
    h = grid[1:] - grid[:-1]
    
    def SF(xi):
        """
        Generates the cubic shape functions.

        Parameters
        ----------
        xi: {vector, int}
            (Normalized) absolute coordinate in he grid

        Returns
        -------
        phi_bar: {tuple}
            Collection of shape functions

        """
        
        phi_1 = 1 - 3 * xi**2 + 2*xi**3
        phi_2 = xi * (xi - 1)**2
        phi_3 = 3 * xi**2 - 2 * xi**3
        phi_4 = xi**2 * (xi - 1)
        
        phi_bar = (phi_1, phi_2, phi_3, phi_4)
        
        return phi_bar

    
    def phi(y):
        """
        Computes the basis functions defined inside the ansatz space

        Parameters
        ----------
        y: {vector, int}
            Absolute position in the grid.

        Returns
        -------
        funct_odd: {vector, int}
            Basis function related with position.
        funct_even: {vector, int}
            Basis function related with derivative.

        """

        funct_odd  = np.zeros(y.shape[0])
        funct_even = np.zeros(y.shape[0])
        
        if i == 0:
            funct_odd[ (y >= grid[0]) & (y < grid[1])] = SF(y[ (y >= grid[0]) & (y < grid[1])]/h[0])[0]
            funct_even[(y >= grid[0]) & (y < grid[1])] = h[0] * SF(y[ (y >= grid[0]) & (y < grid[1])]/h[0])[1]
           
        elif i == grid.shape[0]-1:
            funct_odd[ (y >= grid[-2]) & (y <= grid[-1])] = SF((y[ (y >= grid[-2]) & (y <= grid[-1])] - grid[-2])/h[0])[2]
            funct_even[(y >= grid[-2]) & (y <= grid[-1])] = h[0] * SF((y[ (y >= grid[-2]) & (y <= grid[-1])] - grid[-2])/h[0])[3]
           
        else:
            funct_odd[ (y>= grid[i - 1]) & (y < grid[i])] = SF((y[ (y>= grid[i - 1]) & (y < grid[i])] - grid[i - 1])/h[i])[2]
            funct_odd[ (y>= grid[i]) & (y < grid[i + 1])] = SF((y[ (y>= grid[i]) & (y < grid[i + 1])] - grid[i])/h[i])[0]
            
            funct_even[(y>= grid[i - 1]) & (y < grid[i])] = h[i] * SF((y[(y>= grid[i - 1]) & (y < grid[i])] - grid[i - 1])/h[i])[3]
            funct_even[(y>= grid[i]) & (y < grid[i + 1])] = h[i] * SF((y[(y>= grid[i]) & (y < grid[i + 1])] - grid[i])/h[i])[1]
            
        
        return funct_odd, funct_even
    
    return phi


def plotBeam(grid, solution, nData = 200):
    """
    Plots the deformed beam

    Parameters
    ----------
    grid: {array}
        Vector with gridpoints.
    solution: {array}
        Solution vector (the odd positions represent deformation
                         and the even ones, derivative).
    nData: {int, optional}
        Number of plotting datapoints. The default is 200.

    Returns
    -------
    None.

    """
    nN     = len(grid)
    x_plot = np.linspace(grid.min(), grid.max(), nData) 
    
    beam   = np.zeros(x_plot.shape)
    
    # NOTE: this is a bit slow. Suggestions accepted.
    
    for idx in range(1, nN + 1):
        
        phi   = get_phi(grid, idx - 1)
        
        beam += solution[2 * (idx) - 2] * phi(x_plot)[0]
        beam += solution[2 * (idx) - 1] * phi(x_plot)[1]
        
    
    plt.rcParams['text.usetex'] = True
    plt.rcParams.update({'font.size' : 9})
    
    fig, ax = plt.subplots(figsize=(5, 3), dpi = 3300)
    
    ax.plot(x_plot, beam, color= '#808080')
    ax.plot([grid.min(), grid.max()], [0, 0], color= '#959595', linestyle= '--')
    
    
    ax.axvline(x=0, color="black", linestyle="-", linewidth = 5)
    
    ax.set_xlabel('x-direction (-)')
    ax.set_ylabel('deformation (-)')
    
    ax.tick_params(direction= 'in', which= 'major', length= 4, bottom= True,
        top=True, right= False, left=True, width = 1)
    
    low, high = plt.ylim()
    bound = max(abs(low), abs(high))
    plt.ylim(-bound, bound)
    
    plt.text(0.875, 0.425,'undeformed', ha='center', va='center', transform=ax.transAxes, color= '#959595')