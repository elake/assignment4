""" 
The zombie game

python3 zombiegame.py --normals nn --defenders nd --zombies nz --debug dflag

Perform the partygame simulation with initial conditions of 
    nn normals
    nd defenders
    nz zombies.
Also set the debug flag to dflag if present.  dflag is an unsigned integer 
representing a bit vector, where the power of two means:
      1 - agentsim framework related
      2 - Person or subclass related
      4 - Shape or subclass related
      8 - reserved
     16 - MoveEnhanced related
     32 - Normal
     64 - Defender
    128 - Zombie
    256 - Identify caller name

Eg.
    python3 zombiegame.py --defenders 2 --zombies 7 --normals 10

"""

import sys
import random

from person import Person
import moveenhanced
from normal import Normal
from zombie import Zombie
from defender import Defender

# globals - read only
person_size = 40
person_move_limit = 10

# globals - writable
# initial numbers of people of varous kinds
init_num_normals = 10
init_num_defenders = 3
init_num_zombies = 5

"""
    The teleport functionality is in the MoveEnhanced class.  But the function
    to check if one class can teleport another cannot be defined there because
    it needs to mention by name that a Defender instance can teleport a Zombie
    instance.

    So the moveenhanced module has a global function pointer called
    can_teleport that we bind to this function at initialization.

    can_teleport_fn is a constraint function that informs a MoveEnhanced object
    that is it permissible for the teleporter object to teleport the target 
    object

    It needs to be hooked into the MoveEnhanced class by this binding
        moveenhanced.can_teleport = can_teleport_fn
    because the MoveEnhanced class has no idea about the derived classes that
    might want to teleport.

    This really should be enforced at the level of the do_step() function
    in the simulator.
    """

def can_teleport_fn(teleporter, target):
    if not isinstance(teleporter, Defender):
        raise Exception("Error: teleporting object {} type is not Defender".format(type(teleporter)))

    if not isinstance(target,Zombie):
        raise Exception("Error: teleported object {} type is not Zombie".format(type(target)))

    return True


def create_persons(num_normals, num_defenders, num_zombies):
    
    for i in range(num_normals):
        Normal(size=person_size, haircolor='yellow', 
            move_limit=person_move_limit)

    for i in range(num_defenders):
        Defender(size=person_size, haircolor='blue', 
            move_limit=person_move_limit)

    for i in range(num_zombies):
        Zombie(size=person_size, haircolor='green', 
            move_limit=person_move_limit)


# position p into a random spot on the canvas, return True if it worked,
# False if the move would have collided with someone.
def position_randomly(p, x_min, x_max, y_min, y_max):
    # random spot in canvas
    x = random.randint(x_min, x_max)
    y = random.randint(y_min, y_max)

    # original position
    x_orig = p.get_xpos()
    y_orig = p.get_ypos()

    # internal method, not to be used other than as part of setup
    p._move_to(x, y)

    # if we didn't move, then we collided with someone, so return false
    return p.get_xpos() != x_orig or p.get_ypos() != y_orig

def do_init():

    # position everyone randomly about the canvas
    (x_min, y_min, x_max, y_max) = agentsim.gui.get_canvas_coords()

    # because we create additional zombies, we want to remove them 
    # from the simulation before we start.  We might as well remove all
    # the persons and start fresh.

    for p in Person.get_all_instances():
       Person.del_instance(p) 

    # create all the new people at the party
    create_persons(init_num_normals, init_num_defenders, init_num_zombies)

    # position them randomly about
    for p in Person.get_all_instances():
        i = 3
        while not position_randomly(p, x_min, x_max, y_min, y_max) and i > 0 :
            i -= 1

        # if after 3 tries we could not position p, then make it leave the party
        if i <= 0:
            print("Could not position {} into random spot".format(p.get_name()))
            p.leave()

    # have all the people arrive at the simulation before we start
    for p in Person.get_all_instances():
        p.arrive()


def do_step():
    # Buffer all the move_by calls and do at once.

    # Note that this does not buffer other state changes made in objects,
    # such as a teleport - we really should have that facility for a proper
    # simulation of a time step

    # we should also enforce the restriction on the move limit for each
    # type of object.  At the moment, you can get around this limit by calling
    # move_by in the compute_next_move method!

    moves = [ ]

    # give the defenders a chance to tell the normals what to do
    # and try to teleport any zombies

    for p in Defender.get_all_present_instances():
        moves.append( (p,) + p.compute_next_move() )

    # then give the normals a chance
    for p in Normal.get_all_present_instances():
        moves.append( (p,) + p.compute_next_move() )

    # and finally the zombies, which may have been teleported to new positions
    for p in Zombie.get_all_present_instances():
        moves.append( (p,) + p.compute_next_move() )

    # then execute the moves, even though other state may have been changed
    # earlier
    for (p, delta_x, delta_y) in moves:
        p.move_by(delta_x, delta_y)

    # then convert normals into zombies if the zombies are close enough

    # Warning: z - number of zombies, n - number of normals, then the
    # time complexity of this is O( z n )

    for z in Zombie.get_all_present_instances():
        for n in Normal.get_all_present_instances():
            d_e_e = z.distances_to(n)[3]
            d_touch = z.get_touching_threshold()

            # print(z.get_name(), n.get_name(), d_e_e, d_touch)

            if round(d_e_e,3) <= d_touch:

                x = n.get_xpos()
                y = n.get_ypos()

                new_z = Zombie(size=n.get_size(), haircolor='green', 
                    xpos = x, ypos = y, move_limit=person_move_limit)

                new_z.arrive()
                n.leave()

                Person.del_instance(n)


def main():
    """
    process the command line arguments
    """

    # we update these when processing arguments, so they are made global
    global init_num_normals
    global init_num_defenders
    global init_num_zombies

    arg_debug = 0
    arg_i = 1
    while arg_i < len(sys.argv):
        arg = sys.argv[arg_i]
        if arg == "--debug":
            arg_i += 1
            arg_debug = int(sys.argv[arg_i])
        elif arg == "--normals":
            arg_i += 1
            init_num_normals = int(sys.argv[arg_i])
        elif arg == "--defenders":
            arg_i += 1
            init_num_defenders = int(sys.argv[arg_i])
        elif arg == "--zombies":
            arg_i += 1
            init_num_zombies = int(sys.argv[arg_i])
        else:
            raise(Exception("Unknown command line argument " + arg))
        # next argument
        arg_i += 1

    # instantiate the framework
    agentsim.init(title="Zombie Game", init_fn=do_init, step_fn=do_step)

    agentsim.debug.set(arg_debug)
    agentsim.start()


if __name__ == "__main__":
    # if we don't have this conditional main body code, then pydoc3 gets
    # really cofused trying to partially run the code to extract out the
    # methods etc.

    # only bring in all the tk stuff when really running
    import agentsim

    # bind to the move enhanced class
    moveenhanced.can_teleport = can_teleport_fn

    main()
