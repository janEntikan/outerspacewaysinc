import sys
import pman.shim
from random import choice
from direct.showbase.ShowBase import ShowBase

from panda3d.core import loadPrcFile, Filename
from panda3d.core import WindowProperties
from panda3d.core import NodePath, Camera, DirectionalLight
from panda3d.core import CollisionTraverser

from road import RoadMan
from ship import Ship
from hud import Hud


loadPrcFile(
    Filename.expand_from('$MAIN_DIR/settings.prc')
)


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        pman.shim.init(self)
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        base.win.requestProperties(props)
        base.disableMouse()
        self.mouse = [0,0]
        self.setFrameRateMeter(True)
        self.win.setClearColor((0,0,0,1))
        self.cTrav = CollisionTraverser()
        self.cTrav.setRespectPrevTransform(True)
        self.delay = [0,5]
        base.win.display_regions[1].dimensions = (0, 1, 0.25, 1)
        render.setShaderAuto()
        self.music = None
        self.shuffleSong()

        self.mode = "edit"
        self.defineKeys()
        self.hud = Hud(self)
        self.road = RoadMan(self)
        self.road.enableEditing()
        self.spawn()
        self.taskMgr.add(self.update)

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
            ("tab",		"mode"),
            ("delete",	 	"delete"),
            ("s",		"save"),
            ("l",		"load"),
            ("n",		"clear_map"),
            ("/",		"create_map"),
            (".",		"next_map"),
            (",",		"prev_map"),
            ("c",		"color"),
            ("9",		"n_shape"),
            ("7",		"p_shape"),
            ("6",		"c_left"),
            ("4",		"c_right"),
            ("8",		"c_up"),
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
            camY = -6+self.ship.node.getY()+(self.ship.speed*5)
            base.camLens.setFov(60+(self.ship.speed*150))
            if self.keys["mode"] == 2:
                self.mode = "edit"
                self.ship.audio["engine"].stop()
                self.road.enableEditing()
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
                if self.keys["delete"]:	  road.remove(); t=True
                if self.keys["save"] == 2:
                    road.saveMap()
                if self.keys["load"] == 2:
                    road.loadMap()
                if self.keys["clear_map"] == 2:
                    road.clearMap()
                if self.keys["next_map"] == 2:
                    road.nextMap()
                if self.keys["prev_map"] == 2:
                    road.prevMap()
                if self.keys["create_map"] == 2:
                    road.newMap()
                if self.keys["n_shape"] == 2:
                    road.shape("n")
                if self.keys["p_shape"] == 2: 
                    road.shape("p")
                if self.keys["c_up"]:
                    road.moveCol("u"); t=True
                if self.keys["c_down"]:
                    road.moveCol("d"); t=True
                if self.keys["c_left"]:
                    road.moveCol("l"); t=True
                if self.keys["c_right"]:
                    road.moveCol("r"); t=True
                if self.keys["mode"] == 2:
                    self.mode = "game"
                    self.road.disableEditing()
                    self.ship.respawn()
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

    def shuffleSong(self):
        if self.music:
            vol = self.music.getVolume()
            self.music.stop()
        else:
            vol = 0.03
        songs = (
            "assets/audio/ogg/road1.ogg",
            "assets/audio/ogg/road8.ogg",
            "assets/audio/ogg/road3.ogg"
        )
        self.music = loader.loadSfx(choice(songs))
        self.music.setVolume(vol)
        self.music.setLoop(True)
        self.music.play()


def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()
