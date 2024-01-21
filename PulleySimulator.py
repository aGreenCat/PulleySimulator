from vpython import *
#Web VPython 3.2
# OVERVIEW
# --------------------------------
# 3      overview
# 18     constants
# 22     global variables
# 27     scenes setup
# 31     pulley class
# 71     mass class
# 101    string class
# 169    configuration class
# 289    configuration runs
# 454    simulation buttons
# 500    configuration buttons
# 509    init

#CONSTANTS
ACCEL_G = 9.81  #acceleration due to gravity
DT = 0.02       #time elapsed per frame

# GLOBAL VARIABLES
sim_status = None     #simulation status
exit_boolean = False  #collision status
config_run = 0        #initial configuration

# SCENES SETUP
scenes = []
scenes.append(scene)

# PULLEY CLASS
class pulley:
    def __init__(self, pos=None, radius=None, color=None):
        self.type = 'pulley'
        
        self.pos = pos
        self.radius = radius
        self.mass = radius*radius*pi*4 #mass is proportional to volume
        self.accel = 0
        self.vel = 0
        self.disp = 0
        self.ang_accel = 0
        self.ang_vel = 0
        self.ang_disp = 0
        
        self.curves = [None, None, None, None, None, None]
        self.color = color

        self.body = cylinder(pos=self.pos, axis=vector(0,0,-0.5), radius=self.radius, color=self.color, texture=textures.rock)
        self.axel = cylinder(pos=self.pos+vec(0, 0, 0.4), axis=vector(0,0,-1.3), radius=0.1, color=vector(0.8, 0.8, 0.8))
        
    def update(self):
        #apply angular motion
        dQ = self.ang_vel*DT + 0.5*self.ang_accel*DT*DT
        self.body.rotate(angle=dQ)
        
        #update angular variables
        self.ang_disp += dQ
        self.ang_vel += self.ang_accel*DT
        
        #apply translational motion
        dX = self.vel*DT + 0.5*self.accel*DT*DT
        self.body.pos += vec(0, dX, 0)
        self.axel.pos += vec(0, dX, 0)
        
        #update translational variables
        self.pos += vec(0, dX, 0)
        self.disp += dX
        self.vel += self.accel*DT
        
# MASS CLASS
class mass:
    def __init__(self, pos=None, mass=None, color=None):
        self.type = 'mass'
        self.mass = mass
        self.width = pow(mass, 1/3)/2 #volume is proportional to mass
        
        self.pos = pos
        self.disp = 0
        self.vel = 0
        self.accel = 0
        
        self.sl = None
        self.slc = None
        
        self.curves = [None, None, None, None, None, None]
        self.color = color
        
        self.body = box(pos=self.pos+vec(0, -self.width/2, 0), size=vec(self.width, self.width, self.width), color=self.color)

    def update(self):
        #apply translational motion
        ds = self.vel*DT + 0.5*self.accel*DT*DT
        self.body.pos += vec(0, ds, 0)
        
        #update translational variables
        self.pos += vec(0, ds, 0)
        self.disp += ds
        self.vel += self.accel*DT

