'''
    dialogue.py
    Softly Into the Night, a sci-fi/Lovecraftian roguelike
    Copyright (C) 2020 Jacob Wharton.

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

from const import *
import rogue as rog
import components as cmp
import dice
import random
import math
import messages

class BarterOffer:
    def __init__(self, money=0, items=None):
        self.money=money                    # value of money offered
        self.items=items if items else ()   # tuple of items offered
        
# Player -on- NPC dialogue #

MESSAGES={
TALK_GREETING       :(messages.GREETING,None,),
TALK_INTRODUCTION   :(messages.INTRODUCTION,None,),
TALK_PESTER         :(messages.PESTER,None,),
TALK_ASKQUESTION    :(messages.QUESTION_SUCCESS,messages.QUESTION_FAILURE,),
TALK_GOSSIP         :(messages.GOSSIP_SUCCESS,messages.GOSSIP_FAILURE),
TALK_INTERROGATE    :(messages.INTERROGATE_SUCCESS,messages.INTERROGATE_FAILURE,),
TALK_ASKFAVOR       :(messages.ASKFAVOR_SUCCESS,messages.ASKFAVOR_FAILURE,),
TALK_BEG            :(messages.BEG_SUCCESS,messages.BEG_FAILURE,),
TALK_BARTER         :(messages.BARTER_SUCCESS,messages.BARTER_FAILURE,),
TALK_TORTURE        :(messages.TORTURE_SUCCESS,messages.TORTURE_FAILURE,),
TALK_CHARM          :(messages.CHARM_SUCCESS,messages.CHARM_FAILURE,),
TALK_BOAST          :(messages.BOAST_SUCCESS,messages.BOAST_FAILURE,),
TALK_SMALLTALK      :(messages.SMALLTALK_SUCCESS,messages.SMALLTALK_FAILURE,),
TALK_BRIBERY        :(messages.BRIBERY_SUCCESS,messages.BRIBERY_FAILURE,),
TALK_INTIMIDATION   :(messages.INTIMIDATION_SUCCESS,messages.INTIMIDATION_FAILURE,),
TALK_FLATTERY       :(messages.FLATTERY_SUCCESS,messages.FLATTERY_FAILURE,),
TALK_FLIRTATION     :(messages.FLIRTATION_SUCCESS,messages.FLIRTATION_FAILURE,),
TALK_DEBATE         :(messages.DEBATE_SUCCESS,messages.DEBATE_FAILURE,),
TALK_TAUNT          :(messages.TAUNT_SUCCESS,messages.TAUNT_FAILURE,),
    }

PERSONALITY_STRINGS={
PERSON_NONE                 : "NONE",
PERSON_PROUD                : "proud",
PERSON_LOWSELFESTEEM        : "low-self-esteem",
PERSON_ARGUMENTATIVE        : "argumentative",
PERSON_NONCONFRONTATIONAL   : "non-confrontational",
PERSON_OUTGOING             : "outgoing",
PERSON_SHY                  : "shy",
PERSON_INDEPENDENT          : "independent",
PERSON_CODEPENDENT          : "codependent",
PERSON_BUBBLY               : "bubbly",
PERSON_LOWENERGY            : "low-energy",
PERSON_MOTIVATED            : "motivated",
PERSON_UNMOTIVATED          : "unmotivated",
PERSON_RELAXED              : "relaxed",
PERSON_UPTIGHT              : "uptight",
PERSON_PROACTIVE            : "proactive",
PERSON_APATHETIC            : "apathetic",
    }

def _change_disposition(ent, amt):
    print("ent {} disp change: {}".format(rog.getname(ent), amt))
    rog.world().component_for_entity(ent,cmp.Disposition).disposition += amt

def _get_likes   (personality:int): return PERSONALITIES[personality][1]
def _get_dislikes(personality:int): return PERSONALITIES[personality][2]

# tag substitution
def __cap(string:str): # capitalize first letter
    if len(string)==0: return string
    if len(string)==1: return string.upper()
    return "{}{}".format(string[0].upper(), string[1:])
def __tod(): return rog.get_time_of_day_colloquial()
def __toe(): return random.choice(messages.TERM_OF_ENDEARMENT)
def __gcomp(): return random.choice(messages.COMPLIMENT_GENERIC)
def __wcomp(): return random.choice(messages.COMPLIMENT_WHACKY)
def __comp(): return random.choice(messages.COMPLIMENT)
def __insult(): return random.choice(messages.INSULT)
def __cuss(): return random.choice(messages.CUSS)
def __slur(): return random.choice(messages.SLUR[0])
def __slurs(): return random.choice(messages.SLUR[1])
def __nc(): return random.choice(messages.NAMECALLING[0])
def __ncs(): return random.choice(messages.NAMECALLING[1])
def __aslur(): return __a(__slur())
def __anc(): return __a(__nc())
def __a(string:str): # "a(n) + string"
    if (string[0] == "a"
        or string[0] == "e"
        or string[0] == "i"
        or string[0] == "o"
        or string[0] == "u"):
        n = "n"
    else:
        n = ""
    return "a{n} {string}".format(n=n, string=string)
def __tof():
    pcgender = rog.get_gender(rog.pc())
    return random.choice(messages.TERM_OF_FRIENDSHIP[pcgender])
def __flirt():
    pcgender = rog.get_gender(rog.pc())
    return random.choice(messages.TERM_OF_FLIRTATION[pcgender])
def __icomp():
    # TODO: new dialogue pool for if you're fully naked;
    #   will never call this function in that case.
    lis = rog.list_equipment(rog.pc())
    if lis:
        ent = random.choice(lis)
        return rog.getname(ent)
    else:
        return "pubes"
def _substitute_tags(ent:int, message:str) -> str:
    pc=rog.pc()
    world=rog.world()
    # component data which may or may not exist
    if world.has_component(ent,cmp.Gender):
        npcgg=rog.get_pronoun_generic(ent)
    else:
        npcgg="&person" # temporary (remove & -- that's a flag to indicate where in the code this string is)
    if world.has_component(ent,cmp.Job):
        compo=world.component_for_entity(ent,cmp.Job)
        npcc=CLASSES[compo.job]
    else:
        npcc="hobo"
    #
    return message.format(
        # NPC data
        npcc=npcc,
        npct=TITLES[world.component_for_entity(ent,cmp.Name).title],
        npcn=world.component_for_entity(ent,cmp.Name).name,
        npcgg=npcgg,
        # PC data
        pct=TITLES[world.component_for_entity(pc,cmp.Name).title],
        pcn=world.component_for_entity(pc,cmp.Name).name,
        pcc=CLASSES[world.component_for_entity(pc,cmp.Job).job],
        pcgg=rog.get_pronoun_generic(pc),
        pcgp=rog.get_pronoun_polite(pc),
        pcgs=rog.get_pronoun_subject(pc),
        pcgo=rog.get_pronoun_object(pc),
        pcgi=rog.get_pronoun_informal(pc),
        # other
        nc=__nc(),
        anc=__anc(),
        ncs=__ncs(),
        slur=__slur(),
        slurs=__aslur(),
        aslur=__slurs(),
        cuss=__cuss(),
        flirt=__flirt(),
        tod=__tod(),
        tof=__tof(),
        toe=__toe(),
        gcomp=__gcomp(),
        wcomp=__wcomp(),
        icomp=__icomp(),
        comp=__comp(),
        insult=__insult(),
        # capitalized
        Nc=__cap(__nc()),
        Anc=__cap(__anc()),
        Ncs=__cap(__ncs()),
        Slur=__cap(__slur()),
        Slurs=__cap(__aslur()),
        Aslur=__cap(__slurs()),
        Cuss=__cap(__cuss()),
        Flirt=__cap(__flirt()),
        Tod=__cap(__tod()),
        Tof=__cap(__tof()),
        Toe=__cap(__toe()),
        Gcomp=__cap(__gcomp()),
        Wcomp=__cap(__wcomp()),
        Icomp=__cap(__icomp()),
        Comp=__cap(__comp()),
        Insult=__cap(__insult()),
    )
# end def

    #-----------------------------#
    # response / reaction by NPCS #
    #-----------------------------#

# get possible responses
def __eval(
    personality_string: str, disposition:int, padding:int,
    meta: dict, lis: list
    ):
    if not meta: return
    DMAX = MAX_DISPOSITION
    for k,v in meta.items():
        if (k=="generic" or k==personality_string):
            for disp_ratio, strings in v.items():
                if (disposition >= rog.around(disp_ratio*DMAX)
                    and disposition <= rog.around((disp_ratio+padding)*DMAX)
                    ):
                    for string in strings:
                        lis.append(string)
def _get_possible_responses(
    talk_type:int, personality: int, disposition: int, padding=0.2
    ) -> tuple:
    ''' get a list of possible NPC text dialogue responses given:
        talk_type:   the type of conversation,
        personality: the personality type of the dialogue partner
        disposition: the sentiments the person has towards the PC
        padding:     float, affects size of range of possibilities
        Return both generic and personality-specific responses together.
            Format: (strings for success, strings for failure,)
    '''
    DMAX = MAX_DISPOSITION
    on_success = []
    on_failure = []
    meta_success = MESSAGES[talk_type][0]
    meta_failure = MESSAGES[talk_type][1]
    pid = PERSONALITY_STRINGS[personality]
    __eval(pid, disposition, padding, meta_success, on_success)
    __eval(pid, disposition, padding, meta_failure, on_failure)
    return (on_success, on_failure,)

def _get_response(possible: tuple, success: bool) -> str:
    ''' get response from list of possible responses '''
    lis = possible[0] if success else possible[1]
    response = random.choice(lis)
    return response

def _get_response_full(
    talk_type: int, possible: tuple, success: bool
    ) -> tuple:
    ''' Return a feedback string for failure or success,
        as well as the response by the NPC, given the possible options
    '''
    successfailure = "success" if success else "failure"
    cap = "<{} {}>".format(talk_type, successfailure)
    string = _get_response(possible, success)
    return (cap, string,)

def _response(ent:int, response_type:int):
    __record(ent, response_type)

def __record(ent:int, memory):
    world=rog.world()
    if world.has_component(ent, cmp.ConversationMemory):
        compo=world.component_for_entity(ent, cmp.ConversationMemory)
        compo.memories.append(memory)
        if len(compo.memories) > compo.max_len:
            compo.memories.pop(0)
    else:
        world.add_component(ent, cmp.ConversationMemory(
            MAX_NPC_CONVO_MEMORIES, memory))
# end def
        
def __forget(self, n=-1):
    world=rog.world()
    if world.has_component(ent, cmp.ConversationMemory):
        compo=world.component_for_entity(ent, cmp.ConversationMemory)
        if n==-1:
            compo.memories=[]
        else:
            for _ in range(n): compo.memories.pop(0)
        return True
    return False
# end def

# get reaction / change in disposition
def _get_reaction(
    ent:int, persuasion_type:int, personality:int, disposition:int,
    mx=1, value=0, style=0
    ) -> int:
    ''' get reaction from an entity based on conversational parameters
        mx: multiplier for intensity
        value: value of transaction, if it's a barter or bribe
        Returns >0 values for positive reactions, <0 for negative
            the greater the value, the higher the intensity
    '''
    world=rog.world()
    pc=rog.pc()
    DMAX = MAX_DISPOSITION
    reaction = -20 + dice.roll(20)  # add element of random chance
    
        # ---- initialize ---- #
    
    # get stats for player
    speech = rog.getskill(pc, SKL_PERSUASION)
    speech_penalty = max(0, MAX_SKILL - speech)
    speech_bonus_modf = 0.5 + speech / MAX_SKILL
    speech_penalty_modf = 1.5 - speech / MAX_SKILL
    pc_idn = rog.getms(pc, 'idn')
    pc_bea = rog.getms(pc, 'bea')
    pc_cou = rog.getms(pc, 'cou')
    pc_str = rog.getms(pc, 'str')//MULT_STATS
    pc_int = rog.getms(pc, 'int')//MULT_STATS
    pc_pos = world.component_for_entity(pc, cmp.Position)
    
    # get stats for conversational partner
    ent_sight = rog.getms(ent,'sight')
    ent_cansee = rog.can_see(ent, pc_pos.x,pc_pos.y, ent_sight)
    
    # (perceived) value of the transaction
    value_modf = max(1, (value//MULT_VALUE)*0.1)
    
        # ---- special cases ---- #
    
    # people of high moral standing who never accept a bribe
    if world.has_component(ent, cmp.NeverAcceptsBribes):
        value_modf = 1
        
    # rich people don't care about low-value deals
    if (world.has_component(ent, cmp.Rich) and value < 100*MULT_VALUE):
        value_modf = 0
        if value < 10*MULT_VALUE:
            reaction -= 20
        else:
            reaction -= 10
    
        # ---- intensity ---- #

    # intensity of the conversation based on transaction value    
    intensity = value_modf
    # intensity based on type of conversation / persuasion
    if persuasion_type==TALK_TORTURE:
        intensity = 10 * intensity
    elif persuasion_type==TALK_INTIMIDATION:
        intensity = 5 * intensity
    elif persuasion_type==TALK_INTERROGATE:
        intensity = 5 * intensity
    elif persuasion_type==TALK_BEG:
        intensity = 3 * intensity
    elif persuasion_type==TALK_DEBATE:
        intensity = 2 * intensity
    elif persuasion_type==TALK_FLIRTATION:
        intensity = 2 * intensity
    elif persuasion_type==TALK_ASKFAVOR:
        intensity = 2 * intensity
    elif persuasion_type==TALK_FLATTERY:
        intensity = 1.5 * intensity
    elif persuasion_type==TALK_TAUNT:
        intensity = 1.5 * intensity
    elif persuasion_type==TALK_SMALLTALK:
        intensity = 0.5 * intensity
    elif persuasion_type==TALK_GREETING:
        intensity = 0.25 * intensity
    elif persuasion_type==TALK_BARTER:
        intensity = intensity + 0.1 * (value//MULT_VALUE)
    elif persuasion_type==TALK_BRIBERY:
        intensity = intensity + 0.05 * (value//MULT_VALUE)
    
        # ---- attraction ---- #
    
    attraction = 0
    pc_isfemale = rog.get_gender(pc)=="female"
    pc_ismale = rog.get_gender(pc)=="male"
    
    # Sexual Attraction to Women
    if (ent_cansee and pc_isfemale
        and world.has_component(ent, cmp.AttractedToWomen)
        ):
        intensity += 1
        attraction += pc_bea/4 # note no limits in any direction
    # Sexual Attraction to Men
    elif (ent_cansee and pc_ismale
        and world.has_component(ent, cmp.AttractedToMen)
        ):
        intensity += 1
            # vvv lower this value if women are too easy vvv
        attraction -= 5 # picky when choosing a man
        
        # many stats factor into attraction:
            # intimidation -- inverse quadratic
                # 200 IDN is where it crosses 0
                # max gain from IDN ~10 from ~80 to 120 IDN
        attraction += pc_idn/5 - (0.001 * pc_idn**2)
            # beauty -- matters less than it does when judging women
        attraction += pc_bea/10 # note no limits in any direction
            # strength
        attraction += (pc_str - BASE_STR)/2
            # intelligence
        attraction += (pc_int - BASE_INT)
            # courage
                # max gain from COU 20
        if pc_cou <= 0.5*BASE_COU:
            attraction -= 20
        elif pc_cou <= BASE_COU:
            attraction -= 10
        elif pc_cou >= 2*BASE_COU:
            attraction += 5
        elif pc_cou >= 3*BASE_COU:
            attraction += 10
        elif pc_cou >= 4*BASE_COU:
            attraction += 20
    # end if
        
    # apply attraction reaction
    attraction = rog.around(attraction)
        # flirtation-specific
    if persuasion_type==TALK_FLIRTATION:

            # special cases #
            
        # sorry hun, I'm taken.
        if world.has_component(ent, cmp.Taken):
            reaction -= 20
        
        # I don't do sex.
        if world.has_component(ent, cmp.Ascetic):
            reaction -= 40
        
            #
        
        # attraction matter more for flirtation than other
        #   types of conversation.
        reaction -= 15
        reaction += attraction*2
        speech_mod = 0.2
    else:
        # other
        reaction += attraction
        speech_mod = 0.1
    # end if

    # finally, add speech modifier
    reaction += speech * speech_mod
        
        # ---- compatibility ---- #
    
    # personality compatibility
    pc_personality = rog.get_personality(pc)
    compat = PERSONALITY_COMPATIBILITIES[personality][pc_personality]
    if compat==1:
        reaction -= 20
    elif compat==2:
        reaction -= 10
    elif compat==3:
        pass
    elif compat==4:
        reaction += 10
    elif compat==5:
        reaction += 20
    print("personalities: ent: {}, player: {}".format(
        personality, pc_personality))
    print("personalities: ent: {}, player: {}".format(
        PERSONALITIES[personality][0], PERSONALITIES[pc_personality][0]))
    print("personality compatibility: ", compat)
    
    # likes and dislikes
    likes=_get_likes(personality)
    dislikes=_get_dislikes(personality)
            # persuasion types
    if persuasion_type == likes[0]:
        reaction += ( 0.01*DMAX * speech_bonus_modf * 1 * mx ) * intensity
    elif persuasion_type == dislikes[0]:
        reaction -= ( 0.02*DMAX * speech_penalty_modf * 0.1 * mx ) * intensity
    
    # special cases
    if (world.has_component(ent, cmp.NeverAcceptsBribes)
        and persuasion_type==TALK_BRIBERY):
        reaction = -0.05 * DMAX * mx
    if personality==PERSON_NONCONFRONTATIONAL:
        reaction -= (intensity - 2)
    if persuasion_type==TALK_TORTURE:
        reaction -= 0.1 * DMAX * mx
    if (persuasion_type==TALK_BEG and personality==PERSON_PROUD):
        reaction -= 0.05 * DMAX * mx
    elif (persuasion_type==TALK_INTERROGATE and personality==PERSON_RELAXED):
        reaction -= 0.02 * DMAX * mx
    elif (persuasion_type==TALK_CHARM and personality==PERSON_LOWENERGY):
        reaction -= 0.01 * DMAX * mx
    elif (persuasion_type==TALK_CHARM and personality==PERSON_BUBBLY):
        reaction += 0.01 * DMAX * mx
    elif (persuasion_type==TALK_BOAST and personality==PERSON_PROACTIVE):
        reaction -= 0.01 * DMAX * mx
    elif (persuasion_type==TALK_BOAST and personality==PERSON_MOTIVATED):
        reaction += 0.01 * DMAX * mx
    
    return math.ceil(abs(reaction)) * rog.sign(reaction)
# end def

# get value of a transaction
def _get_transaction_value(
    ent:int, personality:int, disposition:int,
    pc_offer:BarterOffer, npc_offer:BarterOffer,
    style=0
    ) -> int:
    world = rog.world()
    pc = rog.pc()
    DMAX = MAX_DISPOSITION
    total = 0        

    # modifiers
    my_base = 2     # by default, I value my own things more highly
    pc_base = 0.5   # other people's stuff is much less valuable
    my_modf = PERSONALITIES[personality][3]
    pc_modf = PERSONALITIES[personality][4]

    # disposition
    disp_influence = 0.5 # how much does disp. affect perceived value?
    dr = (disposition - 0.5*DMAX)/DMAX
    my_disp_modf = 1 - dr*disp_influence
    pc_disp_modf = 1 + dr*disp_influence

    # speech skill level
    speech_influence = 1 # how much does speech affect perceived value?
    pc_speech = rog.getskill(pc, SKL_PERSUASION)
    my_speech = rog.getskill(ent, SKL_PERSUASION)
    sr = (my_speech - pc_speech)/MAX_SKILL
    my_speech_modf = 1 - sr*speech_influence
    pc_speech_modf = 1 + sr*speech_influence
    
    # PC offer
    total += pc_offer.money # money
    for item in pc_offer.items: # items
        value = world.component_for_entity(item, cmp.Form).value
        total += value*pc_base*pc_modf*pc_disp_modf*pc_speech_modf
    
    # NPC offer
    total += npc_offer.money # money
    for item in npc_offer.items: # items
        value = world.component_for_entity(item, cmp.Form).value
        total -= value*my_base*my_modf*my_disp_modf*my_speech_modf
    
    return int(total)
# end def



    #-------------------#
    # public interface  #
    #-------------------#

def say(ent, string:str):
    ''' converse with an entity and msg out that entity's response '''
    # TODO: elapse time while talking as interruptable delayed action
    # temporary: just do a one-time AP cost for each thing said
    rog.spendAP(rog.pc(), NRG_TALK)
    rog.spendAP(ent, NRG_TALK)
    message = "{}: {}".format(rog.getname(ent), string)
    rog.alert(message) # just in case it doesn't get displayed right away.
    rog.msg(message)
    
