#Battlecode
import battlecode as bc
import numpy as np
import random
import sys
import traceback
import math

"""
Brother? I'm your daddy!

New Plan:
    Earth
 - Start by scanning for karbonite locations
 - Workers sprint to build factories in the same location, workers stay together in a group
 - Troops move together in formations, never too far away from friendly troops (3 - 5 distance)
 - Build rockets as soon as troop quota is reached, but only populate if not in battle

    Mars
 - spread out across the map to have vision of every sqaure, report rocket landing location to swarm with nearby troops
 - land in all areas (those unreachable by walking)

    Both
 - Scan map for empty areas, create matrix of map in numpy (1 for passible terrain, 0 for unpassable)
 - Create gradients of friendly and enemy concentrations (steepest gradient can be used as attack or run away)
 - Map out enemy team through "scouts" (we can randomly spawn workers that int into the enemy and gather data, every 50 rounds or so when we aren't in a firefight)

Troops:
 - Single-target attack
    Priority Targets - look at health, then at troop & range (mages, ranger, knight), factory, worker
 - Knight (mid game, half, front line), too little range
 - Rangers (early game, half, back line)
 - Mages (late game)
 - Healers (3 to a unit) - cancel ranger dmg
 - Max number of troops to prevent extreme runtime (or save a copy of a previous unit's settings for future units)
 - Unit ratios that change throughout the game, groups of enemies together -> mages, single knights -> more rangers, etc

"""

"""
Parameters
"""
mesh_radius = 3
unit_limit = 300
params = {
    bc.UnitType.Worker : {
        "ratio" : 0.15,
        "count" : 0
    },
    bc.UnitType.Knight : {
        "ratio" : 0.02,
        "count" : 0
    },
    bc.UnitType.Ranger : {
        "ratio" : 0.6,
        "count" : 0
    },
    bc.UnitType.Mage : {
        "ratio" : 0.03,
        "count" : 0
    },
    bc.UnitType.Healer : {
        "ratio" : 0.2,
        "count" : 0
    }
}
buildings = {
    bc.UnitType.Factory : {
        "ratio" : 0,
        "count" : 0,
        "cap" : 4
    },
    bc.UnitType.Rocket :{
        "ratio": 0,
        "count": 0,
        "cap" : 1
    }
}

"""
Data
"""
earth_mesh = []
mars_mesh = []

enemies = []
enemy_mesh = []
friendly_mesh = []
unit_grad = []

directions = list(bc.Direction)

"""
Helper Methods
"""
def next_turn():
    gc.next_turn()
    sys.stdout.flush()
    sys.stderr.flush()

def get_enemy_team(my_team):
    if my_team == bc.Team.Red:
        return bc.Team.Blue
    return bc.Team.Red

"""
Upgrades
"""
def manage_upgrades():
    upgrades = [
    bc.UnitType.Ranger,
    bc.UnitType.Healer,
    bc.UnitType.Ranger,
    bc.UnitType.Healer,
    bc.UnitType.Healer,
    bc.UnitType.Knight,
    bc.UnitType.Knight,
    bc.UnitType.Mage,
    bc.UnitType.Mage,
    bc.UnitType.Mage,
    bc.UnitType.Rocket
    ]
    for u in upgrades:
        gc.queue_research(u)

"""
Unit Spawning
"""
def next_unit():
    units = []
    for k in params:
        c = params[k]["count"]
        units.append( (k, c/params[k]["ratio"]) )
    return min(units, key = lambda t: t[1])[0]

"""
Map Evaluation
"""
def scan_map():
    global map_mesh, enemy_mesh, friendly_mesh
    planet_map = gc.starting_map(gc.planet())

    map_mesh = [ [ -1 for y in range(planet_map.height) ] for x in range(planet_map.width) ]
    enemy_mesh = [ [ 0 for y in range(planet_map.height) ] for x in range(planet_map.width) ]
    friendly_mesh = [ [ 0 for y in range(planet_map.height) ] for x in range(planet_map.width) ]

    for x in range(planet_map.width):
        for y in range(planet_map.height):
            loc = bc.MapLocation(gc.planet(),x,y)

            if planet_map.on_map(loc):
                if planet_map.is_passable_terrain_at(loc):
                    map_mesh[x][y] = planet_map.initial_karbonite_at(loc)

"""
Gradients
"""
def scan_enemies():
    for u in enemies:
        if u.location.is_on_map():
            loc = u.location.map_location()
            enemy_mesh[loc.x][loc.y] -= 1