# STRING CLASS
class string:
    def __init__(self):
        self.components = []
        self.refs = []
        self.arms = {}
        
        self.body = curve(pos=[vec(0,0,0)],radius=0.05, emmisive=True)
        
    def addPoint(self, p=None):
        self.body.append(p)
            
    def connect_component(self, startang=None, endang=None, pulley=None, head=None, tail=None):
        if head != None:
            #attach string beginning to object
            self.body.modify(0, head.pos)
            self.components.append(head)
            self.refs.append(0)
        elif tail != None:
            #attach string end to object
            self.addPoint(p=tail.pos)
            self.components.append(tail)
            self.refs.append(self.body.npoints-1)
        else:
            #wrap string around pulley
            self.components.append(pulley)
            self.arms[pulley] = []
            temp = self.body.npoints
            
            #ensure direction
            step = pi/30
            if startang > endang:
                step = -step
            
            #make correct curve
            for theta in arange(startang, endang, step):
                arm = vec(pulley.radius*cos(theta), pulley.radius*sin(theta), 0)
                self.arms[pulley].append(arm)
                self.addPoint(p=arm+pulley.pos)
            
            #final point
            arm = vec(pulley.radius*cos(endang), pulley.radius*sin(endang), 0)
            self.arms[pulley].append(arm)
            self.addPoint(p=arm+pulley.pos)
            
            #add reference
            self.refs.append((temp, self.body.npoints))
            
    def update(self):
        #goes through linked components and sets new positions
        for i in range(len(self.components)):
            comp = self.components[i]
            ref = self.refs[i]
            
            if comp.type == 'mass':
                #follows mass position
                self.body.modify(ref, comp.pos)
            elif comp.type == 'pulley':
                #two types of pulley connections
                if type(ref) == type([]):
                    #curvature follows pulley pos
                    offset = ref[0]
                    for j in range(ref[0], ref[1]):
                        self.body.modify(j, self.arms[comp][j-offset]+comp.pos)
                else:
                    #end of string follows pulley pos
                    self.body.modify(ref, comp.pos)

# CONFIGURATION CLASS
class config:
    def __init__(self):
        self.masses = []
        self.pulleys = []
        self.strings = []
        self.graphs = []
        self.time = 0
        
        self.condition_func = None
        self.var_func = None
        
        self.types = ['disp', 'vel', 'accel', 'ang_disp', 'ang_vel', 'ang_accel'] #graph type shorthands
            
        scenes[len(scenes)-1].autoscale = True #autoscale makes it look weird
        
    def addMass(self, pos=None, m=None, slider=None, slider_caption=None, color=None):
        #make mass
        self.masses.append(mass(pos=pos, mass=m, color=vec(204/256, 12/256, 86/256) if color == None else color))
        last = len(self.masses)-1
        
        #make slider and slider caption if needed
        if slider != None:
            slider.id = last
            slider.value = m
            self.masses[last].sl = slider
            slider_caption.text = '<b>mass</b> = '+ m +'\n\n'
            self.masses[last].slc = slider_caption
            
    def addPulley(self, pos=None, radius=None, color=None):
        #make pulley
        self.pulleys.append(pulley(pos=pos, radius=radius, color=vector(49/256, 138/256, 105/256) if color == None else color))
  
    def addGraph(self, type, *components):
        #graph shorthand dictionary
        titles = {
            'disp': 'Displacement',
            'vel': 'Velocity',
            'accel': 'Acceleration',
            'ang_disp': 'Angular Displacement',
            'ang_vel': 'Angular Velocity',
            'ang_accel': 'Angular Acceleration',
        }
        
        #make graph
        self.graphs.append(graph(align='right', title=titles[type]+' vs Time'))
        
        #make curves for listed components
        for comp in components:
            comp.curves[self.types.index(type)] = gcurve(graph=self.graphs[len(self.graphs)-1], color=comp.color)

    def attachString(self, func=None):
        #python workarounds...
        func(self)

    def attachVariables(self, func=None):
        #python workarounds...
        self.var_func = func
        
    def attachCondition(self, func=None):
        #python workarounds...
        self.condition_func = func
        
    def run_config(self):
        #begin simulation
        global sim_status
        sim_status = 'init'
        scenes[len(scenes)-1].autoscale = False
        
        self.time = 0
        
        while True:
            rate(1/DT)
            
            #update variables and components affected by sliders
            self.var_func(self)
        
            #main run loop
            if sim_status == 'run' and not exit_boolean:
                #update and plot pulleys
                for p in self.pulleys:
                    p.update()
                    
                    for i in range(6):
                        if p.curves[i] != None:
                            p.curves[i].plot(self.time, p[self.types[i]])
                
                #update and plot masses, and disable sliders
                for m in self.masses:
                    m.update()
                    m.sl.disabled = True
                    
                    for i in range(6):
                        if m.curves[i] != None:
                            m.curves[i].plot(self.time, m[self.types[i]])
                
                #update strings
                for s in self.strings:
                    s.update()
                
                #check constraints
                exit_boolean = self.condition_func(self)
                    
                if exit_boolean:
                    global sim_status
                    sim_status = 'stop'
            
            #delete graphs and sliders when reset
            if sim_status == 'reset':
                for g in self.graphs:
                    g.delete()
                
                for m in self.masses:
                    m.sl.delete()
                    m.slc.delete()
                    
                break
            
            self.time += DT

