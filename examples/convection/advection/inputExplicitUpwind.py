#!/usr/bin/env python

## 
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "inputExplicitUpwind.py"
 #                                    created: 12/16/03 {3:23:47 PM}
 #                                last update: 2/18/05 {3:02:08 PM} 
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  FiPy is an experimental
 # system.  NIST assumes no responsibility whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 # 
 # This software can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #  
 #  Description: 
 # 
 #  History
 # 
 #  modified   by  rev reason
 #  ---------- --- --- -----------
 #  2003-11-10 JEG 1.0 original
 # ###################################################################
 ##

""" 
This example shows the failure of advecting a square pulse with a first
order explicit upwind scheme.
"""

import Numeric
     
from fipy.meshes.grid2D import Grid2D
from fipy.solvers.linearCGSSolver import LinearCGSSolver
from fipy.iterators.iterator import Iterator
from fipy.variables.cellVariable import CellVariable
from fipy.viewers.gist1DViewer import Gist1DViewer
from fipy.terms.explicitUpwindConvectionTerm import ExplicitUpwindConvectionTerm
from fipy.boundaryConditions.fixedValue import FixedValue
from fipy.boundaryConditions.fixedFlux import FixedFlux

valueLeft = 0.
valueRight = 0.
L = 10.
nx = 400
ny = 1
dx = L / nx
dy = L / ny
cfl = 0.1
velocity = -1.
timeStepDuration = cfl * dx / abs(velocity)
steps = 1000

mesh = Grid2D(dx, dy, nx, ny)

startingArray = Numeric.zeros(nx * ny, 'd')
startingArray[50:90] = 1. 

var = CellVariable(
    name = "advection variable",
    mesh = mesh,
    value = startingArray)

boundaryConditions = (
    FixedValue(mesh.getFacesLeft(), valueLeft),
    FixedValue(mesh.getFacesRight(), valueRight),
    FixedFlux(mesh.getFacesTop(), 0.),
    FixedFlux(mesh.getFacesBottom(), 0.)
    )

from fipy.terms.transientTerm import TransientTerm
from fipy.terms.explicitUpwindConvectionTerm import ExplicitUpwindConvectionTerm

eq = TransientTerm() - ExplicitUpwindConvectionTerm(coeff = (velocity, 0.))

if __name__ == '__main__':
    
    viewer = Gist1DViewer(vars=(var,))
    for step in range(steps):
        eq.solve(var,
                 dt = timeStepDuration,
                 boundaryConditions = boundaryConditions,
                 solver = LinearCGSSolver(tolerance = 1.e-15, steps = 2000))
        viewer.plot()
    viewer.plot()
    raw_input('finished')
