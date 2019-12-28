'''
    rogue.py
    Softly Into the Night, a sci-fi/Lovecraftian roguelike
    Copyright (C) 2019 Jacob Wharton.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>

    This file glues everything together.
'''

import esper
import tcod as libtcod
import math

from const import *
from colors import COLORS as COL
import components as cmp
import processors as proc
import orangio  as IO
import action
import debug
import dice
import entities
import game
import levelgen
import lights
import misc
import managers
import maths
import player
import tilemap


EQUIPABLE_CONSTS={
EQ_MAINHAND : cmp.EquipableInHandSlot,
EQ_OFFHAND  : cmp.EquipableInHandSlot,
EQ_BODY     : cmp.EquipableInBodySlot,
EQ_BACK     : cmp.EquipableInBackSlot,
EQ_HEAD     : cmp.EquipableInHeadSlot,
EQ_AMMO     : cmp.EquipableInAmmoSlot,
    }

EQUIP_CONSTS={
EQ_MAINHAND : cmp.BP_Hand,
EQ_OFFHAND  : cmp.BP_Hand,
EQ_BODY     : cmp.BP_TorsoFront,
EQ_BACK     : cmp.BP_TorsoBack,
EQ_HEAD     : cmp.BP_Head,
EQ_AMMO     : cmp.BP_Hips,
    }


    #----------------#
    # global objects #
    #----------------#

class Rogue:
    occupations={}
    et_managers={} #end of turn managers
    bt_managers={} #beginning of turn managers
    c_managers={} #const managers
    manager = None # current active game state manager
    
    @classmethod
    def run_endTurn_managers(cls, pc):
        for v in cls.et_managers.values():
            v.run(pc)
    @classmethod
    def run_beginTurn_managers(cls, pc):
        for v in cls.bt_managers.values():
            v.run(pc)
    
    @classmethod
    def create_settings(cls): # later controllers might depend on settings
        cls.settings = game.GlobalSettings()
        cls.settings.read() # go ahead and read/apply settings
        cls.settings.apply()
    @classmethod
    def create_world(cls):      cls.world = esper.World()
    @classmethod
    def create_controller(cls): cls.ctrl = game.Controller()
    @classmethod
    def create_window(cls):
        cls.window = game.Window(
            cls.settings.window_width, cls.settings.window_height
            )
    @classmethod
    def create_consoles(cls):   cls.con = game.Console(window_w(),window_h())
    @classmethod
    def create_data(cls):       cls.data = game.GameData()
    @classmethod
    def create_map(cls, w, h):
        cls.map = tilemap.TileMap(w,h)
    @classmethod
    def create_clock(cls):      cls.clock = game.Clock()
    @classmethod
    def create_updater(cls):    cls.update = game.Update()
    @classmethod
    def create_view(cls):       cls.view = game.View(view_port_w(),view_port_h(), ROOMW,ROOMH)
    @classmethod
    def create_log(cls):        cls.log = game.MessageLog()
    @classmethod
    def create_savedGame(cls):  cls.savedGame = game.SavedGame()
    @classmethod
    def create_player(cls, sx,sy):
        cls.pc = player.chargen(sx, sy)
    @classmethod
    def create_processors(cls):
        #Processor class, priority (higher = processed first)
        cls.world.add_processor(proc.MetersProcessor(), 31)
        cls.world.add_processor(proc.StatusProcessor(), 30)
        cls.world.add_processor(proc.FluidProcessor(), 22)
        cls.world.add_processor(proc.FireProcessor(), 21)
        cls.world.add_processor(proc.TimersProcessor(), 20)
        cls.world.add_processor(proc.ActionQueueProcessor(), 11)
            # after all changes have been made
        cls.world.add_processor(proc.FOVProcessor(), 2)
        cls.world.add_processor(proc.GUIProcessor(), 1) 

    @classmethod
    def create_perturn_managers(cls):
        '''
            constant managers, ran each turn
        '''
        #beginning of turn (beginning of monster's turn)
        cls.bt_managers.update({'sounds' : managers.Manager_SoundsHeard()})
        cls.bt_managers.update({'sights' : managers.Manager_SightsSeen()})
        cls.bt_managers.update({'actors' : managers.Manager_Actors()})
        #end of turn (end of monster's turn)
##        cls.et_managers.update(managers.Manager_SightsSeen())
    
    @classmethod
    def create_const_managers(cls):
        '''
            constant managers, manually ran
        '''
##        cls.c_managers.update({'sights' : managers.Manager_SightsSeen()})
##        cls.c_managers.update({'sounds' : managers.Manager_SoundsHeard()})
        cls.c_managers.update({'events' : managers.Manager_Events()})
        cls.c_managers.update({'lights' : managers.Manager_Lights()})
        
        
'''
WHAT DO WE DO WITH THESE MANAGERS????
    FOV and ActionQueue is now a processor.... Events?????
    Rogue.c_managers.update({'fov'        : managers.Manager_FOV()})
    Rogue.c_managers.update({'events'     : managers.Manager_Events()})
    Rogue.c_managers.update({'actionQueue': managers.Manager_ActionQueue()})

'''
'''
    old update function:
    
    clearMsg = False
    Ref.update.activate_all_necessary_updates()
    pc=Ref.pc
    for update in Ref.update.get_updates():
        if update=='hud'        : render_hud(pc)
        elif update=='game'     : render_gameArea(pc)
        elif update=='msg'      : Ref.log.drawNew(); clearMsg=True
        elif update=='final'    : blit_to_final( con_game(),0,0)
        elif update=='base'     : refresh()
    if clearMsg: msg_clear()
    Ref.update.set_all_to_false()
'''

    # EXPIRED: Environment class
#/Rogue


    #----------------#
    #   Functions    #
    #----------------#

# global objects
def settings():     return Rogue.settings

# ECS
def get_slots(obj): # should only be used if absolutely necessary...
   return set(getattr(obj, '__slots__', set()))

# world
def world():    return Rogue.world

# player
def pc():       return Rogue.pc
def is_pc(ent): return (ent==Rogue.pc)

# saved game
def playableJobs():
    return entities.getJobs().items() #Rogue.savedGame.playableJobs

# log
def logNewEntry():
    Rogue.log.drawNew()
def msg(txt, col=None):
    if col is None: #default text color
        col=COL['white']
    Rogue.log.add(txt, str(get_turn()) )
def msg_clear():
    clr=libtcod.console_new(msgs_w(), msgs_h())
    libtcod.console_blit(clr, 0,0, msgs_w(),msgs_h(),  con_game(), 0,0)
    libtcod.console_delete(clr)

# game data
def dlvl():             return Rogue.data.dlvl() #current dungeon level of player
def level_up():         Rogue.data.dlvl_update(Rogue.data.dlvl() + 1)
def level_down():       Rogue.data.dlvl_update(Rogue.data.dlvl() - 1)
def level_set(lv):      Rogue.data.dlvl_update(lv)

# clock
def turn_pass():        Rogue.clock.turn_pass()
def get_turn():         return Rogue.clock.turn

# view
def view_nudge(dx,dy):      Rogue.view.nudge(dx,dy)
def view_nudge_towards(ent):Rogue.view.follow(ent)
def view_center(ent):
    pos=Rogue.world.component_for_entity(ent, cmp.Position)
    Rogue.view.center(pos.x, pos.y)
def view_center_player():
    pos=Rogue.world.component_for_entity(Rogue.pc, cmp.Position)
    Rogue.view.center(pos.x, pos.y)
