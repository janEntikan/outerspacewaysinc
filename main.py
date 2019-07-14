import sys
import panda3d
import pman.shim
from direct.showbase.ShowBase import ShowBase
from panda3d.core import ColorAttrib
from panda3d.core import NodePath, Camera
from panda3d.core import BitMask32
from panda3d.core import DirectionalLight, AmbientLight
from panda3d.core import CollisionTraverser
from ship import Ship


panda3d.core.loadPrcFile(
    panda3d.core.Filename.expand_from('$MAIN_DIR/settings.prc')
)

P = None			# None part
N = [P]				# None tile
D = [(0,(0.6,0.3,0.6,1))]	# Default tile (grey floor)
H = [P, (1,(0.6,1,0.6,1))]
T = D+[(5,(0.6,0,0,1))]
NR = [N,N,N,N,N,N,N,N,N] 	# Empty row/space
EM = [				# Clean start map
    [D, D, D, D, D, N, D, D, N],
    [N, N, N, N, D, N, N, N, N],
    [N, N, N, N, T, N, N, N, N],
    [N, N, N, D, T, D, N, N, N],
    [N, N, N, N, D, N, N, N, N],
    [N, N, N, D, N, D, N, N, N],
    [N, N, N, N, D, N, N, N, N],
]
for i in range(100):
    EM.append([N, N, N, D, D, D, N, N, N])
    EM.append([N, H, N, D, D, D, N, H, N])
    EM.append([N, N, D, T, D, T, D, N, N])


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        pman.shim.init(self)
        # self.win.setClearColor((0,0,0,1))
        self.cTrav = CollisionTraverser()
        self.mode = "game"
        self.defineKeys()
        self.loadParts()
        self.newMap()
        self.buildMap()
        self.lighten()
        self.sky()
        #self.hud()
        self.spawn()
        render.analyze()
        self.taskMgr.add(self.update)

    def update(self, task):
        if self.mode == "game":
            ship = self.ship
            if self.keys["quit"]:
                sys.exit()
            if self.keys["up"]:
                ship.set += ship.acceleration
            elif self.keys["down"]:
                ship.set -= ship.acceleration
            if self.keys["left"]:
                ship.steer = -1
            elif self.keys["right"]:
                ship.steer = 1
            else:
                ship.steer = 0
            if self.keys["jump"] == 2:
                if ship.jump and ship.fall < 0.05:
                    ship.fall = -0.1
                    ship.jump = False
        self.skysphere.setH(self.skysphere.getH()+0.1)


        self.ship.update()
        camY = -6+self.ship.node.getY()+(self.ship.current*5)
        base.cam.setPos(4, camY, 2)
 
        base.camLens.setFov(60+(self.ship.current*150))
        self.updateKeys()
        return task.cont

    def defineKeys(self):
        self.keys = {}
        keys = (
            # Key	 	 Name
            ("arrow_left", 	"left"),
            ("arrow_right", 	"right"),
            ("arrow_up", 	"up"),
            ("arrow_down",	"down"),
            ("space", 		"jump"),
            ("escape", 		"quit"),
        )
        for key in keys:
            # 2 =  first down, 1 = hold down, 0 = let go
            self.accept(key[0], self.setKey, [key[1], 2])
            self.accept(key[0]+"-up", self.setKey, [key[1], 0])
            self.keys[key[1]] = 0
        self.accept('shift-q', sys.exit) # Force exit

    def setKey(self, key, pos):
        self.keys[key] = pos

    def updateKeys(self):
        for key in self.keys:
            if self.keys[key] == 2:
                self.keys[key] = 1

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


    def newMap(self):
        self.map = []
        for r in EM: self.map.append(r[:])

    def buildMap(self):
        self.mapNode = NodePath("map")
        for y, row in enumerate(self.map):
            if not row == NR:
                for x, col in enumerate(row):
                    if not col == N:
                        for z, part in enumerate(col):
                            if not part == None:
                                newPart = self.parts[part[0]]
                                newPart.setColor(part[1])
                                newPart.setPos(x, (y*2), (z/2))
                                newPart.copyTo(self.mapNode)                           
        self.mapNode.flattenStrong()
        self.mapNode.reparentTo(render)
        #self.mapNode.analyze()

    def sky(self):
        s = loader.loadModel("assets/models/sky.bam")
        s.reparentTo(base.cam)
        s.setBin('background', 0)
        s.setDepthWrite(False)
        s.setCompass()
        s.setLightOff()
        self.skysphere = s

    def hud(self):
        s = loader.loadModel("assets/models/hud.bam")
        s.reparentTo(base.cam)
        s.setPos(0,0.1,0)


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

    def spawn(self):
        self.camLens.setFar(200)
        base.camLens.setNear(0.1)
        base.camLens.setFov(120)
        base.cam.setPos(0,0,1.5)
        model = loader.loadModel("assets/models/vehicle.bam")
        self.ship = Ship(self, model)
        self.ship.node.reparentTo(render)
        self.ship.node.setPos(4,0,1)

def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()