def scan_friendlies():
    for u in gc.my_units():
        if u.location.is_on_map():
            loc = u.location.map_location()
            friendly_mesh[loc.x][loc.y] += 1

def calculate_gradient():
    global unit_grad
    unit_mesh = np.add(enemy_mesh,friendly_mesh)
    unit_grad = np.gradient(unit_mesh)

"""
Karbonite
"""
def sense_karbonite(u):
    if u.location.is_on_map():
        loc = u.location.map_location()
        radius = u.vision_range
        #Awkward for loop to put the closest karbonite at the front of the array
        for x in range(max(0,loc.x-radius),min(gc.starting_map(gc.planet()).width,loc.x+radius)):
            for y in range(max(0,loc.y-radius),min(gc.starting_map(gc.planet()).height,loc.y+radius)):
                index_loc = bc.MapLocation(gc.planet(),x,y) # THIS GAVE ME AN ERROR
                # incorrect type of arg planet: should be Planet, is {}".format(type(planet)) IDK what that means
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
    maxk=0
    location = None
    for x in range(0,gc.starting_map(1).width):
        for y in range(0,gc.starting_map(1).height):
            index_loc=bc.MapLocation(gc.starting_map(1),x,y)
            if gc.starting_map(1).on_map(index_loc):
                if gc.karbonite_at(index_loc)>maxk:
                    maxk=gc.karbonite_at(index_loc)
                    location = index_loc
    return location


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
    global my_mesh
    planet_map = gc.starting_map(gc.planet())
    my_mesh = [ [0 for y in range(planet_map.height)] for x in range(planet_map.width) ]
    for u in gc.my_units():
        if u.location.is_on_map():
            loc = u.location.map_location()
            my_mesh[loc.x][loc.y] = len(gc.sense_nearby_units_by_team(loc, mesh_radius, my_team))

def create_enemy_mesh():
    global op_mesh
    planet_map = gc.starting_map(gc.planet())
    op_mesh = [ [0 for y in range(planet_map.height)] for x in range(planet_map.width) ]
    for u in enemy_loc:
        if u.location.is_on_map():
            loc = u.location.map_location()
            try:
                op_mesh[loc.x][loc.y] = len(gc.sense_nearby_units_by_team(loc, mesh_radius, op_team))
            except:
                op_mesh[loc.x][loc.y] = 1

def get_lowest_unit(u):
    units = gc.sense_nearby_units_by_type(u.location.map_location(),30, bc.UnitType.Ranger)
    minIndex = 0
    if len(units)==0:
        return None
    for x in range(len(units)):
        if units[x].health<units[minIndex].health:
            minIndex=x
    #print("UNITS:",units[minIndex])
    return units[minIndex]



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

def group_up(u): # Workers to head toward factories
    global friendly_mesh
    loc = u.location.map_location()

    if len(gc.sense_nearby_units_by_team(u.location.map_location(), int(u.vision_range/2), my_team)) > min( len(gc.my_units()), math.exp(len(gc.my_units())) ) :
        return True

    planet_map = gc.starting_map(gc.planet())

    max_friends = (0, None)
    for x in range(planet_map.width):
        for y in range(planet_map.height):
            friends = friendly_mesh[x][y]
            if friends > max_friends[0]:
                max_friends = (friends, bc.MapLocation(gc.planet(), x, y) )

    d = u.location.map_location().direction_to( max_friends[1] )
    if gc.can_move(u.id,d):
        gc.move_robot(u.id,d)
        return False
    else:
        spread_out(u, d)

def run_away(u): # Run away from enemy troops toward safety
    global enemy_mesh
    global friendly_mesh
    loc = u.location.map_location()
    enemies = enemy_mesh[loc.x][loc.y]#op mesh???
    if enemies < friendly_mesh[loc.x][loc.y] + 1:#my mesh???
        return False
    planet_map = gc.starting_map(gc.planet())
    for x in range(planet_map.width):
        for y in range(planet_map.height):
            friends = friendly_mesh[x][y] + 1
            if friends > enemies:
                d = u.location.map_location().direction_to( bc.MapLocation(gc.planet(), x, y) )
                if gc.can_move(u.id,d):
                    gc.move_robot(u.id,d)
                    return True
                else:
                    spread_out(u, d)
                    return True
    return True