def view_center_coords(x,y):Rogue.view.center(x,y)
def view_x():       return  Rogue.view.x
def view_y():       return  Rogue.view.y
def view_w():       return  Rogue.view.w
def view_h():       return  Rogue.view.h
def view_max_x():   return  ROOMW - Rogue.view.w #constraints on view panning
def view_max_y():   return  ROOMH - Rogue.view.h
def fixedViewMode_toggle(): Rogue.view.fixed_mode_toggle()

# map
def map(z = -99):
    # TODO: code for loading / unloading levels into the map
    if z == -99:
        z = dlvl()
    if dlvl() == z:
        return Rogue.map
    else:
        # unload current map from Rogue.map into the levels dict
        # load new map into Rogue.map from the levels dict
        # update dlvl
        level_set(z)
        return Rogue.map
def tile_get(x,y):          return Rogue.map.get_char(x,y)
def tile_change(x,y,char):
    updateNeeded=Rogue.map.tile_change(x,y,char)
    if updateNeeded:
        update_all_fovmaps()
def map_reset_lighting():   Rogue.map.grid_lighting_init()
def tile_lighten(x,y,value):Rogue.map.tile_lighten(x,y,value)
def tile_darken(x,y,value): Rogue.map.tile_darken(x,y,value)
def tile_set_light_value(x,y,value):Rogue.map.tile_set_light_value(x,y,value)
def get_light_value(x,y):   return Rogue.map.get_light_value(x,y)
##def map_generate(Map,level): levels.generate(Map,level) #OLD OBSELETE
def identify_symbol_at(x,y):
    asci = libtcod.console_get_char(0, getx(x),gety(y))
    char = "{} ".format(chr(asci)) if (asci < 128 and not asci==32) else ""
    desc="__IDENTIFY UNIMPLEMENTED__" #IDENTIFIER.get(asci,"???")
    return "{}{}".format(char, desc)
def grid_remove(ent): #remove thing from grid of things
    return Rogue.map.remove_thing(ent)
def grid_insert(ent): #add thing to the grid of things
    return Rogue.map.add_thing(ent)
def grid_fluids_insert(obj):    Rogue.map.grid_fluids[obj.x][obj.y].append(obj)
def grid_fluids_remove(obj):    Rogue.map.grid_fluids[obj.x][obj.y].remove(obj)

# updater
def update_base():      Rogue.update.base()
#def update_pcfov():     Rogue.update.pcfov()
def update_game():      Rogue.update.game()
def update_msg():       Rogue.update.msg()
def update_hud():       Rogue.update.hud()
def update_final():     Rogue.update.final()
#apply all updates if applicable
def game_update():      Rogue.update.update()

# consoles
def con_game():             return Rogue.con.game
def con_final():            return Rogue.con.final

# controller
def end():                  Rogue.ctrl.end()
def game_state():           return Rogue.ctrl.state
def game_is_running():      return Rogue.ctrl.isRunning
def game_set_state(state="normal"):
    print("$---Game State changed from {} to {}".format(game_state(), state))
    Rogue.ctrl.set_state(state)
def game_resume_state():    return Rogue.ctrl.resume_state
def set_resume_state(state):Rogue.ctrl.set_resume_state(state)

# window
def window_w():         return Rogue.window.root.w
def window_h():         return Rogue.window.root.h
def view_port_x():      return Rogue.window.scene.x
def view_port_y():      return Rogue.window.scene.y
def view_port_w():      return Rogue.window.scene.w
def view_port_h():      return Rogue.window.scene.h
def hud_x():            return Rogue.window.hud.x
def hud_y():            return Rogue.window.hud.y
def hud_w():            return Rogue.window.hud.w
def hud_h():            return Rogue.window.hud.h
def msgs_x():           return Rogue.window.msgs.x
def msgs_y():           return Rogue.window.msgs.y
def msgs_w():           return Rogue.window.msgs.w
def msgs_h():           return Rogue.window.msgs.h
def set_hud_left():     Rogue.window.set_hud_left()
def set_hud_right():    Rogue.window.set_hud_right()



    # functions from modules #

# orangio

def init_keyBindings():
    IO.init_keyBindings()


# game

def dbox(x,y,w,h,text='', wrap=True,border=0,margin=0,con=-1,disp='poly'):
    '''
        x,y,w,h     location and size
        text        display string
        border      border style. None = No border
        wrap        whether to use automatic word wrapping
        margin      inside-the-box text padding on top and sides
        con         console on which to blit textbox, should never be 0
                        -1 (default) : draw to con_game()
        disp        display mode: 'poly','mono'
    '''
    if con==-1: con=con_game()
    misc.dbox(x,y,w,h,text, wrap=wrap,border=border,margin=margin,con=con,disp=disp)
    
def makeConBox(w,h,text):
    con = libtcod.console_new(w,h)
    dbox(0,0, w,h, text, con=con, wrap=False,disp='mono')
    return con




    # printing functions #

#@debug.printr
def refresh():  # final to root and flush
    libtcod.console_blit(con_final(), 0,0,window_w(),window_h(),  0, 0,0)
    libtcod.console_flush()
#@debug.printr
def render_gameArea(pc) :
    con = Rogue.map.render_gameArea(pc, view_x(),view_y(),view_w(),view_h() )
    #libtcod.console_clear(con_game())
    libtcod.console_clear(con_game())
    libtcod.console_blit(con, view_x(),view_y(),view_w(),view_h(),
                         con_game(), view_port_x(),view_port_y())
#@debug.printr
def render_hud(pc) :
    con = misc.render_hud(hud_w(),hud_h(), pc, get_turn(), d_level() )
    libtcod.console_blit(con,0,0,0,0, con_game(),hud_x(),hud_y())
#@debug.printr
def blit_to_final(con,xs,ys, xdest=0,ydest=0): # window-sized blit to final
    libtcod.console_blit(con, xs,ys,window_w(),window_h(),
                         con_final(), xdest,ydest)
#@debug.printr
def alert(text=""):    # message that doesn't go into history
    dbox(msgs_x(),msgs_y(),msgs_w(),msgs_h(),text,wrap=False,border=None,con=con_final())
    refresh()



    # "Fun"ctions #

def around(i): # round with an added constant to nudge values ~0.5 up to 1 (attempt to get past some rounding errors)
    return round(i + 0.00001)
def sign(n):
    if n>0: return 1
    if n<0: return -1
    return 0
# tilemap
def thingat(x,y):       return Rogue.map.thingat(x,y) #Thing object
def thingsat(x,y):      return Rogue.map.thingsat(x,y) #list
def inanat(x,y):        return Rogue.map.inanat(x,y) #inanimate Thing at
def monat (x,y):        return Rogue.map.monat(x,y) #monster at
def solidat(x,y):       return Rogue.map.solidat(x,y) #solid Thing at
def wallat(x,y):        return (not Rogue.map.get_nrg_cost_enter(x,y) ) #tile wall
def fluidsat(x,y):      return Rogue.et_managers['fluids'].fluidsat(x,y) #list
def lightsat(x,y):      return Rogue.map.lightsat(x,y) #list
def fireat(x,y):        return False #Rogue.et_managers['fire'].fireat(x,y)

def cost_enter(x,y):    return Rogue.map.get_nrg_cost_enter(x,y)
def cost_leave(x,y):    return Rogue.map.get_nrg_cost_leave(x,y)
def cost_move(xf,yf,xt,yt,data):
    return Rogue.map.path_get_cost_movement(xf,yf,xt,yt,data)

