from panda3d.core import ColorAttrib
from panda3d.core import NodePath
from panda3d.core import DirectionalLight, AmbientLight


P = None			# None part
N = [P]				# None tile
D = [(0,(0.6,0.3,0.6,1))]	# Default tile (grey floor)
H = [P, (1,(0.6,1,0.6,1))]
T = D+[(5,(0.6,0,0,1))]
NR = [N,N,N,N,N,N,N,N,N] 	# Empty row/space
EM = [				# Clean start map
    [N, N, N, N, D, N, N, N, N],
]


class RoadMan():
    def __init__(self):
        self.mapNode = NodePath("empty")
        self.loadParts()
        self.newMap()
        self.buildMap()
        self.lighten()
        self.sky()
        self.current = [0, [.5,.5,1,1]]
        self.pos = [4,2,0]
        render.analyze()

    def loadParts(self):
        self.structure = loader.loadModel("assets/models/parts.bam")
        self.structure.ls()
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

    def newMap(self):
        self.map = []
        for r in EM: self.map.append(r[:])

    def buildMap(self):
        print(self.map)
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

    def buildPart(self, pos, part):
        newPart = self.parts[part[0]]
        newPart.setColor(tuple(part[1]))
        newPart.setPos(pos)
        newPart.copyTo(self.mapNode)

    def sky(self):
        s = loader.loadModel("assets/models/sky.bam")
        s.reparentTo(base.cam)
        s.setBin('background', 0)
        s.setDepthWrite(False)
        s.setCompass()
        s.setLightOff()
        self.skysphere = s

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

    def place(self):
        x = self.pos[0]
        y = int(self.pos[1]/2)
        z = int(self.pos[2]*2)
        new_block = (self.current[0], tuple(self.current[1]))        
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

    def remove(self):
        x = self.pos[0]
        y = int(self.pos[1]/2)
        z = int(self.pos[2]*2)
        try:
            self.map[y][x][z] = None
        except IndexError:
            pass
        self.buildMap()


    def move(self, d):
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