def dialogue(ent:int, style=0):
    ''' wrapper dialogue function
        Greet, introduce self if first time meeting,
        Then choose a dialogue type and execute the dialogue.
    '''
    world=rog.world()
    if not world.has_component(ent,cmp.Speaks):
        return False
    dispcompo=world.component_for_entity(ent,cmp.Disposition)
    personality=world.component_for_entity(ent,cmp.Personality).personality

    # greetings
    newdisp = greet(ent, style=style)
    dispcompo.disposition = newdisp
        # introductions
    if not world.has_component(ent,cmp.Introduced):
        response=talk_introduce(ent,personality,dispcompo.disposition,style=style)
    else:
        response=talk_greeting(ent,personality,dispcompo.disposition,style=style)
    print(response)
    say(ent,response)
    
    # dialogue menu
    menu={"*" : "goodbye"}
    _menu={}
    for k,v in PERSUASION.items():
        menu[v[0]] = v[1]
        _menu[v[1]] = k
    entn = world.component_for_entity(ent,cmp.Name)
    opt = rog.menu(
        "{}{}".format(TITLES[entn.title],entn.name),
        rog.view_port_x(),rog.view_port_y(),
        menu,
        autoItemize=False
        )
    if opt==-1: return False
    result = _menu[opt]
    
    # execute the dialogue
    response=_FUNCS[result](ent,personality,dispcompo.disposition,style=style)
    say(ent,response)
    print(response)
    print("New disposition: ", dispcompo.disposition)
    return True
