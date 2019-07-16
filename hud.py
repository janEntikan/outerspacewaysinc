from panda3d.core import NodePath, Camera
from panda3d.core import DirectionalLight, PointLight
from panda3d.core import CollisionTraverser


def moveScreen(screen, d, task):
    speed = 0.03
    z = screen.getZ()
    if d == "u":
        if z < 0:
            screen.setZ(z+speed)
            return task.cont
    else:
        if z > -1:
            screen.setZ(z-speed)
            return task.cont
    return task.done

class Hud():
    def __init__(self):
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

        self.screen.setY(1)
        self.screen.setP(60)

        self.holodek = NodePath("holodek")
        self.lighten()

    def lighten(self):
        l = DirectionalLight("hudlight")
        l.setColor((2,2,2,1))
        ln = NodePath(l)
        ln.setHpr(100,-60,90)
        self.node.setLight(ln)

    def screenUp(self):
        self.screen.setZ(-1)
        taskMgr.add(
            moveScreen, extraArgs=[self.screen, "u"], 
            appendTask=True)

    def screenDown(self):
        self.screen.setZ(0)
        taskMgr.add(
            moveScreen, 
            extraArgs=[self.screen, "d"],
            appendTask=True)

    def setScreen(self, texture):
        self.screencard.setTexture(texture)

    def setCursor(self, x, y, w, h):
        w = 1/w
        h = 1/h
        x = (-0.5+(w/2)+(w*x))
        y = (0.5-(h/2)-(h*y))
        self.cursor.setScale((w, h, 1))
        self.cursor.setPos((x,y,0.001))

    def setHolodek(self, model, lights=[]):
        self.holodek.removeNode()
        self.holodek = NodePath("holodek")
        if model:
            model.setScale(0.15)
            model.setHpr((-20, -10, 10))
            model.setPos(0.8, 1, 0.1)
            model.reparentTo(self.holodek)
            for light in lights:
                model.setLight(light)
        self.holodek.reparentTo(self.node)


