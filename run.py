import battlecode as bc
import random
import sys
import traceback

"""
Help:

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
Helper Methods
"""
def next_turn():
    gc.next_turn()
    sys.stdout.flush()
    sys.stderr.flush()
def manage_updates():
    pass

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
Planet Control
"""
def earth():
    my_map = gc.starting_map(gc.planet())
    my_coms = gc.get_team_array(gc.planet())
    pass
def mars():
    my_map = gc.starting_map(gc.planet())
    my_coms = gc.get_team_array(gc.planet())
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