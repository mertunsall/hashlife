# -*- coding: utf-8 -*-
"""
Created on Sun May  2 23:42:14 2021

@author: MertUnsal
"""

'''
AbstractNode.forward

The test creates a quadtree from the input universe (m, n, data)
and .forward() it. The returned node is compared to the one
returned by the reference implementation.

If you want to replay the test on your computer, you can do
the following:

data = (3, 1, [[True], [True], [True]]) # The test input data
n    = 2 # The number of times .extend() as been called

node = HashLifeUniverse(*data).root
for _ in range(n):
    node = node.extend()
node = node.forward()

where HashLifeUniverse is given in the project subject - you
can use it as-is even if you haven't completed the missing
methods.

'''
import math
import weakref

HC = weakref.WeakValueDictionary()

def hc(s):
    return HC.setdefault(s, s)

GROUP = ["mert.unsal@polytechnique.edu", "aleksandra.petkovic@polytechnique.edu"]

### THE SONG THAT ACCOMPANIED ME DURING THIS PROJECT: https://open.spotify.com/track/4mn2kNTqiGLwaUR8JdhJ1l?si=3046eee3e1724b9a

class Universe:
    def round(self):
        """Compute (in place) the next generation of the universe"""
        raise NotImplementedError

    def get(self, i, j):
        """Returns the state of the cell at coordinates (ij[0], ij[1])"""
        raise NotImplementedError

    def rounds(self, n):
        """Compute (in place) the n-th next generation of the universe"""
        for _i in range(n):
            self.round()
              
class NaiveUniverse(Universe):
    def __init__(self, n, m, cells):
        self.n = n
        self.m = m
        self.cells = cells

    def round(self):
        
        temp = [[self.get(i,j) for j in range(self.m)] for i in range(self.n)]
        # since we already do n*m operations in the following loop, creating this list doesn't change the asymptotic complexity
        # but it makes the implementation easier so we use it. THIS IS NOT THE HARD PART ANYWAY :D
        
        for i in range(self.n):
            for j in range(self.m):
                alive_cells = 0
                
                for k1 in {-1,0,1}:
                    for k2 in {-1,0,1}:
                        if (k1 != 0 or k2 != 0) and i + k1 < self.n and i+k1 >= 0 and j + k2 < self.m and j + k2 >= 0:
                            if self.get(i+k1, j+k2):
                                alive_cells += 1
                            
                if self.get(i,j):
                    if alive_cells < 2 or alive_cells > 3:
                        temp[i][j] = False
                    
                else:
                    if alive_cells == 3:
                        temp[i][j] = True     
                
                print(i,j,self.get(i,j),alive_cells)
        
        self.cells = temp

    def get(self, i, j):
        return self.cells[i][j]
    