def is_in_grid_x(x):    return (x>=0 and x<ROOMW)
def is_in_grid_y(y):    return (y>=0 and y<ROOMH)
def is_in_grid(x,y):    return (x>=0 and x<ROOMW and y>=0 and y<ROOMH)
def in_range(x1,y1,x2,y2,Range):    return (maths.dist(x1,y1, x2,y2) <= Range + .34)

# view
def getx(x):        return x + view_port_x() - view_x()
def gety(y):        return y + view_port_y() - view_y()
def mapx(x):        return x - view_port_x() + view_x()
def mapy(y):        return y - view_port_y() + view_y()

# terraforming
def dig(x,y):
    #dig a hole in the floor if no solids here
    #else dig the wall out
    #use rogue's tile_change func so we update all FOVmaps
    tile_change(x,y,FLOOR)
def singe(x,y): #burn tile
    if Rogue.map.get_char(x,y) == FUNGUS:
        tile_change(x,y,FLOOR)

def wind_force():
    return 0 # TEMPORARY, TODO: create wind processor
def wind_direction():
    return (1,0,) # TEMPORARY, TODO: create wind processor


    # component functions #

# NOTE: generally better to call directly and save the function call overhead
# Thus we should not really use these functions...

def get(ent, component): #return an entity's component
    return Rogue.world.component_for_entity(ent, component)
def has(ent, component): #return whether entity has component
    return Rogue.world.has_component(ent, component)
def match(component):
    return Rogue.world.get_component(component)
def matchx(*components):
    return Rogue.world.get_components(components)
    return True
def copyflags(toEnt,fromEnt): #use this to set an object's flags to that of another object.
    for flag in Rogue.world.component_for_entity(fromEnt, cmp.Flags).flags:
        make(toEnt, flag)


            
    # entity functions #

# GET Modified Statistic (base stat + modifiers (permanent and conditional))
def getms(ent, _var): # NOTE: must set the DIRTY_STATS flag to true whenever any stats or stat modifiers change in any way! Otherwise the function will return an old value!
    if on(ent, DIRTY_STATS): # dirty; re-calculate the stats first.
        makenot(ent, DIRTY_STATS)
        modded=_update_stats(ent)
        return modded.__dict__[_var]
    return Rogue.world.component_for_entity(ent, cmp.ModdedStats).__dict__[_var]
# ALTer Stat -- change stat stat by value val
def alts(ent, stat, val):
    make(ent, DIRTY_STATS)
    Rogue.world.component_for_entity(ent, cmp.Stats).__dict__[stat] += val
def setAP(ent, val):
    actor=Rogue.world.component_for_entity(ent, cmp.Actor)
    actor.ap = val
def spendAP(ent, amt):
    actor=Rogue.world.component_for_entity(ent, cmp.Actor)
    actor.ap = actor.ap - amt

# skills
def getskill(ent, skill): # return skill level in a given skill
    if not Rogue.world.has_component(ent, cmp.Skills):
        return 0
    skills = Rogue.world.component_for_entity(ent, cmp.Skills)
    return skills.skills.get(skill, 0)
def train(ent, skill, pts): # train (improve) skill
    if not Rogue.world.has_component(ent, cmp.Skills):
        return False
    make(ent,DIRTY_STATS)
    skills = Rogue.world.component_for_entity(ent, cmp.Skills)
    skills.skills[skill] = skills.skills.get(skill, 0) + pts
    return True
def forget(ent, skill, pts): # lose skill experience
    if not Rogue.world.has_component(ent, cmp.Skills):
        return False
    make(ent,DIRTY_STATS)
    skills = Rogue.world.component_for_entity(ent, cmp.Skills)
    skills.skills[skill] = skills.skills.get(skill, pts) - pts
    return True

# flags
def on(ent, flag):
    return flag in Rogue.world.component_for_entity(ent, cmp.Flags).flags
def make(ent, flag):
    Rogue.world.component_for_entity(ent, cmp.Flags).flags.add(flag)
def makenot(ent, flag):
    Rogue.world.component_for_entity(ent, cmp.Flags).flags.remove(flag)
#

##def has_equip(obj,item):
##    return item in Rogue.world.component_for_entity(obj, )
def give(ent,item):
    if on(item,FIRE):
        burn(ent, FIRE_BURN)
        cooldown(item)
    Rogue.world.component_for_entity(ent, cmp.Inventory).data.append(item)
def take(ent,item):
    Rogue.world.component_for_entity(ent, cmp.Inventory).data.remove(item)
def mutate(ent):
    # TODO: do mutation
    mutable = Rogue.world.component_for_entity(ent, cmp.Mutable)
    pos = Rogue.world.component_for_entity(ent, cmp.Position)
    entn = Rogue.world.component_for_entity(ent, cmp.Name)
    event_sight(pos.x,pos.y,"{t}{n} mutated!".format(t=entn.title,n=entn.name))
def has_sight(ent):
    if (Rogue.world.has_component(ent, cmp.SenseSight) and not on(ent,BLIND)):
        return True
    else:
        return False
def port(ent,x,y): # move thing to absolute location, update grid and FOV
    grid_remove(ent)
    pos = Rogue.world.component_for_entity(ent, cmp.Position)
    pos.x=x; pos.y=y;
    grid_insert(ent)
    update_fov(ent)
    if Rogue.world.has_component(ent, cmp.LightSource):
        compo = Rogue.world.component_for_entity(ent, cmp.LightSource)
        compo.light.reposition(x, y)
def drop(ent,item,dx=0,dy=0):   #remove item from ent's inventory, place it
    take(ent,item)              #on ground nearby ent.
    itempos=Rogue.world.component_for_entity(item, cmp.Position)
    entpos=Rogue.world.component_for_entity(ent, cmp.Position)
    itempos.x=entpos.x + dx
    itempos.y=entpos.y + dy
    grid_insert(ent)
def givehp(ent,val=9999):
    stats = Rogue.world.component_for_entity(ent, cmp.Stats)
    stats.hp = min(stats.hpmax, stats.hp + val)
    make(ent,DIRTY_STATS)
def givemp(ent,val=9999):
    stats = Rogue.world.component_for_entity(ent, cmp.Stats)
    stats.mp = min(stats.mpmax, stats.mp + val)
    make(ent,DIRTY_STATS)
def caphp (ent):
    stats = Rogue.world.component_for_entity(ent, cmp.Stats)
    stats.hp = min(stats.hp, stats.hpmax)
    make(ent,DIRTY_STATS)
def capmp (ent):
    stats = Rogue.world.component_for_entity(ent, cmp.Stats)
    stats.mp = min(stats.mp, stats.mpmax)
    make(ent,DIRTY_STATS)
#damage hp
def damage(ent, dmg: int):
##    assert isinstance(dmg, int)
    if dmg <= 0: return
    make(ent,DIRTY_STATS)
    stats = Rogue.world.component_for_entity(ent, cmp.Stats)
    stats.hp -= dmg
    if stats.hp <= 0:
        kill(ent)
#damage mp
def sap(ent, dmg: int):
##    assert isinstance(dmg, int)
    if dmg < 0: return
    make(ent,DIRTY_STATS)
    stats = Rogue.world.component_for_entity(ent, cmp.Stats)
    stats.mp -= dmg
    if stats.mp <= 0:
        exhaust(ent) # TODO
