import json, sys

with open('encounters.json') as json_file:
    encounters = json.load(json_file)

DEBUG = False
OFFENSE_STAT = 'offense'
DEFENCE_STAT = 'defense'
LIFE_STAT = 'life'
GOLD_STAT = 'gold'

class Hero:
    stats = {}
    keys = {}
    inventory = {}
    altar_uses = 0

hero = Hero()

def debug(message):
    if DEBUG:
        print "DEBUG: " + message

def print_stats():
    print "Stats={},keys={},inventory={}".format(hero.stats, hero.keys, hero.inventory)

def simple_encounter(encounter, args):
    if 'levelled' in encounter and encounter['levelled']:
        multiplier = int(args[1])
    else:
        multiplier = 1
    for stat in [OFFENSE_STAT, DEFENCE_STAT, LIFE_STAT, GOLD_STAT]:
        if stat in encounter:
            hero.stats[stat] += encounter[stat] * multiplier
            if hero.stats[stat] < 0:
                raise Exception("Insufficient {stat}!".format(stat=stat))
    if 'keys' in encounter:
        for color in encounter['keys']:
            hero.keys[color] += encounter['keys'][color]
            if hero.keys[color] < 0:
                raise Exception("Not enough {} keys!".format(color))
    if 'inventory' in encounter:
        for item in encounter['inventory']:
            if item in hero.inventory:
                hero.inventory[item] += encounter['inventory'][item]
            else:
                hero.inventory[item] = encounter['inventory'][item]
            if hero.inventory[item] < 0:
                raise Exception("Not enough uses of {}".format(item))

def monster_encounter(encounter, args):
    hero_offense = hero.stats[OFFENSE_STAT]
    if 'bane' in encounter and encounter['bane'] in hero.inventory:
        hero_offense *= 2
    if encounter[DEFENCE_STAT] >= hero_offense:
        raise Exception("Not enough offensive power to attack this monster!")
    monster_life = encounter[LIFE_STAT]

    def monster_attack():
        hero.stats[LIFE_STAT] -= max(encounter[OFFENSE_STAT] - hero.stats[DEFENCE_STAT], 0)
        if hero.stats[LIFE_STAT] <= 0:
            hero.stats[LIFE_STAT] = 0
            raise Exception("Died!")

    if len(args) > 1 and args[1] == 'ambush':
        monster_attack()

    in_battle = True
    while in_battle:
        monster_life -= max(hero_offense - encounter[DEFENCE_STAT], 0)
        if monster_life <= 0:
            monster_life = 0
            in_battle = False
        if in_battle:
            monster_attack()
    hero.stats[GOLD_STAT] += encounter[GOLD_STAT]

def altar_encounter(encounter, args):
    if len(args) < 3:
        raise Exception("Usage: altar <multiplier> <stat>")
    """
    Altar cost starts at 20 and increases with each usage.
    The increment increases by 20 each time.
    Thus, the cost is 20, then 40, 80, 140, 220, 320, 440, etc.

    Altar effectiveness depends on the floor.
    An altar in floors 1-10 gives 2 attack or 4 defence,
    an altar in floors 11-20 gives 4 attack or 8 defence, etc.
    """
    def altar_cost(altar_uses):
        if altar_uses == 0:
            return 20
        else:
            return altar_cost(altar_uses - 1) + (altar_uses * 20)

    cost = altar_cost(hero.altar_uses)
    debug("Altar will cost {} gold.".format(cost))
    if hero.stats[GOLD_STAT] >= cost:
        hero.stats[GOLD_STAT] -= cost
        hero.altar_uses += 1
    else:
        raise Exception("Not enough gold to use altar!")
    multiplier = int(args[1])
    stat = args[2]
    if stat == OFFENSE_STAT:
        hero.stats[stat] += encounter[OFFENSE_STAT] * multiplier
    elif stat == DEFENCE_STAT:
        hero.stats[stat] += encounter[DEFENCE_STAT] * multiplier
    elif stat == LIFE_STAT:
        hero.stats[stat] += encounter[LIFE_STAT] * multiplier
    else:
        raise Exception("Unrecognised altar upgrade: {}, must be offense/defense/life".format(stat))

def do_encounter_chain(encounter):
    for sub_encounter_line in encounter['sub-encounters']:
        do_encounter_line(sub_encounter_line)

def do_encounter(args):
    encounter_name = args[0]
    if encounter_name.isdigit():
        encounter_count = int(encounter_name)
        debug("Running {} encounter {} times".format(args[1], encounter_count))
        for encounter_index in range(0, encounter_count):
            do_encounter(args[1:])
    elif encounter_name in encounters:
        encounter = encounters[encounter_name]
        debug("Found {}: {}".format(encounter_name, encounter))
        if encounter['type'] == 'simple':
            simple_encounter(encounter, args)
        elif encounter['type'] == 'monster':
            monster_encounter(encounter, args)
        elif encounter['type'] == 'altar':
            altar_encounter(encounter, args)
        elif encounter['type'] == 'chain':
            do_encounter_chain(encounter)
            encounters.pop(encounter_name)
        elif encounter['type'] == 'special':
            if encounter_name == 'use_item':
                item = args[1]
                hero.inventory[item] -= 1
                if hero.inventory[item] < 0:
                    raise Exception("Not enough uses of {}".format(item))
            else:
                raise Exception("Not implemented: special encounter '{}'".format(encounter_name))
        else:
            raise Exception("Not implemented: {}".format(encounter['type']))
    else:
        raise Exception("Unrecognised or duplicate encounter: {}".format(encounter_name))

def do_encounter_line(line):
    if line.startswith('#'):
        print line[1:]
        print_stats()
    elif line == 'print':
        print_stats()
    else:
        do_encounter(line.split())

if len(sys.argv) > 1:
    simulation_file = sys.argv[1]
else:
    simulation_file = 'start.txt'
simulation = open(simulation_file)
line = simulation.readline().strip()
if line.startswith('Start'):
    stats_string = line.split(' ')[1].split('/')
    hero.stats[LIFE_STAT] = int(stats_string[0])
    hero.stats[OFFENSE_STAT] = int(stats_string[1])
    hero.stats[DEFENCE_STAT] = int(stats_string[2])
    hero.stats[GOLD_STAT] = int(stats_string[3])
    hero.keys['yellow'] = int(stats_string[4])
    hero.keys['blue'] = int(stats_string[5])
    hero.keys['red'] = int(stats_string[6])
    line = simulation.readline().strip()
else:
    hero.stats[LIFE_STAT] = 1000
    hero.stats[OFFENSE_STAT] = 100
    hero.stats[DEFENCE_STAT] = 100
    hero.stats[GOLD_STAT] = 0
    hero.keys['yellow'] = 0
    hero.keys['blue'] = 0
    hero.keys['red'] = 0

while line:
    do_encounter_line(line)
    line = simulation.readline().strip()

