#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "trilinosSolver.py"
 #
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #  Author: Maxsim Gibiansky <maxsim.gibiansky@nist.gov>
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
 # ###################################################################
 ##

__docformat__ = 'restructuredtext'

from PyTrilinos import Epetra
from PyTrilinos import EpetraExt

from fipy.solvers.solver import Solver
from fipy.tools import numerix
from fipy.tools.decorators import getsetDeprecated

class TrilinosSolver(Solver):

    """
    .. attention:: This class is abstract. Always create one of its subclasses.

    """
    def __init__(self, *args, **kwargs):
        if self.__class__ is TrilinosSolver:
            raise NotImplementedError, "can't instantiate abstract base class"
        else:
            Solver.__init__(self, *args, **kwargs)

    def _storeMatrix(self, var, matrix, RHSvector):
        self.var = var
        if hasattr(self, 'matrix'):
            self.matrix.matrix = matrix.matrix
        else:
            self.matrix = matrix
        self.RHSvector = RHSvector
        
    @getsetDeprecated
    def _getGlobalMatrixAndVectors(self):
        return self._globalMatrixAndVectors

    @property
    def _globalMatrixAndVectors(self):
        if not hasattr(self, 'globalVectors'):
            globalMatrix = self.matrix.asTrilinosMeshMatrix()

            mesh = self.var.mesh
            localNonOverlappingCellIDs = mesh._localNonOverlappingCellIDs

            nonOverlappingVector = Epetra.Vector(globalMatrix.nonOverlappingColMap, 
                                                 self.var[localNonOverlappingCellIDs])

            nonOverlappingRHSvector = Epetra.Vector(globalMatrix.nonOverlappingRowMap, 
                                                    self.RHSvector[localNonOverlappingCellIDs])

            overlappingVector = Epetra.Vector(globalMatrix.overlappingColMap, self.var)

            self.globalVectors = (globalMatrix, nonOverlappingVector, nonOverlappingRHSvector, overlappingVector)

        return self.globalVectors
        
    def _deleteGlobalMatrixAndVectors(self):
        self.matrix.flush()
        del self.globalVectors
        
    def _solve(self):
        from fipy.terms import SolutionVariableNumberError
        
        globalMatrix, nonOverlappingVector, nonOverlappingRHSvector, overlappingVector = self._globalMatrixAndVectors

        if ((globalMatrix.matrix.NumGlobalRows() != globalMatrix.matrix.NumGlobalCols())
            or (globalMatrix.matrix.NumGlobalRows() != len(self.var.globalValue))):

            raise SolutionVariableNumberError
            
#         self._solve_(globalMatrix.matrix, 
#                      overlappingVector, 
#                      nonOverlappingRHSvector)
        self._solve_(globalMatrix.matrix, 
                     nonOverlappingRHSvector, 
                     overlappingVector)

#         overlappingVector.Import(nonOverlappingVector, 
#                                  Epetra.Import(globalMatrix.overlappingColMap, 
#                                                globalMatrix.nonOverlappingColMap), 
#                                  Epetra.Insert)

        self.var.value = overlappingVector

        self._deleteGlobalMatrixAndVectors()
        del self.var
        del self.RHSvector
            
    @getsetDeprecated
    def _getMatrixClass(self):
        return self._matrixClass

    @property
    def _matrixClass(self):
        from fipy.solvers import _MeshMatrix
        return _MeshMatrix

    def _calcResidualVector(self, residualFn=None):
        if residualFn is not None:
            return residualFn(self.var, self.matrix, self.RHSvector)
        else:
            globalMatrix, nonOverlappingVector, nonOverlappingRHSvector, overlappingVector = self._globalMatrixAndVectors
                
            # If A is an Epetra.Vector with map M
            # and B is an Epetra.Vector with map M
            # and C = A - B
            # then C is an Epetra.Vector with *no map* !!!?!?!
            residual = Epetra.Vector(globalMatrix.nonOverlappingRowMap)

            residual.Import(globalMatrix * overlappingVector, 
                            Epetra.Import(globalMatrix.nonOverlappingRowMap, 
                                          globalMatrix.overlappingRowMap), 
                            Epetra.Insert)

            residual -= nonOverlappingRHSvector
            
            return residual
            
    def _calcResidual(self, residualFn=None):
        if residualFn is not None:
            return residualFn(self.var, self.matrix, self.RHSvector)
        else:
            comm = self.var.mesh.communicator
            return comm.Norm2(self._calcResidualVector())
        
    def _calcRHSNorm(self):
        return self.nonOverlappingRHSvector.Norm2()
