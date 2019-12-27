'''
    action.py
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
'''

# wrapper for things that creatures can do in the game
#   - actions cost energy
# PC actions are for the player object to give feedback
#   - (if you try to eat something inedible, it should say so, etc.)
#

import math

from const import *
import rogue as rog
import components as cmp
import dice
import maths
##import entities




dirStr=" <hjklyubn.>"


# pickup
# grab an item from the game world, removing it from the grid
def pickup_pc(pc):
    world = rog.world()
    pos = world.component_for_entity(pc, cmp.Position)
    pcx = pos.x
    pcy = pos.y
    rog.alert("Pick up what?{d}".format(d=dirStr))
    args=rog.get_direction()
    if not args:
        rog.alert()
        return
    dx,dy,dz=args
    xx,yy = pcx + dx, pcy + dy
    
    things=rog.thingsat(xx,yy)
    if pc in things: #can't pick yourself up.
        things.remove(pc)

    choice=None
    if len(things) > 1:
        rog.alert("There are multiple things here. Pick up which item?")
        choices = [] #["all",] #should player be able to pickup multiple things at once? Maybe could be a delayed action?
        for thing in things:
            choices.append(thing)
        choice=rog.menu(
            "pick up", rog.view_port_x()+2, rog.view_port_y()+2, choices
            )
    else:
        if things:
            choice=things[0]

    if (choice and not choice == "all"):

        if choice == K_ESCAPE:
            return
        
        #thing is creature! You can't pick up creatures :( or can you...?
        if world.has_component(choice, cmp.Creature):
            rog.alert("You can't pick that up!")
            return
        #thing is on fire, prompt user & burn persistent rogues
        if rog.on(choice,FIRE):
            answer=""
            while True:
                answer=rog.prompt(0,0,rog.window_w(),1,maxw=1,
                    q="That thing is on fire! Are you sure? y/n",
                    mode='wait',border=None)
                answer=answer.lower()
                if answer == "y" or answer == " " or answer == K_ENTER:
                    rog.alert("You burn your hands!")
                    rog.burn(pc, FIRE_BURN)
                    rog.hurt(pc, FIRE_PAIN)
                    rog.damage(pc, FIRE_DAMAGE)
                    break
                elif answer == "n" or answer == K_ESCAPE:
                    return
        # put in inventory
        pocketThing(pc, choice)
##    elif choice == "all":
##        for tt in things:
##            pocketThing(pc, tt)
    else:
        rog.alert("There is nothing there to pick up.")


def inventory_pc(pc):
    world=rog.world()
##    assert world.has_component(pc, cmp.Inventory), "PC missing inventory"
    pcInv = world.component_for_entity(pc, cmp.Inventory)
    pcn = world.component_for_entity(pc, cmp.Name)
    x=0
    y=rog.view_port_y()
#   items menu
    item=rog.menu("{}{}'s Inventory".format(
        pcn.title,pcn.name), x,y, pcInv.items)
    
#   viewing an item
    if not item == -1:
        itemn = world.component_for_entity(item, cmp.Name)
##        itemn = world.component_for_entity(item, cmp.Name)
        keysItems={}
        
    #   get available actions for this item...
        if world.has_component(item, cmp.Edible):
            keysItems.update({"E":"Eat"})
        if world.has_component(item, cmp.Quaffable):
            keysItems.update({"q":"quaff"})
        if world.has_component(item, cmp.Equipable):
            keysItems.update({"e":"equip"})
            # throwables - subset of equipables
            if world.component_for_entity(item, cmp.Equipable).equipType == EQ_MAINHAND:
                keysItems.update({"t":"throw"})
        if world.has_component(item, cmp.Usable):
            keysItems.update({"u":"use"})
        if world.has_component(item, cmp.Openable):
            keysItems.update({"o":"open"})
        keysItems.update({"x":"examine"})
        keysItems.update({"d":"drop"})
        #
        
        opt=rog.menu(
            "{}".format(itemn.name), x,y,
            keysItems, autoItemize=False
        )
        #print(opt)
        if opt == -1: return
        opt=opt.lower()
        
        rmg=False
        if   opt == "drop":     rmg=True; drop_pc(pc, item)
        elif opt == "equip":    rmg=True; equip_pc(pc, item)
        elif opt == "throw":    rmg=True; target_pc(pc, item)
        elif opt == "eat":      rmg=True; eat_pc(pc, item)
        elif opt == "quaff":    rmg=True; quaff_pc(pc, item)
        elif opt == "use":      rmg=True; use_pc(pc, item)
        elif opt == "examine":  rmg=True; examine_pc(pc, item)
        
        if rmg: rog.drain(pc, 'nrg', NRG_RUMMAGE)
