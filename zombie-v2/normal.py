import random
import agentsim
from person import Person
from moveenhanced import MoveEnhanced
import callername
import re

# co-dependent imports
import zombie
import defender

class Normal(MoveEnhanced):

    def __init__(self, **keywords):

        MoveEnhanced.__init__(self, **keywords)

        # this records the information from the most recent
        # zombie alert move.  When compute_next_move() is called, 
        # this information can be processed.

        self._zombie_alert_args = None
        self._proxy_scaling = 100

        if agentsim.debug.get(2):
            print("Normal", self._name)

        self.set_happiness(1 - 2 * random.random())
        self.set_size(random.uniform(self.get_min_size(), self.get_max_size()))

    def get_author(self):
        return "Your names go here"

    def compute_next_move(self):
        # if we have a pending zombie alert, act on that first
        zombies = zombie.Zombie.get_all_present_instances()
        (x, y) = self.influence_map(zombies)
        return (x, y)

    def influence_map(self, zombies):
        ''' 
        get a direction to go based on the influence map determined by zombies,
        where each zombie influences my position based on the inverse of the
        inverse of the magnitude of the vector of their position and mine.
        '''
        relative_vectors = []
        for z in zombies:
            relative_vectors.append(Vector(self.get_xpos() - z.get_xpos(),
                                           self.get_ypos() - z.get_ypos()))
        
        move_to = Vector(0, 0)
        for v in relative_vectors:
            v = v * (1 / v.magnitude())
            move_to = move_to + v
        
        move_to = move_to.normalize() * self.get_move_limit()
        return (move_to.x(), move_to.y())

    def zombie_alert(self, x_dest, y_dest):
        # ignore any request not from a defender!
        caller_name = callername.caller_name()

        if not re.search(r"\.Defender\.", caller_name):
            raise Exception("zombie alert on {} called by non-Defender {}".format(self.get_name(), caller_name))

        if agentsim.debug.get(32):
            print("zombie_alert to ({}, {})".format( self.get_name(), x_dest, y_dest))

        # remember where the alert told us to go so that we can use this
        # information when we compute the next move
        self._zombie_alert_args = (x_dest, y_dest)


class Vector():
    ''' 
    this is a vector class; for now assume only two-dimensional

    >>> v = Vector(1, 1)
    >>> v.x()
    1
    >>> v.y()
    1

    >>> print(v)
    (1, 1)
    
    >>> w = Vector(2, 3)
    >>> v + w
    (3, 4)

    >>> v * 2
    (2, 2)

    >>> v.magnitude()
    >>> v.normalize()
    '''
    def __init__(self, x, y):
        self._x = x
        self._y = y
        
    def x(self):
        return self._x

    def y(self):
        return self._y

    def __repr__(self):
        return "({}, {})".format(self.x(), self.y())

    def __add__(self, other):
        if not isinstance(other, Vector):
            raise ValueError

        new_x = self.x() + other.x()
        new_y = self.y() + other.y()
        return Vector(new_x, new_y)

    def __mul__(self, other):
        try:
            new_x = self.x() * other
            new_y = self.y() * other
            return Vector(new_x, new_y)
        except: # dunno what the error might be, other should be scalar neway
            return self # I guess pretend none of this ever happened?

    def magnitude(self):
        return (self.x() ** 2 + self.y() ** 2)**(1/2)

    def normalize(self):
        return (self * (1 / self.magnitude()))

