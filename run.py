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
Parameters
"""
mesh_radius = 1

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
    upgrades = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage, bc.UnitType.Rocket]
    for u in upgrades:
        gc.queue_research(u)

def count_units():
    for t in bc.UnitType:
        unit_count[t] = 0
    for u in gc.my_units():
        unit_count[u.unit_type] += 1

def next_unit():
    #TODO Doesn't work correctly, seems to return ranger every time
    units = []
    for k in unit_ratio:
        c = 0
        if k in unit_count:
            c = unit_count[k]
        units.append( (k, c/unit_ratio[k]) )
    return min(units, key = lambda t: t[1])[0]

"""
karbonite
"""
def detect_karbonite():
    planet_map = gc.starting_map(gc.planet())

    for x in range(planet_map.width):
        for y in range(planet_map.height):
            loc = bc.MapLocation(gc.planet(),x,y)
            if planet_map.on_map(loc):
                if gc.karbonite_at(loc) > 0:
                    karbonite_loc.append(index_loc)

def sense_karbonite(u):
    if u.location.is_on_map():
        loc = u.location.map_location()
        radius = u.vision_range
        #Awkward for loop to put the closest karbonite at the front of the array
        for x in range(max(0,loc.x-radius),min(gc.starting_map(gc.planet()).width,loc.x+radius)):
            for y in range(max(0,loc.y-radius),min(gc.starting_map(gc.planet()).height,loc.y+radius)):
                index_loc = bc.MapLocation(gc.planet(),x,y)
                try:
                    if gc.karbonite_at(index_loc) > 0:
                        if index_loc not in karbonite_loc:
                            karbonite_loc.append(index_loc)
                    else:
                        if index_loc in karbonite_loc:
                            karbonite_loc.remove(index_loc)
                except:
                    pass

def best_karbonite(u):
    # Distance and value
    dist = [ (kar, u.location.map_location().distance_squared_to( kar )/gc.starting_map(gc.planet()).initial_karbonite_at( kar )) for kar in karbonite_loc]
    if len(dist) < 1:
        return None
    return min(dist, key = lambda t: t[1])[0]

def mars_karbonite():
    array={}
    for x in range(0,gc.starting_map(1).width):
        for y in range(0,gc.starting_map(1).height):
            index_loc=bc.MapLocation
    pass

"""
Enemy Detection
"""
def get_enemy_team(my_team):
    #Red is 0 Blue is 1
    #print(my_team)
    if my_team == bc.Team.Red:
        return bc.Team.Blue
    return bc.Team.Red

def verify_enemy():
    # for en in enemy_loc:
    #     if gc.can_sense_location(en.location.map_location()) and not gc.can_sense_unit(en.id):
    #         enemy_loc.remove(en)
    for en in enemy_loc:
        try:
            if not gc.can_sense_unit(en.id):
                enemy_loc.remove(en)
        except Exception as e:
            if str(e) != "b'The location is outside your vision range.'":
                enemy_loc.remove(en)

def detect_enemy(u):
    if u.location.is_on_map():
        enemies = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range ,op_team)
        for en in enemies:
            if en not in enemy_loc:
                enemy_loc.append(en)

def best_enemy(u):
    #TODO determine target based on DPS, importance, etc
    dist = [ (en, u.location.map_location().distance_squared_to( en.location.map_location() )) for en in enemy_loc]
    if len(dist)>0:
        return min(dist, key = lambda t: t[1])[0]
    else:
        return None

def closest_enemy(u):
    dist = [ (en, u.location.map_location().distance_squared_to( en.location.map_location() )) for en in enemy_loc]
    if len(dist)>0:
        return min(dist, key = lambda t: t[1])[0]
    else:
        return None

"""
Friendly Detection
"""
def create_friendly_mesh():
    global mesh
    planet_map = gc.starting_map(gc.planet())
    mesh = [ [0 for y in range(planet_map.height)] for x in range(planet_map.width) ]
    for u in gc.my_units():
        loc = u.location.map_location()
        mesh[loc.x][loc.y] = len(gc.sense_nearby_units_by_team(loc, mesh_radius, my_team))

"""
Pathfinding
"""
def find_path(start, end):
    my_map = gc.starting_map(gc.planet())
    fringe = [(start, None)]

    for i in range(500): # SET MAX ITERATIONS TO PREVENT LENGTHY SEARCHING
        loc, path = fringe.pop(0)

        if not path:
            path = []

        direction = loc.direction_to(end)
        if direction == bc.Direction.Center:
            print("\n CREATED PATH \n")
            return path

        new_path = path[:].append(direction)
        new_loc = loc.add(direction)

        if my_map.on_map(new_loc) and my_map.is_passable_terrain_at(new_loc):
            fringe.append( (new_loc, new_path) )
        else:
            left = right = direction
            for a in range( int(len(directions)/2) ):
                left = left.rotate_left()
                right = right.rotate_right()

                new_path = path[:].append(left)
                new_loc = loc.add(left)

                if my_map.on_map(new_loc) and my_map.is_passable_terrain_at(new_loc):
                    fringe.append( (new_loc, new_path) )

                new_path = path[:].append(right)
                new_loc = loc.add(right)

                if my_map.on_map(new_loc) and my_map.is_passable_terrain_at(new_loc):
                    fringe.append( (new_loc, new_path) )

    return False

def run_away(u): # Run away from enemy troops, used by worker
    pass

def retreat(u): # Run away if outnumbered/outdps, for troops
    pass

def wander(u):
    current = u.location.map_location()
    #HELLO
    pass

def move_toward_enemy(u, en): # move toward known enemy location
    if u.id in unit_dest:
        unit_dest.pop(u.id, None)
    d=u.location.map_location().direction_to(en.location.map_location())
    if gc.can_move(u.id,d):
        gc.move_robot(u.id,d)
    else:
        spread_out(u, d)

def spread_out(u, d): # walk away from friendly troops if they are right next to you
    left = right = d
    for a in range( int(len(directions)/2) ):
        left = left.rotate_left()
        right = right.rotate_right()
        if gc.can_move(u.id, left):
            gc.move_robot(u.id, left)
            return
        if gc.can_move(u.id, right):
            gc.move_robot(u.id, right)
            return

def move_toward_dest(u, en): # move toward destination if dest exists
    if u.id in unit_dest:
        d = unit_dest[u.id].pop()
        if gc.can_move(u.id,d):
            gc.move_robot(u.id,d)
        else:
            unit_dest.pop(u.id, None)
            spread_out(u, d)
    else:
        move_toward_enemy(u, en)

"""
Unit Management
"""
def worker(u):
    if u.location.is_on_map():
        #TODO Run Away?

        #Build factory
        if gc.karbonite() >= bc.UnitType.Factory.blueprint_cost():
            closest_en = closest_enemy(u)
            if closest_en:
                direction = u.location.map_location().direction_to(closest_en.location.map_location()).opposite()
                if gc.can_blueprint(u.id, bc.UnitType.Factory, direction):
                    gc.blueprint(u.id, bc.UnitType.Factory, direction)
                    return None

        #Replicate worker
        if gc.karbonite() >= 15:
            nu = next_unit()
            if nu == bc.UnitType.Worker:
                for d in (directions):
                    if (gc.can_replicate(u.id,d)):
                        gc.replicate(u.id,d)
                        return None

        #Build factory code
        nearby = gc.sense_nearby_units(u.location.map_location(), 3)
        for units in nearby:
            if units.unit_type == bc.UnitType.Factory:
                if gc.can_build(u.id, units.id):
                    gc.build(u.id,units.id)
                    return None

        #Mining code
        sense_karbonite(u)
        bk = best_karbonite(u)
        if bk:
            direction = u.location.map_location().direction_to(bk)
            if gc.can_harvest(u.id,direction):
                gc.harvest(u.id,direction)
                return None
            else:
                if (gc.is_move_ready(u.id) and gc.can_move(u.id,direction)):
                    gc.move_robot(u.id,direction)
                    return None

        #Random movement code
        for d in directions:
            if gc.is_move_ready(u.id):
                if gc.can_move(u.id,d):
                    gc.move_robot(u.id,d)
                    return None
def knight(u):
    if u.location.is_on_map():
        closest_en = closest_enemy(u)
        if closest_en:
            if gc.is_attack_ready(u.id):
                if gc.can_sense_unit(closest_en.id) and gc.can_attack(u.id, closest_en.id):
                    gc.attack(u.id,closest_en.id)
            if gc.is_move_ready(u.id):
                if u.location.map_location().distance_squared_to( closest_en.location.map_location() ) <= u.vision_range:
                    move_toward_enemy(u, closest_en)
                else:
                    if u.id not in unit_dest:
                        path = find_path( u.location.map_location(), closest_en.location.map_location() )
                        if path:
                            unit_dest[u.id] = path
                    move_toward_dest(u, closest_en)
        else:
            pass
            # wander(u)

    return None
def ranger(u):
    if u.location.is_on_map():
        closest_en = closest_enemy(u)
        if closest_en:
            if gc.is_attack_ready(u.id):
                if gc.can_sense_unit(closest_en.id) and gc.can_attack(u.id, closest_en.id):
                    gc.attack(u.id,closest_en.id)
            if gc.is_move_ready(u.id):
                if u.id in unit_dest:
                    move_toward_dest()
                d=u.location.map_location().direction_to(closest_en.location.map_location())
                if gc.can_move(u.id,d):
                    gc.move_robot(u.id,d)
def mage(u):
    if u.location.is_on_map():
        closest_en = closest_enemy(u)
        if closest_en:
            if gc.is_attack_ready(u.id):
                #BUG this is actually dumb, but can_attack is the one returning the error
                if gc.can_sense_unit(closest_en.id) and gc.can_attack(u.id, closest_en.id):
                    gc.attack(u.id,closest_en.id)
                #     return None
            if gc.is_move_ready(u.id):
                if u.id in unit_dest:
                    move_toward_dest()
                d=u.location.map_location().direction_to(closest_en.location.map_location())
                if gc.can_move(u.id,d):
                    gc.move_robot(u.id,d)
def healer(u):
    pass
def factory(u):
    garrison = u.structure_garrison()
    if len(garrison) > 0:
        closest_en = closest_enemy(u)
        if closest_en:
            direction = u.location.map_location().direction_to(closest_en.location.map_location())

            if gc.can_unload(u.id, direction):
                gc.unload(u.id, direction)
            else:
                for d in directions:
                    if gc.can_unload(u.id, d):
                        gc.unload(u.id, d)
            return None

    nu = next_unit()
    if nu != bc.UnitType.Worker and gc.can_produce_robot(u.id, nu):
        gc.produce_robot(u.id, nu)
    return None
def rocket(u):
#    if gc.can_launch_rocket(u.id,
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
    # detect_karbonite()
    while True:
        print("EARTH CODE {}, K: {} \n".format(gc.round(), gc.karbonite()))
        print(len(enemy_loc))
        verify_enemy()
        count_units()
        # create_mesh()
        for u in gc.my_units():
            # print(u.unit_type)
            detect_enemy(u)
            unit_dict[u.unit_type](u)
        next_turn()
def mars():
    # sense_karbonite(u)
    while True:
        next_turn()

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
    bc.UnitType.Mage : mage,
    bc.UnitType.Rocket : rocket,
    bc.UnitType.Factory : factory
}
unit_dest = {}
unit_ratio = {
    bc.UnitType.Worker: 5,
    bc.UnitType.Ranger: 20,
    # bc.UnitType.Mage: 10
}
    # bc.UnitType.Knight: 10,
unit_count = {
    bc.UnitType.Worker: len(gc.my_units())
}



# Communications for same planet
enemy_loc = [u for u in gc.starting_map(gc.planet()).initial_units if u.team == op_team]
karbonite_loc = []
mesh = None

manage_upgrades()

if gc.planet() == bc.Planet.Earth:
    earth()
else:
    mars()