#

def drop_pc(pc,item):
    rog.alert("Place {i} where?{d}".format(d=dirStr,i=item.name))
    args=rog.get_direction()
    if not args: return
    dx,dy,dz=args
    
    if not drop(pc, item):
        rog.alert("You can't put that there!")

def open_pc(pc):
    # pick what to open/close
    rog.alert("Open what?{d}".format(d=dirStr))
    args=rog.get_direction()
    if not args: return
    dx,dy,dz=args
    pos = rog.world().component_for_entity(pc, cmp.Position)
    xto = pos.x + dx
    yto = pos.y + dy
    # do the open/close action
    success = openClose(pc, xto, yto)
    if success:
        pass
    else:
        rog.alert("It won't open.")
    rog.update_game()

def sprint_pc(pc):
    #if sprint cooldown elapsed
    if not rog.world().has_component(pc, cmp.StatusTired):
        sprint(pc)
    else:
        rog.alert("You're too tired to sprint.")

def target_pc(pc):
    target = IO.aim_find_target()
    if target:
        pass

def examine_self_pc(pc):
    choices=['body (whole body)']
    
    ans=rog.menu(item=rog.menu("Examine what?".format(
        pcn.title,pcn.name), x,y, choices))

def equip_pc(pc,item):
    pass
    #fornow, just wield it THIS SCRIPT NEEDS SERIOUS WORK*****>>>>...
    '''
    rog.drain(pc, 'nrg', NRG_RUMMAGE + NRG_WIELD)
    if rog.has_equip(pc, item):
        if rog.deequip(pc, item.equipType):
            rog.msg("{t}{n} wields {i}.".format(t=pc.title,n=pc.name,i=item.name))
        else: rog.alert("You are already wielding something in that hand.")
    else: rog.wield(pc,item)'''

def examine_pc(pc, item):
    rog.drain(pc, 'nrg', NRG_EXAMINE)
    rog.dbox(0,0,40,30, thing.DESCRIPTIONS[item.name])

def rest_pc(pc):
    turns=rog.prompt(0,0,rog.window_w(),1,maxw=3,
                     q="How long do you want to rest? Enter number of turns:",
                     mode='wait',border=None)
    for t in range(turns):
        rog.queue_action(pc, wait)

# item use functions

##def use_towel_pc(pc, item):
##    world=rog.world()
##    options={}
####    options.update({"W" : "wrap around"}) # THESE SHOULD ALL BE COVERED BY THE EQUIPABLE COMPONENTS.
####    options.update({"w" : "wield"})
####    options.update({"h" : "wear on head"})
##    options.update({"d" : "dry [...]"})
##    options.update({"l" : "lie on"})
##    options.update({"x" : "wave"})
####    options.update({"s" : "sail"})
##    choice=rog.menu("use towel",0,0,options,autoItemize=False)
##            
##    if choice == "dry":
##        answer=rog.prompt(0,0,rog.window_w(),1,maxw=1,
##                    q="Dry what?",
##                    mode='wait',border=None)
##        # TODO: logic for what you want to dry...
####        if answer=='self' # how to handle this??????
##        #itSeemsCleanEnough=...
##        if ( itSeemsCleanEnough and not rog.on(item, WET) ):
##            pass #dry self
##        else:
##            if not itSeemsCleanEnough:
##                rog.alert("It doesn't seem clean enough.")
##            elif world.component_for_entity(item,cmp.Wets).wetness > 0:
##                rog.alert("It's too wet.")
                

