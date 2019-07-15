import json
from panda3d.core import ColorAttrib
from panda3d.core import NodePath
from panda3d.core import DirectionalLight, AmbientLight
from panda3d.core import PNMImage
from panda3d.core import Datagram, DatagramIterator


# Load colors (256)
#0 = White  - debug
#1 = Yellow - endlevel
#2 = LRed   - death
#3 = LGreen - turbo
#4 = LBlue  - hp/fuel
#5 = Dgray  - slide
#6 = Dgreen - slow
#7 = Magenta- parking
#>7= Safe
colors = []
palette = PNMImage()
palette.read("assets/palette.png")
for y in range(16):
    for x in range(16):
        c = palette.getXel(x,y)
        colors.append(tuple(c)+(1,))

# Set default parts, tiles and rows
# a tile is a stack of parts
# a row is 9 tiles wide
P = None			# None part
N = [P]				# None tile
D = [(0,0)]			# Default
H = [P, (1,0)]			# Test block
T = D+[(5,0)]			# Test tunnel
NR = [N,N,N,N,N,N,N,N,N] 	# Empty row/space
EM = [[H,N,N,N,D,N,N,N,H]]	# Empty start map


class RoadMan():
    def __init__(self):
        self.mapNode = NodePath("map")
        self.mapNode.reparentTo(render)
        self.mapNodes = []
        self.loadParts()
        self.loadMap()
        self.buildMap(0)
        self.lighten()
        self.sky()
        self.current = [0, 0]
        self.pos = [4,2,0]

    # add skysphere
    def sky(self):
        s = loader.loadModel("assets/models/sky.bam")
        s.reparentTo(base.cam)
        s.setBin('background', 0)
        s.setDepthWrite(False)
        s.setCompass()
        s.setLightOff()
        self.skysphere = s

    # add lights
    def lighten(self):
        dl = DirectionalLight("light_directional")
        dl.setColor((1,1,1,1))
        dlna = render.attachNewNode(dl)
        dlna.setHpr(-50, -50, 0)
        dl = DirectionalLight("light_directional")
        dl.setColor((0.1,0.1,0.1,1))
        dlnb = render.attachNewNode(dl)
        dlnb.setHpr(50, 50, 90)
        al = AmbientLight("light_ambient")
        al.setColor((0.05,0.05,0.05,1))
        aln = render.attachNewNode(al)
        render.setLight(dlna)
        render.setLight(dlnb)
        render.setLight(aln)

    # load geomnodes from model to clone later
    def loadParts(self): 
        self.structure = loader.loadModel("assets/models/parts.bam")
        self.parts = []
        leftout = "btd", "td"
        self.partnames = "f", "b", "btu", "tu"
        for part in self.partnames:
            p = self.structure.find("**/"+part).getParent()
            p.show()
            p.setPos(0,0,0)
            self.parts.append(p)
        self.select = self.structure.find("_select")
        self.select.reparentTo(render)
        self.select.setPos(4,2,0)
            
    def buildMap(self, at_row=None): # turn map into model
        # decrease chunksize if placing part is slow
        # increase chunksize if framerate is low
        chunksize = 32
        if at_row == None: # build entire map
            c = 0
            s = 0
            e = len(self.map)
        else: # build chunk that contains at_row
            c = int(at_row/chunksize)
            s = c*chunksize
            e = s+chunksize
        chunk = NodePath("map_"+str(c))
        cy = 0
        for y in range(e-s):
            if len(self.map) <= y+s:
                row = NR
            else: 
                row = self.map[y+s]
            if not row == NR: 
                self.buildRow(y+s, chunk, row)
            if cy >= chunksize:
                cy = 0
                self.addChunk(c, chunk)
                chunk = NodePath("map_"+str(c))
                c += 1
            cy += 1
        self.addChunk(c, chunk)

    def addChunk(self, c, chunk):
        chunk.flattenStrong()
        chunk.reparentTo(self.mapNode)
        while len(self.mapNodes) <= c:
            self.mapNodes.append(NodePath("empty"))
        self.mapNodes[c].removeNode()
        self.mapNodes[c] = chunk

    def buildRow(self, y, node, row):
        for x, col in enumerate(row):
            if not col == N:
                for z, part in enumerate(col):
                    if not part == None:
                        pos = (x, (y*2), (z/2))
                        self.buildPart(node, pos, part)

    def buildPart(self, node, pos, part): # place model
        newPart = self.parts[part[0]]
        newPart.setColor(colors[part[1]])
        newPart.setPos(pos)
        newPart.copyTo(node)

    def move(self, d): # Move edit cursor
        if d == "f": self.pos[1] += 2
        if d == "b": self.pos[1] -= 2
        if d == "l": self.pos[0] -= 1
        if d == "r": self.pos[0] += 1
        if d == "u": self.pos[2] += 0.5
        if d == "d": self.pos[2] -= 0.5

        if self.pos[1] < 2: self.pos[1] = 2
        if self.pos[0] < 0: self.pos[0] = 0
        if self.pos[0] > len(NR)-1:
            self.pos[0] = len(NR)-1
        if self.pos[2] < 0: self.pos[2] = 0
        self.select.setPos(tuple(self.pos))

    def moveCol(self, d): # Move color cursor
        if d == "u": self.current[1]-=16
        if d == "d": self.current[1]+=16
        if d == "l": self.current[1]-=1
        if d == "r": self.current[1]+=1
        if self.current[1] < 0:
            self.current[1] += 256
        if self.current[1] > 256:
            self.current[1] -= 256

    def shape(self, d):
        if d == "n": self.current[0] += 1
        if d == "p": self.current[0] -= 1
        if self.current[0] < 0:
            self.current[0] += len(self.partnames)
        if self.current[0] >= len(self.partnames):
            self.current[0] -= len(self.partnames)

    def clone(self): # Copy part at cursor
        x = self.pos[0]
        y = int(self.pos[1]/2)
        z = int(self.pos[2]*2)
        try:
            c = self.map[y][x][z]
        except:
            c = P
        if not c == P:
            self.current[0] = c[0]
            self.current[1] = c[1]

    def place(self): # Place part at cursor
        x = self.pos[0]
        y = int(self.pos[1]/2)
        z = int(self.pos[2]*2)
        new_block = tuple(self.current)        
        if y >= len(self.map):
            for i in range((y-len(self.map))+1):
               self.map.append(NR[:])
        if self.map[y][x] == N:
            self.map[y][x] = [None]
        if z >= len(self.map[y][x]):
            for i in range((z-len(self.map[y][x]))+1):
                self.map[y][x].append(None)
        self.map[y][x][z] = new_block
        self.buildMap(y)

    def remove(self): # Remove tile at cursor
        x = self.pos[0]
        y = int(self.pos[1]/2)
        z = int(self.pos[2]*2)
        try:
            self.map[y][x][z] = None
        except IndexError:
            pass
        self.buildMap(y)

    # FILE OPERATIONS
    def newMap(self): # Clear map
        self.map = []
        for r in EM: self.map.append(r[:])
        for node in self.mapNodes:
            node.removeNode()
        self.buildMap()

    def saveMap(self): # Save map to bytes-file
        data = Datagram()
        no_part = 64
        next_tile = 65
        for y in self.map:
            for x in y:
                for z in x:
                    if z == P:
                        data.addUint8(no_part)
                    else:
                        data.addUint8(z[0])
                        data.addUint8(z[1])
                data.addUint8(next_tile)
        with open('saved.map', 'wb') as outfile:
            outfile.write(bytes(data))

    def loadMap(self): # Load map from bytes-file
        file_data = open('saved.map', 'rb').read()
        data = Datagram(file_data)
        iterator = DatagramIterator(data)
        is_color = False
        map, row, tile  = [], [], []
        x, y, z = 0, 0, 0
        for i in range(iterator.getRemainingSize()):
            n = iterator.getUint8()
            if is_color:
                is_color = False
                part.append(n)
                tile.append(part)
            else:
                if n < 64:
                    part = [n]
                    is_color = True
                else:
                    if n == 64: 
                        tile.append(P)
                        z += 1
                    if n == 65: 
                        x += 1
                        row.append(tile)
                        tile = []
                    if x >= 9:
                        x = 0
                        y += 1
                        map.append(row)
                        row = []
        self.map = map
        self.buildMap()
        self.mapNode.analyze()
