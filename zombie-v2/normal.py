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
 
        if agentsim.debug.get(2):
            print("Normal", self._name)

        self.set_happiness(1 - 2 * random.random())
        self.set_size(random.uniform(self.get_min_size(), self.get_max_size()))

    def get_author(self):
        return "Your names go here"

    def n_wall(self):
        """
        returns the coordinates of a fake zombie that keeps you away from walls
        """
        zinf = 15
        (my_x, my_y) = (self.get_xpos(), self.get_ypos())
        (x_min, y_min, x_max, y_max) = agentsim.gui.get_canvas_coords()
        x_trv = (my_x / (x_max - x_min))
        y_trv = (my_y / (y_max - y_min))
        if x_trv > 0.5:
            x_closest = x_max
        else:
            x_closest = x_min
        if y_trv > 0.5:
            y_closest = y_max
        else:
            y_closest = y_min

        """
        if abs(0.5 - x_trv) > abs(0.5 - y_trv):
            ny = my_y
            nx = sum([my_x, x_closest]) / 2
        else:
            ny = sum([my_y, y_closest]) / 2
            nx = my_x
        """

        ny = my_y + (zinf / (-0.5 + y_trv))
        nx = my_x + (zinf / (-0.5 + x_trv))

        return (nx, ny)

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
        
        nf = 50
        
        try: gd
        except UnboundLocalError: gd = 0
        try: gr
        except UnboundLocalError: gr = 0

        # Top left corner
        if self.get_xpos() < (x_min + nf) and self.get_ypos() < (y_min + nf):
            if self.avg_c_side(1, 1, zombies) or gd and not gr: # Go down
                dx = self.get_move_limit() * -1
                dy = self.get_move_limit()
                gd = 1
            else: # Go right
                dx = self.get_move_limit()
                dy = self.get_move_limit() * -1
                gr = 1
        else: (gr, gd) = (0, 0)

        # Bottom left corner
        if self.get_xpos() < (x_min + nf) and self.get_ypos() > (y_max - nf):
            if self.avg_c_side(-1, 1, zombies) or gd and not gr: # Go right
                dx = self.get_move_limit() 
                dy = self.get_move_limit()
                gd = 1
            else: # Go up
                dx = self.get_move_limit() * -1
                dy = self.get_move_limit() * -1 
                gr = 1
        else: (gr, gd) = (0,0)

        # Top right corner
        if self.get_xpos() > (x_max - nf) and self.get_ypos() < (y_min + nf):
            if self.avg_c_side(1, -1, zombies) or gd and not gr: # Go down
                dx = self.get_move_limit()
                dy = self.get_move_limit()
                gd = 1
            else: # Go left
                dx = self.get_move_limit() * -1
                dy = self.get_move_limit() * -1
                gr = 1
        else: (gr, gd) = (0,0)
            
        # Bottom right corner
        if self.get_xpos() > (x_max - nf) and self.get_ypos() > (y_max - nf):
            if self.avg_c_side(-1, -1, zombies) or gd and not gr: # Go left
                dx = self.get_move_limit() * -1
                dy = self.get_move_limit()
                gd = 1
            else: # Go up
                dx = self.get_move_limit()
                dy = self.get_move_limit() * -1
                gr = 1
        else: (gr, gd) = (0,0)

        return (dx, dy)

    def nearest_z(self):
        """
        Returns the zombie nearest you
        """
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
            return near_z

    def corner_side(self, z, d1, d2):
        """
        Determines which side a zombie is approaching a corner from. d1
        determines whether the corner is on the top or bottom of the canvas
        and d2 determines left or right.

        Returns 0 for the Zombie approaching from the bottom and 1 for
        the Zombie approaching from the top.
        """
        (zx, zy) = (z.get_xpos(), z.get_ypos())
        (x_min, y_min, x_max, y_max) = agentsim.gui.get_canvas_coords()
        x_travelled = (zx/ (x_max-x_min))
        if d1*d2 < 0:
            x_travelled = 1 - x_travelled
        if x_travelled < (zy / (y_max-y_min)):
                return 0
        else: return 1

    def avg_c_side(self, d1, d2, zombies):
        """
        Determines which side the zombies are approaching a corner from. d1
        determines whether the corner is on the top or bottom of the canvas
        and d2 determines left or right.

        Returns 0 for the Zombie approaching from the bottom and 1 for
        the Zombie approaching from the top.
        """
        (zx, zy) = center_of_mass(zombies)
        (x_min, y_min, x_max, y_max) = agentsim.gui.get_canvas_coords()
        x_travelled = (zx/ (x_max-x_min))
        if d1*d2 < 0:
            x_travelled = 1 - x_travelled
        if x_travelled < (zy / (y_max-y_min)):
                return 0
        else: return 1
        
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
        for n in Normal.get_all_present_instances():
            if n.get_name() != self.get_name():
                rel_vectors.append(Vector(my_x - n.get_xpos(),
                                           my_y - n.get_ypos()))
        for d in defender.Defender.get_all_present_instances():
            rel_vectors.append(Vector(my_x - d.get_xpos(),
                                      my_y - d.get_ypos()))

        rel_vectors.append(Vector(my_x - self.n_wall()[0], 
                                  my_y - self.n_wall()[1]))
        
        """
        # don't get surrounded at the corner!
        # currently uses incomplete functions. I apologize for how crappy this
        # big block of if statements is. I'll hopefully have it cleaned up
        # by the time I submit this.
        of = 25
        nf = 80
        (min_x, min_y, max_x, max_y) = agentsim.gui.get_canvas_coords()
        
        # Top left corner
        # if self.get_xpos() < (min_x + nf) and self.get_ypos() < (min_y + nf):
        if self.corner_side(self.nearest_z(), 1, 1): # Go down
            rel_vectors.append(Vector(my_x - (min_x), my_y - (min_y)))
        else: # Go right
            rel_vectors.append(Vector(my_x - (min_x), my_y - (min_y)))
            print("Zombie coming from {n}".format(n=self.corner_side(self.nearest_z(), 1, 1)))

        # Bottom left corner
        #if self.get_xpos() < (min_x + nf) and self.get_ypos() > (max_y - nf):
        if self.corner_side(self.nearest_z(), -1, 1): # Go up
            rel_vectors.append(Vector(my_x - (min_x + 2*of), my_y - (max_y - of)))
        else: # Go right
            rel_vectors.append(Vector(my_x - (min_x + of), my_y - (max_y + of)))
            print("Zombie coming from {n}".format(n=self.corner_side(self.nearest_z(), -1, 1)))

        # Top right corner
        #if self.get_xpos() > (max_x - nf) and self.get_ypos() < (min_y + nf):
        if self.corner_side(self.nearest_z(), 1, -1): # Go down
            rel_vectors.append(Vector(my_x - (max_x - of), my_y - (min_y - of)))
        else: # Go left
            rel_vectors.append(Vector(my_x - (max_x + of), my_y - (min_y + of)))
            
        # Bottom right corner
        #if self.get_xpos() > (max_x - nf) and self.get_ypos() > (max_y - nf):
        if self.corner_side(self.nearest_z(), -1, -1): # Go left
            rel_vectors.append(Vector(my_x - (max_x + of), my_y - (max_y-of)))
        else: # Go up
            rel_vectors.append(Vector(my_x - (max_x - of), my_y - (max_y+of)))
        """
        move_to = Vector(0, 0)
        for v in rel_vectors:
            v = v * (1 / v.magnitude() ** 3)
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

def center_of_mass(persons):
    '''
    get and return the center of mass of the given persons
    '''
    zxs = [z.get_xpos() for z in persons]
    zys = [z.get_ypos() for z in persons]
    zx = sum(zxs) / len(zxs)
    zy = sum(zys) / len(zys)
    return (zx, zy)

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

