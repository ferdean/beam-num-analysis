"""
Bending of Bernoulli beams project (numerical analysis) library of functions.
=============================================================================
 Last reviewed:  05.2022
=============================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import fixed_quad
from scipy import sparse
import scipy as sp
import sympy as sm


# ++++++++++++++++++++++++++++++++++++++++++++++
# +             BASIS FUNCTIONS                +
# ++++++++++++++++++++++++++++++++++++++++++++++

def get_phi(grid, i, derivative = 0):
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
    
    def SF(xi, derivative = derivative):
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
        
        if derivative == 0:
            phi_1 = 1 - 3 * xi**2 + 2*xi**3
            phi_2 = xi * (xi - 1)**2
            phi_3 = 3 * xi**2 - 2 * xi**3
            phi_4 = xi**2 * (xi - 1)
        
        elif derivative == 1:
            phi_1 = -6 * xi + 6 * xi**2
            phi_2 = 3 * xi**2 - 4 * xi + 1
            phi_3 = -6 * (xi - 1) * xi
            phi_4 = xi * (3 * xi - 2)
            
        elif derivative == 2:
            phi_1 = -6 + 12 * xi
            phi_2 = 6 * xi - 4
            phi_3 = 6 - 12 * xi
            phi_4 = 6 * xi - 2
            
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
        
        if type(y) == int or float: 
            y = np.array(y)
            
        funct_odd  = np.zeros(y.shape)
        funct_even = np.zeros(y.shape)   
    
        if i == 0:
            funct_odd[ (y >= grid[0]) & (y <= grid[1])] = SF(y[ (y >= grid[0]) & (y <= grid[1])]/h[0])[0]
            funct_even[(y >= grid[0]) & (y <= grid[1])] = h[0] * SF(y[ (y >= grid[0]) & (y <= grid[1])]/h[0])[1]
           
        elif i == grid.shape[0]-1:
            funct_odd[ (y >= grid[-2]) & (y <= grid[-1])] = SF((y[ (y >= grid[-2]) & (y <= grid[-1])] - grid[-2])/h[0])[2]
            funct_even[(y >= grid[-2]) & (y <= grid[-1])] = h[0] * SF((y[ (y >= grid[-2]) & (y <= grid[-1])] - grid[-2])/h[0])[3]
           
        else:
            funct_odd[ (y>= grid[i - 1]) & (y <= grid[i])] = SF((y[ (y>= grid[i - 1]) & (y <= grid[i])] - grid[i - 1])/h[i])[2]
            funct_odd[ (y>= grid[i]) & (y <= grid[i + 1])] = SF((y[ (y>= grid[i]) & (y <= grid[i + 1])] - grid[i])/h[i])[0]
            
            funct_even[(y>= grid[i - 1]) & (y <= grid[i])] = h[i] * SF((y[(y>= grid[i - 1]) & (y <= grid[i])] - grid[i - 1])/h[i])[3]
            funct_even[(y>= grid[i]) & (y <= grid[i + 1])] = h[i] * SF((y[(y>= grid[i]) & (y <= grid[i + 1])] - grid[i])/h[i])[1]
    
        
        return funct_odd, funct_even
    
    return phi


def getGaussParams():
    nodes = (np.sort(np.array([(3/7 - (2/7)*(6/5)**0.5)**0.5, -(3/7 - (2/7)*(6/5)**0.5)**0.5 , 
                              (3/7 + (2/7)*(6/5)**0.5)**0.5, -(3/7 + (2/7)*(6/5)**0.5)**0.5])) +1) /2
    weights = np.array([(18-30**0.5)/36, (18+30**0.5)/36, (18+30**0.5)/36, (18-30**0.5)/36]) /2
    
    return nodes, weights


# ++++++++++++++++++++++++++++++++++++++++++++++
# +             MATRICES COMPUT.               +
# ++++++++++++++++++++++++++++++++++++++++++++++
    
    
def getMatrices(grid, E, I, mu, quadrature = True):
    """
    Computes mass and stiffness matrices for a 1D problem. 

    Parameters
    ----------
    grid: {array}
        Vector with gridpoints.
    E: {function} or {scalar}
        Young modulus [N/mm2]
    I: {function} or {scalar}
        Area moment of inertia.
    mu: {function} or {scalar}
        Density.
    quadrature: {boolean, optional}
        States if the integration is performed numercially (True) or 
        anallytically (False). The default is True.

    Returns
    -------
    S: {array}
        Stiffness matrix.
    M: {array}
        Mass matrix.

    """      
    def getLocalMatrices(idx):
        
        if callable(E): 
            constantprops = False 
        else: 
            constantprops = True;
        
        x0 = grid[idx]
        x1 = grid[idx + 1]
        
        S = np.zeros((4,4))        
        M = np.zeros((4,4))
        
        h  = (x1 - x0)
                    
        first_mode = np.array([ [1,0,1,0],
                                [0,0,0,0],
                                [1,0,1,0],
                                [0,0,0,0] ])  * h**-3

        second_mode = np.array([ [0,1,0,1],
                                 [1,0,1,0],
                                 [0,1,0,1],
                                 [1,0,1,0] ]) * h**-2
    
        third_mode = np.array([ [0,0,0,0],
                                [0,1,0,1],
                                [0,0,0,0],
                                [0,1,0,1] ]) * h**-1
        
        h_array = first_mode + second_mode + third_mode
            
        if not quadrature:
            xi = sm.Symbol('xi')
            x  = (x1 - x0) * xi + x0

            phi1 = 1 - 3 * xi**2 + 2 * xi**3
            phi2 = xi * (xi - 1)**2
            phi3 = 3 * xi**2 - 2 * xi**3
            phi4 = xi**2 * (xi - 1)
            phi  = [phi1, phi2, phi3, phi4]
    
            if constantprops:
                for i in range(4):
                    for j in range(4):
                    
                        S[i,j] = float(sm.integrate(sm.diff(phi[i], xi, 2)*sm.diff(phi[j], xi ,2), (xi, 0, 1)))
                        M[i,j] = float(sm.integrate(phi[i]*phi[j],                                 (xi, 0, 1))) 
                                        
                S = S*E*I
                M = mu*M
                        
            else:
                for i in range(4):
                    for j in range(4):
                        
                        # TBD: Check if we need to multiply with Jacobian (x1 - x0)
                        
                        S[i,j] = float(sm.integrate(E(x) * I(x) * sm.diff(phi[i], xi, 2)*sm.diff(phi[j], xi ,2), (xi, 0, 1)))
                        M[i,j] = float(sm.integrate(mu(x) * phi[i]*phi[j],                                       (xi, 0, 1)))      

        else:
                             
            phi   = [lambda x :1-3*x*x+2*x*x*x, lambda x :x*(x-1)**2, lambda x :3*x*x - 2*x*x*x, lambda x :x*x*(x-1)]
            ddphi = [lambda x :-6 + 12 * x, lambda x :6 * x - 4, lambda x :6 - 12 * x, lambda x :6 * x - 2]
            
            nodes, weights = getGaussParams()
            
            if constantprops: 
                 for i in range(4):
                    for j in range(4):
                        for k in range(4):
                            S[i,j] += weights[k] * E * I * ddphi[i](nodes[k])  * ddphi[j](nodes[k]) 
                            M[i,j] += weights[k] * mu * phi[j](nodes[k]) 
            else:
                
                for i in range(4):
                    for j in range(4):
                        for k in range(4):
                            S[i,j] += weights[k] * E((x1 - x0) * nodes[k] + x0) * I((x1 - x0) * nodes[k] + x0) * ddphi[i](nodes[k])  * ddphi[j](nodes[k])
                            M[i,j] += weights[k] * mu(nodes[k]) * phi[i](nodes[k])  * phi[j](nodes[k])
                        
        return np.multiply(S, h_array), np.multiply(M, h_array)
        
    # ++++++++++++++++++++++++++++++++++++++++++++++
    # +            Function starts here            +
    # ++++++++++++++++++++++++++++++++++++++++++++++
       
    nN    = grid.shape[0]  # Number of nodes
    nE    = nN - 1         # Number of elements
    nNe   = 2              # Number of nodes per element
    nDOFn = 2              # Number of DOF per node
    nDOFg = nDOFn * nN     # Global number of DOF
    nDOFe = nDOFn * nNe    # Number of DOF per element
    
    S = np.zeros((nDOFg, nDOFg))
    M = np.zeros((nDOFg, nDOFg))
    
    Ig = np.zeros((nDOFe**2 + (nE - 1)*nDOFe**2,))
    Jg = np.zeros((nDOFe**2 + (nE - 1)*nDOFe**2,))
    Mg = np.zeros((nDOFe**2 + (nE - 1)*nDOFe**2,))
    Sg = np.zeros((nDOFe**2 + (nE - 1)*nDOFe**2,))
    
    top = np.repeat(range(nN), 2)[1:-1]  # Topology matrix
    top = top.reshape((-1, nNe))
        
    for idx in range(nE):
        e_k = np.array([top[idx, 0] + idx, top[idx, 0] + idx + 1, 
                        top[idx, 0] + idx + 2, top[idx, 0] + idx + 3])  # Local DOF
        
        S_loc, M_loc = getLocalMatrices(idx)
        
        # Matrix fast assembly [ref: F. Cuvelier, et al, arXiv preprint arXiv:1305.3122]     
        t     = np.array(range(nDOFe))
        Tt, T = np.meshgrid(t, t)
        
        ii  = T.flatten()
        jj  = Tt.flatten()
        kk  = np.array(range(nDOFe**2))
        kkk = kk + nDOFe**2 * (idx)
        
        Ig[kkk] = e_k[ii]
        Jg[kkk] = e_k[jj]
        Mg[kkk] = M_loc.flatten() 
        Sg[kkk] = S_loc.flatten()
    
    M = sp.sparse.csc_matrix((Mg, (Ig, Jg)), shape = (nDOFg, nDOFg))
    S = sp.sparse.csc_matrix((Sg, (Ig, Jg)), shape = (nDOFg, nDOFg))
       
    return S, M 


def getRHS(grid, q): 
    """
    Computes inhomogeneity. Everything is done in the matrix-vector multiplication 
    form (not super obvious, but less for loops and increased efficiency). Since 
    the test functions are 4th order, it has been decided to do 4-point gauss 
    quadrature, not to waste precision

    Parameters
    ----------
    grid: {array}
        Vector with gridpoints.
    q: {function}
        Applied force. It has to work with numpy arrays

    Returns
    -------
    RHS: {vector}
        Right-hand-side.

    """
    
    N = len(grid)
    h = grid[1:] - grid[0:-1]
    
    nodes, weights = getGaussParams() # 4-point Gauss quadrature (https://en.wikipedia.org/wiki/Gaussian_quadrature)

    # Basis functions on the unit interval
    phis = [lambda x :1-3*x*x+2*x*x*x, lambda x :x*(x-1)**2, lambda x :3*x*x - 2*x*x*x, lambda x :x*x*(x-1)]
    
    # Initialize and fill local matrix
    s = np.zeros((4,4))
    
    for i in range(4):
        for j in range(4):
            s[i,j] = weights[j] * phis[i](nodes[j]) 
            
    # Global matrix assembly
    G = np.zeros((N*2,(N-1)*4))
    
    for i in range(N-1):
        G[2*i:2*i+4, 4*i:4*i+4] = s

    # Locations on the beam where q has to be evaluated (4 points per element)
    q_nodes = np.tile(nodes,(N-1,1)) * np.tile(h,(4,1)).T + np.tile(grid[:-1],(4,1)).T
    
    # Compute q at those locations and scale each q value by the element length(the element at which this node happened to be)
    q_vec = (q(q_nodes) * np.tile(h,(4,1)).T).flatten() 

    RHS  = G @ q_vec
    
    return RHS

def fixBeam(M, S, RHS, e, d, BC):
    """
    Applies boundary conditions to the problem

    Parameters
    ----------
    S: {array}
        Free stiffness matrix.
    RHS: {vector} 
        Free right-hand-side of the equation (inhomogeneities).
    e: {array}
        Basis functions evaluated at x = 0 and x = L.
    d: {array} 
        Derivatives of basis functions evaluated at x = 0 and x = L.
    BC: {Tuple}
        Boundary conditions, such that
            *BC[0] = Deformation at x = 0 (essential bc)
            *BC[1] = Derivative of the deformation at x = 0 (essential bc)
            *BC[2] = Shear force at x = L (physical bc)
            *BC[3] = Bending moment at x = L (physical bc)

    Returns
    -------
    Se: {array}
        Constrained stiffness matrix.
    RHSe: {vector}
        Constrained right-hand-side.
    """   
    
    nDOF = M.shape[0]
    
    e0, eL = e
    d0, dL = d
    a, b, QL, ML = BC
    
    basisVector = sparse.csr_matrix(np.vstack((e0, d0)))
            
    RHSe = RHS + QL * eL + ML * dL
    RHSe = np.hstack((RHSe, np.array([a, b])))
    
    Se   = sparse.vstack((S, basisVector))
    Se   = sparse.hstack((Se, (sparse.hstack((basisVector, sparse.csr_matrix((2, 2))))).T))
    
    Me   = sparse.vstack((sparse.hstack((M, sparse.csr_matrix((nDOF, 2)))), sparse.csr_matrix((2, nDOF + 2))))
    
    return Me, Se, RHSe


# ++++++++++++++++++++++++++++++++++++++++++++++
# +               POSTPROCESS                  +
# ++++++++++++++++++++++++++++++++++++++++++++++

def get_sol(grid, coeffs):
    """
    Returns the solution function

    Parameters
    ----------
    grid: {array}
        Vector with gridpoints.
    coeffs: {array}
        Solution vector (the odd positions represent deformation
                         and the even ones, derivative).
    Returns
    -------
    w: {function}
        Solution function.
    """
    
    # This for loop will be removed using the matrices ex and dx from computeMatrices()
    def w(y):
        beam = np.zeros(y.shape)
        
        for idx in range(int(coeffs.shape[0]/2)):
            phi   = get_phi(grid, idx)
            beam += coeffs[2 * idx] * phi(y)[0] + coeffs[2 * idx + 1] * phi(y)[1]

        return beam
    
    return w

def plotBeam(grid, coeffs, nData, *argv):
    """
    Plots the deformed beam

    Parameters
    ----------
    grid: {array}
        Vector with gridpoints.
    coeffs: {array}
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
    
    beam = get_sol(grid, coeffs)
    
    plt.rcParams['text.usetex'] = True
    plt.rcParams.update({'font.size' : 9})
    
    fig, ax = plt.subplots(figsize=(5, 3), dpi = 200)
    
    ax.plot(x_plot, beam(x_plot) * 1e3, color= '#808080', label = 'numerical')
    ax.plot([grid.min(), grid.max()], [0, 0], color= '#959595', linestyle= '--')
    
    for arg in argv: 
        ax.plot(x_plot, arg(x_plot) * 1e3, color = 'r', linestyle = '-.', label = 'exact')
    
    ax.axvline(x=0, color="black", linestyle="-", linewidth = 5)
    
    ax.set_xlabel('x-direction (-)')
    ax.set_ylabel('deformation (mm)')
    
    ax.tick_params(direction= 'in', which= 'major', length= 4, bottom= True,
        top=True, right= False, left=True, width = 1)
    
    low, high = plt.ylim()
    bound = max(abs(low), abs(high))
    plt.ylim(-bound, bound)
    
    plt.text(0.875, 0.425,'undeformed', ha='center', va='center', transform=ax.transAxes, color= '#959595')
    
    plt.legend(loc = 'lower left')
    
    plt.show()



# ++++++++++++++++++++++++++++++++++++++++++++++
# +              NEWMARK METHOD                +
# ++++++++++++++++++++++++++++++++++++++++++++++


def Newmarkmethod_step(u,u_1,u_2,h,M,S,p,beta = 1/4,gamma = 1/2):
    #calculating intermediate steps, i.e. step (a) in the transcript
    u_star = u + u_1*h+(0.5-beta)*u_2*h**2
    u_1_star = u_1 + (1-gamma)*u_2*h
    
    #Creating and solving linear system to solve for u"_{j+1}
    S = S.tocsr()
    A = beta*h**2*S
    A[0:M.shape[0],0:M.shape[1]] += M
    b = p - S@u_1_star
    u_2 = sparse.linalg.spsolve(A, b)

    #Solving for u_{j+1}, u'_{j+1}
    u = u_star + beta*h**2*u_2
    u_1 = u_1_star + gamma*h*u_2

    return u,u_1,u_2
