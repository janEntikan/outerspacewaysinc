from panda3d.core import NodePath
from panda3d.core import DirectionalLight, AmbientLight
from panda3d.core import PNMImage
from panda3d.core import Datagram, DatagramIterator
from purses3d import Purses
from ship import clamp


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
        self.lighten()
        self.sky()
        self.currentMap = 0
        self.current = [0, 0]
        self.pos = [4,2,0]
        self.colors = loader.loadTexture("assets/palette.png")
        self.colors.setMagfilter(0)
        self.colors.setMinfilter(0)
        self.moveCol("l"); self.moveCol("r")
        self.root.hud.setScreen(self.colors)
        self.hudPiece = NodePath("hud")
        self.stat = Purses(50,40)
        self.stat.node.setScale(0.35,1,0.7)
        self.stat.node.setPos(-.65, 0, -1.5)
        try:
            self.loadMap()
        except FileNotFoundError:
            self.map = []
            self.maps = [self.map]
            self.clearMap()
        self.help = Purses(50,40)
        self.help.node.setScale(0.35,1,0.7)
        self.help.node.setPos(-.65, 0, .3)
        self.showHelp = False
        self.help.addstr("press ` for help")
        self.help.refresh()
        self.printStat()

    def printStat(self):
        self.stat.fill()
        self.stat.move(0,0)
        cm = str(self.currentMap)
        le = str(len(self.maps)-1)
        sreds = (
            " ROAD " + cm +"-"+ le,
            "GRAVITY " + str((self.gravity+2)*100),
            "FUEL DRAIN " + str(self.fueldrain),
            "o2 DRAIN " + str(self.o2drain),
        )
        for sred in sreds:
            self.stat.addstr(sred+"\n", ["green", None])
        self.stat.refresh()

    def printHelp(self):
        self.help.fill()
        self.help.move(0,0)
        controls = (
            "EDIT MODE",
            "tab            start game",
            "f and +/-      set fuel drain",
            "g and +/-      set gravity",
            "h and +/-      set o2 drain",            
            "arrows         move cursor on x and y",
            "pgup/pgdown    move cursor on z",
            "space/delete   place/remove piece",
            "numpad 7 and 8 prev/next shape",
            "numpad 2,4,6,8 select color",
            "c              copy piece",
            "n              clear track",
            "/              append new track",
            ", and .        prev/next track",
            "s and l        save/load all tracks",
            " "," ",
            "Based on:",
            "    Skyroads by Bluemoon Software in 1993",
            "Programming, Art and SFX: ",
            "    Hendrik-Jan in 2019",
            "Music:",
            "    composed by Ott Aaloe",
            "    reimagined by Hendrik-Jan",

        )
        for i in controls:
            self.help.addstr(i+"\n", ["grey", None])
        self.help.refresh()

    def toggleHelp(self):
        if self.showHelp:
            self.showHelp = False
            self.help.fill()
            self.help.addstr(0,0,"press ` for help")
            self.help.refresh()
        else:
            self.showHelp = True
            self.printHelp()

    def enableEditing(self):
        self.stat.node.show()
        self.help.node.show()
        self.root.music.setVolume(0.03)
        self.select.show()
        self.setHudPiece()
        self.root.hud.screenUp()

    def disableEditing(self):
        self.stat.node.hide()
        self.help.node.hide()
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
    def getMap(self):
        self.destroyMap()
        self.map = self.maps[self.currentMap]
        self.gravity = self.map[0]
        self.fueldrain = self.map[1]
        self.o2drain = self.map[2]
        self.printStat()
        self.map = self.map[3:] # seperate gravity/drains
        self.buildMap()

    def rememberMap(self):
        base = [self.gravity, self.fueldrain, self.o2drain]
        self.maps[self.currentMap] = base+self.map

    def playNextMap(self):
        self.currentMap += 1
       # TODO: if last map, play credits map.
       # Repeat from start for now
        if self.currentMap >= len(self.maps):
            self.currentMap = 0
        self.getMap()
        self.root.shuffleSong()

    def newMap(self):
        self.rememberMap()
        self.currentMap = len(self.maps)
        self.maps.append([])
        self.clearMap()
        self.pos[1] = 0

    def nextMap(self):
        self.rememberMap()
        self.currentMap += 1
        if self.currentMap >= len(self.maps):
            self.currentMap = 0
        self.getMap()
        self.root.shuffleSong()
        self.pos[1] = 0

    def prevMap(self):
        self.rememberMap()
        self.currentMap -= 1
        if self.currentMap < 0:
            self.currentMap = len(self.maps)-1
        self.getMap()
        self.pos[1] = 0
        self.root.shuffleSong()

    def destroyMap(self):
        for node in self.mapNodes:
            node.removeNode()

    def clearMap(self): # Clear map
        self.gravity = 3
        self.fueldrain = 1
        self.o2drain = 1
        self.map = [3,1,1] # default gravity/drains
        for r in EM: self.map.append(r[:])
        self.maps[self.currentMap] = self.map
        self.pos[1] = 0
        self.getMap()


    # FILE OPERATIONS
    def saveMap(self): # Save map to bytes-file
        self.rememberMap()
        data = Datagram()
        no_part = 64
        next_tile = 65
        next_map = 66
        for m, map in enumerate(self.maps):
            if len(map) >= 1:
                data.addUint8(map[0]) # gravity
                data.addUint8(map[1]) # fuel-drain
                data.addUint8(map[2]) # o2-drain
                map = map[3:]
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
        with open('tracks.trk', 'wb') as outfile:
            outfile.write(bytes(data))

    def loadMap(self): # Load map from bytes-file
        file_data = open('tracks.trk', 'rb').read()
        data = Datagram(file_data)
        iterator = DatagramIterator(data)
        is_color = False
        mm = 0
        maps, map, row, tile  = [], [], [], []
        x, y, z = 0, 0, 0
        for i in range(iterator.getRemainingSize()):
            n = iterator.getUint8()
            if mm <= 2: # gravity and drains
                map.append(n)
                mm += 1
            else:
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
                            mm = 0
                            x = y = z = 0
                            maps.append(map)
                            map, row, tile = [],[],[]
                        if x >= 9:
                            x = 0
                            y += 1
                            map.append(row)
                            row = []
        self.maps = maps
        self.currentMap = 0
        self.getMap()

    def setHudPiece(self):
        new_part = NodePath("rep")
        self.buildPart(new_part, (0,0,0), self.current)
        lights = (self.dlna, self.dlnb, self.aln)
        self.root.hud.setHolodek(new_part, lights)

    def setGravity(self, inc):
        self.gravity += inc
        self.gravity = clam(self.gravity, 1, 10)
        self.printStat()
        self.root.ship.respawn()

    def setFuelDrain(self, inc):
        self.fueldrain += inc
        self.fueldrain = clam(self.fueldrain, 1, 20)
        self.printStat()
        self.root.ship.respawn()

    def setO2Drain(self, inc):
        self.o2drain += inc
        self.o2drain = clam(self.o2drain, 1, 20)
        self.printStat()
        self.root.ship.respawn()