################################################

#wait
#just stand still and do nothing
#recover your Action Points to their maximum
def wait(ent):
    rog.world().component_for_entity(ent, cmp.Actor).ap = 0

def cough(ent):
    world = rog.world()
    pos = world.component_for_entity(ent, cmp.Position)
    entn = world.component_for_entity(ent, cmp.Name)
    wait(ent)
    rog.event_sound(pos.x,pos.y, SND_COUGH)
    rog.event_sight(pos.x,pos.y, "{t}{n} doubles over coughing.".format(
        t=entn.title,n=entn.name))

def intimidate(ent):
    world=rog.world()
    stats=world.component_for_entity(ent, cmp.Stats)
    pos=world.component_for_entity(ent, cmp.Position)
    entn=world.component_for_entity(ent, cmp.Name)
    fear=rog.getms(ent, 'intimidation')
    world.add_component(ent, cmp.StatusFrightening(10))
    rog.event_sound(pos.x,pos.y,SND_ROAR)
    rog.event_sight(pos.x,pos.y,"{t}{n} makes an intimidating display.".format(
        t=entn.title,n=entn.name))

#use
#"use" an item, whatever that means for the specific item
def use(obj, item):
    pass


#pocket thing
#a thing puts a thing in its inventory
def pocketThing(ent, item):
##    if not item: return False
    world = rog.world()
    rog.drain(ent, 'nrg', NRG_POCKET)
    rog.give(ent, item)
    rog.release_entity(item)
    entn = world.component_for_entity(ent, cmp.Name)
    itemn = world.component_for_entity(item, cmp.Name)
    rog.msg("{t}{n} packs {ti}{ni}.".format(
        t=entn.title,n=entn.name,ti=itemn.title,ni=itemn.name))
##    return True

def drop(ent, item):
    world = rog.world()
    pos = world.component_for_entity(ent, cmp.Position)
    dx=0; dy=0; # TODO: code AI to find a place to drop item
    if not rog.wallat(pos.x+dx,pos.y+dy):
        rog.drain(ent, 'nrg', NRG_RUMMAGE)
        rog.drop(ent,item, dx,dy)
        entn = world.component_for_entity(ent, cmp.Name)
        itemn = world.component_for_entity(item, cmp.Name)
        rog.msg("{t}{n} drops {ti}{ni}.".format(
            t=entn.title,n=entn.name,ti=itemn.title,ni=itemn.name))
        return True
    else:
        return False


#quaff
#drinking is instantaneous action
def quaff(ent, drink): 
    world = rog.world()
    pos = world.component_for_entity(ent, cmp.Position)
    quaffable=world.component_for_entity(drink, cmp.Quaffable)
    entn = world.component_for_entity(ent, cmp.Name)
    drinkn = world.component_for_entity(drink, cmp.Name)
    
    #quaff function
    quaffable.func(ent)
    
    # TODO: do delayed action instead of immediate action.
    rog.drain(ent, 'nrg', quaffable.timeToConsume)
    rog.givemp(ent, quaffable.hydration)

    #events - sight
    if ent == rog.pc():
        rog.msg("It tastes {t}".format(t=quaffable.taste))
    else:
        rog.event_sight(pos.x,pos.y, "{t}{n} quaffs a {p}.".format(
            t=entn.title, n=entn.name, p=drinkn.name))
    #events - sound
    rog.event_sound(pos.x,pos.y, SND_QUAFF)
    # TODO: make sure this works...
    world.delete_entity(drink)