def move_toward_enemy(u, en): # move toward known enemy location
    if u.id in unit_dest:
        unit_dest.pop(u.id, None)
    d = u.location.map_location().direction_to(en.location.map_location())
    if gc.can_move(u.id,d):
        gc.move_robot(u.id,d)
    else:
        spread_out(u, d)

def kite(u, en):
    d = u.location.map_location().distance_squared_to(en.location.map_location())
    ran = en.vision_range
    try:
        ran = en.attack_range()
    except:
        pass
    if d > ran or u.attack_range() < d:
        move_toward_enemy(u, en)
    else:
        print("KITING")
        di = u.location.map_location().direction_to(en.location.map_location()).opposite()
        if gc.can_move(u.id,di):
            gc.move_robot(u.id,di)
        else:
            spread_out(u, di)

def spread_out(u, d): # walk away from friendly troops if they are right next to you
    left = right = d
    for a in range( int(len(directions)/2) ):
        left = left.rotate_left()
        right = right.rotate_right()
        if gc.is_move_ready(u.id) and gc.can_move(u.id, left):
            gc.move_robot(u.id, left)
            return
        if gc.is_move_ready(u.id) and gc.can_move(u.id, right):
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
        kite(u, en)


"""
Unit Management
"""
def worker(u):
    if u.location.is_on_map():
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

        #rocket
        if buildings[bc.UnitType.Rocket]["count"]<=buildings[bc.UnitType.Rocket]["cap"]:
            for d in directions:
                if gc.can_blueprint(u.id, bc.UnitType.Rocket, d):
                    gc.blueprint(u.id,bc.UnitType.Rocket,d)

        #Build factory
        if gc.karbonite() >= bc.UnitType.Factory.blueprint_cost() and buildings[bc.UnitType.Factory]["count"] <= buildings[bc.UnitType.Factory]["cap"]:
            print("CAN BUILD FACTORY")
            closest_en = closest_enemy(u)
            if closest_en:
                direction = u.location.map_location().direction_to(closest_en.location.map_location()).opposite()
                if gc.can_blueprint(u.id, bc.UnitType.Factory, direction):
                    gc.blueprint(u.id, bc.UnitType.Factory, direction)
                else:
                    d = direction
                    for a in range( int(len(directions)/2) ):
                        d.rotate_left()
                        if gc.can_blueprint(u.id, bc.UnitType.Factory, d):
                            gc.blueprint(u.id, bc.UnitType.Factory, d)
                            break
            else:
                d = random.choice(directions)
                for a in range( int(len(directions)/2) ):
                    d.rotate_left()
                    if gc.can_blueprint(u.id, bc.UnitType.Factory, d):
                        gc.blueprint(u.id, bc.UnitType.Factory, d)
                        break
            return None

        #Mining code
        sense_karbonite(u)
        bk = best_karbonite(u)
        if bk:
            direction = u.location.map_location().direction_to(bk)
            if gc.can_harvest(u.id,direction):
                gc.harvest(u.id,direction)
                return None


        # Movement code
        if gc.is_move_ready(u.id):
            if not run_away(u):
                if group_up(u):
                    if gc.can_move(u.id, u.location.map_location().direction_to(bk)):
                        gc.move_robot(u.id, u.location.map_location().direction_to(bk))
                        return None

def knight(u):
    if u.location.is_on_map():
        closest_en = closest_enemy(u)
        if closest_en:
            if u.location.map_location().distance_squared_to( closest_en.location.map_location() ) <= u.vision_range:
                if gc.is_attack_ready(u.id):
                    if gc.can_sense_unit(closest_en.id) and gc.can_attack(u.id, closest_en.id):
                        gc.attack(u.id,closest_en.id)

        if gc.is_move_ready(u.id):
            if not run_away(u):
                if u.location.map_location().distance_squared_to( closest_en.location.map_location() ) <= u.vision_range:
                    move_toward_enemy(u, closest_en)
                else:
                    path = find_path( u.location.map_location(), closest_en.location.map_location() )
                    if path:
                        unit_dest[u.id] = path
                    move_toward_dest(u, closest_en)

    return None