# elemental damage
def burn(ent, dmg, maxTemp=1000):
    return entities.burn(ent, dmg, maxTemp)
def cool(ent, dmg, minTemp=-100):
    return entities.burn(ent, dmg, minTemp)
def bleed(ent, dmg):
    return entities.bleed(ent, dmg)
def hurt(ent, dmg):
    return entities.hurt(ent, dmg)
def disease(ent, dmg):
    return entities.disease(ent, dmg)
def intoxicate(ent, dmg):
    return entities.intoxicate(ent, dmg)
def irradiate(ent, dmg):
    return entities.irradiate(ent, dmg)
def irritate(ent, dmg):
    return entities.irritate(ent, dmg)
def exposure(ent, dmg):
    return entities.exposure(ent, dmg)
def corrode(ent, dmg):
    return entities.corrode(ent, dmg)
def cough(ent, dmg):
    return entities.cough(ent, dmg)
def vomit(ent, dmg):
    return entities.vomit(ent, dmg)
def electrify(ent, dmg):
    return entities.electrify(ent, dmg)
def paralyze(ent, dur):
    return entities.paralyze(ent, dur)
def mutate(ent):
    return entities.mutate(ent)
    
def kill(ent): #remove a thing from the world
    if on(ent, DEAD): return
    world = Rogue.world
    _type = world.component_for_entity(ent, cmp.Draw).char
    if world.has_component(ent, cmp.DeathFunction): # call destroy function
        world.component_for_entity(ent, cmp.DeathFunction).func(ent)
    make(ent, DEAD)
    clear_status_all(ent)
    #drop inventory
    if world.has_component(ent, cmp.Inventory):
        for tt in world.component_for_entity(ent, cmp.Inventory):
            drop(ent, tt)
    #creatures
    isCreature = world.has_component(ent, cmp.Creature)
    if isCreature:
        #create a corpse
        if dice.roll(100) < entities.corpse_recurrence_percent[_type]:
            create_corpse(ent)
    #inanimate things
    else:
        #burn to ashes
        if on(ent, FIRE):
            mat = world.component_for_entity(ent, cmp.Material).flag
            if (mat==MAT_FLESH
                or mat==MAT_WOOD
                or mat==MAT_FUNGUS
                or mat==MAT_VEGGIE
                or mat==MAT_LEATHER
                ):
                create_ashes(ent)
    #remove dead thing
    if Rogue.world.has_component(ent, cmp.Position):
        if isCreature:
            release_creature(ent)
        else:
            release_entity(ent)
def zombify(ent):
    kill(ent) # temporary
def explosion(name, x, y, radius):
    event_sight(x, y, "{n} explodes!".format(n=name))
def metabolize(ent, food=1, water=1):
    entities.metabolism(ent, food, water)





    #----------------------#
    #        Events        #
    #----------------------#

def event_sight(x,y,text):
    if not text: return
    Rogue.c_managers['events'].add_sight(x,y,text)
def event_sound(x,y,data):
    if (not data): return
    volume,text1,text2=data
    Rogue.c_managers['events'].add_sound(x,y,text1,text2,volume)
# TODO: differentiate between 'events' and 'sights' / 'sounds' which are for PC entity only (right???)
def listen_sights(ent):     return  Rogue.c_managers['events'].get_sights(ent)
def add_listener_sights(ent):       Rogue.c_managers['events'].add_listener_sights(ent)
def remove_listener_sights(ent):    Rogue.c_managers['events'].remove(ent)
def clear_listen_events_sights(ent):Rogue.c_managers['events'].clear_sights(ent)
def listen_sounds(ent):     return  Rogue.c_managers['events'].get_sounds(ent)
def add_listener_sounds(ent):       Rogue.c_managers['events'].add_listener_sounds(ent)
def remove_listener_sounds(ent):    Rogue.c_managers['events'].remove(ent)
def clear_listen_events_sounds(ent):Rogue.c_managers['events'].clear_sounds(ent)
def clear_listeners():              Rogue.c_managers['events'].clear()
    
##def listen_sights(ent):     return  Rogue.c_managers['sights'].get_sights(ent)
##def add_listener_sights(ent):       Rogue.c_managers['sights'].add_listener_sights(ent)
##def remove_listener_sights(ent):    Rogue.c_managers['sights'].remove_listener_sights(ent)
##def clear_listen_events_sights(ent):Rogue.c_managers['sights'].clear_sights(ent)
##def listen_sounds(ent):     return  Rogue.c_managers['sounds'].get_sounds(ent)
##def add_listener_sounds(ent):       Rogue.c_managers['sounds'].add_listener_sounds(ent)
##def remove_listener_sounds(ent):    Rogue.c_managers['sounds'].remove_listener_sounds(ent)
##def clear_listen_events_sounds(ent):Rogue.c_managers['sounds'].clear_sounds(ent)

def pc_listen_sights(): # these listener things for PC might need some serious work...
    pc=Rogue.pc
    lis=listen_sights(pc)
    if lis:
        for ev in lis:
            Rogue.c_managers['sights'].add(ev)
        manager_sights_run()
def pc_listen_sounds():
    pc=Rogue.pc
    lis=listen_sounds(pc)
    if lis:
        for ev in lis:
            Rogue.c_managers['sounds'].add(ev)
        manager_sounds_run()




    #----------------#
    #       FOV      #
    #----------------#

def fov_init():  # normal type FOV map init
    #TODO: THIS CODE NEEDS TO BE UPDATED. ONLY MAKE AS MANY FOVMAPS AS NEEDED.
    fovMap=libtcod.map_new(ROOMW,ROOMH)
    libtcod.map_copy(Rogue.map.fov_map,fovMap)  # get properties from Map
    return fovMap
#@debug.printr
def fov_compute(ent):
    pos = Rogue.world.component_for_entity(ent, cmp.Position)
    senseSight = Rogue.world.component_for_entity(ent, cmp.SenseSight)
    libtcod.map_compute_fov(
        senseSight.fov_map, pos.x, pos.y, getms(ent, 'sight'),
        light_walls = True, algo=libtcod.FOV_RESTRICTIVE
        )
def update_fovmap_property(fovmap, x,y, value):
    libtcod.map_set_properties( fovmap, x,y,value,True)
def update_fov(ent):    proc.FOV.add(ent)
##def compute_fovs():     Rogue.c_managers['fov'].run()
# circular FOV function
def can_see(ent,x,y):
    world = Rogue.world
    if (get_light_value(x,y) == 0 and not on(ent,NVISION)):
        return False
    pos = world.component_for_entity(ent, cmp.Position)
    senseSight = world.component_for_entity(ent, cmp.SenseSight)
    return ( in_range(pos.x,pos.y, x,y, getms(ent, "sight")) #<- circle-ize
             and libtcod.map_is_in_fov(senseSight.fov_map,x,y) )
#copies Map 's fov data to all creatures - only do this when needed
#   also flag all creatures for updating their fov maps
def update_all_fovmaps():
    for ent, compo in Rogue.world.get_component(cmp.SenseSight):
        fovMap=compo.fov_map
        libtcod.map_copy(Rogue.map.fov_map, fovMap)
        update_fov(ent)
#******we should overhaul this FOV system!~*************
        #creatures share fov_maps. There are a few fov_maps
        #which have different properties like x-ray vision, etc.
        #the only fov_maps we have should all be unique. Would save time.
        #update_all_fovmaps only updates these unique maps.
        #this would probably be much better, I should do this for sure.



    #----------------#
    #      Paths     #
    #----------------#

