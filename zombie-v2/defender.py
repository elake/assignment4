import random
import agentsim
from person import Person
from moveenhanced import MoveEnhanced

# Design note:
# The only reason for importing zombie and normal is to allow the class queries
# for zombies, normals such as
#   zombie.Zombie.get_all_instances()
# 
# If we used the import form:
#   from zombie import Zombie
# we would say
#   Zombie.get_all_instances()
# but this won't work because circular references would be created among 
# the three subclasses Zombies, Normals, and Defenders.  That is, the three
# classes are co-dependent in that they need to know that each other exists.

# The proper solution is that zombie, normal, defender would all be placed
# in the same module file to achieve the co-dependencies without the import.  
# But we want them in different files for the tournament.  There is never
# a good pure solution in the real world.

import zombie
import normal

class Defender(MoveEnhanced):
    """
    Goes around attempting to prevent zombies form reaching normals
    """

    def __init__(self, **keywords):
        MoveEnhanced.__init__(self, **keywords)

        if agentsim.debug.get(2):
            print("Defender", self._name)

    def get_author(self):
        return "Your names go here"

    def compute_next_move(self):
        delta_x = 0
        delta_y = 0

        # find nearest zombie if there is one!
        all_z = zombie.Zombie.get_all_present_instances()
        if all_z:
            nearest = min(
                # make pairs of (person, distance from self to person)
                [ (z, self.distances_to(z)[0] ) for z in all_z ]
                ,
                # and sort by distance
                key=(lambda x: x[1])
                )

            (near_z, near_d) = nearest

            # move towards nearest zombie
            (d, delta_x, delta_y, d_edge_edge) = self.distances_to(near_z)

            if agentsim.debug.get(64):
                print("nearest zombie to {} is {}, dx {} dy {}".format(
                    self.get_name(), near_z.get_name(), delta_x, delta_y, d_edge_edge))

            # but if close enough to teleport, send the zombie to a random
            # point instead
            if round(d_edge_edge,3) <= self.get_teleport_threshold() :
                (x_min, y_min, x_max, y_max) = agentsim.gui.get_canvas_coords()
                x = random.randint(x_min, x_max)
                y = random.randint(y_min, y_max)
                self.teleport(near_z, x, y)

            # and change happiness proportional to distance
            (w,h) = agentsim.gui.get_canvas_size()
            diag = (w*w + h*h) ** .5
            delta_h = min( d/diag, .05)
            if agentsim.debug.get(64):
                print("d", d, "diag", diag, "dh", delta_h)

            self.set_happiness(delta_h + self.get_happiness())

        # alert the normals
        for n in normal.Normal.get_all_present_instances():
            n.zombie_alert(0, 0)

        return (delta_x, delta_y)