def ranger(u):
    if u.location.is_on_map():
        closest_en = closest_enemy(u)
        if closest_en:
            if u.location.map_location().distance_squared_to( closest_en.location.map_location() ) <= u.vision_range:
                if gc.is_attack_ready(u.id):
                    if gc.can_sense_unit(closest_en.id) and gc.can_attack(u.id, closest_en.id):
                        gc.attack(u.id,closest_en.id)

        if gc.is_move_ready(u.id):
            if not run_away(u):
                if closest_en:
                    if u.location.map_location().distance_squared_to( closest_en.location.map_location() ) <= u.vision_range:
                        kite(u, closest_en)
                        return None
                path = find_path( u.location.map_location(), closest_en.location.map_location() )
                if path:
                    unit_dest[u.id] = path
                move_toward_dest(u, closest_en)

    return None
def mage(u):
    if u.location.is_on_map():
        closest_en = closest_enemy(u)
        if closest_en:
            if u.location.map_location().distance_squared_to( closest_en.location.map_location() ) <= u.vision_range:
                if gc.is_attack_ready(u.id):
                    if gc.can_sense_unit(closest_en.id) and gc.can_attack(u.id, closest_en.id):
                        gc.attack(u.id,closest_en.id)

        if gc.is_move_ready(u.id):
            if not run_away(u):
                if u.location.map_location().distance_squared_to( closest_en.location.map_location() ) <= u.vision_range:
                    move_toward_enemy(u, closest_en)
                else:
                    path = find_path( u.location.map_location(), closest_en.location.map_location() )
                    if path:
                        unit_dest[u.id] = path
                    move_toward_dest(u, closest_en)

    return None
def healer(u):
    if u.location.is_on_map():
        healFirst = get_lowest_unit(u)
    if healFirst is not None:
        if gc.can_heal(u.id,healFirst.id):
            gc.heal(u.id,healFirst.id)
            return None
    closest_en = closest_enemy(u)
    if gc.is_move_ready(u.id):
        if u.id in unit_dest:
            move_toward_dest()
        #Direction of closest enemy
        d=u.location.map_location().direction_to(closest_en.location.map_location())
        #Check if enemy is out of attack range
        if u.location.map_location().distance_squared_to(closest_en.location.map_location()) > 40:
            if gc.can_move(u.id,d):
                gc.move_robot(u.id,d)
        else:
            d = d.opposite()
            if gc.can_move(u.id,d):
                    gc.move_robot(u.id,d)
def factory(u):
    garrison = u.structure_garrison()
    if len(garrison) > 0:
        closest_en = closest_enemy(u)
        if closest_en:
            direction = u.location.map_location().direction_to(closest_en.location.map_location())
        else:
            direction = random.choice(directions)
        if gc.can_unload(u.id, direction):
            gc.unload(u.id, direction)
        else:
            for d in directions:
                if gc.can_unload(u.id, d):
                    gc.unload(u.id, d)
            return None

    nu = next_unit()
    if gc.can_produce_robot(u.id, nu):
        gc.produce_robot(u.id, nu)
    return None
def rocket(u):
    # if len(u.structure_garrison())<8:
    #     for f in adjacent_troops:
    #         if gc.can_load(u.id, f.id):
    #             gc.load(u.id,f.id)
    #             return None
    if gc.can_launch_rocket(u.id, mars_karbonite()):
        gc.launch_rocket(u.id,mars_karbonite())
        return None

"""
Planet Control
"""
def init_setup():
    manage_upgrades()
    scan_map()
def earth():
    # detect_karbonite()
    while True:
        print("EARTH CODE {}, K: {} \n".format(gc.round(), gc.karbonite()))

        scan_enemies()
        scan_friendlies()
        calculate_gradient()

        for u in gc.my_units():
            # print(u.unit_type)
            unit_dict[u.unit_type](u)
            # detect_enemy(u)
        next_turn()
def mars():
    # sense_karbonite(u)
    while True:
        next_turn()

"""
Running
"""
gc = bc.GameController()

# Basic Constants
my_team = gc.team()
op_team = get_enemy_team(my_team)

unit_dict = {
    bc.UnitType.Worker : worker,
    bc.UnitType.Knight : knight,
    bc.UnitType.Ranger : ranger,
    bc.UnitType.Mage : mage,
    bc.UnitType.Rocket : rocket,
    bc.UnitType.Factory : factory
}

unit_dest = {}


# Communications for same planet
enemy_loc = [u for u in gc.starting_map(gc.planet()).initial_units if u.team == op_team]
enemy_targets = []
karbonite_loc = []
op_mesh = None
my_mesh = None

init_setup()
if gc.planet() == bc.Planet.Earth:
    earth()
else:
    mars()