# CONFIGURATION RUNS
# config0-config3 are identical in structure, so only config0 is commented
def config0(c, modify_mass):
    #decide on mass position, mass, color, slider/no-slider, and which graphs to plot
    c.addMass(pos=vec(-2, -1, 0), m=25, slider=slider(bind=modify_mass, min=1, max=200, step=1), slider_caption=wtext(), graphs=['d', 'v'], color=color.red)
    c.addMass(pos=vec(2, -2, 0), m=20, slider=slider(bind=modify_mass, min=1, max=200, step=1), slider_caption=wtext(), graphs=['d', 'v'], color=color.blue)
    
    #decide on pulley position and radius
    c.addPulley(pos=vec(0, 5, 0), radius=2)
    
    #make graphs and components linked
    c.addGraph('vel', c.masses[0], c.masses[1])   
    c.addGraph('disp', c.masses[0], c.masses[1])   
    
    #make string
    def make_string(s):
        s.strings.append(string())
        last = len(s.strings)-1
        
        s.strings[last].connect_component(head=s.masses[0])
        s.strings[last].connect_component(startang=pi, endang=0, pulley=s.pulleys[0])
        s.strings[last].connect_component(tail=s.masses[1])
        
    #system variables
    def make_variables(s):
        a = (s.masses[1].mass - s.masses[0].mass) / (s.masses[0].mass + s.masses[1].mass + 1/2*s.pulleys[0].mass) * ACCEL_G
        
        #setup object vars
        s.pulleys[0].ang_accel = a/s.pulleys[0].radius
        s.masses[0].accel = a
        s.masses[1].accel = -a
    
    #make constraints
    def check_collision(s):
        return mag(vec(s.masses[0].pos.x + s.masses[0].width/2, s.masses[0].pos.y, 0)-s.pulleys[0].pos) < s.pulleys[0].radius or mag(vec(s.masses[1].pos.x - s.masses[1].width/2, s.masses[1].pos.y, 0)-s.pulleys[0].pos) < s.pulleys[0].radius
    
    #pass to config
    c.attachString(func=make_string)
    c.attachVariables(func=make_variables)
    c.attachCondition(func=check_collision)
    
