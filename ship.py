from panda3d.core import NodePath
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import CollisionHandlerPusher, CollisionSphere
from panda3d.core import CollideMask


def clamp(i, mini, maxi):
    if i < mini:    i = mini
    elif i > maxi:  i = maxi
    return i

def colSpheres(parent, spheres=[((0,0,0),1)]):
    col = CollisionNode(parent.getName()+"-colSpheres")
    for sphere in spheres:
        col.addSolid(CollisionSphere(*sphere))
    col.setIntoCollideMask(CollideMask.allOff())
    colNode = parent.attachNewNode(col)
    handler = CollisionHandlerQueue()
    base.cTrav.addCollider(colNode, handler)
    #colNode.show()
    return handler

def colRay(parent, origin=(0,0,0.1), direction=(0,0,-1)):
    ray = CollisionRay()
    ray.setOrigin(origin)
    ray.setDirection(direction)
    col = CollisionNode(parent.getName()+"-ray")
    col.addSolid(ray)
    col.setIntoCollideMask(CollideMask.allOff())
    colNode = parent.attachNewNode(col)
    handler = CollisionHandlerQueue()
    base.cTrav.addCollider(colNode, handler)
    #colNode.show()
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
            h = colRay(self.node, ((-1+i)/4, y, -0.005))
            self.handlers.append(h)
        self.colNose = colSpheres(self.node, 
            [((0,.2,.05),.05)])
        self.colLeft = colSpheres(self.node, 
            [((-.15,-.1,.1), .1)])
        self.colRight = colSpheres(self.node, 
            [((.15,-.1,.1), .1)])
        self.colTop = colSpheres(self.node,
            [((0,0.2,0.3), .1)])

    def update(self):
        oldfall = self.fall
        if self.colNose.getNumEntries() > 0:
            if self.current > 0.12:
                self.respawn() # crash
            else:
                self.set = 0
                self.current = 0
        if self.colLeft.getNumEntries() > 0:
            self.steer = 1
        elif self.colRight.getNumEntries() > 0:
            self.steer = -1

        hit = False
        self.root.cTrav.traverse(render)
        for handler in self.handlers:
            if len(list(handler.entries)) > 0:
                handler.sortEntries()
                entry = list(handler.entries)[0]
                hitPos = entry.getSurfacePoint(render)
                distToGround =  self.node.getZ() - hitPos.getZ()
                if distToGround < self.fall+0.1:
                    if self.fall > 0.05: #go bounce
                        self.fall = -0.04
                        self.jump = True
                    elif self.fall > 0: #land
                        self.fall = 0
                        self.jump = True
                    if self.colTop.getNumEntries() >  0:
                        self.fall = 0
                    hit = True
                    self.node.setZ(hitPos.getZ()+0.08)
        if not hit:
            self.fall += self.gravity/50
            if self.colTop.getNumEntries() > 0:
                self.fall += 0.1
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
        # Point nose to fall speed
        self.model.setP(-(self.fall*300))
        # Set flame color to speed
        cc = self.current*5
        self.model.getChild(0).setColorScale(cc*2,cc,cc,1)
        # Respawn if fallen off.
        if z < -20:
            self.respawn()

    def accelerate(self):
        self.set += self.acceleration

    def decelerate(self):
        self.set -= self.acceleration

    def goLeft(self):
        if self.colLeft.getNumEntries() == 0:        
            self.steer = -1

    def goRight(self):
        if self.colRight.getNumEntries() == 0:
            self.steer = 1

    def jumpUp(self):
        if self.colTop.getNumEntries() == 0:
            if self.jump and self.fall < 0.05:
                self.fall = -0.1
                self.jump = False

    def respawn(self):
        self.node.setPos(4,0,0.7)
        self.fall = 0
        self.set = 0
        self.current = 0
        self.jump = True