class AbstractNode:
    
    def __init__(self):
        self._hash = None
        self._cache = None
        
    @property
    def cache(self):
        return self._cache
        
    def __hash__(self):
        if self._hash is None:
            self._hash = (
                self.population,
                self.level     ,
                self.nw        ,
                self.ne        ,
                self.sw        ,
                self.se        ,
            )
            self._hash = hash(self._hash)
        return self._hash
        
    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, AbstractNode):
            return False
        return \
            self.level      == other.level      and \
            self.population == other.population and \
            self.nw         is other.nw         and \
            self.ne         is other.ne         and \
            self.sw         is other.sw         and \
            self.se         is other.se
            
    @property
    def level(self):
        """Level of this node"""
        raise NotImplementedError()

    @property
    def population(self):
        """Total population of the area"""
        raise NotImplementedError()
        
    @staticmethod
    def canon(node):
        return hc(node)
    
    @staticmethod
    def cell(alive):
        node = CellNode(alive)
        return AbstractNode.canon(node)
    
    @staticmethod
    def node(nw, ne, sw, se):
        node = Node(nw, ne, sw, se)
        return AbstractNode.canon(node)
    
    @staticmethod
    def zero(k):
        if k == 0:
            return AbstractNode.cell(0)
        temp = AbstractNode.zero(k-1)
        return AbstractNode.node(temp, temp, temp, temp)
        
    def extend(self):
        if self.level == 0:
            zero = self.zero(0)
            return AbstractNode.node(zero, self, zero, zero)

        k = self.level - 1
        zerok = self.zero(k)
        nw2 = AbstractNode.node(zerok, zerok, zerok, self.nw)
        ne2 = AbstractNode.node(zerok, zerok, self.ne, zerok)
        sw2 = AbstractNode.node(zerok, self.sw, zerok, zerok)
        se2 = AbstractNode.node(self.se, zerok, zerok, zerok)
        return AbstractNode.node(nw2, ne2, sw2, se2)
        
    def get(self, i, j):
        node = self
        k = node.level
        
        if k == 0:
            if i == 0 and j == 0:
                return node.population
            else:
                return False
        
        l = 2**(k-1)
        if i >= l or i < -l or j >= l or j < -l:
            return False
        
        while k > 1:

            if i >= 0 and j >= 0:
                node = node.ne
                i -= 2**(k-2)
                j -= 2**(k-2)
                
            elif i >= 0 and j < 0:
                node = node.se
                i -= 2**(k-2)
                j += 2**(k-2)             

            elif i < 0 and j < 0:
                node = node.sw
                i += 2**(k-2)
                j += 2**(k-2)          

            else:
                node = node.nw
                i += 2**(k-2)
                j -= 2**(k-2)          
                
            k = node.level
        
        if i == 0 and j == 0:
            return node.ne.population
        elif i == 0 and j == -1:
            return node.se.population
        elif i == -1 and j == -1:
            return node.sw.population
        else:
            return node.nw.population
            
    def forward(self, l = None):
        
        k = self.level
        if k < 2:
            return None

        # the base case
        if l is not None:
            if l == k - 2:
                l = None       

        if l is None:
            
            # cache will be a dictionary such that {key: value} = {l: l forward return}
            if self.cache is not None:
                value = None
                try:
                    value = self.cache[k-2]
                except:
                    pass
                if value is not None:
                    return value
            
            if self.population == 0:
                return AbstractNode.zero(k-1)
            
            if k == 2:
                
                cell1 = self.nw.se.population
                cell2 = self.ne.sw.population
                cell3 = self.sw.ne.population
                cell4 = self.se.nw.population
                
                cells = [cell1, cell2, cell3, cell4]
                
                filter5 = 0b11101010111
                filter6 = filter5 << 1
                filter9 = 0b111010101110000
                filter10 = filter9 << 1
                
                w = 0
                w += self.se.se.population << 0 
                w += self.se.sw.population << 1 
                w += self.sw.se.population << 2
                w += self.sw.sw.population << 3
                w += self.se.ne.population << 4
                w += self.se.nw.population << 5
                w += self.sw.ne.population << 6
                w += self.sw.nw.population << 7
                w += self.ne.se.population << 8
                w += self.ne.sw.population << 9
                w += self.nw.se.population << 10
                w += self.nw.sw.population << 11
                w += self.ne.ne.population << 12
                w += self.ne.nw.population << 13
                w += self.nw.ne.population << 14
                w += self.nw.nw.population << 15
                
                w5 = w & filter5
                w6 = w & filter6
                w9 = w & filter9
                w10 = w & filter10
                
                ls = [w10,w9,w6,w5]
                s = [0,0,0,0]
                
                for i in range(4):
                    while ls[i] != 0:
                        ls[i] &= ls[i] - 1
                        s[i] += 1
                
                states = []
                
                for i in range(4):
                    if cells[i]:
                        if s[i] == 2 or s[i] == 3:
                            states.append(1)
                        else:
                            states.append(0)
                    else:
                        if s[i] == 3:
                            states.append(1)
                        else:
                            states.append(0)
                            
                nw = AbstractNode.cell(states[0])
                ne = AbstractNode.cell(states[1])
                sw = AbstractNode.cell(states[2])
                se = AbstractNode.cell(states[3])
                
                node = AbstractNode.node(nw, ne, sw, se)
                if self.cache is None:
                    self._cache = dict()
                self._cache[k-2] = node
                return node
            
            else:
                
                RNW = self.nw.forward() 
                RNE = self.ne.forward()
                RSW = self.sw.forward()
                RSE = self.se.forward()
                
                QCC = AbstractNode.node(self.nw.se, self.ne.sw, self.sw.ne, self.se.nw)
                QTC = AbstractNode.node(self.nw.ne, self.ne.nw, self.nw.se, self.ne.sw)
                QCL = AbstractNode.node(self.nw.sw, self.nw.se, self.sw.nw, self.sw.ne)
                QBC = AbstractNode.node(self.sw.ne, self.se.nw, self.sw.se, self.se.sw)
                QCR = AbstractNode.node(self.ne.sw, self.ne.se, self.se.nw, self.se.ne)
                
                RCC = QCC.forward()
                RTC = QTC.forward()
                RCL = QCL.forward()
                RBC = QBC.forward()
                RCR = QCR.forward()
                
                # state of central cells parts in 2**k-2 generations
                NW = AbstractNode.node(RNW, RTC, RCL, RCC).forward()
                NE = AbstractNode.node(RTC, RNE, RCC, RCR).forward()
                SW = AbstractNode.node(RCL, RCC, RSW, RBC).forward()
                SE = AbstractNode.node(RCC, RCR, RBC, RSE).forward()
                
                node = AbstractNode.node(NW,NE,SW,SE)
                if self.cache is None:
                    self._cache = dict()
                self._cache[k-2] = node
                return node
        
        else:
                    
            if self.cache is not None:
                value = None
                try:
                    value = self.cache[l]
                except:
                    pass
                if value is not None:
                    return value
                    
            k = self.level
            
            # we know for sure that k>2, i.e. this exists because for k = 2 l has to take the value 0, hence it will be included in the case where l == k-2 
            RNW = AbstractNode.node(self.nw.nw.se, self.nw.ne.sw, self.nw.sw.ne, self.nw.se.nw) 
            RNE = AbstractNode.node(self.ne.nw.se, self.ne.ne.sw, self.ne.sw.ne, self.ne.se.nw)
            RSW = AbstractNode.node(self.sw.nw.se, self.sw.ne.sw, self.sw.sw.ne, self.sw.se.nw)
            RSE = AbstractNode.node(self.se.nw.se, self.se.ne.sw, self.se.sw.ne, self.se.se.nw)
            
            RCC = AbstractNode.node(self.nw.se.se, self.ne.sw.sw, self.sw.ne.ne, self.se.nw.nw)
            RTC = AbstractNode.node(self.nw.ne.se, self.ne.nw.sw, self.nw.se.ne, self.ne.sw.nw)
            RCL = AbstractNode.node(self.nw.sw.se, self.nw.se.sw, self.sw.nw.ne, self.sw.ne.nw)
            
            RBC = AbstractNode.node(self.sw.ne.se, self.se.nw.sw, self.sw.se.ne, self.se.sw.nw)
            RCR = AbstractNode.node(self.ne.sw.se, self.ne.se.sw, self.se.nw.ne, self.se.ne.nw)
            
            ANW = AbstractNode.node(RNW, RTC, RCL, RCC)
            ANE = AbstractNode.node(RTC, RNE, RCC, RCR)
            ASW = AbstractNode.node(RCL, RCC, RSW, RBC)
            ASE = AbstractNode.node(RCC, RCR, RBC, RSE)
            
            NW = ANW.forward(l)
            NE = ANE.forward(l)
            SW = ASW.forward(l)
            SE = ASE.forward(l)
            
            node = AbstractNode.node(NW,NE,SW,SE)
            if self.cache is None:
                self._cache = dict()
            self._cache[l] = node
            return node            
            
    def __str__(self):
        s = ''
        k = self.level - 1
        for i in range(-2**k, 2**k):
            for j in range(-2**k, 2**k):
                if self.get(i,j) == 1:
                    s += '* '
                if self.get(i,j) == 0:
                    s += '. '
            s += '\n'
        
        return s

    nw = property(lambda self : None)
    ne = property(lambda self : None)
    sw = property(lambda self : None)
    se = property(lambda self : None)
    
    
    
