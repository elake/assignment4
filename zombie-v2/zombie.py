import random
import agentsim
from person import Person
from moveenhanced import MoveEnhanced

# co-dependent imports
import normal
import defender

class Zombie(MoveEnhanced):

    def __init__(self, **keywords):
        MoveEnhanced.__init__(self, **keywords)
        self.set_happiness(1)

        if agentsim.debug.get(2):
            print("Zombie", self._name)

    def get_author(self):
        return "Your names go here"

    def compute_next_move(self):
        if agentsim.debug.get(128):
            pass
        if 1:
            delta_x = 0
            delta_y = 0

            # find nearest normal if there is one!
            all_n = normal.Normal.get_all_present_instances()
            if all_n:
                nearest = min(
                    # make pairs of (person, distance from self to person)
                    [ (n, self.distances_to(n)[0] ) for n in all_n ]
                    ,
                    # and sort by distance
                    key=(lambda x: x[1])
                    )

                (near_n, near_d) = nearest

                # move towards nearest normal
                (d, delta_x, delta_y, d_edge_edge) = self.distances_to(near_n)
            return (delta_x, delta_y)
        else:
            return self.attack_weakest()

    def attack_weakest(self):
        delta_x = 0
        delta_y = 0

        all_n = normal.Normal.get_all_present_instances()
        all_d = defender.Defender.get_all_present_instances()
        if all_d:
            print("all_d passed")
            victim = max([n for n in all_n], key=lambda x:
                             max([x.distances_to(d)[0] for d in all_d]))
            print("Victim is {v}".format(v=victim._name))
            (d, delta_x, delta_y, d_edge_edge) = self.distances_to(victim)
        return (delta_x, delta_y)
