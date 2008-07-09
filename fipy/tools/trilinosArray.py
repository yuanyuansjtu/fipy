import PyTrilinos
from PyTrilinos import Epetra

import numpy

IV = 0
V = 1

# imposed shape needs:
# translate functions: imposed --> actual, local --> global (inc. axis?)
# string translate function
# reshaping
# _indexShape

# the shape attribute of a trilArr is a global imposed shape.  it does
# NOT reflect the actual shape of the array.

class trilArr:

    def __init__(self, shp=None, eMap=None, dType='l', \
                 parallel=True, vector=None):
        # should deal with imposed shape if len(shape)>2

        self.shape = trilShape(shp)

        if vector is None:
        
            self.shape = shape
            
            if eMap is not None:
                
                self.comm = eMap.Comm()
                self.eMap = eMap

            if eMap is None:

                self.comm = Epetra.PyComm()

                if not parallel:

                    self.eMap = None

                    if dType=='l':

                        self.vector = Epetra.IntVector(NUMERIX.zeros(shape,dType))
                        self.vtype = IV

                    if dType=='f':

                        self.vector = Epetra.Vector(NUMERIX.zeros(shape,dType))
                        self.vtype = V

                elif parallel:

                    if type(shape)==int:

                        self.eMap = Epetra.Map(shape,0,self.comm)
                        
                    elif type(shape)==tuple or type(shape)==list:

                        totSize = 1
                        for i in range(len(shape)):
                            totSize *= shape[i]
                        self.eMap = Epetra.Map(totSize,0,self.comm)

            if not hasattr(self, "vector"):
                if dType == 'l':

                    self.vector = Epetra.IntVector(self.eMap)
                    self.vtype = IV

                if dType == 'f':

                    self.vector = Epetra.Vector(self.eMap)
                    self.vtype = V

            self.dtype = dType

        elif vector is not None:

            self.vector = vector.copy()
            self.comm = vector.Comm()
            self.eMap = vector.Map()
            self.shape = vector.shape
            # may need to be updated on account of shapemap

            if isinstance(vector, Epetra.IntVector):

                self.vtype = IV
                self.dtype = 'l'
                
            elif isinstance(vector, Epetra.Vector):

                self.vtype = V
                self.dtype = 'f'

        self.array = self.vector.array

    def fillWith(self, value):
        
        if self.vtype==IV:
            self.vector.PutValue(value)
            
        else:
            self.vector.PutScalar(value)

    def put(self, ids, values):
        self.insertValues(ids, values)

    def insertValues(self, ids, values):

        # this should operate in accordance with the new shapemap method

        if type(values)==int:
            values = [values]*len(ids)

        if self.eMap is not None:
            elms = list(self.eMap.MyGlobalElements())
            rowlen = self.eMap.NumGlobalElements()
            mylen = self.eMap.NumMyElements()
            values = [v for (i,v) in zip(ids,values) if elms.count(i%rowlen)>0]
            ids = [i/rowlen*mylen+self.eMap.LID(i%rowlen) for i in ids if elms.count(i%rowlen)>0]
        numpy.put(self.array, ids, values)

    def getValues(self, ids):

        idee = [i for i in ids if self.m.MyGlobalElements().count(i)>0]
        return self.vector[idee]

    def _applyFloatFunction(self, f, optarg=None):

        if optarg is None:
            res = f(self.array)
        else:
            res = f(self.array, optarg.array)    
        v = Epetra.Vector(self.eMap, res)
        return trilArr(vector=v)

    def arccos(self):
        return _applyFloatFunction(self, numpy.arccos)

    def arccosh(self):
        return _applyFloatFunction(self, numpy.arccosh)

    def arcsin(self):
        return _applyFloatFunction(self, numpy.arcsin)

    def arcsinh(self):
        return _applyFloatFunction(self, numpy.arcsinh)

    def arctan(self):
        return _applyFloatFunction(self, numpy.arctan)

    def arctanh(self):
        return _applyFloatFunction(self, numpy.arctanh)

    def arctan2(self, other):
        return _applyFloatFunction(self, numpy.arctan2, other)

    def cos(self):
        return _applyFloatFunction(self, numpy.cos)

    def cosh(self):
        return _applyFloatFunction(self, numpy.cosh)

    def tan(self):
        return _applyFloatFunction(self, numpy.tan)

    def tanh(self):
        return _applyFloatFunction(self, numpy.tanh)

    def log10(self):
        return _applyFloatFunction(self, numpy.log10)

    def sin(self):
        return _applyFloatFunction(self, numpy.sin)

    def sinh(self):
        return _applyFloatFunction(self, numpy.sinh)

    def floor(self):
        return _applyFloatFunction(self, numpy.floor)

    def ceil(self):
        return _applyFloatFunction(self, numpy.ceil)

    def exp(self):
        return _applyFloatFunction(self, numpy.exp)
        
    def log(self):
        return _applyFloatFunction(self, numpy.log)
        
    def conjugate(self):
        return _applyFloatFunction(self, numpy.conjugate)

    def dot(self, other):
        return self.vector.Dot(other.vector)

    def allequal(self, other):
        return numpy.sum(self.array == other.array) == numpy.size(self.array)

    def allclose(self, other, rtol, atol):
        if self.array.shape != other.array.shape:
            return False
        return numpy.abs(self.array-other.array) < atol+rtol*numpy.abs(other.array)

    def globalSum(self):
        return self.comm.SumAll(localSum(self))

    def localSum(self):
        return numpy.sum(self.array)

    def globalTake(self, ids):
        els = list(self.localTake(ids))
        locsize = len(myIDs)
        maxsize = comm.MaxAll(locsize)
        sizes = comm.GatherAll(locsize)       
        while locsize<maxsize:
            els.append(-1)
            locsize=len(els)
        allEls = comm.GatherAll(els)
        allEls = [l for (el,proc) in zip(allEls,range(procs)) for (l,pos) in zip(el,range(sizes[proc]))]
        allEls = numpy.array(allEls).reshape(shp)
        return allEls

    def localTake(self, ids):

        # this should operate in accordance with the new shapemap method

        pid = self.comm.MyPID()
        glob = self.eMap.MyGlobalElements()
        indices = numpy.array(indices)
        shp = indices.shape
        indices = indices.reshape(-1)
        myIDs = [m.LID(el) for el in indices if list(glob).count(el)>=1]
        return self[myIDs]



    def reshape(self, shape):
        
        self.shape = shape

    def getShape(self):
        return self.shape

    def getRank(self):
        return len(self.shape)
    
    def __setitem__(self, i, y):
        # should operate in accordance with shapemap
        self.vector.__setitem__(i, y)

    def __getitem__(self, y):
        # should operate in accordance with shapemap
        return self.vector.__getitem__(y)

    # needs proper iterator

    def __repr__(self):
        # this should operate in accordance with the new shapemap method

        return self.vector.__repr__()

    def __str__(self):
        # this should operate in accordance with the new shapemap method
        return self.vector.__str__()

    def __or__(self, other):

        return self.array | other.array