def can_hear(ent, x,y, volume):
    world = Rogue.world
    if ( on(ent,DEAD) or (not world.has_component(ent, cmp.SenseHearing)) ):
         return False
    pos = world.component_for_entity(ent, cmp.Position)
    senseHearing = world.component_for_entity(ent, cmp.SenseHearing)
    dist=maths.dist(pos.x, pos.y, x, y)
    maxHearDist = volume * senseHearing.hearing / AVG_HEARING
    if (pos.x == x and pos.y == y): return (0,0,maxHearDist,)
    if dist > maxHearDist: return False
    # calculate a path
    path=path_init_sound()
    path_compute(path, pos.x,pos.y, x,y)
    pathSize=libtcod.path_size(path)
    if dist >= 2:
        semifinal=libtcod.path_get(path, 0)
        xf,yf=semifinal
        dx=xf - pos.x
        dy=yf - pos.y
    else:
        dx=0
        dy=0
    path_destroy(path)
    loudness=(maxHearDist - pathSize - (pathSize - dist))
    if loudness > 0:
        return (dx,dy,loudness)

def path_init_movement():
    pathData=0
    return Rogue.map.path_new_movement(pathData)
def path_init_sound():
    pathData=0
    return Rogue.map.path_new_sound(pathData)
def path_compute(path, xfrom,yfrom, xto,yto):
    libtcod.path_compute(path, xfrom,yfrom, xto,yto)
def path_destroy(path):
    libtcod.path_delete(path)
def path_step(path):
    x,y=libtcod.path_walk(path, True)
    return x,y





    #----------------#
    #     Things     #
    #----------------#

def register_entity(ent):
    grid_insert(ent)
    create_moddedStats(ent) # is there a place this would belong better?
    make(ent,DIRTY_STATS)
def release_entity(ent):
    grid_remove(ent)
    delete_entity(ent)
def delete_entity(ent):
    Rogue.world.delete_entity(ent)
def create_stuff(ID, x,y): # create & register an item from stuff list
    tt = entities.create_stuff(ID, x,y)
    register_entity(tt)
    return tt
def create_rawmat(ID, x,y): # create & register an item from raw materials
    tt = entities.create_rawmat(ID, x,y)
    register_entity(tt)
    return tt
def create_entity():
    return Rogue.world.create_entity()
##def create_entity_flagset(): # create an entity with a flagset
##    ent = Rogue.world.create_entity()
##    Rogue.world.add_component(ent, cmp.Flags) #flagset
##    return ent

#  creature/monsters  #

def register_creature(ent):
    register_entity(ent)
def release_creature(ent):
    release_entity(ent)
    remove_listener_sights(ent)
    remove_listener_sounds(ent)

def create_monster(typ,x,y,col,mutate=3): #init from entities.py
    '''
        call this to create a monster from the bestiary

        TODO: figure out what to do to create monsters/creatures in general
            code for that is not complete...
    '''
    if monat(x,y):
        return None #tile is occupied by a creature already.
    ent = entities.create_monster(typ,x,y,col,mutate)
##    init_inventory(monst, monst.stats.get('carry')) # do this in create_monster
    givehp(ent)
    register_creature(ent)
    return monst

def create_corpse(ent):
    corpse = entities.create_corpse(ent)
    register_entity(corpse)
    return corpse
def create_ashes(ent):
    ashes = entities.create_ashes(ent)
    register_entity(ashes)
    return ashes

    

    #---------------#
    #   Inventory   #
    #---------------#

def init_inventory(ent, capacity):
    Rogue.world.add_component(ent, cmp.Inventory(capacity))



    #------------#
    #   Fluids   #
    #------------#

def create_fluid(name, x,y, volume):
    fluid = fluids.create_fluid(x,y,name,volume)
    register_fluid(fluid)

def port_fluid(fluid, xto, yto):
    grid_fluids_remove(fluid)
    pos = Rogue.world.component_for_entity(fluid, cmp.Position)
    pos.x = xto
    pos.y = yto
    grid_fluids_insert(fluid)
##def flow_fluid(fluid, xto, yto, amt): #fluids should be object instances?
##    grid_fluids_remove(fluid)
##    fluid.x=xto
##    fluid.y=yto
##    grid_fluids_insert(fluid)
    

def register_fluid(ent):
    grid_fluids_insert(ent)
##    list_add_fluid(ent)
def release_fluid(ent):
    grid_fluids_remove(ent)
##    list_remove_fluid(obj)
    
#fluid containers
def init_fluidContainer(ent, size):
    make(ent,HOLDSFLUID)
    Rogue.world.add_component(ent, cmp.FluidContainer(size))




    #---------------------#
    #   Equipment / Body  #
    #---------------------#


#equipping things
def equip(ent,item,equipType): # equip an item in 'equipType' slot
    '''
        equip ent with item in the slot designated by equipType const
        return the effect ID for the stat modifier if successful
        return a negative error value otherwise
    '''
    world = Rogue.world
    equipableConst = EQUIPABLE_CONSTS[equipType]
    equipConst = EQUIP_CONSTS[equipType]
    if world.has_component(item, equipableConst):
        if world.has_component(ent, equipConst):
            slot=world.component_for_entity(ent, equipConst)
            if slot.item==None:
                if world.has_component(item, cmp.Position):
                    world.remove_component(item, cmp.Position)
                slot.item = item
                make(ent, DIRTY_STATS)
                return 1
            else:
                return -102 # already have something equipped there
        else:
            return -101 # entity doesn't have the slot necessary
    else:
        return -100 # item can't be equipped in this slot
    
##                if world.has_component(item, cmp.Stats):
##                    stats=world.component_for_entity(item, cmp.Stats)
##                    world.add_component(item, cmp._Stats(
##                        hp=stats.hp, hpmax=stats.hpmax
##                        mp=stats.mp, mpmax=stats.mpmax
##                        resfire=stats.resfire,
##                        resbio=stats.resbio,
##                        reselec=stats.reselec,
##                        resphys=stats.resphys
##                        )
##                    world.remove_component(item, cmp.Stats)
    
##                world.add_component(item, cmp.Equipped(ent, equipType))
##                equipData=world.component_for_entity(item, equipableConst)
##                modID = effect_add(ent, equipData.mods)
##                slot.modID = modID
##                #TODO: add special effects; light, etc.

def deequip(ent,equipType): # remove equipment from slot 'equipType'
    equipConst = EQUIP_CONSTS[equipType]
    slot=world.component_for_entity(ent, equipConst)
    if not slot.item: #nothing equipped here
        return None
    item = slot.item
    slot.item = None
    make(ent, DIRTY_STATS)
    return item

##    equipableConst = EQUIPABLE_CONSTS[equipType]
##    #TODO: remove any special effects; light, etc.
##    world.remove_component(item, cmp.Equipped)
##    effect_remove(slot.modID)
##    slot.modID = None

##    #put item back in the world # THIS SHOULD BE DONE BY ANOTHER FUNCTION
##    pos = world.component_for_entity(ent, cmp.Position)
##    world.add_component(item, cmp.Position(pos.x,pos.y))

# build equipment and place in the world
def create_weapon(name,x,y):
    weap=entities.create_weapon(name,x,y)
    givehp(weap) #give random quality based on dlvl?
    register_entity(weap)
    return weap
def create_gear(name,x,y):
    ent=entities.create_gear(name,x,y)
    givehp(ent) #give random quality based on dlvl?
    register_entity(ent)
    return ent

