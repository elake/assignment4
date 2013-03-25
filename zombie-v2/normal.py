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
        (dx, dy) = self.influence_map(zombies)
        
        x_pos = self.get_xpos()
        y_pos = self.get_ypos()
        y_dir = (dy / abs(dy))
        x_dir = (dx / abs(dx))
        
         
        (x_min, y_min, x_max, y_max) = agentsim.gui.get_canvas_coords()
    
        if not (x_min < x_pos + dx < x_max): # Out of bounds move.
            real_dx = min(x_min + x_pos, x_max - x_pos)
            dy = dy + (y_dir * (abs(dx)-abs(real_dx)))
            dx = x_dir*real_dx
        if not (y_min < y_pos + dy < y_max):
            real_dy = min(y_min + y_pos, y_max - y_pos)
            dx = dx + (x_dir * (abs(dy)-abs(real_dy)))
            dy = y_dir*real_dy
        return (dx, dy)

    def nearest_zombie(self):
        """
        Returns the zombie nearest you
        """
        pass

    def corner_side(z, corner):
        """
        Determines which side a zombie is approaching a corner from
        """
        pass
        
    def influence_map(self, zombies):
        ''' 
        get a direction to go based on the influence map determined by zombies,
        where each zombie influences my position based on the inverse of the
        inverse of the magnitude of the vector of their position and mine.
        '''
        (my_x, my_y) = (self.get_xpos(), self.get_ypos())
        
        rel_vectors = []
        for z in zombies:
            rel_vectors.append(Vector(my_x - z.get_xpos(),
                                           my_y - z.get_ypos()))
        
        # don't get surrounded at the corner!
        # currently uses incomplete functions. I apologize for how crappy this
        # big block of if statements is. I'll hopefully have it cleaned up
        # by the time I submit this.
        of = 20
        (min_x, min_y, max_x, max_y) = agentsim.gui.get_canvas_coords()
        if top left corner self.get_xpos() < (min_x + of) and self.get_ypos() < (min_y + of):
            if corner_side(nearest_zombie(), tl) == "Go down":
                rel_vectors.append(Vector(my_x - (min_x + of), my_y - (min_y - of)))
            if corner_side(nearest_zombie(), tl) == "Go right":
                rel_vectors.append(Vector(my_x - (min_x - of), my_y - (min_y + of)))
        if bottom left corner self.get_xpos() < (min_x + of) and self.get_ypos() > (max_y - of):
            if corner_side(nearest_zombie(), bl) == "Go right":
                rel_vectors.append(Vector(my_x - (min_x + of), my_y - (max_y - of)))
            if corner_side(nearest_zombie(), bl) == "Go up":
                rel_vectors.append(Vector(my_x - (min_x + of), my_y - (max_y - of)))
        if top right self.get_xpos() > (max_x - of) and self.get_ypos() < (min_y + of):
            if corner_side(nearest_zombie(), tr) == "Go down":
                rel_vectors.append(Vector(my_x - (max_x - of), my_y - (min_y - of)))
            if corner_side(nearest_zombie(), tr) == "Go left":
                rel_vectors.append(Vector(my_x - (max_x + of), my_y - (min_y + of)))
        if self.get_xpos() > (max_x * 0.85) and self.get_ypos() > (max_y * 0.85):
            if corner_side(nearest_zombie(), br) == "Go left":
                rel_vectors.append(Vector(my_x - (max_x + of), my_y - (max_y-of)))
            if corner_side(nearest_zombie(), br) == "Go up":
                rel_vectors.append(Vector(my_x - (max_x - of), my_y - (max_y+of)))
        
        move_to = Vector(0, 0)
        for v in rel_vectors:
            v = v * (1 / v.magnitude() ** 2)
            move_to = move_to + v
        
        move_to = move_to.normalize() * self.get_move_limit()
        print("self.get_move_limit() = {s}".format(s=self.get_move_limit()))
        print("move to x: {a} move to y: {b}".format(a=move_to.x(), b=move_to.y()))
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
        retval = (self.x() ** 2 + self.y() ** 2)**(1/2)
        if not retval:
            return (0.0000000000000000000001)
        return retval

    def normalize(self):
        if (self.magnitude() == 0):
            return (float("inf"), float("inf"))
        return (self * (1 / self.magnitude()))

