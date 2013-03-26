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
        
        self._defending = None

        if agentsim.debug.get(2):
            print("Defender", self._name)
        

    def get_author(self):
        return "Your names go here"
    
    def set_defending(self, who):
        '''
        defend given person
        '''
        self._defending = who

    def get_defending(self):
        '''
        get the normal I am currently defending
        '''
        return self._defending

    def goto(self, x, y):
        '''
        tells self to go to the given coordinates, given that I have a move 
        limit; returns a vector scaled to my move limit pointing in the
        direction determined by the vector of my position and the given
        position
        '''
        v = Vector(-self.get_xpos() + x, -self.get_ypos() + y)
        v = (v.normalize()) * self.get_move_limit()
        return (v.x(), v.y())

    def compute_next_move(self):
        # intervention procedure:
        normals = normal.Normal.get_all_present_instances()
        if not normals: # nobody to defend
            return (0, 0) 
        zombies = zombie.Zombie.get_all_present_instances()
        other_defenders = Defender().get_all_present_instances()
        other_defenders.remove(self)

        '''
        nearest_z = self.nearest_z
        if (nearest_z):
            if (self.distances_to(nearest_z)[3] < self.
        '''

        (attacked_n, attacking_z) = self.intervene(normals, zombies,
                                                   other_defenders)
        if ((attacked_n is not None) and (attacking_z is not None)):
            # found someone to defend! so defend them!
            self.set_defending(attacked_n)
            line_between = Line((attacked_n.get_xpos(), attacked_n.get_ypos()), 
                                (attacking_z.get_xpos(), attacking_z.get_ypos()))
            my_position = (self.get_xpos(), self.get_ypos())
            perpendicular_point = line_between.perpendicular_from(my_position)
            # ah the drawbacks of goto being an otherwise-readable function:
            return self.goto(perpendicular_point[0], perpendicular_point[1])
        
        # intervention procedure has failed! Go to next procedure!
        return self.goto(self.get_xpos(), self.get_ypos())

    def intervene(self, normals, zombies, defenders):
        '''
        for each normal in normals.(sorted by distance), for each zombie in
        zombie.(sorted by distance) determine if there is a defender already
        between the normal and the zombie using code also in the zombie class
        if there is not, determine the point between these two to which to 
        move and return it using intervention_point.
        '''
        # sort normals and zombies by distance
        sorted_n = [(n, self.distances_to(n)[0]) for n in normals]
        sorted_n.sort(key = (lambda x: x[1])) # didn't work on 1 line :/

        for n in sorted_n: # holy crap is this ever an expensive algorithm!!
            sorted_z = [(z, self.distances_to(n[0])[0]) for z in zombies]
            sorted_z.sort(key = (lambda x: x[1])) # didn't work on 1 line :/
            for z in sorted_z:
                if self.intervention_criteria_satisfied(n[0], z[0], defenders): 
                    return (n[0], z[0])
        return (None, None) # if I couldn't find anyone to defend

    def intervention_criteria_satisfied(self, normal, zombie, defenders):
        '''
        determines whether I can intervene with the given zombie attacking the
        given normal. To determine this:
        0) determine whether the normal is aleady being defended, if so, move to
           the next normal
        1) determine whether there is a defender already between the normal
           and zombie. If so, criteria not satisfied
        2) return whether I can get between the normal and zombie. 

        '''
        if already_defended(normal, defenders):
            return 0

        if defender_between(normal, zombie, defenders):
            return 0
        
        return self.can_get_between(normal, zombie)


    def can_get_between(self, normal, zombie):
        '''
        to determine if I can get between, drop a perpendicular line to the line
        formed by the normal and the zombie, and check whether the point of 
        intersection of these two lines is contained in the line segment 
        starting at the normal and ending at the zombie. Here's a picture!!
        ______________________________   _____________________________
        |                     N      |  |                            |
        |                     |      |  |         N--------Z--       |
        |                     |      |  |                    |       |
        |               D-----|      |  |                    |       |
        |                     |      |  |                    |       |
        |                     Z      |  |                    D       |
        |                            |  |                            |
        |                            |  |                            |
        ______________________________   _____________________________
               CAN intervene                    CAN'T intervene 
        '''
        line = Line((normal.get_xpos(), normal.get_ypos()), 
                    (zombie.get_xpos(), zombie.get_ypos()))
        my_position = (self.get_xpos(), self.get_ypos())
        
        return line.contains_perpendicular_from(my_position)

    def nearest_z(self, zombies = None):
        """
        Returns the zombie nearest me;
        """
        if not zombies: # sometimes I will pass args, sometimes I won't!
            all_z = zombie.Zombie.get_all_present_instances()
        else:
            all_z = zombies

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
        else:
            return None