# end def

def greet(ent:int, style=0) -> int: # attempt to init conversation
    pc=rog.pc()
    world=rog.world()
    personality=world.component_for_entity(ent,cmp.Personality).personality
    dispcompo=world.component_for_entity(ent,cmp.Disposition)
    # new disposition after dialogue concludes
    new_disposition = dispcompo.disposition
    # effective disposition during this dialogue (not the new disposition)
    ed = dispcompo.disposition + _get_reaction(
        ent, TALK_GREETING, personality, dispcompo.disposition,
        style=style, mx=0.5
        )
    new_disposition += rog.sign(ed) # just nudge disposition
    fdisp = ed / MAX_DISPOSITION
    
    # roll for speech success
    speech_bonus = rog.getskill(pc, SKL_PERSUASION)
    roll=dice.roll(100) + speech_bonus
    if fdisp < 0.4:
        roll -= 8/fdisp
    else:
        roll += 100*fdisp
    # cases
    if roll <= 0:
        _response(ent, RESPONSE_REJECTION)
    else:
        _response(ent, RESPONSE_ACCEPT)
    return new_disposition
# end def



    #---------------------------------#
    # persuasion / conversation types #
    #---------------------------------#

def _talk(ent:int, success:bool, ttype:int, personality:int, disposition:int, padding=0.2) -> str:
    possible=_get_possible_responses(ttype,personality,disposition,padding)
    response=_get_response(possible, success)
    return _substitute_tags(ent, response)

