from panda3d.core import NodePath
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import CollisionHandlerPusher, CollisionSphere
from panda3d.core import CollideMask
from random import uniform

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


class Explode:
    def __init__(self, dad, model):
        self.dad = dad
        self.model = model
        self.model.show()
        self.model.setPos(dad.node.getPos())
        self.scale = 0.5
        self.age = 0
        taskMgr.add(self.update)

    def update(self, task):
        self.scale += 0.2/((self.age/2)+1)
        self.model.setH(self.model.getH()+1)
        self.model.setScale(self.scale, self.scale, self.scale/1.2)
        self.age += 1
        self.dad.current /= 2
        if self.age > 40:
            self.model.hide()
            self.dad.respawn()
            return task.done
        return task.cont

class Ship: 
    set = 0
    fuel = 1
    air = 1
    current = 0
    acceleration = 0.002
    max = 0.25
    fall = 0.001
    gravity = 0.3
    steer = 0
    steerspeed = 0.05
    jumpheight = 0.2
    jump = True
    control = True
    dead = False

    def __init__(self, root, model):
        self.root = root
        self.node = NodePath("ship")
        self.model = model
        self.model.reparentTo(self.node)
        self.node.reparentTo(render)
        self.setCollisions()

        self.explosion = loader.loadModel("assets/models/explosion.bam")
        self.explosion.reparentTo(render)
        self.explosion.hide()
        self.explosion.setLightOff()

        self.loadAudio()

    def loadAudio(self): # each ship has their own set of sounds
        folder = "assets/audio/sfx/"
        self.audio = {
            "bounce":loader.loadSfx(folder+"bounce.wav"),
            "engine":loader.loadSfx(folder+"engine.wav"),
            "explode":loader.loadSfx(folder+"explode.wav"),
            "land":loader.loadSfx(folder+"land.wav"),
            "pickup":loader.loadSfx(folder+"pickup.wav"),
            "shave":loader.loadSfx(folder+"shave.wav"),
        }
        
    def setCollisions(self):
        self.handlers = []
        for i in range(3):
            if i == 1: y = 0.2
            else: y = -0.2
            h = colRay(self.node, ((-1+i)/4, y, 0))
            self.handlers.append(h)
        self.colNose = colSpheres(self.node, 
            [((0,.1,.07),.02)])
        self.colLeft = colSpheres(self.node, 
            [((-.15,-.1,.1), .1)])
        self.colRight = colSpheres(self.node, 
            [((.15,-.1,.1), .1)])
        self.colTop = colSpheres(self.node,
            [((0,0.2,0.4), .1)])

    def update(self):
        self.air -= 0.0001
        self.fuel -= self.current/1000
        if self.air <= 0 or self.fuel <= 0:
            self.control = False

        if not self.dead:
            oldfall = self.fall
            if self.colNose.getNumEntries() > 0:
                if self.current > 0.1:
                    Explode(self, self.explosion)
                    self.audio["engine"].stop()
                    self.audio["explode"].play()
                    self.node.hide()
                    self.dead = True
                    self.current = -0.4
                    self.set = 0
                else:
                    self.audio["shave"].play()
                    self.set = 0
                    self.current = -0.4
            if self.colLeft.getNumEntries() > 0:
                self.steer = 1
                self.audio["shave"].play()
            elif self.colRight.getNumEntries() > 0:
                self.steer = -1
                self.audio["shave"].play()

            self.grounded = False
            self.root.cTrav.traverse(render)
            for handler in self.handlers:
                if len(list(handler.entries)) > 0:
                    handler.sortEntries()
                    entry = list(handler.entries)[0]
                    hitPos = entry.getSurfacePoint(render)
                    distToGround =  self.node.getZ() - hitPos.getZ()
                    if distToGround < self.fall+0.05:
                        if self.fall > 0.05: #go bounce
                            self.fall = -0.05
                            self.jump = True
                            self.audio["bounce"].play()
                        elif self.fall > 0: #land
                            self.fall = 0
                            self.jump = True
                            self.audio["land"].play()
                        if self.colTop.getNumEntries() >  0:
                            self.fall = 0
                        self.grounded = True
                        self.node.setZ(hitPos.getZ()+0.01)
            if not self.grounded:
                self.fall += self.gravity/50
                if self.colTop.getNumEntries() > 0:
                    if self.fall < 0:
                        self.fall = -self.fall
            # Set fw/bw speed
            self.set = clamp(self.set, 0, self.max)
            if self.current < self.set:
                self.current += self.acceleration
            elif self.current > self.set:
                self.current -= self.acceleration
            if self.current < self.acceleration:
                self.current = 0

            self.audio["engine"].setPlayRate((self.current*7))
            # Update node position
            x = self.node.getX()+(self.steer*self.steerspeed)
            y = self.node.getY()+self.current
            z = self.node.getZ()-self.fall
            self.node.setFluidPos(x, y, z)
            # Point nose to fall speed
            self.model.setP(-(self.fall*300))
            # Set flame color to speed
            cc = (self.current*7)-uniform(0,0.3)
            self.model.getChild(0).setColorScale(cc*2,cc,cc,1)
            # Respawn if fallen off.
            if z < -20:
                self.respawn()
            self.setMeters()

    def setMeters(self):
        self.root.hud.setSpeed(self.current*114)
        self.root.hud.setAir(self.air*14)
        self.root.hud.setFuel(self.fuel*14)
        self.root.hud.setMiles(self.node.getY(), len(self.root.road.map))

    def accelerate(self):
        if not self.dead and self.control:
            self.set += self.acceleration

    def decelerate(self):
        if not self.dead and self.control:
            self.set -= self.acceleration

    def goLeft(self):
        if not self.dead and self.control:
            if self.grounded or self.fall < -0.07:
                if self.colLeft.getNumEntries() == 0:        
                    self.steer = -((self.current*4)+0.1)

    def goRight(self):
        if not self.dead and self.control:
            if self.grounded or self.fall < -0.07:
                if self.colRight.getNumEntries() == 0:
                    self.steer = ((self.current*4)+0.1)

    def jumpUp(self):
        if not self.dead and self.control:
            if self.colTop.getNumEntries() == 0:
                if self.jump and self.fall < 0.05:
                    self.fall = -0.1
                    self.jump = False

    def respawn(self):
        self.audio["engine"].setLoop(True)
        self.audio["engine"].setVolume(1)
        self.audio["engine"].play()
        self.node.show()
        self.node.setPos(4,0,0.7)
        self.fall = 0
        self.set = 0
        self.current = 0
        self.jump = True
        self.control = True
        self.dead = False
        self.air = 1
        self.fuel = 1
        self.setMeters()