class CellNode(AbstractNode):
    def __init__(self, alive):
        super().__init__()

        self._alive = bool(alive)

    level      = property(lambda self : 0)
    population = property(lambda self : int(self._alive))
    alive      = property(lambda self : self._alive)
    

class Node(AbstractNode):
    def __init__(self, nw, ne, sw, se):
        super().__init__()

        self._level      = 1 + nw.level
        self._population =  nw.population + ne.population + sw.population + se.population
        self._nw = nw
        self._ne = ne
        self._sw = sw
        self._se = se

    level = property(lambda self : self._level)
    population = property(lambda self : self._population)

    nw = property(lambda self : self._nw)
    ne = property(lambda self : self._ne)
    sw = property(lambda self : self._sw)
    se = property(lambda self : self._se)
    

class HashLifeUniverse(Universe):
    def __init__(self, *args):
        if len(args) == 1:
            self._root = args[0]
        else:
            self._root = HashLifeUniverse.load(*args)

        self._generation = 0

    @staticmethod
    def load(n, m, cells):
        level = math.ceil(math.log(max(1, n, m), 2))

        mkcell = getattr(AbstractNode, 'cell', CellNode)
        mknode = getattr(AbstractNode, 'node', Node    )

        def get(i, j):
            i, j = i + n // 2, j + m // 2
            return \
                i in range(n) and \
                j in range(m) and \
                cells[i][j]
                
        def create(i, j, level):
            if level == 0:
                return mkcell(get (i, j))

            noffset = 1 if level < 2 else 1 << (level - 2)
            poffset = 0 if level < 2 else 1 << (level - 2)

            nw = create(i-noffset, j+poffset, level - 1)
            sw = create(i-noffset, j-noffset, level - 1)
            ne = create(i+poffset, j+poffset, level - 1)
            se = create(i+poffset, j-noffset, level - 1)

            return mknode(nw=nw, ne=ne, sw=sw, se=se)
                
        return create(0, 0, level)

    def get(self, i, j):
        node = self.root
        k = node.level
        
        if k == 0:
            if i == 0 and j == 0:
                return node.population
            else:
                return False
        
        l = 2**(k-1)
        if i >= l or i < -l or j >= l or j < -l:
            return False
        
        while k > 1:

            if i >= 0 and j >= 0:
                node = node.ne
                i -= 2**(k-2)
                j -= 2**(k-2)
                
            elif i >= 0 and j < 0:
                node = node.se
                i -= 2**(k-2)
                j += 2**(k-2)             

            elif i < 0 and j < 0:
                node = node.sw
                i += 2**(k-2)
                j += 2**(k-2)          

            else:
                node = node.nw
                i += 2**(k-2)
                j -= 2**(k-2)          
                
                
            k = node.level
        
        if i == 0 and j == 0:
            return node.ne.population
        elif i == 0 and j == -1:
            return node.se.population
        elif i == -1 and j == -1:
            return node.sw.population
        else:
            return node.nw.population
        
    def extend(self, k):

        while self._root.level < 2:
            self._root = self._root.extend()
            
        def helper(root):
            
            pop = 0
            pop += root.nw.nw.population
            pop += root.nw.ne.population
            pop += root.ne.nw.population
            pop += root.ne.ne.population
            
            pop += root.se.se.population
            pop += root.se.sw.population
            pop += root.sw.sw.population
            pop += root.sw.se.population
            
            pop += root.nw.sw.population
            pop += root.sw.nw.population
            pop += root.ne.se.population
            pop += root.se.ne.population
            
            return pop
        
        pop = helper(self._root)
        
        while pop or self._root.level < k:
            self._root = self._root.extend()

            pop = helper(self._root)
        
    def rounds(self, n):
        
        if n <= 0:
            return

        extendtimes = math.ceil(math.log2(n)) + 2
        self.extend(extendtimes)
        
        while n > 0:
            if n == 1:
                self._root = self._root.forward(l = 0)
                self._generation += 1
                n -= 1
                return
            else:
                l = 1
                
                while n > 2**l:
                    l += 1
                    
                if 2**l > n:
                    l -= 1
                self._root = self._root.forward(l = l)
                self._generation += 2**l
                n -= 2**l
                
                if n != 0:
                    self.extend(self.root.level + 1)

    def round(self):
        return self.rounds(1)

    @property
    def root(self):
        return self._root
        
    @property
    def generation(self):
        return self._generation
    
    def __str__(self):
        s = ''
        k = self.root.level - 1
        for i in range(-2**k, 2**k):
            for j in range(-2**k, 2**k):
                if self.get(i,j) == 1:
                    s += '* '
                if self.get(i,j) == 0:
                    s += '. '
            s += '\n'
        
        return s
    