def create_body_humanoid(mass=70, female=False):
    return entities.create_body_humanoid(mass=mass, female=female)

def dominant_arm(ent):
    assert(Rogue.world.has_component(ent, cmp.BPC_Arms))
    for arm in Rogue.world.component_for_entity(ent, cmp.BPC_Arms).arms:
        if arm.dominant:
            return arm
    return None
def dominant_leg(ent):
    assert(Rogue.world.has_component(ent, cmp.BPC_Legs))
    for leg in Rogue.world.component_for_entity(ent, cmp.BPC_Legs).legs:
        if leg.dominant:
            return leg
    return None

def homeostasis(ent): entities.homeostasis(ent)
def metabolism(ent, hunger, thirst=0): entities.metabolism(ent, hunger, thirst)
def stomach(ent): entities.stomach(ent)
def starve(ent): entities.starve(ent)
def dehydrate(ent): entities.dehydrate(ent)
        

    #--------------#
    #     Stats    #
    #--------------#
    

def _update_stats(ent): # PRIVATE, ONLY TO BE CALLED FROM getms(...)
    '''
        calculate modified stats
            building up from scratch (base stats)
            add any modifiers from equipment, status effects, etc.
        return the Modified Stats component
        after this is called, you can access the Modified Stats component
            and it will contain the right value, until something significant
            updates which would change the calculation, at which point the
            DIRTY_STATS flag for that entity must be set to True.
    '''
    # NOTE: apply all penalties (w/ limits, if applicable) AFTER bonuses.
        # this is to ensure you don't end up with MORE during a
        #   penalty application; as in the case the value was negative
    
    # init
    offhandItem = False
    addMods=[]
    multMods=[]
    world=Rogue.world
    base=world.component_for_entity(ent, cmp.Stats)
    modded=world.component_for_entity(ent, cmp.ModdedStats)
    if world.has_component(ent, cmp.Skills):
        skills=world.component_for_entity(ent, cmp.Skills)
        armorSkill = (skills.skills.get(SKL_ARMOR,0)) # armored skill value
        unarmored = (skills.skills.get(SKL_UNARMORED,0)) # unarmored skill
    else:
        skills=None
        armorSkill = 0
        unarmored = 0
    # RESET all modded stats to their base
    for k,v in base.__dict__.items():
        modded.__dict__[k] = v
    # /init
    
#~~~~~~~#----------------------------------------------#~~~~~~~~~~~~~~~#
        # bonuses that are applied before gear bonuses #
        #----------------------------------------------#


        #  good multiplier statuses  #    
    # sprint
    if world.has_component(ent, cmp.StatusSprint):
        modded.msp = modded.msp * SPRINT_MSPMOD
    # haste
    if world.has_component(ent, cmp.StatusHaste):
        modded.spd = modded.spd * HASTE_SPDMOD

#~~~~~~~#-------------------------#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # Body Status / Equipment #
        #-------------------------#
    
    if world.has_component(ent, cmp.Body):
        body=world.component_for_entity(ent, cmp.Body)
    else:
        body=None
    if body:
        keys = body.parts.keys()
        if cmp.BPC_Torso in keys:
            entities._update_from_bpc_torso(
                addMods,multMods,
                ent, body.parts[cmp.BPC_Torso],
                armorSkill, unarmored
                )
        if cmp.BPC_Heads in keys:
            entities._update_from_bpc_heads(
                addMods,multMods,
                ent, body.parts[cmp.BPC_Heads],
                armorSkill, unarmored
                )
        if cmp.BPC_Arms in keys:
            entities._update_from_bpc_arms(
                addMods,multMods,
                ent, body.parts[cmp.BPC_Arms],
                armorSkill, unarmored
                )
        if cmp.BPC_Legs in keys:
            entities._update_from_bpc_legs(
                addMods,multMods,
                ent, body.parts[cmp.BPC_Legs],
                armorSkill, unarmored
                )
        if cmp.BPC_Pseudopods in keys:
            entities._update_from_bpc_pseudopods(
                addMods,multMods,
                ent, body.parts[cmp.BPC_Pseudopods],
                armorSkill, unarmored
                )
        if cmp.BPC_Wings in keys:
            entities._update_from_bpc_wings(
                addMods,multMods,
                ent, body.parts[cmp.BPC_Wings],
                armorSkill, unarmored
                )
        if cmp.BPC_Tails in keys:
            entities._update_from_bpc_tails(
                addMods,multMods,
                ent, body.parts[cmp.BPC_Tails],
                armorSkill, unarmored
                )
        if cmp.BPC_Genitals in keys:
            entities._update_from_bpc_genitals(
                addMods,multMods,
                ent, body.parts[cmp.BPC_Genitals],
                armorSkill, unarmored
                )
    #
    
    # apply mods -- addMods
    for mod in addMods:
        for k,v in mod.items():
            modded.__dict__[k] = v + modded.__dict__[k]
            
#~~~~~~~#------------#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # inventory  #
        #------------#

    # add encumberance from all items in inventory
    # TODO


        # statuses that affect attributes #
        
    # pain
    if world.has_component(ent, cmp.StatusPain):
        modded.str = modded.str * PAIN_STRMOD
        modded.end = modded.end * PAIN_ENDMOD
        modded.con = modded.con * PAIN_CONMOD
    # sick
    if world.has_component(ent, cmp.StatusSick):
        modded.str = modded.str * SICK_STRMOD
        modded.end = modded.end * SICK_ENDMOD
        modded.con = modded.con * SICK_CONMOD
        modded.respain = modded.respain + SICK_RESPAINMOD
    
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    # *** Nothing below here that modifies attributes ***!!!
    
#~~~~~~~#------------#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # attributes #
        #------------#

        # These are NOT multiplier modifiers;
        # These only improve stats by adding some value to them.

    # Strength
    _str = modded.str
    modded.encmax += _str * AM_STR_ENCUMBERANCE
    modded.force += _str * AM_STR_FORCE
    modded.gra += _str * AM_STR_GRAPPLING

    # Agility
    _agi = modded.agi
    modded.msp += _agi * AM_AGI_MOVESPEED
    modded.asp += _agi * AM_AGI_ATTACKSPEED

    # Dexterity
    _dex = modded.dex
    modded.atk += _dex * AM_DEX_ATTACK

    # Endurance
    _end = modded.end
    modded.resfire += _end * AM_END_RESHEAT
    modded.rescold += _end * AM_END_RESCOLD
    modded.resphys += _end * AM_END_RESPHYS
    modded.respain += _end * AM_END_RESPAIN
    modded.resbio += _end * AM_END_RESBIO
    modded.resbleed += _end * AM_END_RESBLEED

    # Intelligence
    _int = modded.int

    # Constitution
    _con = modded.con
    modded.hpmax += _con * AM_CON_HP
    modded.encmax += _con * AM_CON_ENCUMBERANCE

    # Luck
    luck = modded.luck
    #
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    #---------------------------------------------------------------#
    #       FINAL        MULTIPLIERS       BEGIN       HERE         #
    #---------------------------------------------------------------#

