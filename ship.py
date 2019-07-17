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


class Explosion:
    def __init__(self, dad, model):
        self.dad = dad
        self.model = model
        self.model.show()
        self.model.setPos(dad.node.getPos())
        self.scale = 0.5
        self.age = 0
        taskMgr.add(self.update)

    def update(self, task):
        self.scale += 0.2/((self.age/4)+1)
        self.model.setH(self.model.getH()+((2-self.age/100)))
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
    slide = 0
    jumpheight = 0.2
    jump = True
    control = True
    dead = False
    under = None

    def __init__(self, root, model):
        self.root = root
        self.node = NodePath("ship")
        self.model = model
        self.model.reparentTo(self.node)
        self.node.reparentTo(render)
        self.setColliders()

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
        
    def setColliders(self):
        self.handlers = []
        for i in range(3):
            if i == 1: y = 0.2
            else: y = -0.2
            h = colRay(self.node, ((-1+i)/4, y, .1))
            self.handlers.append(h)
        self.colNose = colSpheres(self.node, 
            [((0,.1,.1),.02)])
        self.colLeft = colSpheres(self.node, 
            [((-.15,-.1,.2), .1)])
        self.colRight = colSpheres(self.node, 
            [((.15,-.1,.2), .1)])
        self.colTop = colSpheres(self.node,
            [((0,0.2,0.4), .1)])

    def update(self):
        self.control = True
        self.air -= (1/5000)*self.o2drain
        self.fuel -= (self.speed/1000)*self.fueldrain
        if self.air <= 0.01 or self.fuel <= 0.01:
            self.control = False
        
        if not self.dead:
            self.collide()
            self.specialFloor()
            # Set fw/bw speed
            self.speed = clamp(self.speed, 0, self.max)
            self.audio["engine"].setPlayRate((self.speed*7))
            # Update node position
            x = self.node.getX()+((self.steer+self.slide)*self.steerspeed)
            y = self.node.getY()+self.speed
            z = self.node.getZ()-self.fall
            self.node.setFluidPos(x, y, z)
            # Point nose to fall speed
            self.model.setP(-(self.fall*300))
            # Set flame color to speed
            cc = (self.speed*7)-uniform(0,0.3)
            self.model.getChild(0).setColorScale(cc*2,cc,cc,1)
            # Respawn if fallen off.
            if z < -20:
                self.respawn()
            self.setMeters()

    def specialFloor(self):
        f = self.under
        if f:
            if f == 1:
                self.root.road.playNextMap()
                self.respawn()
            elif f == 2:
                self.explode()
            elif f == 3:
                self.speed += self.acceleration*2
            elif f == 4:
                self.fuel = 0.99
                self.air = 0.99
            elif f == 5:
                self.control = False
            elif f == 6:
                self.speed -= self.acceleration*2
    
    def collide(self):
        if self.colNose.getNumEntries() > 0:
            if self.speed > 0.1: # full frontal crash
                self.explode()
            else: # full frontal bump
                self.audio["shave"].play()
                self.speed = 0
                self.node.setY(self.node.getY()-0.2)
        # bounce left and right
        if self.colLeft.getNumEntries() > 0:
            self.steer = 1
            self.audio["shave"].play()
        elif self.colRight.getNumEntries() > 0:
            self.steer = -1
            self.audio["shave"].play()
        # connect to floor
        self.grounded = False
        self.under = under = None
        self.root.cTrav.traverse(render)
        hits = [0,0,0]
        for h, handler in enumerate(self.handlers):
            if len(list(handler.entries)) > 0:
                handler.sortEntries()
                entry = list(handler.entries)[0]
                hitPos = entry.getSurfacePoint(render)
                distToGround =  self.node.getZ() - hitPos.getZ()
                if distToGround < 0.03:
                    hits[h] = 1
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
                    under = entry.getSurfacePoint(render)
                    self.node.setZ(hitPos.getZ()+0.01)
        s = self.getSteerVal()
        if hits == [1,0,0]:
            self.slide += 0.01
        elif hits == [0,0,1]:
            self.slide -= 0.01
        elif not hits == [0,0,0]:
            self.slide = 0
        # fall if not on floor
        if not self.grounded:
            self.fall += (self.gravity)/550
            if self.colTop.getNumEntries() > 0:
                if self.fall < 0:
                    self.fall = -self.fall
        # else see what color the floor is
        elif under:
            x, y, z = under
            x = round(x)
            y = round(y/2)
            z = round(z*2)-1
            try:
                color = self.root.road.map[y][x][z][1]
                if color <= 8 :
                    self.under = color
            except:
                pass

    def setMeters(self):
        self.root.hud.setSpeed(self.speed*114)
        self.root.hud.setAir(self.air*14)
        self.root.hud.setFuel(self.fuel*14)
        self.root.hud.setMiles(self.node.getY(), len(self.root.road.map))
        self.root.hud.setGravity(self.gravity)

    def explode(self):
        Explosion(self, self.explosion)
        self.audio["engine"].stop()
        self.audio["explode"].play()
        self.node.hide()
        self.dead = True

    def accelerate(self):
        if not self.dead and self.control:
            self.speed += self.acceleration

    def decelerate(self):
        if not self.dead and self.control:
            self.speed -= self.acceleration

    def getSteerVal(self):
        return ((self.speed*4)+0.1)

    def goLeft(self):
        if not self.dead and self.control:
            if self.grounded or self.fall < -0.07:
                if self.colLeft.getNumEntries() == 0:
                    self.steer = -self.getSteerVal()
                    self.slide = 0

    def goRight(self):
        if not self.dead and self.control:
            if self.grounded or self.fall < -0.07:
                if self.colRight.getNumEntries() == 0:
                    self.steer = self.getSteerVal()
                    self.slide = 0.01

    def jumpUp(self):
        if self.gravity < 8:
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
        self.speed = 0
        self.jump = True
        self.control = True
        self.dead = False
        self.air = 1
        self.fuel = 1
        self.gravity = self.root.road.gravity
        self.fueldrain = self.root.road.fueldrain
        self.o2drain = self.root.road.o2drain
        self.setMeters()