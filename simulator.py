import json, sys

with open('encounters.json') as json_file:
    encounters = json.load(json_file)

DEBUG = False

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
    for stat in ['offense', 'defense', 'life', 'gold']:
        if stat in encounter:
            hero.stats[stat] += encounter[stat] * multiplier
            if hero.stats[stat] < 0:
                raise Exception("Insufficient {stat}!".format(stat=stat))
    if 'keys' in encounter:
        for color in encounter['keys']:
            hero.keys[color] += encounter['keys'][color]
    if 'inventory' in encounter:
        for item in encounter['inventory']:
            if item in hero.inventory:
                hero.inventory[item] += encounter['inventory'][item]
            else:
                hero.inventory[item] = encounter['inventory'][item]
            if hero.inventory[item] < 0:
                raise Exception("Not enough uses of {}".format(item))

def monster_encounter(encounter, args):
    if encounter['defense'] >= hero.stats['offense']:
        raise Exception("Not enough offensive power to attack this monster!")
    monster_life = encounter['life']
    in_battle = True
    while in_battle:
        monster_life -= max(hero.stats['offense'] - encounter['defense'], 0)
        if monster_life <= 0:
            monster_life = 0
            in_battle = False
        if in_battle:
            hero.stats['life'] -= max(encounter['offense'] - hero.stats['defense'], 0)
            if hero.stats['life'] <= 0:
                hero.stats['life'] = 0
                raise Exception("Died!")
    hero.stats['gold'] += encounter['gold']

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
    if hero.stats['gold'] >= cost:
        hero.stats['gold'] -= cost
        hero.altar_uses += 1
    else:
        raise Exception("Not enough gold to use altar!")
    multiplier = int(args[1])
    stat = args[2]
    if stat == 'offense':
        hero.stats[stat] += encounter['offense'] * multiplier
    elif stat == 'defense':
        hero.stats[stat] += encounter['defense'] * multiplier
    elif stat == 'life':
        hero.stats[stat] += encounter['life'] * multiplier
    else:
        raise Exception("Unrecognised altar upgrade: {}, must be offense/defense/life".format(stat))

def do_encounter(args):
    encounter_name = args[0]
    if encounter_name in encounters:
        encounter = encounters[encounter_name]
        debug("Found {}: {}".format(encounter_name, encounter))
        if encounter['type'] == 'simple':
            simple_encounter(encounter, args)
        elif encounter['type'] == 'monster':
            monster_encounter(encounter, args)
        elif encounter['type'] == 'altar':
            altar_encounter(encounter, args)
        else:
            raise Exception("Not implemented: {}".format(encounter['type']))
    else:
        raise Exception("Unrecognised encounter: {}".format(encounter_name))

if len(sys.argv) > 1:
    simulation_file = sys.argv[1]
else:
    simulation_file = 'start.txt'
simulation = open(simulation_file)
line = simulation.readline().strip()
if line.startswith('Start'):
    stats_string = line.split(' ')[1].split('/')
    hero.stats['life'] = int(stats_string[0])
    hero.stats['offense'] = int(stats_string[1])
    hero.stats['defense'] = int(stats_string[2])
    hero.stats['gold'] = int(stats_string[3])
    hero.keys['yellow'] = int(stats_string[4])
    hero.keys['blue'] = int(stats_string[5])
    hero.keys['red'] = int(stats_string[6])
    line = simulation.readline().strip()
else:
    hero.stats['life'] = 1000
    hero.stats['offense'] = 100
    hero.stats['defense'] = 100
    hero.stats['gold'] = 0
    hero.keys['yellow'] = 0
    hero.keys['blue'] = 0
    hero.keys['red'] = 0

while line:
    if line.startswith('#'):
        print line[1:]
        print_stats()
    elif line == 'print':
        print_stats()
    else:
        do_encounter(line.split())
    line = simulation.readline().strip()

