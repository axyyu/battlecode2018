#Battlecode
import battlecode as bc
import random
import sys
import traceback
# from math import sqrt

"""
Brother? I'm your daddy!

Strategy:
 - Knights/Blitz

Help:

UnitData = dict of units and their respective data not included
    role?
    destination?

Root = starting worker where headquarter is
HQ = headquarter maplocation
"""


"""
Unit data
"""
class UnitData():
    def __init__(self, unit, role, dest):
        self.unit = unit
        self.role = role
        self.dest = dest


"""
Enemy Detection
"""
def get_enemy_team(my_team):
    #Red is 0 Blue is 1
    print(my_team)
    if my_team == bc.Team.Red:
        return bc.Team.Blue
    return bc.Team.Red

def detect_enemy(unit):
    #Can improve by only looking at units at the edge of the visable map
    detected_Enemy.add(gc.sense_nearby_units_by_team(unit.location.map_location(),999,op_team))
"""
Helper Methods
"""
def next_turn():
    gc.next_turn()
    sys.stdout.flush()
    sys.stderr.flush()
def manage_upgrades():
    # upgrades = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Rocket]
    upgrades = [bc.UnitType.Worker, bc.UnitType.Rocket]
    for u in upgrades:
        gc.queue_research(u)

def sense_karbonite(u,radius):
    loc = u.location.map_location()
    karbonite_loc = list()
    #Awkward for loop to put the closest karbonite at the front of the array
    for x in range(0,radius):
        for y in range(0,radius):
            if x!=0 and y!=0:
                index_loc = bc.MapLocation(bc.Planet.Earth,loc.x+x,loc.y+y) # this is not correct but I can't find the correct syntax
                try:
                    if gc.karbonite_at(index_loc):
                            karbonite_loc.append(index_loc)
                except:
                    pass
                index_loc = bc.MapLocation(bc.Planet.Earth,loc.x-x,loc.y-y) # this is not correct but I can't find the correct syntax
                try:
                    if gc.karbonite_at(index_loc):
                            karbonite_loc.append(index_loc)
                except:
                    pass
    return karbonite_loc




def next_unit():
    units = []
    for k in unit_ratio:
        c = 0
        if k in unit_count:
            c = unit_count[k]
        units.append( (k, c/unit_ratio[k]) )
    return min(units, key = lambda t: t[1])[0]


"""
Enemy Detection
"""
def get_enemy_team(my_team):
    #Red is 0 Blue is 1
    #print(my_team)
    if my_team == bc.Team.Red:
        return bc.Team.Blue
    return bc.Team.Red

def detect_enemy(unit):
    #Can improve by only looking at units at the edge of the visable map
    detected_Enemy.add(gc.sense_nearby_units_by_team(unit.location.map_location(),999,op_team))

def closest_enemy(u):
    dist = [ (loc, u.location.map_location().distance_squared_to(loc)) for loc in enemy_loc]
    return min(dist, key = lambda t: t[1])[0]

"""
Pathfinding
"""
def find_path(start, end):
    my_map = gc.starting_map(gc.planet())
    fringe = [(start, None)]

    for i in range(100): # SET MAX ITERATIONS TO PREVENT LENGTHY SEARCHING
        loc, path = fringe.pop(0)

        direction = loc.direction_to(end)
        if direction == bc.Direction.Center:
            return path
        new_path = path[:].append(direction)
        new_loc = loc.add(direction)

        if my_map.on_map(new_loc) and my_map.is_passable_terrain_at(new_loc):
            fringe.append( (new_loc, new_path) )
        else:
            for d in directions:
                if d != direction:
                    new_path = path[:].append(d)
                    new_loc = loc.add(d)

                    if my_map.on_map(new_loc) and my_map.is_passable_terrain_at(new_loc):
                        fringe.append( (new_loc, new_path) )

    return False

def move(unit, direction):
    if gc.is_move_ready(unit.id):
        if gc.can_move(unit.id, direction):
            if gc.move_robot(unit.id, direction):
                return True
    return False

