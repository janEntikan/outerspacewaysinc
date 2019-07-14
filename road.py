from panda3d.core import ColorAttrib
from panda3d.core import NodePath
from panda3d.core import DirectionalLight, AmbientLight
from panda3d.core import PNMImage


# Load colors (8+256)
colors = [ # load special colors first
    ( 1,  1,  1, 1),	#0 = White  - debug
    ( 1,  1,  0, 1),	#1 = Yellow - endlevel
    ( 1, .8, .8, 1), 	#2 = LRed   - death
    (.8,  1, .8, 1),	#3 = LGreen - turby
    (.8, .8,  1, 1),    #4 = LBlue  - hp/fuel
    (.2, .2, .2, 1),    #5 = Dgray  - slide
    ( 0, .2,  0, 1),    #6 = Dgreen - slow
    (.8,  1, .8, 1),    #7 = Magenta- parking
]
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
H = [P, (1,0)]
T = D+[(5,0)]
NR = [N,N,N,N,N,N,N,N,N] 	# Empty row/space
EM = [[N,N,N,N,D,N,N,N,N]]	# Empty start map


class RoadMan():
    def __init__(self):
        self.mapNode = NodePath("empty")
        self.loadParts()
        self.newMap()
        self.buildMap()
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
        parts = "f", "b", "btd", "btu", "td", "tu"
        for part in parts:
            p = self.structure.find("**/"+part).getParent()
            p.show()
            p.setPos(0,0,0)
            self.parts.append(p)
        self.select = self.structure.find("_select")
        self.select.reparentTo(render)
        self.select.setPos(4,2,0)

    def newMap(self): # Create an empty map
        self.map = []
        for r in EM: self.map.append(r[:])

    def buildMap(self): # turn map into model
        # TODO: break up into 9x64 chunks
        # and only build where changed
        # so flattening doesn't slow down
        # when editing larger maps
        self.mapNode.removeNode()
        self.mapNode = NodePath("map")
        for y, row in enumerate(self.map):
            if not row == NR:
                for x, col in enumerate(row):
                    if not col == N:
                        for z, part in enumerate(col):
                            if not part == None:
                                pos = (x, (y*2), (z/2))
                                self.buildPart(pos, part)
        self.mapNode.flattenStrong()
        self.mapNode.reparentTo(render)

    def buildPart(self, pos, part): # place model
        newPart = self.parts[part[0]]
        newPart.setColor(colors[part[1]])
        newPart.setPos(pos)
        newPart.copyTo(self.mapNode)

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
        self.buildMap()

    def remove(self): # Remove tile at cursor
        x = self.pos[0]
        y = int(self.pos[1]/2)
        z = int(self.pos[2]*2)
        try:
            self.map[y][x][z] = None
        except IndexError:
            pass
        self.buildMap()