def move(ent,dx,dy, ap=1.0,sta=1.0):  # actor locomotion
    '''
        move: generic actor locomotion
        Returns True if move was successful, else False
        Parameters:
            ent : entity that's moving
            dx  : change in x position
            dy  : change in y position
            ap  : Action Point cost multiplier value
            sta : Stamina cost multiplier value
    '''
    # init
    world = rog.world()
    pos = world.component_for_entity(ent, cmp.Position)
    xto = pos.x + dx
    yto = pos.y + dy
    terrainCost = rog.cost_move(pos.x, pos.y, xto, yto, None)
    if terrainCost == 0:
        return False        # 0 means we can't move there
    msp=rog.getms(ent,'msp')
    actor = world.component_for_entity(ent, cmp.Actor)
    #
    
    # AP cost
    mult = 1.414 if (dx + dy) % 2 == 0 else 1  # diagonal extra cost
    ap_cost = rog.around(ap * NRG_MOVE * mult * terrainCost / max(1, msp))
    actor.ap -= max(1, ap_cost)

    # Stamina cost ( TODO )
##    sta_cost = (sta * STA_MOVE)
##    rog.sap(ent, sta_cost)

    # Satiation, hydration, fatigue (TODO FOR ALL ACTIONS!)
    
    # perform action
    rog.port(ent, xto, yto)
    return True

def openClose(ent, xto, yto):
    #TODO: containers, test doors
    world = rog.world()
    actor = world.component_for_entity(ent, cmp.Actor)
    entn = world.component_for_entity(ent, cmp.Name)
    #open containers
    #close containers
    #open doors
    if rog.tile_get(xto,yto) == DOORCLOSED:
        actor.ap -= NRG_OPEN
        rog.tile_change(xto,yto, DOOROPEN)
        ss = "opened a door"
        rog.msg("{t}{n} {ss}.".format(t=entn.title,n=entn.name,ss=ss))
        return True
    #close doors
    if rog.tile_get(xto,yto) == DOOROPEN:
        actor.ap -= NRG_OPEN
        rog.tile_change(xto,yto, DOORCLOSED)
        ss = "closed a door"
        rog.msg("{t}{n} {ss}.".format(t=entn.title,n=entn.name,ss=ss))
        return True
    return False

def sprint(ent):
    #if sprint cooldown elapsed
    rog.world().add_component(ent, cmp.Sprint(SPRINT_TIME))
    entn = rog.world().component_for_entity(ent, cmp.Name)
    rog.msg("{n} begins sprinting.".format(n=entn.name))


def _strike(attkr,dfndr,aweap,dweap,adv=0,power=0, counterable=False):
    '''
        strike the target with your primary weapon or body part
            this in itself is not an action -- requires no AP
        (this is a helper function used by combat actions)
    '''
    # init
    hit=killed=crit=ctrd=grazed=False
    pens=trueDmg=rol=0
    feelStrings=[]
    
        # get the data we need
    world = rog.world()
    
    # attacker stats
    acc =   rog.getms(attkr,'atk')//MULT_STATS
    dmg =   rog.getms(attkr,'dmg')//MULT_STATS
    pen =   rog.getms(attkr,'pen')//MULT_STATS
    asp =   rog.getms(attkr,'asp')//MULT_STATS
    
    # defender stats
    dv =    rog.getms(dfndr,'dfn')//MULT_STATS
    prot =  rog.getms(dfndr,'pro')//MULT_STATS
    arm =   rog.getms(dfndr,'arm')//MULT_STATS
    ctr =   rog.getms(dfndr,'ctr')//MULT_STATS
    resphys = rog.getms(dfndr,'resphys')
    
        # roll dice, calculate hit or miss
    rol = dice.roll(CMB_ROLL_ATK)
    hitDie = rol + acc + adv - dv
    if (rog.is_pc(dfndr) and rol==1): # when player is attacked, a roll of 1/20 always results in a miss.
        hit=False
    elif (rog.is_pc(attkr) and rol==20): # when player attacks, a roll of 20/20 always results in a hit.
        hit=True
    elif (hitDie >= 0): # normal hit roll, D&D "to-hit/AC"-style
        hit=True
    else: # miss
        hit=False
    
    # perform the attack
    if hit:
        grazed = (hitDie==0)
            # counter-attack
        if counterable:
            # TODO: make sure defender is in range to counter-attack
            dfndr_ready = rog.on(dfndr,CANCOUNTER)
            if dfndr_ready:
                if (dice.roll(100) <= ctr):
                    dweap = rog.dominant_arm(dfndr).hand.slot.item
                    _strike(dfndr, attkr, dweap, aweap, power=0, counterable=False)
                    rog.makenot(dfndr,CANCOUNTER)
                    ctrd=True
        
        if not grazed: # can't penetrate if you only grazed them
                # penetration (calculate armor effectiveness)
            while (pen-prot-(6*pens) >= dice.roll(6)):
                pens += 1   # number of penetrations ++
            armor = rog.around(arm * (0.5**pens))
        
            # calculate physical damage #

        # additional damage from strength
        #   (TODO!!!!)
        
        if grazed:
            dmg = dmg*0.5
        resMult = 0.01*(100 - resphys)     # resistance multiplier
        rmp = 1 #CMB_MDMGMIN + (CMB_MDMG*random.random()) # random multiplier -> variable damage
        rawDmg = dmg - armor
        
        # bonus damage