def config1(c, modify_mass):
    center = vec(-3, 0, 0)
    c.addMass(pos=vec(-14, -10, 0)-center, m=10, slider=slider(bind=modify_mass, min=1, max=200, step=1), slider_caption=wtext())
    c.addMass(pos=vec(9, -10, 0)-center, m=20, slider=slider(bind=modify_mass, min=1, max=200, step=1), slider_caption=wtext())
    
    c.addPulley(pos=vec(-10, 5, 0)-center, radius=4, color=color.green)
    c.addPulley(pos=vec(0, 6, 0)-center, radius=3, color=color.cyan)
    c.addPulley(pos=vec(5, 2, 0)-center, radius=2, color=color.blue)
    c.addPulley(pos=vec(8, -1, 0)-center, radius=1, color=color.purple)
    
    c.addGraph('ang_vel', *c.pulleys)
    c.addGraph('ang_disp', *c.pulleys)
    
    def make_string(s):
        s.strings.append(string())
        last = len(s.strings)-1
        
        s.strings[last].connect_component(head=s.masses[0])
        s.strings[last].connect_component(startang=pi, endang=pi/2, pulley=s.pulleys[0])
        s.strings[last].connect_component(startang=pi/2, endang=0, pulley=s.pulleys[1])
        s.strings[last].connect_component(startang=pi, endang=3/2*pi, pulley=s.pulleys[2])
        s.strings[last].connect_component(startang=pi/2, endang=0, pulley=s.pulleys[3])
        s.strings[last].connect_component(tail=s.masses[1])
        
    def make_variables(s):
        a = (s.masses[1].mass - s.masses[0].mass) / (s.masses[0].mass + s.masses[1].mass + 1/2*(s.pulleys[0].mass+s.pulleys[1].mass+s.pulleys[2].mass+s.pulleys[3].mass)) * ACCEL_G
        
        s.pulleys[0].ang_accel = a/s.pulleys[0].radius
        s.pulleys[1].ang_accel = a/s.pulleys[1].radius
        s.pulleys[2].ang_accel = -a/s.pulleys[2].radius
        s.pulleys[3].ang_accel = a/s.pulleys[3].radius
        s.masses[0].accel = a
        s.masses[1].accel = -a
    
    def check_collision(s):
        return mag(vec(s.masses[0].pos.x + s.masses[0].width/2, s.masses[0].pos.y, 0)-s.pulleys[0].pos) < s.pulleys[0].radius or mag(vec(s.masses[1].pos.x - s.masses[1].width/2, s.masses[1].pos.y, 0)-s.pulleys[3].pos) < s.pulleys[3].radius
    
    c.attachString(func=make_string)
    c.attachVariables(func=make_variables)
    c.attachCondition(func=check_collision)

def config2(c, modify_mass):
    c.addMass(pos=vec(-4, -3, 0), m=50, slider=slider(bind=modify_mass, min=1, max=200, step=1), slider_caption=wtext(), color=color.magenta)
    
    c.addPulley(pos=vec(0, 6, 0), radius=4)
    c.addPulley(pos=vec(2, -6, 0), radius=2, color=color.cyan)
    
    c.addGraph('vel', c.masses[0], c.pulleys[1])
    c.addGraph('disp', c.masses[0], c.pulleys[1])   
    
    def make_string(s):
        s.strings.append(string())
        last = len(s.strings)-1
        
        s.strings[last].connect_component(head=s.masses[0])
        s.strings[last].connect_component(startang=pi, endang=0, pulley=s.pulleys[0])
        s.strings[last].connect_component(startang=2*pi, endang=pi, pulley=s.pulleys[1])
        s.strings[last].connect_component(tail=s.pulleys[0])
        
        
    def make_variables(s):
        a = (s.pulleys[1].mass-2*s.masses[0].mass)/(2*s.masses[0].mass+s.pulleys[0].mass+3/4*s.pulleys[1].mass) * ACCEL_G
        
        s.pulleys[0].ang_accel = a/s.pulleys[0].radius
        s.pulleys[1].ang_accel = 0.5*a/s.pulleys[1].radius
        s.pulleys[1].accel = -0.5*a
        
        s.masses[0].accel = a
    
    def check_collision(s):
        return mag(vec(s.masses[0].pos.x + s.masses[0].width/2, s.masses[0].pos.y, 0)-s.pulleys[0].pos) < s.pulleys[0].radius or mag(s.pulleys[0].pos-s.pulleys[1].pos) < s.pulleys[0].radius+s.pulleys[1].radius
    
    c.attachString(func=make_string)
    c.attachVariables(func=make_variables)
    c.attachCondition(func=check_collision)
    
