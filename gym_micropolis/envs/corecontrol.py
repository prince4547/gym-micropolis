import sys
import os
import random
import numpy as np
if sys.version_info[0] >= 3:
    from gi.repository import Gtk as gtk
else:
    import gtk

## assumes you've downloaded the micropolis-4bots repo into the same directory as this (the gym-micropolis) repo.
FILE_DIR = os.path.dirname(os.path.realpath(__file__))
GIT_DIR = os.path.abspath(os.path.join(FILE_DIR, os.pardir, os.pardir))
if sys.version_info[0] >= 3:
    MICROPOLISCORE_DIR = GIT_DIR + '/micropolis-4bots-gtk3/MicropolisCore/src'
    sys.path.append(MICROPOLISCORE_DIR)
    from .tilemap import TileMap
else:
    MICROPOLISCORE_DIR = GIT_DIR + '/micropolis-4bots/MicropolisCore/src'
    sys.path.append(MICROPOLISCORE_DIR)
    from tilemap import TileMap

CURR_DIR = os.getcwd()
# we need to do this so the micropolisgenericengine can access images/micropolisEngine/dataColorMap.png


os.chdir(MICROPOLISCORE_DIR)   

from pyMicropolis.gtkFrontend import main


os.chdir(CURR_DIR)

class MicropolisControl():

    def __init__(self, MAP_W=12, MAP_H=12, PADDING=13, parallel_gui=False):
        self.parallel_gui = parallel_gui
        self.pgui = None
        if parallel_gui:
            import pexpect
            self.pgui = pexpect.spawn('/bin/bash')
            self.pgui.expect('sme')
            self.pgui.sendline('cd gym-micropolis')
            self.pgui.expect('sme')
            self.pgui.sendline('pwd')
            self.pgui.expect('sme')
            self.pgui.sendline('python2')
            self.pgui.expect('>>>')
            self.pgui.sendline('from gym_micropolis.envs.gui import MicropolisGUI')
            self.pgui.expect('>>>')
            self.pgui.sendline('m = MicropolisGUI({}, {})'.format(MAP_W, MAP_H))
            self.pgui.expect('>>>')
            self.pgui.sendline('m.render()')
            self.pgui.expect('>>>')

        self.SHOW_GUI=False
        engine, win1 = main.train(bot=self)
        os.chdir(CURR_DIR)
        self.engine = engine
        self.engine.setGameLevel(2)
        self.MAP_X = MAP_W
        self.MAP_Y = MAP_H
        self.PADDING = PADDING
        # shifts build area to centre of 120 by 100 tile map
       # self.MAP_XS = 59 - self.MAP_X // 2
       # self.MAP_YS = 49 - self.MAP_Y //2
        self.MAP_XS = 1
        self.MAP_YS = 1
        self.num_roads = 0
        self.engineTools = ['Residential', 'Commercial', 'Industrial', 
                'FireDept', 
                'PoliceDept', 
                # TODO: implement query (skipped for now by indexing)
               'Query',
               'Wire',
               'Clear',
               'Rail',
               'Road',
                'Stadium',
                'Park', 
                 'Seaport',
                'CoalPowerPlant', 
                'NuclearPowerPlant',
                'Airport',
                'Net',
                'Water',
                'Land',
                'Forest',
                ]
        # Names correspond to those of resultant zones
        self.tools = ['Residential', 'Commercial', 'Industrial', 
                'FireDept', 
                'PoliceDept', 
             # 'Query',
               'Wire',
               'Clear',
               'Rail',
               'Road',
                'Stadium',
                'Park', 
                 'Seaport',
                'CoalPowerPlant', 
                'NuclearPowerPlant',
                'Airport',
                'Net',
                'Water',
                'Land',
                'Forest',
                ]
        #['Residential','Commercial','Industrial','Road','Wire','NuclearPowerPlant', 'Park', 'Clear']
        # since query is exluded for now:
        self.num_tools = len(self.tools)
        self.map = TileMap(self, self.MAP_X + 2 * PADDING, self.MAP_Y + 2 * PADDING)
        self.zones = self.map.zones
        self.num_zones = self.map.num_zones
        # allows building on rubble and forest
        self.engine.autoBulldoze = True
        # for bots 
        win1.playCity()
        self.engine.setFunds(1000000)
        engine.setSpeed(3)
        engine.setPasses(500)
        #engine.simSpeed =99
        self.total_traffic = 0
        self.last_total_traffic = 0
