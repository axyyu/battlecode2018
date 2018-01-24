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
run_threshold = 3
unit_weight = {
    bc.UnitType.Worker : 1,
    bc.UnitType.Knight : 2,
    bc.UnitType.Ranger : 8,
    bc.UnitType.Mage : 6,
    bc.UnitType.Healer : 6,
    bc.UnitType.Factory : 6,
    bc.UnitType.Rocket : 4
}
params = {
    bc.UnitType.Worker : {
        "ratio" : 0.15,
        "count" : 0
    },
    # bc.UnitType.Knight : {
    #     "ratio" : 0.02,
    #     "count" : 0
    # },
    bc.UnitType.Ranger : {
        "ratio" : 0.6,
        "count" : 0
    },
    bc.UnitType.Healer : {
        "ratio" : 0.2,
        "count" : 0
    },
    bc.UnitType.Mage : {
        "ratio" : 0.03,
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
root = None
attack_target = None
nu = None

earth_mesh = []
mars_mesh = []

fight_loc = []
fight_en = []

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

def get_direction(loc):
    # gradient matrix [0] = xcomp [1] = ycomp [0][x][y]
    gradx, grady = unit_grad[0][loc.x][loc.y], unit_grad[1][loc.x][loc.y]

    angles = [math.pi/2,math.pi/4,0,-math.pi/4,-math.pi/2,-math.pi*3/4,-math.pi,math.pi*3/4]
    j = math.atan2(gradx,grady)
    for k in range(angles):
        if math.abs(j-angles[k])<=math.pi/8:
            return directions[k]

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
def count_unit():
    global fight_loc
    fight_loc = []
    for u in gc.my_units():
        if u.unit_type in params:
            params[u.unit_type]["count"] = 0
        if u.unit_type in buildings:
            buildings[u.unit_type]["count"] = 0
    for u in gc.my_units():
        if u.unit_type in params:
            params[u.unit_type]["count"] += 1
        if u.unit_type in buildings:
            buildings[u.unit_type]["count"] +=1
        if u.health < u.max_health and u.unit_type != bc.UnitType.Factory and u.unit_type != bc.UnitType.Rocket:
            fight_loc.append(u.location.map_location())

def next_unit():
    global nu
    units = []
    for k in params:
        c = params[k]["count"]
        units.append( (k, c/params[k]["ratio"]) )
    nu = min(units, key = lambda t: t[1])[0]

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
    global unit_weight
    for u in enemies:
        if u.location.is_on_map():
            loc = u.location.map_location()
            enemy_mesh[loc.x][loc.y] -= unit_weight[u.unit_type]

def scan_friendlies():
    global unit_weight
    for u in gc.my_units():
        if u.location.is_on_map():
            loc = u.location.map_location()
            friendly_mesh[loc.x][loc.y] += unit_weight[u.unit_type]

def calculate_gradient():
    global unit_grad
    planet_map = gc.starting_map(gc.planet())
    unit_mesh = np.add(enemy_mesh,friendly_mesh)
    unit_grad = np.gradient(unit_mesh, planet_map.width)
    print(unit_grad)

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
    loc = u.location.map_location()
    planet_map = gc.starting_map(gc.planet())

    if gc.karbonite_at(loc):
        return None
    for r in range (1, u.vision_range):
        kar = 0
        karloc = None
        for d in directions:
            newloc = loc.add_multiple(d, r)
            if gc.on_map(newloc):
                if gc.karbonite_at(newloc) > kar:
                    karloc = newloc
        if karloc:
            return karloc

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
    if my_team == bc.Team.Red:
        return bc.Team.Blue
    return bc.Team.Red

def verify_enemy():
    for en in enemies:
        try:
            if not gc.can_sense_unit(en.id):
                enemies.remove(en)
        except Exception as e:
            if str(e) != "b'The location is outside your vision range.'":
                enemies.remove(en)

def add_enemies(nearby_en):
    for en in nearby_en:
        if en not in enemies:
            enemies.append(en)

def closest_enemy(u):
    dist = [ (en, u.location.map_location().distance_squared_to( en.location.map_location() )) for en in enemies]
    if len(dist)>0:
        return min(dist, key = lambda t: t[1])[0]
    else:
        return None

def worst_enemy(u, nearby_en):
    for n in fight_en:
        if n in nearby_en:
            return n
    en = [(n, unit_weight[n.unit_type]) for n in nearby_en]
    return max(en, key = lambda t: t[1])[0]

"""
Pathfinding
"""
def group_up(u, nearby_fr): # Workers to head toward factories
    if gc.is_move_ready(u.id):
        loc = u.location.map_location()
        if len([e for e in nearby_fr if e.team == my_team]) < min(3, gc.round()):
            direction = u.location.map_location().direction_to( root.location.map_location() )
            spread_out(u, direction)
            return False
        else:
            return True
    return False

def run_away(u, nearby_en): # Run away from enemy troops toward safety
    if gc.is_move_ready(u.id):
        loc = u.location.map_location()
        if len(nearby_en) > 1:
            en = worst_enemy(u, nearby_en)
            if en:
                direction = u.location.map_location().direction_to( en.location.map_location() ).opposite()
                spread_out(u, direction)
                return True
            else:
                return False
    return False

def spread_out(u, d): # try directions in an arc
    if gc.is_move_ready(u.id):
        left = right = d
        for a in range( int(len(directions)/2) ):
            if gc.can_move(u.id, left):
                gc.move_robot(u.id, left)
                return
            if gc.can_move(u.id, right):
                gc.move_robot(u.id, right)
                return
            left = left.rotate_left()
            right = right.rotate_right()

"""
Worker Code
"""
def blueprint_out(u, d, bp):
    left = right = d
    for a in range( int(len(directions)/2) ):
        if gc.can_blueprint(u.id, bp, left):
            gc.blueprint(u.id, bp, left)
            return
        if gc.can_blueprint(u.id, bp, right):
            gc.blueprint(u.id, bp, right)
            return
        left = left.rotate_left()
        right = right.rotate_right()

def replicate_worker(u):
    if gc.karbonite() >= 15:
        for d in (directions):
            if gc.can_replicate(u.id, d):
                gc.replicate(u.id,d)
                return

def build_structures(u):
    nearby = gc.sense_nearby_units(u.location.map_location(), 2)
    for units in nearby:
        if units.unit_type == bc.UnitType.Factory or units.unit_type == bc.UnitType.Rocket:
            if gc.can_build(u.id, units.id):
                gc.build(u.id,units.id)
                return

def blueprint_factory(u):
    if gc.karbonite() >= bc.UnitType.Factory.blueprint_cost():
        loc = u.location.map_location()

        d = loc.direction_to(root.location.map_location())
        blueprint_out(u, d, bc.UnitType.Factory)

def blueprint_rocket(u):
    if gc.karbonite() >= bc.UnitType.Rocket.blueprint_cost():
        loc = u.location.map_location()

        d = loc.direction_to(root.location.map_location()) #TODO change to nearby troops
        blueprint_out(u, d, bc.UnitType.Factory)

def mine_karbonite(u):
    bk = best_karbonite(u)
    if bk:
        d = u.location.map_location().direction_to(bk)

        if gc.can_harvest(u.id, d):
            gc.harvest(u.id, d)

        if gc.is_move_ready(u.id):
            spread_out(u, d)

def worker(u):
    if u.location.is_on_map():
        nearby = gc.sense_nearby_units(u.location.map_location(), u.vision_range)
        nearby_en = [n for n in nearby if n.team == op_team]
        nearby_fr = [n for n in nearby if n.team == my_team]

        add_enemies(nearby_en)

        print("\t{}".format(nu))
        if nu == bc.UnitType.Worker:
            replicate_worker(u)

        if not run_away(u, nearby_en):

            if group_up(u, nearby_fr):
                #Structures
                build_structures(u)

                if buildings[bc.UnitType.Factory]["count"] <= buildings[bc.UnitType.Factory]["cap"]:
                    blueprint_factory(u);

                if buildings[bc.UnitType.Rocket]["count"] <= buildings[bc.UnitType.Rocket]["cap"]:
                    blueprint_rocket(u)

                #Mining
                mine_karbonite(u)

"""
Knight
"""

def knight(u):
    """ we actually dont need knights rn """
    # if u.location.is_on_map():
    #     closest_en = closest_enemy(u)
    #     if closest_en:
    #         if u.location.map_location().distance_squared_to( closest_en.location.map_location() ) <= u.vision_range:
    #             if gc.is_attack_ready(u.id):
    #                 if gc.can_sense_unit(closest_en.id) and gc.can_attack(u.id, closest_en.id):
    #                     gc.attack(u.id,closest_en.id)
    #
    #     if gc.is_move_ready(u.id):
    #         if not run_away(u):
    #             if u.location.map_location().distance_squared_to( closest_en.location.map_location() ) <= u.vision_range:
    #                 move_toward_enemy(u, closest_en)
    #             else:
    #                 path = find_path( u.location.map_location(), closest_en.location.map_location() )
    #                 if path:
    #                     unit_dest[u.id] = path
    #                 move_toward_dest(u, closest_en)

"""
Rangers and Mages
"""
def guard(u, nearby_fr):
    if gc.is_move_ready(u.id):
        if len(nearby_fr) < 0:
            d = u.location.map_location().direction_to( root.location.map_location() )
            spread_out(u, d)
            return

        dist = [ (fr, u.location.map_location().distance_squared_to( fr.location.map_location() )) for fr in nearby_fr]
        fr = min(dist, key = lambda t: t[1])
        print("\t",fr[1])

        if fr[1] <= 3:
            d = u.location.map_location().direction_to( fr[0].location.map_location() ).opposite()
            spread_out(u, d)
            return

        elif fr[1] > 8:
            d = u.location.map_location().direction_to( fr[0].location.map_location() )
            spread_out(u, d)
            return

def battle(u, en):
    dist = u.location.map_location().distance_squared_to( en.location.map_location() )
    ran  = 0

    try:
        ran = en.attack_range()
    except:
        pass

    if dist > u.attack_range():
        if gc.is_move_ready(u.id):
            d = u.location.map_location().direction_to( en.location.map_location() )
            spread_out(u, d)

    elif u.attack_range() > ran:
        if gc.is_attack_ready(u.id) and gc.can_attack(u.id, en.id):
            gc.attack(u.id, en.id)
            if en not in fight_en:
                fight_en.append(en)

        if gc.is_move_ready(u.id):
            d = u.location.map_location().direction_to( en.location.map_location() )
            spread_out(u, d)
    else:
        if gc.is_attack_ready(u.id) and gc.can_attack(u.id, en.id):
            gc.attack(u.id, en.id)
            if en not in fight_en:
                fight_en.append(en)

        if gc.is_move_ready(u.id):
            d = u.location.map_location().direction_to( en.location.map_location() ).opposite()
            spread_out(u, d)

def pursue(u):
    if gc.is_move_ready(u.id):
        dist = [ (loc, u.location.map_location().distance_squared_to( loc )) for loc in fight_loc]
        loc = min(dist, key = lambda t: t[1])

        d = u.location.map_location().direction_to( loc[0] ).opposite()
        spread_out(u, d)

def ranger(u):
    if u.location.is_on_map():
        nearby = gc.sense_nearby_units(u.location.map_location(), u.attack_range())
        nearby_en = [n for n in nearby if n.team == op_team]
        nearby_fr = [n for n in nearby if n.team == my_team]

        add_enemies(nearby_en)

        if len(nearby_en) > 0:
            bad_guy = worst_enemy(u, nearby_en)
            battle(u, bad_guy)
        elif len(fight_loc) > 0:
            pursue(u)
        else:
            guard(u, nearby_fr)

def mage(u):
    if u.location.is_on_map():
        nearby = gc.sense_nearby_units(u.location.map_location(), u.attack_range())
        nearby_en = [n for n in nearby if n.team == op_team]
        nearby_fr = [n for n in nearby if n.team == my_team]

        add_enemies(nearby_en)

        if len(nearby_en) > 0:
            bad_guy = worst_enemy(u, nearby_en)
            battle(u, bad_guy)
        elif len(fight_loc) > 0:
            pursue(u)
        else:
            guard(u, nearby_fr)

"""
Healers
"""
def go_to_heal(u, nearby_fight):
    if gc.is_move_ready(u.id):
        d = u.location.map_location().direction_to( nearby_fight )
        spread_out(u, d)

def heal_lowest_unit(u, nearby_fr):
    if gc.is_heal_ready(u.id):
        health = [ (fr, fr.max_health - fr.health) for fr in nearby_fr]
        fr = max(health, key = lambda t: t[1])

        if gc.can_heal(u.id, fr[0].id):
            gc.heal(u.id, fr[0].id)

def nearest_fight(u):
    dist = [ (loc, u.location.map_location().distance_squared_to( loc )) for loc in fight_loc]
    loc = min(dist, key = lambda t: t[1])
    return loc[0]

def healer(u):
    if u.location.is_on_map():
        nearby = gc.sense_nearby_units(u.location.map_location(), u.vision_range)
        nearby_en = [n for n in nearby if n.team == op_team]
        nearby_fr = [n for n in nearby if n.team == my_team]

        if len(fight_loc) > 0:
            nearby_fight = nearest_fight(u)
            if u.location.map_location().distance_squared_to( nearby_fight ) < u.attack_range():
                if len(nearby_fr) > 0:
                    heal_lowest_unit(u, nearby_fr)
            go_to_heal(u, nearby_fight)
        else:
            guard(u, nearby_fr)

"""
Factory
"""
def deploy_troop(u):
    for d in directions:
        if gc.can_unload(u.id, d):
            gc.unload(u.id, d)

def factory(u):
    garrison = u.structure_garrison()
    if len(garrison) > 0:
        deploy_troop(u)

    if gc.can_produce_robot(u.id, nu):
        gc.produce_robot(u.id, nu)

"""
Rocket
"""

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
    global root
    root = random.choice(gc.my_units())
    while True:
        print("EARTH {}, K: {} \n".format(gc.round(), gc.karbonite()))

        verify_enemy()
        scan_enemies()
        scan_friendlies()

        # calculate_gradient()

        count_unit()
        next_unit()

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

my_team = gc.team()
op_team = get_enemy_team(my_team)

unit_dict = {
    bc.UnitType.Worker : worker,
    bc.UnitType.Knight : knight,
    bc.UnitType.Ranger : ranger,
    bc.UnitType.Mage : mage,
    bc.UnitType.Healer : healer,
    bc.UnitType.Rocket : rocket,
    bc.UnitType.Factory : factory
}

init_setup()
if gc.planet() == bc.Planet.Earth:
    earth()
else:
    mars()
