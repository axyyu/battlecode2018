#Battlecode
import battlecode as bc
import numpy as np
import random
import sys
import traceback
import math
import operator

# TODO IMPLEMENT Pathfinding

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
small_map = False
mesh_radius = 3
unit_limit = 100
run_threshold = 3
unit_weight = {
    bc.UnitType.Worker : 1,
    bc.UnitType.Knight : 4,
    bc.UnitType.Ranger : 6,
    bc.UnitType.Mage : 8,
    bc.UnitType.Healer : 6,
    bc.UnitType.Factory : 3,
    bc.UnitType.Rocket : 5
}
params = {
    bc.UnitType.Worker : {
        "ratio" : 0.15,
        "count" : 0,
        "cap" : 6
    },
    bc.UnitType.Knight : {
        "ratio" : 0.02,
        "count" : 0
    },
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
        "cap" : 2
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
landing_loc = []

fight_loc = []
fight_en = []

enemies = []
enemy_mesh = []
friendly_mesh = []
unit_grad = []

rocket_loc = []

directions = list(bc.Direction)
unit_types = list(bc.UnitType)

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
Unit Spawning
"""
def count_unit():
    global fight_loc, rocket_loc
    fight_loc = []
    rocket_loc = []
    for u in unit_types:
        if u in params:
            params[u]["count"] = 0
        if u in buildings:
            buildings[u]["count"] = 0
    for u in gc.my_units():
        if u.location.is_on_map():
            if u.unit_type in params:
                params[u.unit_type]["count"] += 1
            if u.unit_type in buildings:
                buildings[u.unit_type]["count"] +=1
            if u.unit_type == bc.UnitType.Rocket:
                rocket_loc.append( u.location.map_location() )
            if u.health < u.max_health and u.unit_type != bc.UnitType.Factory and u.unit_type != bc.UnitType.Rocket:
                fight_loc.append(u.location.map_location())

def next_unit():
    global nu
    units = []
    for k in params:
        c = params[k]["count"]
        r = params[k]["ratio"]
        if r != 0:
            units.append( (k, c/r) )
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

def obtain_landing_locations():
    global landing_loc
    planet_map = gc.starting_map(bc.Planet.Mars)

    first_mesh = [ [ 0 for y in range(planet_map.height) ] for x in range(planet_map.width) ]

    for x in range(planet_map.width):
        for y in range(planet_map.height):
            loc = bc.MapLocation(bc.Planet.Mars,x,y)

            if planet_map.on_map(loc) and planet_map.is_passable_terrain_at(loc):
                first_mesh[x][y] = 1

    neighorhood_loc = {}

    for x in range(1, planet_map.width-1):
        for y in range(1, planet_map.height-1):

            if first_mesh[x][y] == 1:
                neighbors = -1
                for a in range(-1, 2):
                    for b in range(-1, 2):
                        neighbors += first_mesh[x+a][y+b]

                if neighbors > 0:
                    neighorhood_loc[ (x, y) ] = neighbors

    sorted_locations = sorted( neighorhood_loc.items(), key = operator.itemgetter(1), reverse=True)
    print("\n NUMBER OF LANDING LOCATIONS : {} \n".format(len(sorted_locations)) )
    for loc in sorted_locations:
        x, y = loc[0]
        landing_loc.append( (bc.MapLocation(bc.Planet.Mars, x, y), loc[1]) )

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
def best_karbonite(u):
    loc = u.location.map_location()

    if gc.karbonite_at(loc):
        return loc
    for r in range (1, u.vision_range):
        kar = 0
        karloc = None
        for d in directions:
            newloc = loc.add_multiple(d, r)
            try:
                if gc.karbonite_at(newloc) > kar:
                    karloc = newloc
            except:
                pass
        if karloc:
            return karloc

"""
Enemy Detection
"""
def get_enemy_team(my_team):
    if my_team == bc.Team.Red:
        return bc.Team.Blue
    return bc.Team.Red

def verify_enemy():
    for en in fight_en:
        try:
            if not gc.can_sense_unit(en.id):
                fight_en.remove(en)
        except Exception as e:
            if str(e) != "b'The location is outside your vision range.'":
                fight_en.remove(en)

def closest_enemy(u, nearby_en):
    dist = [ (en, u.location.map_location().distance_squared_to( en.location.map_location() )) for en in nearby_en]
    if len(dist)>0:
        return min(dist, key = lambda t: t[1])[0]
    else:
        return None

def worst_enemy(u, nearby_at):
    # for n in nearby_at:
    #     if n in fight_en:
    #         return n
    en = []
    for n in nearby_at:
        if n.location.is_on_map():
            weight = unit_weight[n.unit_type]
            dist = u.location.map_location().distance_squared_to( n.location.map_location() )
            health = n.max_health/n.health

            en.append( (n, weight+dist+health) )
    return max(en, key = lambda t: t[1])[0]

"""
Pathfinding
"""
def group_up(u, nearby_fr): # Workers to head toward factories
    if len(nearby_fr) >= min(3, len(gc.my_units())):
        return True

    if gc.is_move_ready(u.id):
        direction = u.location.map_location().direction_to( root.location.map_location() )
        if direction == bc.Direction.Center:
            return True
        spread_out(u, direction)
    return False

def run_away(u, nearby_en): # Run away from enemy troops toward safety
    if gc.is_move_ready(u.id):
        loc = u.location.map_location()
        if len(nearby_en) > 0:
            en = worst_enemy(u, nearby_en)

            if en and en.unit_type != bc.UnitType.Worker and en.unit_type != bc.UnitType.Factory and en.unit_type != bc.UnitType.Rocket:
                r = en.attack_range()
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

def wander(u):
    if gc.is_move_ready(u.id):
        d = random.choice(directions)
        spread_out(u, d)

"""
Worker Code
"""
def blueprint_out(u, d, bp):
    while d == bc.Direction.Center:
        d = random.choice(directions)
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
    if gc.karbonite() >= 60:
        for d in (directions):
            if gc.can_replicate(u.id, d):
                gc.replicate(u.id,d)
                return

def build_structures(u, nearby_fr):
    nearby_fr = sorted(nearby_fr, key = lambda x: u.location.map_location().distance_squared_to(x.location.map_location()) )
    for units in nearby_fr:
        if units.unit_type == bc.UnitType.Factory or units.unit_type == bc.UnitType.Rocket:
            if units.max_health != units.health:
                if gc.can_build(u.id, units.id):
                    gc.build(u.id,units.id)
                    return True
                if gc.can_repair(u.id, units.id):
                    gc.repair(u.id,units.id)
                    return True

                d = u.location.map_location().direction_to(units.location.map_location())
                if gc.is_move_ready(u.id):
                    spread_out(u, d)
                    return False

    return False

def blueprint_factory(u):
    if gc.round() < 20 and u != root:
        return
    if gc.karbonite() >= bc.UnitType.Factory.blueprint_cost():
        loc = u.location.map_location()

        d = loc.direction_to(root.location.map_location())
        blueprint_out(u, d, bc.UnitType.Factory)

def blueprint_rocket(u):
    if gc.karbonite() >= bc.UnitType.Rocket.blueprint_cost():
        loc = u.location.map_location()

        d = loc.direction_to(root.location.map_location()) #TODO change to nearby troops
        blueprint_out(u, d, bc.UnitType.Rocket)

def mine_karbonite(u):
    bk = best_karbonite(u)
    if bk:
        d = u.location.map_location().direction_to(bk)

        if gc.can_harvest(u.id, d):
            gc.harvest(u.id, d)

        if d != bc.Direction.Center:
            if gc.is_move_ready(u.id):
                spread_out(u, d)

        return True
    return False

def worker(u):
    if u.location.is_on_map():
        nearby_en = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, op_team)
        nearby_fr = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, my_team)
        nearby_rocket = gc.sense_nearby_units_by_type(u.location.map_location(), 2, bc.UnitType.Rocket)

        if gc.planet() == bc.Planet.Earth:
            if not small_map and gc.round() < 50 and u == root:
                if params[bc.UnitType.Worker]["count"] <= params[bc.UnitType.Worker]["cap"]:
                    replicate_worker(u)
                    params[bc.UnitType.Worker]["count"] += 1
            else:
                if nu == bc.UnitType.Worker and params[nu]["count"] <= params[nu]["cap"]:
                    replicate_worker(u)

        if not run_away(u, nearby_en):

            if not build_structures(u, nearby_fr):

                if gc.planet() == bc.Planet.Earth:

                    if group_up(u, nearby_fr) or len(fight_loc) < 1:

                        if (gc.round() > 100 and len(fight_loc) > 0) or gc.round() > 450:
                            if buildings[bc.UnitType.Rocket]["count"] <= buildings[bc.UnitType.Rocket]["cap"] or gc.karbonite() > 300 or gc.round() > 700:
                                blueprint_rocket(u)

                        if buildings[bc.UnitType.Factory]["count"] <= buildings[bc.UnitType.Factory]["cap"]:
                            blueprint_factory(u);

                        #Mining
                        if not mine_karbonite(u):
                            if u != root:
                                guard(u, nearby_fr)

                else:
                    if not mine_karbonite(u):
                        wander(u)

"""
Troops
"""

# BUG Sometimes the rangers don't attack a target right in front of their faces, not sure why?

def guard(u, nearby_fr):
    if gc.is_move_ready(u.id):
        if len(nearby_fr) <= 2:
            if root:
                d = u.location.map_location().direction_to( root.location.map_location() )
                spread_out(u, d)
            else:
                wander(u)
            return

        dist = [ (fr, u.location.map_location().distance_squared_to( fr.location.map_location() )) for fr in nearby_fr if fr != u]
        fr = min(dist, key = lambda t: t[1])

        if fr[1] <= 3:
            d = u.location.map_location().direction_to( fr[0].location.map_location() ).opposite()
            spread_out(u, d)
            return

        elif fr[1] > 6:
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

        if gc.is_attack_ready(u.id) and gc.can_attack(u.id, en.id):
            gc.attack(u.id, en.id)
            if en not in fight_en:
                fight_en.append(en)

    elif dist > ran+1:
        if gc.is_attack_ready(u.id) and gc.can_attack(u.id, en.id):
            gc.attack(u.id, en.id)
            if en not in fight_en:
                fight_en.append(en)

    else: # DIST < range
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

        d = u.location.map_location().direction_to( loc[0] )
        spread_out(u, d)

def chase(u, en):
    if gc.is_move_ready(u.id):
        d = u.location.map_location().direction_to( en.location.map_location() )
        spread_out(u, d)

def board_rocket(u, nearby_rocket):
    if len(nearby_rocket) > 0:
        dist = [ (rocket, u.location.map_location().distance_squared_to( rocket.location.map_location() )) for rocket in nearby_rocket]
        rocket = min(dist, key = lambda t: t[1])
        if gc.can_load(rocket[0].id, u.id):
            gc.load(rocket[0].id, u.id)
            return True
    return False

def run_toward_rocket(u):
    dist = [ (loc, u.location.map_location().distance_squared_to( loc )) for loc in rocket_loc]
    if len(dist)>0:
        r_loc = min(dist, key = lambda t: t[1])[0]

        d = u.location.map_location().direction_to( r_loc )
        spread_out(u, d)
    else:
        return None

def knight(u):
    if u.location.is_on_map():
        nearby_en = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, op_team)
        nearby_at = gc.sense_nearby_units_by_team(u.location.map_location(), u.attack_range(), op_team)
        nearby_fr = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, my_team)
        nearby_rocket = gc.sense_nearby_units_by_type(u.location.map_location(), 2, bc.UnitType.Rocket)

        if gc.planet() == bc.Planet.Earth:
            if gc.round() > 600:
                if not board_rocket(u, nearby_rocket):
                    run_toward_rocket(u)

            if len(nearby_at) > 0:
                bad_guy = worst_enemy(u, nearby_at)
                battle(u, bad_guy)
            elif len(nearby_en) > 0:
                bad_guy = closest_enemy(u, nearby_en)
                chase(u, bad_guy)
            elif not board_rocket(u, nearby_rocket):
                if len(fight_loc) > 0:
                    pursue(u)
                else:
                    guard(u, nearby_fr)
        else:
            if len(nearby_at) > 0:
                bad_guy = worst_enemy(u, nearby_at)
                battle(u, bad_guy)
            elif len(nearby_en) > 0:
                bad_guy = closest_enemy(u, nearby_en)
                chase(u, bad_guy)
            elif len(fight_loc) > 0:
                pursue(u)
            else:
                guard(u, nearby_fr)

def ranger(u):
    if u.location.is_on_map():
        nearby_en = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, op_team)
        nearby_at = gc.sense_nearby_units_by_team(u.location.map_location(), u.attack_range(), op_team)
        nearby_fr = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, my_team)
        nearby_rocket = gc.sense_nearby_units_by_type(u.location.map_location(), 2, bc.UnitType.Rocket)

        if gc.planet() == bc.Planet.Earth:
            if gc.round() > 600:
                if not board_rocket(u, nearby_rocket):
                    run_toward_rocket(u)

            if len(nearby_at) > 0:
                bad_guy = worst_enemy(u, nearby_at)
                battle(u, bad_guy)
            elif len(nearby_en) > 0:
                bad_guy = closest_enemy(u, nearby_en)
                chase(u, bad_guy)
            elif not board_rocket(u, nearby_rocket):
                if len(fight_loc) > 0:
                    pursue(u)
                else:
                    guard(u, nearby_fr)
        else:
            if len(nearby_at) > 0:
                bad_guy = worst_enemy(u, nearby_at)
                battle(u, bad_guy)
            elif len(nearby_en) > 0:
                bad_guy = closest_enemy(u, nearby_en)
                chase(u, bad_guy)
            elif len(fight_loc) > 0:
                pursue(u)
            else:
                guard(u, nearby_fr)

def mage(u):
    if u.location.is_on_map():
        nearby_en = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, op_team)
        nearby_at = gc.sense_nearby_units_by_team(u.location.map_location(), u.attack_range(), op_team)
        nearby_fr = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, my_team)
        nearby_rocket = gc.sense_nearby_units_by_type(u.location.map_location(), 2, bc.UnitType.Rocket)

        if gc.planet() == bc.Planet.Earth:
            if gc.round() > 600:
                if not board_rocket(u, nearby_rocket):
                    run_toward_rocket(u)

            if len(nearby_at) > 0:
                bad_guy = worst_enemy(u, nearby_at)
                battle(u, bad_guy)
            elif len(nearby_en) > 0:
                bad_guy = closest_enemy(u, nearby_en)
                chase(u, bad_guy)
            elif not board_rocket(u, nearby_rocket):
                if len(fight_loc) > 0:
                    pursue(u)
                else:
                    guard(u, nearby_fr)
        else:
            if len(nearby_at) > 0:
                bad_guy = worst_enemy(u, nearby_at)
                battle(u, bad_guy)
            elif len(nearby_en) > 0:
                bad_guy = closest_enemy(u, nearby_en)
                chase(u, bad_guy)
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
        nearby_en = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, op_team)
        nearby_fr = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, my_team)
        nearby_rocket = gc.sense_nearby_units_by_type(u.location.map_location(), 2, bc.UnitType.Rocket)

        if len(fight_loc) > 0:
            nearby_fight = nearest_fight(u)
            if u.location.map_location().distance_squared_to( nearby_fight ) < u.attack_range():
                if len(nearby_fr) > 0:
                    heal_lowest_unit(u, nearby_fr)

            # GET ON ROCKET GODDAMMIT

            if gc.planet() == bc.Planet.Earth:
                if gc.round() > 600:
                    if not board_rocket(u, nearby_rocket):
                        run_toward_rocket(u)

                if not board_rocket(u, nearby_rocket):
                    go_to_heal(u, nearby_fight)
            else:
                go_to_heal(u, nearby_fight)
        else:
            guard(u, nearby_fr)

"""
Factory
"""
def deploy_troop(u):
    d = random.choice(directions)

    left = right = d
    for a in range( int(len(directions)/2) ):
        if gc.can_unload(u.id, left):
            gc.unload(u.id, left)
            return
        if gc.can_unload(u.id, right):
            gc.unload(u.id, right)
            return
        left = left.rotate_left()
        right = right.rotate_right()

def factory(u):
    garrison = u.structure_garrison()
    if len(garrison) > 0:
        deploy_troop(u)

    if gc.can_produce_robot(u.id, nu) and ( sum([ params[c]["count"] for c in params]) < unit_limit or gc.karbonite() > 300 ):
        if nu == bc.UnitType.Worker:
            if params[nu]["count"] <= params[nu]["cap"]:
                gc.produce_robot(u.id, nu)
        else:
            gc.produce_robot(u.id, nu)

"""
Rocket
"""
def best_landing():
    if len(landing_loc) > 0:
        count = landing_loc[0][1]

        similar = [ 0 ]

        for l in range(len(landing_loc)):
            if landing_loc[l][1] == count:
                similar.append( l )

        land = random.choice(similar)
        return landing_loc.pop(land)[0]
    return False

def emergency_launch(u, nearby_en, garrison):
    if len(nearby_en) < 1:
        return False
    if u.health >= u.max_health:
        return False

    if len(garrison) > 0 or gc.round() > 740:
        loc = best_landing()

        if loc:
            if gc.can_launch_rocket(u.id, loc):
                gc.launch_rocket(u.id, loc)

                return True
    return False

def launch_rocket(u, garrison):
    if len(garrison) > 4:
        next_dur = gc.orbit_pattern().duration(gc.round()+1)
        cur_dur = gc.current_duration_of_flight()
        if cur_dur < next_dur or gc.round() > 600:
            loc = best_landing()

            if loc:
                if gc.can_launch_rocket(u.id, loc):
                    gc.launch_rocket(u.id, loc)

def rocket(u):
    if u.location.is_on_map():
        nearby_en = gc.sense_nearby_units_by_team(u.location.map_location(), u.vision_range, op_team)
        garrison = u.structure_garrison()

        if gc.planet() == bc.Planet.Earth:
            if not emergency_launch(u, nearby_en, garrison):
                launch_rocket(u, garrison)
        else:
            if len(garrison) > 0:
                deploy_troop(u)

"""
Planet Control
"""
def determine_root():
    if root is None or not gc.can_sense_unit(root.id):
        roots = []
        for u in gc.my_units():
            if u.location.is_on_map():
                friendlies = len(gc.sense_nearby_units_by_team( u.location.map_location(), u.vision_range, my_team ))
                enemies = len(gc.sense_nearby_units_by_team( u.location.map_location(), u.vision_range, op_team ))
                roots.append( (u, friendlies - 2*enemies) )

        if len(roots) > 0:
            loc = max(roots, key = lambda t: t[1])
            return loc[0]
        return None
    return root

def tweak_parameters(planet_map):
    global small_map
    if sum( [ len(gc.len(gc.sense_nearby_units_by_team( u.location.map_location(), u.vision_range, op_team ))) for u in gc.my_team() ] ):
        small_map = True
        params[bc.UnitType.Knight]["ratio"] = 0.4
    if planet_map.width > 30:
        params[bc.UnitType.Knight]["ratio"] = 0

def manage_upgrades(planet_map):
    upgrades = []
    if planet_map.width < 25:
        upgrades = [
        bc.UnitType.Knight, #25
        bc.UnitType.Ranger, #25
        bc.UnitType.Healer, #25
        bc.UnitType.Mage, #25
        bc.UnitType.Rocket, #100
        bc.UnitType.Knight, #75
        bc.UnitType.Mage, #75
        bc.UnitType.Healer, #100
        bc.UnitType.Ranger, #100
        bc.UnitType.Healer, #100
        bc.UnitType.Mage, #100
        ]
    else:
        upgrades = [
        bc.UnitType.Rocket, #100
        bc.UnitType.Ranger, #25
        bc.UnitType.Healer, #25
        bc.UnitType.Knight, #25
        bc.UnitType.Mage, #25
        bc.UnitType.Ranger, #100
        bc.UnitType.Healer, #100
        bc.UnitType.Healer, #100
        bc.UnitType.Knight, #75
        bc.UnitType.Mage, #75
        bc.UnitType.Mage, #100
        ]
    for u in upgrades:
        gc.queue_research(u)

def earth():
    global root

    earth_map = gc.starting_map(bc.Planet.Earth)
    manage_upgrades(earth_map)
    obtain_landing_locations()
    tweak_parameters(earth_map)

    while True:
        root = determine_root()

        # verify_enemy()

        count_unit()
        next_unit()

        for u in gc.my_units():
            # print(u.unit_type)
            verify_enemy()
            unit_dict[u.unit_type](u)
            # detect_enemy(u)
        next_turn()

def mars():
    while True:
        root = determine_root()

        # verify_enemy()

        count_unit()
        next_unit()

        for u in gc.my_units():
            verify_enemy()
            unit_dict[u.unit_type](u)
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

if gc.planet() == bc.Planet.Earth:
    earth()
else:
    mars()