"""
Unit Management
"""
def worker(u):
    #starting rounds
    if unit_data[u.id] == "root":
        if gc.round() == 0:
            #Build factory away from enemy on round 0
            direction = u.location.map_location().direction_to(closest_enemy(u))
            if gc.karbonite() > bc.UnitType.Factory.blueprint_cost() and gc.can_blueprint(unit.id, bc.UnitType.Factory, d):
                gc.blueprint(unit.id, bc.UnitType.Factory, direction)
                return None
    #Build factory code
    nearby = gc.sense_nearby_units(u.location.map_location(), 2)
    for units in nearby:
        if units.unit_type == bc.UnitType.Factory:
            gc.build(u.id,units.id)
            return None

    #Mining code
    #BUG Fundemental Error with the below line is that vision range is a circle and our sense nearby checks a box
    #nearby_karbonite = sense_karbonite(u, u.vision_range ** .5) -- Line that doess not work

    nearby_karbonite = sense_karbonite(u, 4)
    print("ERROR")
    temp=len(nearby_karbonite)
    if temp>0:
        direction = u.location.map_location().direction_to(nearby_karbonite[0])
        if gc.can_harvest(u.id,direction):
            gc.harvest(u.id,direction)
            return None
        else:
            if (gc.is_move_ready(u.id) and gc.can_move(u.id,direction)):
                gc.move_robot(u.id,direction)
                return None

    #Random movement code
    d = random.choice(directions)
    if (gc.is_move_ready(u.id) and gc.can_move(u.id,d)):
        gc.move_robot(u.id,d)
        return None


def knight(u):
    pass
def ranger(u):
    nearby= gc.sense_nearby_units(u.location.map_location(),8)
    for other in nearby:
        if other.team != my_team and gc.is_attack_ready(u.id) and gc.can_attack(u.id, other.id):
            gc.attack(u.id, other.id)
            return None
    d=random.choice(directions)
    if gc.is_move_ready(u.id) and gc.can_move(u.id,d):
        gc.move_robot(u.id,d)

def mage(u):
    pass
def healer(u):
    pass
def factory(u):
    garrison = u.structure_garrison()
    if len(garrison) > 0:
        direction = u.location.map_location().direction_to(closest_enemy(u))
        if gc.can_unload(unit.id, direction):
            gc.unload(unit.id, direction)
        else:
            for d in directions:
                if gc.can_unload(unit.id, d):
                    gc.unload(unit.id, d)
        return None

    nu = next_unit()
    if gc.can_produce_robot(u.id, nu):
        gc.produce_robot(u.id, nu)
    return None
def rocket(u):

    pass

"""
Experimental
"""
def testEarth():
    for unit in root:
        detect_enemy(unit)
        print(detected_Enemy)

"""
Planet Control
"""
def earth():
    for u in gc.my_units():
        unit_dict[u.unit_type](u)
def mars():
    pass

"""
Running
"""

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()
my_team = gc.team()
op_team = get_enemy_team(my_team)

# Basic Constants
directions = list(bc.Direction)
unit_dict = {
    bc.UnitType.Worker : worker,
    bc.UnitType.Knight : knight,
    bc.UnitType.Ranger : ranger,
    bc.UnitType.Factory : factory
}
unit_data = {}
unit_ratio = {
    bc.UnitType.Worker: 2,
    bc.UnitType.Knight: 2,
    bc.UnitType.Ranger: 1,
    bc.UnitType.Mage: 1
}
unit_count = {
    bc.UnitType.Worker: len(gc.my_units())
}



# Communications for same planet
unit_data[ gc.my_units()[0].id ] = "root"
enemy_loc = [u.location.map_location() for u in gc.starting_map(gc.planet()).initial_units if u.team == op_team]

manage_upgrades()
while True:
    try:
        if gc.planet() == bc.Planet.Earth:
            earth()
        else:
            mars()
        next_turn()
    except Exception as e:
        print('Error:', e)
        traceback.print_exc()
