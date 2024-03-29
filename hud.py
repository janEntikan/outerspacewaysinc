from panda3d.core import NodePath, Camera
from panda3d.core import DirectionalLight, PointLight
from panda3d.core import CollisionTraverser
from panda3d.core import SequenceNode, SwitchNode
from purses3d import Purses


class Hud():
    def __init__(self, root):
        self.root = root
        self.cam = Camera("hudcam")
        self.cam.getLens().setFov(90)
        self.cam.getLens().setNear(0.8)
        self.camNode = NodePath(self.cam)
        self.region = base.win.makeDisplayRegion()
        self.region.setCamera(self.camNode)

        self.node = loader.loadModel("assets/models/hud.bam")
        self.node.reparentTo(self.camNode)
        self.node.setZ(-0.6)

        self.screen = self.node.find("**/screen")
        self.screen.setScale((0.8, 0.5, 1))
        self.screen.reparentTo(self.node)
        self.screencard = self.screen.find("**/card")
        self.cursor = self.screen.find("**/cursor")

        self.gauge = {}
        for gauge in ("speed", "air", "fuel"):
            self.gauge[gauge] = self.node.find("**/levels_"+gauge)
            SwitchNode(gauge).replaceNode(self.gauge[gauge].node())
        self.gauge["mileage"] = self.node.find("**/levels_miles")

        self.val = Purses(30,1)
        self.val.move(0,0)
        self.val.addstr(" 500", ["yellow",None])
        self.val.move(21,0)
        self.val.addstr("NULL", ["yellow",None])
        self.val.refresh()
        self.val.node.setScale((0.5, 1, 0.03))
        self.val.node.setPos((0.075, 0, -0.68))

      
        self.screen.setY(1)
        self.screen.setP(60)

        self.holodek = NodePath("holodek")
        self.hololight = self.node.find("**/hololight")

        self.lighten()


    def lighten(self):
        l = DirectionalLight("hudlight")
        l.setColor((2,2,2,1))
        ln = NodePath(l)
        ln.setHpr(100,-60,90)
        self.node.setLight(ln)

    def setGravity(self, gravity):
        a = ["yellow", None]
        self.val.addstr(0,0,"     ",a)
        self.val.addstr(0,0,str((gravity+2)*100), a)
        self.val.refresh()

    def setSpeed(self, speed):
        self.gauge["speed"].node().setVisibleChild(int(speed))

    def setAir(self, air):
        if int(air) < -1:
            air = -1
        self.gauge["air"].node().setVisibleChild(int(air)+1)

    def setFuel(self, fuel):
        if int(fuel) < -1:
            fuel = 0
        self.gauge["fuel"].node().setVisibleChild(int(fuel)+1)

    def setMiles(self, miles, maplength):
        miles = 1/(miles+0.001)
        l = 1/(maplength*2)
        w = l/miles
        if w > 1:
            w = 1
        self.gauge["mileage"].setScale(w,1,1)

    def screenUp(self):
        self.val.node.hide()
        self.screen.setZ(-1)
        taskMgr.add(
            self.moveScreen, 
            extraArgs=["u"], 
            appendTask=True)

    def screenDown(self):
        self.screen.setZ(0)
        taskMgr.add(
            self.moveScreen, 
            extraArgs=["d"],
            appendTask=True)

    def setScreen(self, texture):
        self.screencard.setTexture(texture)

    def moveScreen(self, d, task):
        speed = 0.03
        z = self.screen.getZ()
        if d == "u":
            self.val.node.hide()
            if z < 0:
                self.screen.setZ(z+speed)
                return task.cont
        else:
            if z > -1:
                self.screen.setZ(z-speed)
                return task.cont
            self.val.node.show()
        return task.done

    def setCursor(self, x, y, w, h):
        w = 1/w
        h = 1/h
        x = (-0.5+(w/2)+(w*x))
        y = (0.5-(h/2)-(h*y))
        self.cursor.setScale((w, h, 1))
        self.cursor.setPos((x,y,0.001))

    def setHolodek(self, model, lights=[]):
        self.holodek.removeNode()
        self.hololight.hide()
        self.holodek = NodePath("holodek")
        if model:
            model.setScale(0.15)
            model.setHpr((-20, -10, 10))
            model.setPos(0.8, 1, 0.1)
            model.reparentTo(self.holodek)
            for light in lights:
                model.setLight(light)
            self.hololight.show()

            taskMgr.add(self.holospin, "holospin", 
                extraArgs=[model],
                appendTask=True)

        self.holodek.reparentTo(self.node)

    def holospin(self, node, task):
        node.setH(node.getH()+1)
        return task.cont

