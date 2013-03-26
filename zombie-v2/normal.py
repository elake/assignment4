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
        return "Connor Peck and Eldon Lake"

    def n_wall(self):
        """
        This function is used to create a "fake zombie" for the influence map.
        It works by detecting which walls you are closest to, and then making
        the fake zombie get closer to you as you approach walls. This helps
        you to avoid getting trapped against a wall or backed into a corner.
        Returns the coordinates of the fake zombie.

        Legend:
        zinf  - Lower values give the fake zombie a greater influence.
        x_trv - How far along the x axis you have travelled. 0-1.
        y_trv - How far along the y axis you have travelled. 0-1.
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

        # Generate coordinates based on current position of self.
        try: ny = my_y + (zinf / (-0.5 + y_trv))
        except ZeroDivisionError:
            ny = float("inf") # If you're in the center, fake zombie irrelevant.
        try: nx = my_x + (zinf / (-0.5 + x_trv))
        except ZeroDivisionError:
            ny = float("inf")

        return (nx, ny)

    def compute_next_move(self):
        # Pending zombie alerts are disregarded
        zombies = zombie.Zombie.get_all_present_instances()
        (dx, dy) = self.influence_map(zombies)
        
        x_pos = self.get_xpos()
        y_pos = self.get_ypos()
        try: y_dir = (dy / abs(dy))
        except ZeroDivisionError:
            y_dir = 1 # Direction of 0 magnitude movement irrelevant.
        try: x_dir = (dx / abs(dx))
        except ZeroDivisionError:
            x_dir = 1
        
         
        (x_min, y_min, x_max, y_max) = agentsim.gui.get_canvas_coords()
        
        # This block changes running into walls into running along walls
        if not (x_min < x_pos + dx < x_max): # Out of bounds move.
            real_dx = min(x_min + x_pos, x_max - x_pos)
            dy = dy + (y_dir * (abs(dx)-abs(real_dx)))
            dx = x_dir*real_dx
        if not (y_min < y_pos + dy < y_max):
            real_dy = min(y_min + y_pos, y_max - y_pos)
            dx = dx + (x_dir * (abs(dy)-abs(real_dy)))
            dy = y_dir*real_dy
        
        """
        The following lines prevent you from becoming trapped in a corner. Our
        influene map currently uses "fake zombies" to prevent you from entering
        a corner in the first place, but we left this because we feared someone
        writing zombie code that somehow drove us into a corner despite our
        influence map. This code comes into play when you've already entered a
        corner. It determines if the average zombie position is above or below
        the diagonal running out of the corner you're in, and then commits your
        normal to crossing the corner at a 45 degree angle. Normals will not
        change trajectory while crossing because that's how you get trapped.

        Legend:
        nf   - How close you need to be to the corner to cross it
        gd   - Equals 1 if you are committed to crossing the corner
        gr   - Equals 1 if you are committed in the opposite direction
        """

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
                gd = 1 # Commit to this direction
            else: # Go right
                dx = self.get_move_limit()
                dy = self.get_move_limit() * -1
                gr = 1
        else: (gr, gd) = (0, 0) # You've finished crossing

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

    def avg_c_side(self, d1, d2, zombies):
        """
        Determines which side the zombies are approaching a corner from. d1
        determines whether the corner you are checking is on the top or bottom
        of the canvas and d2 determines left or right. From there it checks if
        the average zombie coordinate is above or below the diagonal drawn from
        your corner.

        Returns 0 for the Zombie approaching from the bottom and 1 for
        the Zombie approaching from the top.

        Legend:
        
        x_trv - Distance travelled across the x axis. 0-1.
        """
        (zx, zy) = center_of_mass(zombies)
        (x_min, y_min, x_max, y_max) = agentsim.gui.get_canvas_coords()
        x_trv = (zx/ (x_max-x_min))
        if d1*d2 < 0:
            x_trv = 1 - x_trv
        if x_trv < (zy / (y_max-y_min)):
                return 0
        else: return 1
        
    def influence_map(self, zombies):
        ''' 
        Get a direction to go based on the influence map determined by all
        other persons on the map. By accounting for all other persons and not
        just zombies, we avoid getting stuck by colliding with one another. The
        degree of influence that a person has on the map is inversely
        proportional to their distance from self.
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
        
        move_to = Vector(0, 0)
        for v in rel_vectors:
            v = v * (1 / v.magnitude() ** 3)
            move_to = move_to + v
        
        move_to = move_to.normalize() * self.get_move_limit()

        return (move_to.x(), move_to.y())

    def zombie_alert(self, x_dest, y_dest):
        """
        This code was provided in class, and left here for completeness' sake,
        but is never actually called and can be ignored.
        """
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
    Get and return the center of mass of the given persons
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
        except: # dunno what the error might be, other should be scalar anyway
            return self # I guess pretend none of this ever happened?

    def magnitude(self):
        """
        A simple function to return the magnitude of a direct distance.
        """
        retval = (self.x() ** 2 + self.y() ** 2)**(1/2)
        if not retval:
            return (0.0000000000000000000001)
        return retval

    def normalize(self):
        """
        A simple function to normalize a vector.
        """
        if (self.magnitude() == 0):
            return (float("inf"), float("inf"))
        return (self * (1 / self.magnitude()))

