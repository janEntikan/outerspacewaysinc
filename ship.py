
from panda3d.core import NodePath
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import CollisionHandlerPusher, CollisionSphere
from panda3d.core import CollideMask


def clamp(i, mini, maxi):
    if i < mini:    i = mini
    elif i > maxi:  i = maxi
    return i

def Ray(parent, origin=(0,0,0.1), direction=(0,0,-1)):
        ray = CollisionRay()
        ray.setOrigin(origin)
        ray.setDirection(direction)
        col = CollisionNode(parent.getName()+"-ray")
        col.addSolid(ray)
        colNode = parent.attachNewNode(col)
        handler = CollisionHandlerQueue()
        base.cTrav.addCollider(colNode, handler)
        colNode.show()
        return handler


class Ship:
    set = 0
    current = 0
    acceleration = 0.002
    max = 0.4
    fall = 0.001
    gravity = 0.2
    steer = 0
    steerspeed = 0.05
    jumpheight = 0.2
    jump = True

    def __init__(self, root, model):
        self.root = root
        self.node = NodePath("ship")
        self.model = model
        self.model.reparentTo(self.node)
        self.node.reparentTo(render)
        self.setCollisions()

    def setCollisions(self):
        self.handlers = []
        for i in range(3):
            if i == 1: y = 0.2
            else: y = -0.2
            h = Ray(self.node, ((-1+i)/4, y, -0.005))
            self.handlers.append(h)

    def update(self):
        # Do collisions
        hit = False
        self.root.cTrav.traverse(render)
        for handler in self.handlers:
            for entry in list(handler.entries):
                hitPos = entry.getSurfacePoint(render)
                distToGround =  self.node.getZ() - hitPos.getZ()
                if distToGround < 0.1:
                    if self.fall > 0.05:
                        self.fall = -0.04
                        self.jump = True
                    elif self.fall > 0: 
                        self.fall = 0
                        self.jump = True
                    hit = True
                    self.node.setZ(hitPos.getZ()+0.08)
        if not hit:
            self.fall += self.gravity/50
        # Point noise to fall speed

        self.model.setP(-(self.fall*300))

        cc = self.current*5

        self.model.getChild(0).setColorScale(cc*2,cc,cc,1)

        # Set fw/bw speed
        self.set = clamp(self.set, 0, self.max)
        if hit:
            if self.current < self.set:
                self.current += self.acceleration
            elif self.current > self.set:
                self.current -= self.acceleration
            if self.current < self.acceleration:
                self.current = 0

        # Update node position
        x = self.node.getX()+(self.steer*self.steerspeed)
        y = self.node.getY()+self.current
        z = self.node.getZ()-self.fall
        self.node.setPos(x, y, z)

        # Respawn if fallen off.
        if z < -20:
            self.respawn()

    def respawn(self):
        self.node.setPos(4,0,0.5)
        self.fall = 0
        self.set = 0
        self.current = 0
        self.jump = True