'''
            
            
            #here is the previous naive algorithm for self.forward n == something small case
            
            cell1 = self.nw.se.population
            cell2 = self.ne.sw.population
            cell3 = self.sw.ne.population
            cell4 = self.se.nw.population
            
            cells = [cell1, cell2, cell3, cell4]
            
            s = sum(cells)
            s1 = (s - cell1) + (self.nw.population - cell1) + self.ne.nw.population + self.sw.nw.population
            s2 = (s - cell2) + (self.ne.population - cell2) + self.se.ne.population + self.nw.ne.population
            s3 = (s - cell3) + (self.sw.population - cell3) + self.nw.sw.population + self.se.sw.population
            s4 = (s - cell4) + (self.se.population - cell4) + self.ne.se.population + self.sw.se.population
            ls = [s1,s2,s3,s4]
            
            states = []
            
            for i in range(4):
                if cells[i]:
                    if ls[i] == 2 or ls[i] == 3:
                        states.append(1)
                    else:
                        states.append(0)
                else:
                    if ls[i] == 3:
                        states.append(1)
                    else:
                        states.append(0)
                        
            nw = AbstractNode.cell(states[0])
            ne = AbstractNode.cell(states[1])
            sw = AbstractNode.cell(states[2])
            se = AbstractNode.cell(states[3])
            
            node = AbstractNode.node(nw, ne, sw, se)
            self._cache = node
            return node
            '''
                
        
