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
        return "Connor Peck and Eldon Lake"

    def compute_next_move(self):
        if agentsim.debug.get(128):
            pass
        '''
        get the nearest normal. Determine if there is a defender "between" that
        normal. By "between" I mean:
        _______________________________________________
        |                                              |
        |                                              |
        |                             N                |
        |                           (/)                |
        |                          (/) D               |
        |                         (/)                  |
        |                         Z                    |
        |                                              |
        |                                              |
        |                                              |
        |                                              |
        _______________________________________________
        
        Above is my best approximation of a "circle": so, take the vector 
        between the zombie and the normal. Get the magnitude of the vector
        between the zombie and the normal. Divide the vector into n parts
        at each point in the separation of Z and N, determine from the defender
        stockpile whether there is a defender in the circle of radius the magn
        --itude of the vector between Z and N centered at each point of 
        separation. If there is, then choose the next nearest normal; repeat
        this procedure until there are no normals remaining.
        '''
        defenders = defender.Defender.get_all_present_instances()
        normals = normal.Normal.get_all_present_instances()

        (dx, dy) = (0, 0)
        
        # priority 1: get nearest undefended normal
        target = self.nearest_undefended(normals, defenders)
        if target: # then there is an undefended target
            (dx, dy) = self.attack_target(target)
        else:
            pass
            #target = self.nearest(normals)
            
        return (dx, dy)
        
    def nearest_undefended(self, normals, defenders):
        '''
        Finds a nearby target that's far away from a defender.
        Returns that target.
        '''
        sorted_n = [(n, self.distances_to(n)[0]) for n in normals]
        sorted_n.sort(key = (lambda x: x[1])) # didn't work on 1 line :/
        
        nearest_undefended = [None, None]
        while (sorted_n):
            nearest = sorted_n.pop(0)
            if not self.defender_between(nearest[0], defenders):
                nearest_undefended = nearest
                break

        return nearest_undefended[0]

    def defender_between(self, normal, defenders):
        '''
        if there is a defender between self and normal, return 1; else return
        0. Between here is described above, but to reiterate: 
        1) take the vector of my position minus the normal position, 
        2) mangitudize this vector to be the radius, 
        3) scalar multiply the vector between self and normal by 1/n, n int
        4) go by intervals of 1/n along the vector, and check if a defender 
           lies in a circle about that point of radius defined above
        '''
        x_start = self.get_xpos()
        x_end = normal.get_xpos()
        y_start = self.get_ypos()
        y_end = normal.get_ypos()


        vector_reg = Vector(x_start - x_end, y_start - y_end)
        vector_norm = vector_reg.normalize()
        radius = vector_reg.magnitude() # radius
        n = 9 # division
        radius = radius / n
        # 3)
        while (vector_reg.magnitude() > radius):
            this_step = vector_norm * (radius/n)
            x_start = x_start - this_step.x()
            y_start = y_start - this_step.y()

            if self.defender_in_circle((x_start, y_start), radius, defenders):
                return 1
            vector_reg = Vector(x_start - x_end, y_start - y_end)

        return 0

    def defender_in_circle(self, center, radius, defenders):
        '''
        loop through defenders. If a defender is within the circle with given
        center c and radius r, return 1; if the coast is clear, return 0
        '''
        for d in defenders:
            v = Vector(d.get_xpos() - center[0], d.get_ypos() - center[1])
            if (v.magnitude() < radius):
                return 1
        return 0
        
    def attack_target(self, target):
        """
        Move towards target
        """
        v = Vector(target.get_xpos() - self.get_xpos(), 
                   target.get_ypos() - self.get_ypos())
        v = v.normalize()
        v = v * self.get_move_limit()
        
        return (v.x(), v.y())

    def attack_weakest(self):
        """
        Determines ANY normal that's furthest from a defender. Proximity to
        self is not considered. (In case you were trying to discern the
        difference between this and the similar function above)
        """
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

    def __sub__(self, other):
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
        """
        A simple function returning the magnitude of a straight line distance.
        """
        retval = (self.x() ** 2 + self.y() ** 2)**(1/2)
        if not retval:
            return (0.0000000000000000000001)
        return retval

    def normalize(self):
        """
        A simple function that normalizes a vector.
        """
        if (self.magnitude() == 0):
            return (float("inf"), float("inf"))
        return (self * (1 / self.magnitude()))
