import json, sys

with open('encounters.json') as json_file:
    encounters = json.load(json_file)

DEBUG = False
stats = {}
keys = {}
inventory = {}
altar_uses = 0

def debug(message):
    if DEBUG:
        print "DEBUG: " + message

def print_stats():
    print "Life={},offense={},defence={},gold={},keys={},blue keys={},red keys={},inventory={}".format(stats['life'], stats['offense'], stats['defense'], stats['gold'], keys['yellow'], keys['blue'], keys['red'], inventory)

def altar_cost(altar_uses):
    if altar_uses == 0:
        return 20
    else:
        return altar_cost(altar_uses - 1) + (altar_uses * 20)

if len(sys.argv) > 1:
    simulation_file = sys.argv[1]
else:
    simulation_file = 'start.txt'
simulation = open(simulation_file)
line = simulation.readline().strip()
if line.startswith('Start'):
    stats_string = line.split(' ')[1].split('/')
    stats['life'] = int(stats_string[0])
    stats['offense'] = int(stats_string[1])
    stats['defense'] = int(stats_string[2])
    stats['gold'] = int(stats_string[3])
    keys['yellow'] = int(stats_string[4])
    keys['blue'] = int(stats_string[5])
    keys['red'] = int(stats_string[6])
    line = simulation.readline().strip()
else:
    stats['life'] = 1000
    stats['offense'] = 100
    stats['defense'] = 100
    stats['gold'] = 0
    keys['yellow'] = 0
    keys['blue'] = 0
    keys['red'] = 0

while line:
    if line.startswith('#'):
        print line[1:]
        print_stats()
    elif line == 'print':
        print_stats()
    else:
        args = line.split()
        if args[0] == 'key':
            color = line.split(' ')[1]
            keys[color] += 1
            debug("Found a " + color + " key.")
        elif args[0] == 'door':
            color = line.split(' ')[1]
            if keys[color] > 0:
                keys[color] -= 1
                debug("Used a " + color + " key.")
            else:
                raise Exception("Not enough " + color + " keys!")
        elif args[0] == 'altar':
            """
            Altar cost starts at 20 and increases with each usage.
            The increment increases by 20 each time.
            Thus, the cost is 20, then 40, 80, 140, 220, 320, 440, etc.

            Altar effectiveness depends on the floor.
            An altar in floors 1-10 gives 2 attack or 4 defence,
            an altar in floors 11-20 gives 4 attack or 8 defence, etc.
            """
            cost = altar_cost(altar_uses)
            debug("Altar will cost {} gold.".format(cost))
            if stats['gold'] >= cost:
                stats['gold'] -= cost
                altar_uses += 1
            else:
                raise Exception("Not enough gold to use altar!")
            multiplier = int(args[1])
            stat = args[2]
            if stat == 'offense':
                stats[stat] += 2 * multiplier
            elif stat == 'defense':
                stats[stat] += 4 * multiplier
            else:
                raise Exception("Can only raise offense and defense at altars - if you're raising health, you're doing it wrong")
        else:
            encounter = encounters[args[0]]
            debug("Found " + line + ": " + str(encounter))
            if encounter['type'] == 'simple':
                if 'levelled' in encounter and encounter['levelled']:
                    multiplier = int(args[1])
                else:
                    multiplier = 1
                for stat in ['offense', 'defense', 'life', 'gold']:
                    if stat in encounter:
                        stats[stat] += encounter[stat] * multiplier
                        if stats[stat] < 0:
                            raise Exception("Insufficient {stat}!".format(stat=stat))
                if 'keys' in encounter:
                    for color in encounter['keys']:
                        keys[color] += encounter['keys'][color]
                if 'inventory' in encounter:
                    for item in encounter['inventory']:
                        if item in inventory:
                            inventory[item] += encounter['inventory'][item]
                        else:
                            inventory[item] = encounter['inventory'][item]
                        if inventory[item] < 0:
                            raise Exception("Not enough uses of {}".format(item))
            elif encounter['type'] == 'monster':
                if encounter['defense'] >= stats['offense']:
                    raise Exception("Not enough offensive power to attack this monster!")
                monster_life = encounter['life']
                in_battle = True
                while in_battle:
                    monster_life -= max(stats['offense'] - encounter['defense'], 0)
                    if monster_life <= 0:
                        monster_life = 0
                        in_battle = False
                    if in_battle:
                        stats['life'] -= max(encounter['offense'] - stats['defense'], 0)
                        if stats['life'] <= 0:
                            stats['life'] = 0
                            raise Exception("Died!")
                stats['gold'] += encounter['gold']
            else:
                raise Exception("Not implemented: " + encounter['type'])
    line = simulation.readline().strip()

