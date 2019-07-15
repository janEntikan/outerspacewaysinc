import sys
import pman.shim
from direct.showbase.ShowBase import ShowBase

from panda3d.core import loadPrcFile, Filename
from panda3d.core import NodePath, Camera, DirectionalLight
from panda3d.core import CollisionTraverser

from road import RoadMan
from ship import Ship


loadPrcFile(
    Filename.expand_from('$MAIN_DIR/settings.prc')
)


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        pman.shim.init(self)
        self.setFrameRateMeter(True)
        self.win.setClearColor((0,0,0,1))
        self.cTrav = CollisionTraverser()
        self.cTrav.setRespectPrevTransform(True)
        self.delay = [0,5]
        self.mode = "edit"
        base.win.display_regions[1].dimensions = (0, 1, 0.25, 1)
        self.defineKeys()
        self.road = RoadMan()
        self.hud()
        self.spawn()
        self.taskMgr.add(self.update)
        render.setShaderAuto()

    def defineKeys(self):
        self.keys = {}
        keys = (
            # Key	 	 Name
            ("arrow_left", 	"left"),
            ("arrow_right", 	"right"),
            ("arrow_up", 	"forward"),
            ("arrow_down",	"backward"),
            ("page_up",		"up"),
            ("page_down",	"down"),
            ("space", 		"jump"),
            ("delete",	 	"del"),
            ("e",		"mode"),
            ("s",		"save"),
            ("l",		"load"),
            ("n",		"new"),
            ("c",		"color"),
            (".",		"n_shape"),
            (",",		"p_shape"),
            ("6",		"c_left"),
            ("4",		"c_right"),
            ("8",  		"c_up"),
            ("2",		"c_down"),
            ("c",		"copy"),
            ("a",		"analyze"),
            ("escape", 		"quit"),
        )
        for key in keys:
            # 2 =  first down, 1 = hold down, 0 = not down
            self.accept(key[0], self.setKey, [key[1], 2])
            self.accept(key[0]+"-up", self.setKey, [key[1], 0])
            self.keys[key[1]] = 0
        self.accept('shift-q', sys.exit) # Force exit

    def update(self, task):
        self.road.skysphere.setH(self.road.skysphere.getH()+0.1)
        if self.keys["quit"]:    sys.exit()
        if self.keys["analyze"] == 2:
            render.analyze()
            render.ls()
        if self.mode == "game":
            ship = self.ship
            if self.keys["forward"]:   ship.accelerate()
            elif self.keys["backward"]:ship.decelerate()
            if self.keys["left"]:      ship.goLeft()
            elif self.keys["right"]:   ship.goRight()
            else:                      ship.steer = 0
            if self.keys["jump"]:      ship.jumpUp()
            self.ship.update()
            camY = -6+self.ship.node.getY()+(self.ship.current*5)
            base.camLens.setFov(60+(self.ship.current*150))
            if self.keys["mode"] == 2:
                self.mode = "edit"
                self.road.select.show()
        elif self.mode == "edit":
            self.delay[0] += 1
            t = False
            if self.delay[0] > self.delay[1]:
                road = self.road
                if self.keys["forward"]:  road.move("f");t=True
                if self.keys["backward"]: road.move("b");t=True
                if self.keys["left"]: 	  road.move("l");t=True
                if self.keys["right"]:    road.move("r");t=True
                if self.keys["up"]:	  road.move("u");t=True
                if self.keys["down"]:	  road.move("d");t=True
                if self.keys["copy"]:	  road.clone()  ;t=True
                if self.keys["jump"]:	  road.place();  t=True
                if self.keys["del"]:	  road.remove(); t=True
                if self.keys["save"] == 2:
                    road.saveMap()
                if self.keys["load"] == 2:
                    road.loadMap()
                if self.keys["new"] == 2:
                    road.newMap()
                if self.keys["n_shape"]:  road.shape("n")
                if self.keys["p_shape"]:  road.shape("p")
                if self.keys["c_up"]: 	  road.moveCol("u")
                if self.keys["c_down"]:   road.moveCol("d")
                if self.keys["c_left"]:   road.moveCol("l")
                if self.keys["c_right"]:  road.moveCol("r")
                if self.keys["mode"] == 2:
                    self.mode = "game"
                    self.ship.respawn()
                    self.road.select.hide()
            if t:
                self.delay[0] = 0
            camY = -6+self.road.select.getY()
            base.camLens.setFov(90)
        base.cam.setPos(4.001, camY, 2)
        self.updateKeys()
        return task.cont

    def setKey(self, key, pos):
        self.keys[key] = pos

    def updateKeys(self):
        for key in self.keys:
            if self.keys[key] == 2:
                self.keys[key] = 1

    def spawn(self):
        self.camLens.setFar(100)
        base.camLens.setNear(0.1)
        base.camLens.setFov(120)
        base.cam.setPos(0.01,0,1.5)
        model = loader.loadModel("assets/models/vehicle.bam")
        self.ship = Ship(self, model)
        self.ship.node.reparentTo(render)
        self.ship.node.setPos(4,0,1)

    def hud(self):
        hudCam = Camera("hudcam")
        hudCam.getLens().setFov(90)
        hudCamNode = NodePath(hudCam)
        hudRegion = base.win.makeDisplayRegion()
        hudRegion.setCamera(hudCamNode)
        self.hud = loader.loadModel("assets/models/hud.bam")
        self.hud.reparentTo(hudCamNode)

        self.hud.setZ(-0.6)

        l = DirectionalLight("hudlight")
        l.setColor((2,2,2,1))
        ln = NodePath(l)
        ln.setHpr(100,-60,90)
        self.hud.setLight(ln)

def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()