#       engine.clearMap()
        self.win1=win1

    def layGrid(self, w, h):

        for i in range(self.MAP_X):
            for j in range(self.MAP_Y):
            #   gtk.mainiteration()
                self.engine.simTick()
                # vertical road
                if ((i + 4) % w == 0):
                    self.doTool(i, j,'Road')
                    if ((j + 1) % h in [1, h - 1]) and \
                            j not in [0, self.MAP_Y -1]:
                        self.doTool(i, j, 'Wire')
                # horizontal roads
                elif ((j + 1) % h == 0):
                    self.doTool(i, j,'Road')
                    if ((i + 4) % w in [1, w - 1]) and \
                            i not in [0, self.MAP_X - 1]:
                        self.doTool(i, j, 'Wire')
                # random zones
                elif ((i + 2 - (i + 4) // w) % 3) ==0 and \
                     ((j + 2 - (j + 1) // h) % 3) ==0:
     
                    tool_i = random.randint(0, 3-1)
                    self.doTool(i, j, ['Residential', 'Commercial', 'Industrial'][tool_i])
    
    def clearMap(self):
        self.engine.clearMap()
        self.map.setEmpty()
        if self.parallel_gui:
            self.pgui.sendline('m.clearMap()')
            self.pgui.expect('>>>')

    def getPopDensityMap(self):
        pop_density_map = np.zeros((1, self.MAP_X, self.MAP_Y))
        for i in range (self.MAP_X):
            for j in range(self.MAP_Y):
                im = i + self.MAP_XS
                jm = j + self.MAP_YS
                im -= 2
                jm -= 2
                pop_density_map[0][i][j] = self.engine.getPopulationDensity(im, jm)
        return pop_density_map

    def getTrafficDensityMap(self):
        self.last_total_traffic = self.total_traffic
        self.total_traffic = 0
        traffic_density_map = np.zeros((1, self.MAP_X, self.MAP_Y))
        for i in range (self.MAP_X):
            for j in range(self.MAP_Y):
                im = i + self.MAP_XS
                jm = j + self.MAP_YS
                im -= 2
                jm -= 4
                xy_density = self.engine.getTrafficDensity(im, jm)
                self.total_traffic += xy_density
                traffic_density_map[0][i][j] = self.engine.getTrafficDensity(im, jm)
        return traffic_density_map

    def getPowerMap(self):
        power_map = np.zeros((1, self.MAP_X, self.MAP_Y))
        for i in range (self.MAP_X):
            for j in range(self.MAP_Y):
                im = i + self.MAP_XS
                jm = j + self.MAP_YS
                power_map[0][i][j] = self.engine.getPowerGrid(im, jm)
        return power_map

    def getFunds(self):
        return self.engine.totalFunds

    def render(self):
        while gtk.events_pending():
            gtk.main_iteration()

    def setFunds(self, funds):
        return self.engine.setFunds(funds)

        # called by map module
    def doBulldoze(self, x, y):
        return self.doSimTool(x,y,'Clear')

    def doBotTool(self, x, y, tool, static_build=False):
        '''Takes string for tool'''
        return self.map.addZone(x + self.PADDING, y + self.PADDING, tool, static_build) 

    def doTool(self, x, y, tool):
        '''Takes string for tool'''
        return self.map.addZone(x, y, tool) 

    def playerToolDown(self, tool_int, x, y):
        zone_int = self.map.zoneInts[self.engineTools[tool_int]]
       #x += self.MAP_XS
       #y += self.MAP_YS
        self.map.addZoneSquare(zone_int, x, y, static_build=True)

    def toolDown(self, x, y, tool):
        '''Takes int for tool, depending on engine's index'''
        self.map.addZone(x, y, self.engineTools[tool])

        # called by map module
    def doSimTool(self, x, y, tool):
        x += self.MAP_XS
        y += self.MAP_YS
        tool = self.engineTools.index(tool)
        return self.doSimToolInt(x, y, tool)

    def doSimToolInt(self, x, y, tool):
        if self.parallel_gui:
            self.pgui.sendline('m.doSimToolInt({}, {}, {})'.format(x, y, tool))
            self.pgui.expect('>>>')
        return self.engine.toolDown(tool, x, y)

    def getResPop(self):
        return self.engine.resPop

    def getComPop(self):
        return self.engine.comPop

    def getIndPop(self):
        return self.engine.indPop

    def getTotPop(self):
        return self.engine.totalPop

    def takeSetupAction(self, a):
        tool = self.tools[a[0]]
        x = a[1]
        y = a[2]
        self.doTool(x, y, tool)

    def takeAction(self, a, static_build=False):
        '''tool int depends on self.tools indexing'''
        tool = self.tools[a[0]]
        x = int(a[1])
        y = int(a[2])
        self.doBotTool(x, y, tool, static_build)
        self.engine.simTick()
#       gtk.mainiteration()
 
    def close(self):
    #   self.engine.doReallyQuit()
        del(self.engine)