def defender_between(normal, zombie, defenders, fineness = 9):
    '''
    if there is a defender between self and normal, return 1; else return
    0. Between here is described above, but to reiterate: 
    1) take the vector of my position minus the normal position, 
    2) mangitudize this vector to be the radius, 
    3) scalar multiply the vector between self and normal by 1/n, n int
    4) go by intervals of 1/n along the vector, and check if a defender 
    lies in a circle about that point of radius defined above
    '''
    x_start = zombie.get_xpos()
    x_end = normal.get_xpos()
    y_start = zombie.get_ypos()
    y_end = normal.get_ypos()   
    
    vector_reg = Vector(x_start - x_end, y_start - y_end)
    
    vector_norm = vector_reg.normalize()
    radius = vector_reg.magnitude() 

    ##
    n = fineness
    # fineness; determines fineness of the line check; higher n for a higher
    # frequency of checks but a smaller circle about each point whereas lower
    # n means for faster but much-less-precise checks. If n is too low, for 
    # instance 2, this check determines whether there is a defender in a circle
    # of radius half the distance between the normal and zombie at the midpoint
    # of the line
    ##
    radius = radius / n
    while (vector_reg.magnitude() > radius):
        this_step = vector_norm * (radius/n)
        x_start = x_start - this_step.x()
        y_start = y_start - this_step.y()
        
        if circle_contains((x_start, y_start), radius, defenders):
            return 1
        vector_reg = Vector(x_start - x_end, y_start - y_end)
    return 0    

def circle_contains(center, radius, defenders):
    '''
    loop through defenders. If a defender is within the circle with given
    center c and radius r, return 1; if the coast is clear, return 0
    '''
    for d in defenders:
        v = Vector(d.get_xpos() - center[0], d.get_ypos() - center[1])
        if (v.magnitude() < radius):
            return 1
    return 0

def already_defended(normal, defenders):
    '''
    loop through defenders and return whether one of them is defending the given
    normal
    '''
    for d in defenders:
        if (d.get_defending() == normal):
            return 1
    return 0

def midpoint_between(person1, person2):
    '''
    determine the midpoint between the two persons on a canvas
    '''
    (n_x, n_y) = (person1.get_xpos(), person1.get_ypos())
    (z_x, z_y) = (person2.get_xpos(), person2.get_ypos())
    return ((n_x + z_x)/2, (n_y + z_y)/2)

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

class Line:
    '''
    geometric line class, defined in two-dimensional Cartesian coordinates
    with a starting point and an ending point
    ''' 
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def contains(self, point):
        
        x_in = min(self.start[0], self.end[0]) <= point[0] <= (
               max(self.start[0], self.end[0]))
        y_in = min(self.start[1], self.end[1]) <= point[1] <= (
               max(self.start[1], self.end[1]))

        return (x_in and y_in)

    def perpendicular_from(self, point):
        '''
        returns a point (x, y), foot of the perpendicular dropped from 
        point to this line
        '''     
        x1 = self.start[0]
        y1 = self.start[1]
        x2 = self.end[0]
        y2 = self.end[1]

        x3 = point[0]
        y3 = point[1]

        k = ((y2 - y1)*(x3 - x1) - (x2 - x1) * (y3 - y1)) / (
            (y2 - y1) ** 2 + (x2 - x1) ** 2 )
        
        return (x3 - (k * (y2 - y1)), y3 + (k * (x2 - x1)))

    def contains_perpendicular_from(self, point):
        '''
        there wasn't any nice way of checking to see whether this line contains
        the perpendicular from while saving that point that I could tell given
        the defender architecture, so I wrote this check to see whether this
        line contains the point calculated by the above; it's additional
        computing time but constant anyway as it's just a series of bit 
        operations and doing them twice isn't very expensive. But I'm sad I have
        to resort to this. Please let me know if you see an alternative!
        '''
        return self.contains((self.perpendicular_from(point)))


