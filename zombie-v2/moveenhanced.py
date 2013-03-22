import agentsim
from person import Person
import random
import callername

# we need to hook in the predicate that tests is one class is permitted
# to teleport another.  You can do importing here because the classes you
# want to mention are derived from MoveEnhanced.

global can_teleport

# need to have the properties of how close is close, and when zombies are
# close enough to turn a normal into a zombie.

class MoveEnhanced(Person):

    def __init__(self, move_limit = None, **keywords):

        """
        # fetch and remove the move_limit keyword so that we don't confuse
        # the explicit keywords in the Person constructor
        if "move_limit" in keywords:
            move_limit = abs(keywords["move_limit"])
            del(keywords["move_limit"])
        else:
            move_limit = None
        """

        # now ok to initialize parent
        Person.__init__(self, **keywords)

        # initialize the move limit
        self._move_limit = move_limit

        if agentsim.debug.get(2):
            print("MoveEnhanced", self._name)

    # returns True if self is exactly this class, not a subclass
    def is_exactly_MoveEnhanced(self):
        return repr(MoveEnhanced) == repr(type(self))

    def get_move_limit(self):
        return self._move_limit

    def get_max_size(self):
        return 60

    # overload set_size to prevent setting of size once created for any
    # derived class
    def set_size(self, size):
        # only let callers of the same type as me set my size
        my_name = callername.caller_name(level = 0)
        # get back module.class.method, match just the invoking class
        my_name_parts = my_name.split(".")
        my_class = my_name_parts[1]
        pattern = r"\." + my_class + r"\."
        callername.caller_name_match(pattern, 
            abort = True, debug = agentsim.debug.get(256))

        # ok, we can our size, but not too big
        super(MoveEnhanced, self).set_size(min(size, self.get_max_size()))

        # when you set your size, also change the move limit
        # nominal move limit is 10, range it from 5 to 15

        min_size = self.get_min_size()
        adjust = 10 * (
            (self.get_size() - min_size) / (self.get_max_size() - min_size) )

        if my_class == "Normal":
            # normals are slow when small, fast when big
            self._move_limit = 5 + adjust
        elif my_class == "Zombie":
            # normals are fast when small, slow when big
            self._move_limit = 15 - adjust

    # PRIVATE - no derived class is every supposed to call this.
    # it is just to support the simulation.

    def _move_to(self, x, y):
        # guard against anyone but the main program or teleport calling me
        callername.caller_name_match(
            "__main__|^moveenhanced.Defender.teleport$",
            abort = True,
            debug = agentsim.debug.get(256))
            
        old_move_limit = self._move_limit
        self._move_limit = None
        self.move_by(x - self.get_xpos(), y - self.get_ypos())
        self._move_limit = old_move_limit

    # overload move_by to make sure move is limited
    def move_by(self, delta_x, delta_y):
        # guard against anyone but the main program or _move_to calling me
        callername.caller_name_match(r"__main__|\._move_to$",
            abort = True,
            debug = agentsim.debug.get(256))

        if self._move_limit is not None:
            delta_d = (delta_x * delta_x + delta_y * delta_y) ** 0.5

            if delta_d > self._move_limit:
                delta_x = delta_x * self._move_limit / delta_d
                delta_y = delta_y * self._move_limit / delta_d

        # Don't allow you to move onto another person.  This means that if 
        # you are already on a person, you have to jump off by making a big
        # move.

        no_collision = True;
        # only collide with someone present
        for p in Person.get_all_present_instances():

            # would we collide with p?
            if self.is_near_after_move(p, delta_x, delta_y):
                if agentsim.debug.get(16):
                    print("MoveEnhanced.move_by", self.get_name(), "would collide with", p.get_name(), delta_x, delta_y)

                no_collision = False
                break

        # make the move if no collision
        if no_collision:
            if agentsim.debug.get(16):
                print("MoveEnhanced.move_by", self.get_name(), "moving by", delta_x, delta_y)
            super(MoveEnhanced, self).move_by(delta_x, delta_y)

    def is_near_after_move(self, target, delta_x, delta_y, epsilon = 0):
        # you are not near yourself
        if self is target: return False

        # distances before move
        (d, dx, dy, d_e_e) = self.distances_to(target)

        # after move
        dx = dx - delta_x
        dy = dy - delta_y
        d = (dx*dx + dy*dy) ** 0.5  - (self.get_size() + target.get_size()) / 2

        r = d <= epsilon 

        return r

    def is_near(self, target, epsilon = 0):
        # you are not near yourself
        if self is target: return False

        # near means within epsilon units or overlapping the other
        d_e_e = self.distances_to(target)[3]
        #round to reduce floating point precision errors
        return round(d_e_e,3) <= epsilon

    # if the e_to_e distance is <= this value, two persons are near to 
    # touch each other
    def get_touching_threshold(self):
        return 3;

    # if the e_to_e distance is <= this, a defender can teleport a zombie
    def get_teleport_threshold(self):
        return 3;

    # teleport person target to x_dest, y_dest if allowed.
    def teleport(self, target, x_dest, y_dest):
        if can_teleport is not None and can_teleport(self, target) and self.is_near(target, self.get_teleport_threshold()):
            if agentsim.debug.get(16):
                print("{} is teleporting {} to ({}, {})".format(
                    self.get_name(), target.get_name(), x_dest, y_dest))

            # the teleport occurs immediately, not bufferred like a move_by.
            # this means you can cheat by repeatedly calling teleport inside
            # the compute_next_move function. 
            target._move_to(x_dest, y_dest)

