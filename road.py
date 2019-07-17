from panda3d.core import NodePath
from panda3d.core import DirectionalLight, AmbientLight
from panda3d.core import PNMImage
from panda3d.core import Datagram, DatagramIterator
from purses3d import Purses

# Load colors (256)
#0 = White  - debug (bonus points?)
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
    def __init__(self, root):
        self.root = root
        self.mapNode = NodePath("map")
        self.mapNode.reparentTo(render)
        self.mapNodes = []
        self.loadParts()
        self.loadMap()
        self.currentMap = 0
        self.lighten()
        self.sky()
        self.current = [0, 0]
        self.pos = [4,2,0]
        self.hudPiece = NodePath("hud")
        self.colors = loader.loadTexture("assets/palette.png")
        self.colors.setMagfilter(0)
        self.colors.setMinfilter(0)

        self.moveCol("l"); self.moveCol("r")
        self.root.hud.setScreen(self.colors)

        self.console = Purses(50,23)
        self.console.node.setScale(0.25)
        self.console.node.setPos(-.7, 0, .7)

    def printHelp(self):
        self.console.fill()
        cm = str(self.currentMap)
        le = str(len(self.maps)-1)
        self.console.move(0,0)
        self.console.addstr("ROAD " + cm +"-"+ le+"\n", ["red",None])
        self.console.addstr("EDIT MODE\n", ["grey",None])
        controls = (
            "tab            start game",
            "d              set drain",
            "g              set gravity",
            "arrows         move cursor on x and y",
            "pgup/pgdown    move cursor on z",
            "space/delete   place/remove piece",
            "numpad 7 and 8 prev/next shape",
            "numpad 2,4,6,8 select color",
            "c              copy piece",
            "n		    clear track",
            "/              append new track",
            ", and .        prev/next track",
            "s and l        save/load all tracks",
            " ",
            "Based on:",
            "    Skyroads by Bluemoon Software in 1993",
            "Programming, Art and SFX: ",
            "    Hendrik-Jan in 2019",
            "Music:",
            "    composed by Ott Aaloe",
            "    reimagined by Hendrik-Jan",

        )
        for i in controls:
            self.console.addstr(i+"\n", ["grey", None])
        self.console.refresh()

    def enableEditing(self):
        self.printHelp()
        self.root.music.setVolume(0.03)
        self.select.show()
        self.setHudPiece()
        self.root.hud.screenUp()

    def disableEditing(self):
        self.console.fill()
        self.console.refresh()
        self.root.music.setVolume(0.1)
        self.select.hide()
        self.hudPiece.hide()
        self.root.hud.setHolodek(False)
        self.root.hud.screenDown()

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
        self.dlna = render.attachNewNode(dl)
        self.dlna.setHpr(-50, -50, 0)
        dl = DirectionalLight("light_directional")
        dl.setColor((0.1,0.1,0.1,1))
        self.dlnb = render.attachNewNode(dl)
        self.dlnb.setHpr(50, 50, 90)
        al = AmbientLight("light_ambient")
        al.setColor((0.05,0.05,0.05,1))
        self.aln = render.attachNewNode(al)
        render.setLight(self.dlna)
        render.setLight(self.dlnb)
        render.setLight(self.aln)

    # load geomnodes from model to clone later
    def loadParts(self): 
        self.structure = loader.loadModel("assets/models/parts.bam")
        self.parts = []
        leftout = "btd", "td"
        self.partnames = (
            "f", "b", "btu", "tu",)
            #"lf", "lb", "lbtu", "ltu",
            #"rf", "rb", "rbtu", "rtu")
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
        # around 20 seems to be a good balance
        chunksize = 16
        if at_row == None: # build entire map
            c = 0
            s = 0
            e = len(self.map)
        else: # build chunk that contains at_row
            c = int(at_row/chunksize)
            s = (c*chunksize)
            e = (s+chunksize)
        chunk = NodePath("map_"+str(c))
        cy = 0
        for y in range(e-s):
            if cy >= chunksize:
                cy = 0
                self.addChunk(c, chunk)
                chunk = NodePath("map_"+str(c))
                c += 1
            if len(self.map) <= y+s:
                row = NR
            else: 
                row = self.map[y+s]
            if not row == NR: 
                self.buildRow(y+s, chunk, row)
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
                        pos = (x, round((y*2)), round((z/2),1))
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

    def moveCol(self, d=None): # Move color cursor
        if d:
            if d == "u": self.current[1]-=16
            if d == "d": self.current[1]+=16
            if d == "l": self.current[1]+=1
            if d == "r": self.current[1]-=1
        else:
            print(self.root.mouse)
            self.current[1] += int(self.root.mouse[0])
            self.current[1] += int(self.root.mouse[1]*16)

        if self.current[1] < 0:
            self.current[1] += 256
        if self.current[1] >= 256:
            self.current[1] -= 256
        self.setHudPiece()
        x = self.current[1]%16
        y = int(self.current[1]/16)
        self.root.hud.setCursor(x, y, 16,16)

    def shape(self, d):
        if d == "n": self.current[0] += 1
        if d == "p": self.current[0] -= 1
        if self.current[0] < 0:
            self.current[0] += len(self.partnames)
        if self.current[0] >= len(self.partnames):
            self.current[0] -= len(self.partnames)
        self.setHudPiece()

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
        self.setHudPiece()

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

    # MAP OPERATIONS
    def playNextMap(self):
        self.currentMap += 1
       # TODO: if last map, play credits map.
       # Repeat from start for now
        if self.currentMap >= len(self.maps):
            self.currentMap = 0
        self.destroyMap()
        self.map = self.maps[self.currentMap]
        self.buildMap()
        self.root.shuffleSong()


    def newMap(self):
        self.currentMap = len(self.maps)
        self.maps.append(self.map)
        self.clearMap()
        self.buildMap()
        self.printHelp()
        self.pos[1] = 0

    def nextMap(self):
        self.currentMap += 1
        if self.currentMap >= len(self.maps):
            self.currentMap = 0
        self.destroyMap()
        self.map = self.maps[self.currentMap]
        self.buildMap()
        self.printHelp()
        self.root.shuffleSong()
        self.pos[1] = 0

    def prevMap(self):
        self.currentMap -= 1
        if self.currentMap < 0:
            self.currentMap = len(self.maps)-1
        self.destroyMap()
        self.map = self.maps[self.currentMap]
        self.buildMap()
        self.printHelp()
        self.root.shuffleSong()
        self.pos[1] = 0

    def destroyMap(self):
        for node in self.mapNodes:
            node.removeNode()

    def clearMap(self): # Clear map
        self.map = []
        self.maps[self.currentMap] = self.map
        for r in EM: self.map.append(r[:])
        self.destroyMap()
        self.buildMap()
        self.pos[1] = 0

    # FILE OPERATIONS
    def saveMap(self): # Save map to bytes-file
        data = Datagram()
        no_part = 64
        next_tile = 65
        next_map = 66
        for map in self.maps:
            if len(map) > 1:
                for y in map:
                    for x in y:
                        for z in x:
                            if z == P:
                                data.addUint8(no_part)
                            else:
                                data.addUint8(z[0])
                                data.addUint8(z[1])
                        data.addUint8(next_tile)
                data.addUint8(next_map)
        with open('saved.map', 'wb') as outfile:
            outfile.write(bytes(data))

    def loadMap(self): # Load map from bytes-file
        file_data = open('saved.map', 'rb').read()
        data = Datagram(file_data)
        iterator = DatagramIterator(data)
        is_color = False
        maps, map, row, tile  = [], [], [], []
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
                    if n == 66:
                        x = y = z = 0
                        maps.append(map)
                        map, row, tile = [],[],[]
                    if x >= 9:
                        x = 0
                        y += 1
                        map.append(row)
                        row = []
        self.maps = maps
        print(len(self.maps), " maps loaded")
        self.currentMap = 0
        self.map = self.maps[0]
        self.buildMap()

    def setHudPiece(self):
        new_part = NodePath("rep")
        self.buildPart(new_part, (0,0,0), self.current)
        lights = (self.dlna, self.dlnb, self.aln)
        self.root.hud.setHolodek(new_part, lights)