def config3(c, modify_mass):
    c.addMass(pos=vec(-12, -8, 0), m=150, slider=slider(bind=modify_mass, min=1, max=200, step=1), slider_caption=wtext(), color=color.magenta)
    
    c.addPulley(pos=vec(-8, 10, 0), radius=4)
    c.addPulley(pos=vec(-1, 0, 0), radius=3, color=color.cyan)
    c.addPulley(pos=vec(3, -11, 0), radius=4, color=color.green)
    
    c.addPulley(pos=vec(2, 12, 0), radius=2)
    c.addPulley(pos=vec(7, 5, 0), radius=2)
    
    c.addGraph('vel', c.masses[0], c.pulleys[1], c.pulleys[2])
    c.addGraph('disp', c.masses[0], c.pulleys[1], c.pulleys[2])   
    
    def make_string(s):
        s.strings.append(string())
        last = len(s.strings)-1
        
        s.strings[last].connect_component(head=s.masses[0])
        s.strings[last].connect_component(startang=pi, endang=0, pulley=s.pulleys[0])
        s.strings[last].connect_component(startang=pi, endang=2*pi, pulley=s.pulleys[1])
        s.strings[last].connect_component(tail=s.pulleys[3])
        
        s.strings.append(string())
        last = len(s.strings)-1
        
        s.strings[last].connect_component(head=s.pulleys[1])
        s.strings[last].connect_component(startang=pi, endang=2*pi, pulley=s.pulleys[2])
        s.strings[last].connect_component(tail=s.pulleys[4])
        
        
    def make_variables(s):
        a = (s.pulleys[1].mass+0.5*s.pulleys[2].mass-2*s.masses[0].mass)/(2*s.masses[0].mass+s.pulleys[0].mass-3/4*s.pulleys[1].mass-5/16*s.pulleys[2].mass) * ACCEL_G
        
        s.pulleys[0].ang_accel = a/s.pulleys[0].radius
        s.pulleys[1].ang_accel = -0.5*a/s.pulleys[1].radius
        s.pulleys[1].accel = -0.5*a
        s.pulleys[2].ang_accel = -0.25*a/s.pulleys[2].radius
        s.pulleys[2].accel = -0.25*a
        
        s.masses[0].accel = a
    
    def check_collision(s):
        return mag(vec(s.masses[0].pos.x + s.masses[0].width/2, s.masses[0].pos.y, 0)-s.pulleys[0].pos) < s.pulleys[0].radius or mag(s.pulleys[3].pos-s.pulleys[1].pos) < s.pulleys[3].radius+s.pulleys[1].radius
    
    c.attachString(func=make_string)
    c.attachVariables(func=make_variables)
    c.attachCondition(func=check_collision)

# SIMULATION BUTTONS
def run(s):
    global sim_status
    sim_status = 'run'

def stop(s):
    global sim_status
    sim_status = 'stop'
    
def reset(s):
    global sim_status
    sim_status = 'reset'

    #deletes previous canvas and then makes a new one
    scenes[len(scenes)-1].delete()
    new_scene = canvas(width=600,height=450,align="left",userspin=False)
    scenes.append(new_scene)
    
    #new configuration
    c = config()
    
    #python workaround... slider bind function
    def modify_mass(sl):
        c.masses[sl.id].mass = sl.value
        c.masses[sl.id].width = pow(c.masses[sl.id].mass, 1/3)/2
        c.masses[sl.id].body.size = vec(c.masses[sl.id].width, c.masses[sl.id].width, c.masses[sl.id].width)
        c.masses[sl.id].body.pos = c.masses[sl.id].pos+vec(0, -c.masses[sl.id].width/2, 0)
        c.masses[sl.id].slc.text = '<b>mass</b> = '+ c.masses[sl.id].mass +'\n\n'
        
    #choose which config to run
    if config_run == 0:
        config0(c, modify_mass)
    elif config_run == 1:
        config1(c, modify_mass)
    elif config_run == 2:
        config2(c, modify_mass)
    elif config_run == 3:
        config3(c, modify_mass)
        
    #run it!
    c.run_config()

run_butt = button(text="GO", bind=run, pos=scene.caption_anchor)
stop_butt = button(text="STOP",bind=stop, pos=scene.caption_anchor)
reset_butt = button(text="RESET",bind=reset, pos=scene.caption_anchor)

# CONFIGURATION BUTTONS
def set_config(s):
    global config_run
    config_run = s.id
    
    reset()

config_butts = [button(id=i,text=("Configuration " + i), bind=set_config, pos=scene.title_anchor) for i in range(4)]

# INIT
reset()

#note: read line 290 if noticing a lack of comments