#~~~~~~~#----------------------------#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        #   bad multiplier statuses  #
        #----------------------------#

    # frozen
    if world.has_component(ent, cmp.StatusFrozen):
        modded.msp = modded.msp * FROZEN_MSPMOD
    # blind
    if world.has_component(ent, cmp.StatusBlind):
        modded.sight = modded.sight * BLIND_SIGHTMOD
    # deaf
    if world.has_component(ent, cmp.StatusDeaf):
        modded.hearing = modded.hearing * DEAF_HEARINGMOD
    # irritated
    if world.has_component(ent, cmp.StatusIrritated):
        modded.sight = modded.sight * IRRITATED_SIGHTMOD
        modded.hearing = modded.hearing * IRRITATED_HEARINGMOD
    # paralyzed
    if world.has_component(ent, cmp.StatusParalyzed):
        modded.spd = modded.spd * PARALYZED_SPDMOD
    # slow
    if world.has_component(ent, cmp.StatusSlow):
        modded.spd = modded.spd * SLOW_SPDMOD
        

#~~~~~~~#--------------#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        # encumberance #
        #--------------#

    erat = modded.enc/modded.encmax # encumberance ratio
    if erat < 0.05:     # 0: 0 - 5%
        encbp = 0
    elif erat < 0.12:   # 1: 5 - 12%
        encbp = 1
    elif erat < 0.25:   # 2: 12 - 25%
        encbp = 2
    elif erat < 0.5:    # 3: 25 - 50%
        encbp = 3
    elif erat < 0.75:   # 4: 50 - 75%
        encbp = 4
    elif erat < 0.87:   # 5: 75 - 87%
        encbp = 5
    elif erat < 0.95:   # 6: 87 - 95%
        encbp = 6
    elif erat < 1:      # 7: 95 - 100%
        encbp = 7
    else:               # 8: 100% or greater
        encbp = 8

    if encbp > 0:
        index = encbp - 1
        modded.asp = ENCUMBERANCE_MODIFIERS['asp'][index] * modded.asp
        modded.msp = ENCUMBERANCE_MODIFIERS['msp'][index] * modded.msp
        modded.atk = ENCUMBERANCE_MODIFIERS['atk'][index] * modded.atk
        modded.dfn = ENCUMBERANCE_MODIFIERS['dfn'][index] * modded.dfn
        modded.pro = ENCUMBERANCE_MODIFIERS['pro'][index] * modded.pro
        modded.gra = ENCUMBERANCE_MODIFIERS['gra'][index] * modded.gra
        modded.bal = ENCUMBERANCE_MODIFIERS['bal'][index] * modded.bal
    #
    
#~~~~~~~#--------------#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        #   finalize   #
        #--------------#
    
    # apply mods -- mult mods
    for mod in multMods:
        for k,v in mod.items():
            if modded.__dict__[k] > 0:
                modded.__dict__[k] = v * modded.__dict__[k]
    
    # round values as the final step
    for k,v in modded.__dict__.items():
        modded.__dict__[k] = around(v)

    # NOTE: resulting values can be negative, but this can be
    #   checked for, depending on the individual uses for each stat
    #   e.g. MSp cannot be below 1-5 or so for purposes of movement,
    #   Spd cannot be below 1, Dmg cannot be below 0,
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    return modded
# end def


# create and initialize the ModdedStats component
def create_moddedStats(ent):
    world=Rogue.world
    modded=cmp.ModdedStats()
    base=world.component_for_entity(ent, cmp.Stats)
    for k in base.__dict__.keys():
        modded.__dict__.update({ k : 0 })
    world.add_component(ent, modded)
    make(ent, DIRTY_STATS)
    return modded






        
    #-------------#
    # occupations #
    #-------------#

def occupations(ent):
    return Rogue.occupations.get(ent, None)
def occupation_add(ent,turns,fxn,args,helpless):
    '''
        fxn: function to call each turn.
        args: arguments to pass into fxn
        turns: turns remaining in current occupation
        helpless: bool, whether ent can be interrupted
        interrupted: bool, whether ent has been interrupted in this action
    '''
    Rogue.occupations.update({ ent : (fxn,args,turns,helpless,False) })
def occupation_remove(ent):
    del Rogue.occupations[ent]
def occupation_elapse_turn(ent):
    fxn,args,turns,helpless,interrupted = Rogue.occupations[ent]
    if interrupted:
        Rogue.occupations.update({ ent : (fxn,args,turns - 1,helpless,interrupted) })
        return False    # interrupted occupation
    if turns:
        setAP(ent, 0)
        Rogue.occupations.update({ ent : (fxn,args,turns - 1,helpless,interrupted) })
    elif fxn is not None:
        fxn(ent, args)
    return True     # successfully continued occupation
    



    #----------------#
    #    lights      #
    #----------------#

def list_lights(): return list(Rogue.c_managers["lights"].lights.values())
def create_light(x,y, value, owner=None):
    light=lights.Light(x,y, value, owner)
    light.fov_map=fov_init()
    light.shine()
    lightID = Rogue.c_managers['lights'].add(light)
    if owner:
        if Rogue.world.has_component(owner, cmp.LightSource):
            compo = Rogue.world.component_for_entity(owner, cmp.LightSource)
            release_light(compo.lightID)
        Rogue.world.add_component(owner, cmp.LightSource(lightID, light))
    return lightID

def release_light(lightID):
    light = Rogue.c_managers['lights'].get(lightID)
    light.unshine()
    if light.owner:
        Rogue.world.remove_component(light.owner, cmp.LightSource)
    Rogue.c_managers['lights'].remove(lightID)



    #-------------#
    #   fires     #
    #-------------#

#fire tile flag is independent of the status effect of burning
def set_fire(x,y):
    Rogue.et_managers['fire'].add(x,y)
def douse(x,y): #put out a fire at a tile and cool down all things there
    if not Rogue.et_managers['fire'].fireat(x,y): return
    Rogue.et_managers['fire'].remove(x,y)
    for tt in thingsat(x,y):
        Rogue.bt_managers['status'].remove(tt, FIRE)
        cooldown(tt)



    #----------------#
    #    status      #
    #----------------#

#Status for being on fire separate from the fire entity and light entity.

def get_status(ent, statusCompo):
    if Rogue.world.has_component(ent, statusCompo):
        return Rogue.world.component_for_entity(ent, statusCompo)
    else:
        return None
def set_status(ent, status, t=-1):
    '''
        # ent       = Thing object to set the status for
        # status    = status class (not an object instance)
        # t         = duration (-1 is the default duration for that status)
    '''
    proc.Status.add(ent, status, t)
def clear_status(ent, status):
    proc.Status.remove(ent, status)
def clear_status_all(ent):
    proc.Status.remove_all(ent)



    #-----------#
    #  actions  #
    #-----------#

def queue_action(ent, act):
    pass
    #Rogue.c_managers['actionQueue'].add(obj, act)





    #----------#
    # managers #
    #----------#

def manager_sights_run():   Rogue.c_managers['sights'].run()
def manager_sounds_run():   Rogue.c_managers['sounds'].run()

# constant managers #

def register_timer(obj):    Rogue.bt_managers['timers'].add(obj)
def release_timer(obj):     Rogue.bt_managers['timers'].remove(obj)

# game state managers #

def get_active_manager():       return Rogue.manager
def close_active_manager():
    if Rogue.manager:
        Rogue.manager.close()
        Rogue.manager=None
def clear_active_manager():
    if Rogue.manager:
        Rogue.manager.set_result('exit')
        close_active_manager()

def routine_look(xs, ys):
    clear_active_manager()
    game_set_state("look")
    Rogue.manager=managers.Manager_Look(
        xs, ys, Rogue.view, Rogue.map.get_map_state())
    alert("Look where? (<hjklyubn>, mouse; <select> to confirm)")
    Rogue.view.fixed_mode_disable()

