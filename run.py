import battlecode as bc
import random
import sys
import traceback

"""
Help:

UnitData = dict of units and their respective data not included
    role?
    destination?
    
Root = starting worker where headquarter is
HQ = headquarter maplocation
"""

# Basic Constants
directions = list(bc.Direction)

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()
my_team = gc.team()
root = gc.my_units().clone()


"""
Enemy Detection
"""
def get_enemy_team(my_team):
    #Red is 0 Blue is 1
    print(my_team)
    if my_team == bc.Team.Red:
        return bc.Team.Blue
    return bc.Team.Red

op_team = get_enemy_team(my_team)
detected_Enemy=set()



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
def manage_updates():
    updates = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Rocket]
    for u in updates:
        gc.queue_research(u)

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
    if u in root:
        # Set up headquarters
        pass
    else:
        pass
def knight(u):
    pass
def ranger(u):
    pass
def mage(u):
    pass
def healer(u):
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
    #testEarth()
    pass
def mars():
    pass

manage_updates()
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