##        dfndrArmored = False
##        if world.has_component(dfndr, cmp.EquipBody):
##            item=world.component_for_entity(dfndr, cmp.EquipBody).item
##            if item is not None:
##                if rog.on(item, ISHEAVYARMOR): # better way to do this?
##                    dfndrArmored = True
##        if dfndrArmored: # TODO: implement this and bonus to flesh!!!
##            if world.has_component(aweap, cmp.BonusDamageToArmor):
##                compo=world.component_for_entity(aweap, cmp.BonusDamageToArmor)
##                bonus = compo.dmg
##                rawDmg += bonus
        
        trueDmg = rog.around( max(0,rawDmg*resMult*rmp) ) # apply modifiers
        
        # extra critical damage: % based on Attack and Penetration
        # you need more atk and more pen than usual to score a crit.
        if (hitDie >= dice.roll(20) and pen-prot >= 12 + dice.roll(12) ):
            # critical hit!
            if world.has_component(aweap,cmp.WeaponSkill):
                skillCompo=world.component_for_entity(aweap,cmp.WeaponSkill)
                critMult = WEAPONCLASS_CRITDAMAGE[skillCompo.skill]
            else:
                critMult = 0.2
            # critical hits do a percentage of target's max HP in damage
            trueDmg += rog.getms(dfndr, 'hpmax')*critMult
            crit=True
        
            # calculate elemental damage
        # TODO: implement elemental damage!!!!
        if (world.has_component(aweap,cmp.ElementalDamageMelee)):
            elements=world.component_for_entity(aweap,cmp.ElementalDamageMelee).elements
        else:
            elements={}
            
            # deal damage, physical and elemental #

        rog.damage(dfndr, trueDmg//10)
        for element, elemDmg in elements.items():
            if grazed: elemDmg = elemDmg*0.5
            if element == ELEM_FIRE:
                rog.burn(dfndr, elemDmg)
                feelStrings.append("burns!")
            elif element == ELEM_BIO:
                rog.disease(dfndr, elemDmg)
            elif element == ELEM_ELEC:
                rog.electrify(dfndr, elemDmg)
                feelStrings.append("zaps!")                                                                                                                                                                                                                     # I love you Krishna
            elif element == ELEM_CHEM:
                rog.exposure(dfndr, elemDmg)
                feelStrings.append("stings!")
            elif element == ELEM_RADS:
                rog.irradiate(dfndr, elemDmg)
            elif element == ELEM_IRIT:
                rog.irritate(dfndr, elemDmg)
            elif element == ELEM_COLD:
                rog.cool(dfndr, elemDmg)
            elif element == ELEM_PAIN:
                if trueDmg <= 0: continue   # if dmg==0, no pain is felt
                rog.hurt(dfndr, elemDmg)
            elif element == ELEM_BLEED:
                if trueDmg <= 0: continue   # if dmg==0, no bleeding
                rog.bleed(dfndr, elemDmg)
            elif element == ELEM_RUST:
                rog.rust(dfndr, elemDmg)
            elif element == ELEM_ROT:
                rog.rot(dfndr, elemDmg)
            elif element == ELEM_WET:
                rog.wet(dfndr, elemDmg)
                
            # deal damage to the armor
        # TODO: get damage to armor based on material of armor/weapon
        # AND based on the TYPE of weapon. Daggers do little dmg to armor
        # while warhammers and caplock guns do tons of damage to armor.
            # Rather than storing armor-damage as a variable of weapons,
            # it is related to what SKILL is needed for the weapon.
        #
        # return info for the message log
        killed = rog.on(dfndr,DEAD) #...did we kill it?
    return (hit,pens,trueDmg,killed,crit,rol,ctrd,feelStrings,grazed,)


def fight(attkr,dfndr,adv=0,power=0):
    '''
    Combat function. Engage in combat:
    # Arguments:
        # attkr:    attacker (entity initiating combat)
        # dfndr:    defender (entity being attacked by attacker)
        # adv:      advantage attacker has over defender (bonus to-hit)
        # power:    amount of umph to use in the attack
        
        TODO: implement this!
        # power:    how much force putting in the attack?
            0 == use muscles only in the attacking limb(s)
            1 == use muscles in whole body (offensive)
                *leaves those body parts unable to provide defense
                 until your next turn
    '''
    
##    TODO: when you attack, look at your weapon entity to get:
        #-material of weapon
        #-flags of weapon
        
    # setting up
    world = rog.world()
    aactor = world.component_for_entity(attkr, cmp.Actor)
    apos = world.component_for_entity(attkr, cmp.Position)
    dpos = world.component_for_entity(dfndr, cmp.Position)
    aname=world.component_for_entity(attkr, cmp.Name)
    dname=world.component_for_entity(dfndr, cmp.Name)

    # weapons of the combatants
    aweap = rog.dominant_arm(attkr).hand.slot.item
    dweap = rog.dominant_arm(dfndr).hand.slot.item

    # ensure you have the proper amount of Stamina
                 #(TODO)
    
    # strike!
    counterable = True # TODO: this is affected by range/reach!
    _rd = _strike(
        attkr, dfndr, aweap, dweap,
        adv=adv, power=power, counterable=counterable
        )
    hit,pens,trueDmg,killed,crit,rol,ctrd,feelStrings,grazed = _rd
    
    # AP cost
    aactor.ap -= rog.around( NRG_ATTACK * AVG_SPD / max(1, asp) )

    # stamina cost
    if aweap:
        equipable = world.component_for_entity(aweap, cmp.EquipableInHandSlot)
        rog.sap(attkr, equipable.stamina)
    else:
        rog.sap(attkr, 12) # TEMPORARY
                 
    # metabolism
    rog.metabolism(attkr, CALCOST_HEAVYACTIVITY)
    
    # finishing up
    message = True # TEMPORARY!!!!
    a=aname.name; n=dname.name; at=aname.title; dt=dname.title;
    x='.'; ex="";
    dr="d{}".format(CMB_ROLL_ATK) #"d20"
        # make a message describing the fight
    if message:
        # TODO: show messages for grazed, crit, counter, feelStrings
        if hit==False:
            v="misses"
            if rog.is_pc(attkr):
                ex=" ({dr}:{ro})".format(dr=dr, ro=rol)
        else: # hit
            if rog.is_pc(attkr):
                ex=" ({dr}:{ro}|{dm}x{p})".format(
                    dr=dr, ro=rol, dm=trueDmg, p=pens )
            if killed:
                v="kills"
            else:
                if grazed:
                    v="grazes"
                else:
                    v = "crits" if crit else "hits"
        if ctrd:
            m = "and {dt}{n} counters".format(dt=dt,n=n)
        rog.event_sight(
            dpos.x,dpos.y,
            "{at}{a} {v} {dt}{n}{ex}{m}{x}".format(
                a=a,v=v,n=n,at=at,dt=dt,ex=ex,x=x,m=m )
        )
        rog.event_sound(dpos.x,dpos.y, SND_FIGHT)
#


# other actions #

#TODO: UPDATE THIS FUNCTION
def explosion(bomb):
    rog.msg("{t}{n} explodes! <UNIMPLEMENTED>".format(t=bomb.title, n=bomb.name))
    '''
    con=libtcod.console_new(ROOMW, ROOMH)
    fov=rog.fov_init()
    libtcod.map_compute_fov(
        fov, bomb.x,bomb.y, bomb.r,
        light_walls = True, algo=libtcod.FOV_RESTRICTIVE)
    for x in range(bomb.r*2 + 1):
        for y in range(bomb.r*2 + 1):
            xx=x + bomb.x - bomb.r
            yy=y + bomb.y - bomb.r
            if not libtcod.map_is_in_fov(fov, xx,yy):
                continue
            if not rog.is_in_grid(xx,yy): continue
            dist=maths.dist(bomb.x,bomb.y, xx,yy)
            if dist > bomb.r: continue
            
            thing=rog.thingat(xx, yy)
            if thing:
                if rog.on(thing,DEAD): continue
                
                if thing.isCreature:
                    decay=bomb.dmg/bomb.r
                    dmg= bomb.dmg - round(dist*decay) - thing.stats.get('arm')
                    rog.damage(thing, dmg)
                    if dmg==0: hitName="not damaged"
                    elif rog.on(thing,DEAD): hitName="killed"
                    else: hitName="hit"
                    rog.msg("{t}{n} is {h} by the blast.".format(
                        t=thing.title,n=thing.name,h=hitName) )
                else:
                    # explode any bombs caught in the blast
                    if (thing is not bomb
                            and hasattr(thing,'explode')
                            and dist <= bomb.r/2 ):
                        thing.timer=0
                        '''
    
























#use
#"use" an item, whatever that means for the specific item
##def use_pc(obj, item):
##    item.useFunctionPlayer(obj)


# player only actions #

##def bomb_pc(pc): # drop a lit bomb
##    rog.alert("Place bomb where?{d}".format(d=dirStr))
##    args=rog.get_direction()
##    if not args: return
##    dx,dy,dz=args
##    xx,yy=pc.x + dx, pc.y + dy
##    
##    if not rog.thingat(xx,yy):
##        weapons.Bomb(xx,yy, 8)
##        rog.drain(pc, 'nrg', NRG_BOMB)
##        rog.msg("{t}{n} placed a bomb.".format(t=pc.title,n=pc.name))
##    else:
##        rog.alert("You cannot put that in an occupied space.")

''' SCRIPT TO SHOW BOMB DAMAGE AND DECAY

            decay=bomb.dmg/bomb.r
            dmg= bomb.dmg - round(dist*decay)
            libtcod.console_put_char_ex(con, xx, yy, chr(dmg+48), WHITE,BLACK)
            
    libtcod.console_blit(con,rog.view_x(),rog.view_y(),rog.view_w(),rog.view_h(),
                         0,rog.view_port_x(),rog.view_port_y())
    libtcod.console_flush()
    r=rog.Input(0,0,mode="wait")
    '''


'''if (not killed and not hpmax_before == dfndr.stats.hpmax):
            x=", injuring {pronoun}".format(pronoun=pronoun)
'''

'''
#TEST
if (obj.x==x and obj.y==y):
    obj.stats.sight +=1
    if obj.stats.sight >= 9:
        obj.stats.sight=9
else: obj.stats.sight = 5
#'''
