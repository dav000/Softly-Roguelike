'''
    components.py

    Jacob Wharton
'''


class Draw:
    def __init__(self, char, color, bgcol):
        self.char=char
        self.color=color
        self.bgcol=bgcol
        
class Name:
    def __init__(self, name: str, title="the ", pronouns=("it","it","its",)):
        self.name = name
        self.title = title
        self.pronouns = pronouns

class DeathFunction:
    def __init__(self, func):
        self.func=func

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Creature:
    def __init__(self, gender=None, job=None, faction=None):
        self.gender=gender
        self.job=job
        self.faction=faction

class AI:
    def __init__(self, ai=None):
        self.ai=ai

class Mutable:
    def __init__(self):
        self.mutations=0

class Purse: #Money Container
    def __init__(self, purse=0): #, capacity=99999999
        self.purse=purse

class Seer:
    def __init__(self, sight=20):
        self.sight = sight
        self.fov_map = rog.init_fov_map(FOV_NORMAL)
        self.events = []
        
class Listener:
    def __init__(self, hearing=100):
        self.hearing = hearing
        self.events = []

class Skills:
    def __init__(self, *args):
        self.skills=set()
        for arg in args:
            self.skills.add(arg)

class Ammo:
    def __init__(self, ammoType=0, capacity=1, reloadTime=1, jamChance=0):
        self.ammoType=ammoType
        self.capacity=capacity
        self.reloadTime=reloadTime
        self.jamChance=jamChance
        
class EquipBody:
    def __init__(self):
        self.slot=None #(item, modID)
class EquipHead:
    def __init__(self):
        self.slot=None
class EquipBack:
    def __init__(self):
        self.slot=None
class EquipAmmo:
    def __init__(self):
        self.slot=None
class EquipMainhand:
    def __init__(self):
        self.slot=None
class EquipOffhand:
    def __init__(self):
        self.slot=None
        
class CanEquipInBodySlot:
    def __init__(self, mods): #{component : {var : modf}}
        self.mods=mods
class CanEquipInBackSlot:
    def __init__(self, mods): #{component : {var : modf}}
        self.mods=mods
class CanEquipInHeadSlot:
    def __init__(self, mods): #{component : {var : modf}}
        self.mods=mods
class CanEquipInMainhandSlot:
    def __init__(self, mods): #{component : {var : modf}}
        self.mods=mods
class CanEquipInOffhandSlot:
    def __init__(self, mods): #{component : {var : modf}}
        self.mods=mods
class CanEquipInAmmoSlot:
    def __init__(self, mods): #{component : {var : modf}}
        self.mods=mods

class Usable:
    def __init__(self, funcPC, funcNPC=None):
        self.funcPC=funcPC
        self.funcNPC=funcNPC
class Edible:
    def __init__(self, func, satiation, taste, time=1):
        self.func=func
        self.satiation=satiation
        self.taste=taste
        self.timeToConsume=time
class Quaffable:
    def __init__(self, func, hydration, taste, time=1):
        self.func=func
        self.hydration=hydration
        self.taste=taste
        self.timeToConsume=time
class Openable:
    def __init__(self, isOpen=False, isLocked=False):
        self.isOpen=isOpen
        self.isLocked=isLocked

class Form:
    def __init__(self, mass=0): #, volume, shape
        self.mass=mass

class Inventory:
    def __init__(self, capacity):
        self.capacity=capacity
        self.size=0
        self.data=[]

class FluidContainer:
    def __init__(self, capacity):
        self.capacity=capacity
        self.size=0
        self.data={}

class TakesTurns: #participates in the game by gaining and spending action points
    def __init__(self, speed=1):
        self.ap=0 #action points
        self.speed=speed

class BasicStats:
    def __init__(self, hp=1, mp=1,
                 resFire=0,resBio=0,resElec=0,resPhys=0,
                 material=None,value=0):
        self.hpmax=hp
        self.hp=hp
        self.mpmax=mp
        self.mp=mp
        self.resfire=resFire    #resistances
        self.resbio=resBio
        self.reselec=resElec
        self.resphys=resPhys
        self.material=material
        self.value=value
        self.temp=0             #meters
        self.rads=0
        self.sick=0
        self.expo=0
    
class CombatStats:
    def __init__(self, atk=0,dfn=0,dmg=0,arm=0,rng=0,_pow=0,asp=0,msp=0):
        self.atk=atk    #attack
        self.dfn=dfn    #DV
        self.dmg=dmg    #melee damage
        self.arm=arm    #AV
        self.rng=rng    #range
        self.pow=_pow   #ranged damage
        self.asp=asp    #atk spd
        self.msp=msp    #move spd

class ElementalDamage:
    def __init__(self, element, dmg):
        self.element=element
        self.dmg=dmg

class StatMods:
    def __init__(self, *args, **kwargs):
        self.mods=[]
        for arg in args:
            self.mods.append(arg)
        for k,w in kwargs:
            self.mods.append((k,w,))

class StatusEffects:
    def __init__(self):
        self.effects={}


