def talk_greeting(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_GREETING
    return _talk(ent, True, ttype, personality, disposition, padding=0.2)

def talk_introduce(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_INTRODUCTION
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    rog.world().add_component(ent,cmp.Introduced())
    return _talk(ent, True, ttype, personality, disposition, padding=0.1)

def talk_barter(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_BARTER
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition, padding=1)

def talk_question(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_ASKQUESTION
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_interrogate(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_INTERROGATE
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_gossip(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_GOSSIP
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_torture(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_TORTURE
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_askfavor(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_ASKFAVOR
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_beg(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_BEG
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)
    
def talk_charm(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_CHARM
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_boast(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_BOAST
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_smalltalk(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_SMALLTALK
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition, padding=1)

def talk_bribe(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_BRIBERY
    pc_offer = BarterOffer(money, items)
    npc_offer = BarterOffer()
    value = _get_transaction_value(
        ent, personality, disposition, pc_offer, npc_offer, style=style
        )
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_intimidate(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_INTIMIDATION
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition, padding=1)

def talk_flatter(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_FLATTERY
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_flirt(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_FLIRTATION
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_debate(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_DEBATE
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, success, ttype, personality, disposition)

def talk_pester(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_PESTER
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    return _talk(ent, True, ttype, personality, disposition, padding=1)

def talk_taunt(ent:int, personality:int, disposition:int, style=0) -> str:
    ttype = TALK_TAUNT
    reaction=_get_reaction(ent, ttype, personality, disposition, style=style)
    _change_disposition(ent, reaction)
    success = (reaction > 0)
    return _talk(ent, True, ttype, personality, disposition, padding=1)

    #-----------------------------------------------#
    # constants (relying on the above declarations) #
    #-----------------------------------------------#

_FUNCS={
TALK_ASKQUESTION    : talk_question,
TALK_INTERROGATE    : talk_interrogate,
TALK_ASKFAVOR       : talk_askfavor,
TALK_GOSSIP         : talk_gossip,
TALK_BEG            : talk_beg,
TALK_BARTER         : talk_barter,
TALK_TORTURE        : talk_torture,
TALK_CHARM          : talk_charm,
TALK_BOAST          : talk_boast,
TALK_SMALLTALK      : talk_smalltalk,
TALK_BRIBERY        : talk_bribe,
TALK_INTIMIDATION   : talk_intimidate,
TALK_FLATTERY       : talk_flatter,
TALK_FLIRTATION     : talk_flirt,
TALK_DEBATE         : talk_debate,
TALK_PESTER         : talk_pester,
TALK_TAUNT          : talk_taunt,
    }


#--------------------------END OF CODE------------------------------#





