def routine_move_view():
    clear_active_manager()
    game_set_state("move view")
    Rogue.manager=managers.Manager_MoveView(
        Rogue.view, Rogue.map.get_map_state())
    alert("Direction? (<hjklyubn>; <select> to center view)")
    Rogue.view.fixed_mode_disable()

def routine_print_msgHistory():
    clear_active_manager()
    game_set_state("message history")
    width   = window_w()
    height  = window_h()
    strng   = Rogue.log.printall_get_wrapped_msgs()
    nlines  = 1 + strng.count('\n')
    hud1h   = 3
    hud2h   = 3
    scroll  = makeConBox(width,1000,strng)
    top     = makeConBox(width,hud1h,"Message History:")
    bottom  = makeConBox(width,hud2h,"<Up>, <Down>, <PgUp>, <PgDn>, <Home>, <End>; <select> to return")
    Rogue.manager = managers.Manager_PrintScroll( scroll,width,height, top,bottom, h1=hud1h,h2=hud2h,maxy=nlines)

def Input(x,y, w=1,h=1, default='',mode='text',insert=False):
    return IO.Input(x,y,w=w,h=h,default=default,mode=mode,insert=insert)

def get_direction():
    return IO.get_direction()

def adjacent_directions(_dir):
    return ADJACENT_DIRECTIONS.get(_dir, ((0,0,0,),(0,0,0,),) )

#prompt
# show a message and ask the player for input
# Arguments:
#   x,y:        top-left position of the prompt box
#   w,h:        width, height of the prompt dbox
#   maxw:       maximum length of the response the player can give
#   q:          question to display in the prompt dbox
#   default:    text that is the default response
#   mode:       'text' or 'wait'
#   insert:     whether to begin in Insert mode for the response
#   border:     border style of the dbox
def prompt(x,y, w,h, maxw=1, q='', default='',mode='text',insert=False,border=0):
    #libtcod.console_clear(con_final())
    dbox(x,y,w,h,text=q,
        wrap=True,border=border,con=con_final(),disp='mono')
    result=""
    while (result==""):
        refresh()
        if mode=="wait":
            xf=x+w-1
            yf=y+h-1
        elif mode=="text":
            xf=x
            yf=y+h
        result = Input(xf,yf,maxw,1,default=default,mode=mode,insert=insert)
    return result

#menu
#this menu freezes time until input given.
# Arguments:
#   autoItemize: create keys for your keysItems iterable automagically
#   keysItems can be an iterable or a dict.
#       **If a dict, autoItemize MUST be set to False
#       dict allows you to customize what buttons correspond to which options
def menu(name, x,y, keysItems, autoItemize=True):
    manager=managers.Manager_Menu(name, x,y, window_w(),window_h(), keysItems=keysItems, autoItemize=autoItemize)
    result=None
    while result is None:
        manager.run()
        result=manager.result
    manager.close()
    if result == ' ': return None
    return manager.result
    
    

















        # commented out code below. #











        


    


# Skills
# might not use any skills at all
'''
i = 1
AXES        = i; i+=1;  # 
BLADES      = i; i+=1;  # swords and knives, shortblades
BLUNT       = i; i+=1;  # all blunt weapons, flails and quarterstaffs
MARKSMAN    = i; i+=1;  # bows, throwing, other ranged attacks
MEDS        = i; i+=1;  # medicine
REPAIR      = i; i+=1;  # repair armor, weapons,
SPEECH      = i; i+=1;  # and barter
SPELLS      = i; i+=1;  # spellcasting
STEALTH     = i; i+=1;  # 
TRAPS       = i; i+=1;  # find, set, and create traps

STATMODS_WRESTLING  ={'atk':4,'dfn':2,'dmg':1,'nrg':-3}
STATMODS_SWORDS     ={'atk':2,'dfn':2,'dmg':2,'nrg':-2}
STATMODS_DAGGERS    ={'atk':2,'dfn':2,'dmg':2,'nrg':-3}
STATMODS_AXES       ={'atk':2,'dmg':2,'nrg':-2}
STATMODS_CUDGELS    ={'atk':2,'dmg':2,'nrg':-2}
'''




##    #---------------#
##    #     Lists     #
##    #---------------#
##
##class Lists():
##    creatures   =[]     # living things
##    inanimates  =[]     # nonliving
##    lights      =[]
##    fluids      =[]
##    
##    @classmethod
##    def things(cls):
##        lis1=set(cls.creatures)
##        lis2=set(cls.inanimates)
##        return lis1.union(lis2)
##
### lists functions #
##
##def list_creatures():           return Lists.creatures
##def list_inanimates():          return Lists.inanimates
##def list_things():              return Lists.things()
##def list_lights():              return Lists.lights
##def list_fluids():              return Lists.fluids
##def list_add_creature(ent):     Lists.creatures.append(ent)
##def list_remove_creature(ent):  Lists.creatures.remove(ent)
##def list_add_inanimate(ent):    Lists.inanimates.append(ent)
##def list_remove_inanimate(ent): Lists.inanimates.remove(ent)
##def list_add_light(ent):        Lists.lights.append(ent)
##def list_remove_light(ent):     Lists.lights.remove(ent)
##def list_add_fluid(ent):        Lists.fluids.append(ent)
##def list_remove_fluid(ent):     Lists.fluids.remove(ent)
##

    #------------------------#
    # Stats Functions + vars #
    #------------------------#

# Stat mod Effects are handled entirely by components.

##class Effects:
##    effects={}
##    ID=0
##    # OLD IDEA: individually apply each mod in "mod" and divide / sort by entity, component and stat (variable of component)
##    # *** BETTER IDEA *** :
##     #  when durability of an equipped item drops below certain percentages,
##     #  (constants like 75%, 50%, and 25%, etc.)
##     #  it becomes unequipped and re-equipped, and when you equip
##     #  an item with those percentages of durability you receive
##     #  a penalty to stats that is implemented on-the-fly by
##     #  predetermined constants. THIS WOULD WORK WITH EXISTING SYSTEM.
##    @classmethod
##    def add(cls, ent, mod):
##        # add in new effect
##        Effects.ID+=1
##        Effects.effects.update({Effects.ID : (ent, mod,)})
##        # apply changes to stats
##        compo = Rogue.world.component_for_entity(ent, cmp.Stats)
##        for _var, _modf in mod.items():
##            entCompo.__dict__[_var] += _modf
##        return Effects.ID
##    @classmethod
##    def remove(cls, effID):
##        if not effID in Effects.effects.keys():
##            print("ERROR: failed to remove effect ID ",effID)
##            return False
##        # undo stat modifiers
##        ent,mod = Effects.effects[modID]
##        for compo, data in mod.items():
##            if not Rogue.world.has_component(ent, compo):
##                continue
##            entCompo = Rogue.world.component_for_entity(ent, compo)
##            for _var, _modf in data.items():
##                entCompo.__dict__[_var] -= _modf
##        # remove effect from dict
##        del Effects.effects[effID]
##        return True
####    @classmethod
####    def get(cls, ent, comp, stat):
####        base = Rogue.world.component_for_entity(ent, comp).__dict__[stat]
####        modBonus = Effects.modData.get()
##
##def effect_add(ent,mod):        # Stat mod create
##    effID=Effects.add(ent,mod)
##    return effID
##def effect_remove(modID):   # Stat mod delete
##    Effects.remove(modID)
##