class trilShape:

    def __init__(self, shape, eMap=None):
        self.globalShape = shape
        self.dimensions = self._dimensions(shape)
        self.actualShape = self._size(shape)
        if eMap is not None:
            self.map = eMap

    def setMap(eMap):
        self.map = eMap

    def getGlobalShape(self):
        return self.globalShape

    def getRank(self):
        return self.dimensions

    def getGlobalIndex(self, index):
        return shape._globalTranslateShape(index)

    def getLocalIndex(self, index):
        ind = self.getGlobalIndex(index)
        return self._globalToLocal(ind)

    def _globalToLocal(self, i):
        if self.map is None:
            return -1
        return self.map.LID(i)
    
    def _globalTranslateShape(self, index):

        if self._dimensions(index) != self.dimensions:
            return -1
        elif sum([i<j for (i,j) in zip(index,self.globalShape)]):
            return -2
        
        mult = 1
        lineIndex = 0

        for i in range(len(self.globalShape)+1)[1:]:
            lineIndex += mult*index[-i]
            mult *= self.globalShape[-i]

        return lineIndex

    def _size(self, shape):
        if type(shape)==tuple or type(shape)==list:
            size = shape[0]
            for i in range(self.dimensions)[1:]:
                size*=shape[i]
        elif type(shape)==int:
            size = shape
        return size

    def _dimensions(self, shape):
        return len(shape)

    def reshape(self, shape):
        if self.actualShape != self._size(shape):
            return -1

        self.globalShape = shape
        self.actualShape = self._size(shape)
        self.dimensions = self._dimensions(shape)

        return 1
    

def isTrilArray(obj):
    return isinstance(obj, trilArr)
