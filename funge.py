import math
import sys
from copy import deepcopy
from datetime import datetime
from random import choice


class FungeSpace:
    def __init__(self, path):
        with open(path) as f:
            lines = list(map(lambda l: l.rstrip(), f.readlines()))

        self.max_cols = 0
        self.cells = []
        for l in lines:
            t = list(map(lambda c: ord(c), l))
            t = list(filter(lambda v: v not in [10, 12, 13], t))
            if len(t) > self.max_cols:
                self.max_cols = len(t)
            self.cells.append(t)

        self.x_offset, self.y_offset = 0, 0

    # this checks if the coordinate is within the maximum rectangle
    # defined by this funge space
    def in_bounds_rect(self, x, y):
        gx, gy = x + self.x_offset, y + self.y_offset
        return (gy in range(0, len(self.cells)) and
                gx in range(0, self.max_cols))

    # this checks if this coordinate actually has a value (since the
    # space is represented as a jagged array to save memory)
    def in_bounds(self, x, y):
        gx, gy = x + self.x_offset, y + self.y_offset
        return (gy in range(0, len(self.cells)) and
                gx in range(0, len(self.cells[gy])))

    def get(self, x, y):
        gx, gy = x + self.x_offset, y + self.y_offset
        return self.cells[gy][gx] if self.in_bounds(x, y) else 32

    def put(self, ox, oy, v):
        # get coordinate with offset, and adjust bounds for negative
        # indexing (will only affect rows that already have cells to
        # help save memory and processing time)
        x = ox + self.x_offset
        y = oy + self.y_offset
        if y < 0:
            for _ in range(abs(y)):
                self.cells.insert(0, [])
                self.y_offset += 1
        if x < 0:
            for row in self.cells:
                if len(row) == 0:
                    continue
                for _ in range(abs(x)):
                    row.insert(0, 32)
            self.x_offset += abs(x)

        # recalculate the coordinates and pad them in the positive
        # direction so whatever is being set can be set (this may
        # not actually apply)
        x = ox + self.x_offset
        y = oy + self.y_offset

        while y >= len(self.cells):
            self.cells.append([])
        while x >= len(self.cells[y]):
            self.cells[y].append(32)

        # check to make sure this row is not the longest row now
        if len(self.cells[y]) > self.max_cols:
            self.max_cols = len(self.cells[y])

        self.cells[y][x] = v

    def least_point(self):
        return [-self.x_offset, -self.y_offset]

    def greatest_point(self):
        return [self.max_cols, len(self.cells) - self.y_offset + 1]

    def __str__(self):
        s = ''
        justify = len(str(len(self.cells))) + 3
        for i, row in enumerate(self.cells):
            s += f"{i} | ".rjust(justify)
            for c in row:
                s += chr(c)
            s += '\n'
        return s


class Stack:
    def __init__(self):
        self.stacks = [[]]

    def push(self, v):
        self.stacks[0].append(v)

    def push_all(self, l):
        self.stacks[0].extend(reversed(l))

    def pop(self):
        return 0 if len(self.stacks[0]) == 0 else self.stacks[0].pop()

    def clear(self):
        self.stacks[0].clear()

    # this doesn't do bounds checking
    def pick(self, v):
        return self.stacks[0][len(self.stacks[0]) - v]

    def push_soss(self, v):
        self.stacks[1].append(v)

    def pop_soss(self):
        return 0 if len(self.stacks[1]) == 0 else self.stacks[1].pop()

    def begin_block(self, x_soffset, y_soffset):
        n = self.pop()

        self.stacks.insert(0, [])
        if n > 0:
            tmp = []
            for _ in range(n):
                tmp.append(self.pop_soss())
            while tmp:
                self.push(tmp.pop())
        elif n < 0:
            for _ in range(abs(n)):
                self.push_soss(0)

        self.push_soss(x_soffset)
        self.push_soss(y_soffset)

    def end_block(self):
        if len(self.stacks) == 1:
            return True, 0, 0

        n = self.pop()
        y_soffset = self.pop_soss()
        x_soffset = self.pop_soss()

        if n > 0:
            tmp = []
            for _ in range(n):
                tmp.append(self.pop())
            while tmp:
                self.push_soss(tmp.pop())
        elif n < 0:
            for _ in range(abs(n)):
                self.pop_soss()
        self.stacks = self.stacks[1:]

        return False, x_soffset, y_soffset

    def stack_under_stack(self):
        if len(self.stacks) == 1:
            return True

        n = self.pop()
        if n > 0:
            for _ in range(n):
                self.push(self.pop_soss())
        elif n < 0:
            for _ in range(abs(n)):
                self.push_soss(self.pop())

        return False

    def __str__(self):
        s = '['
        for v in self.stacks[0]:
            s += f"{v} "
        if s != '[':
            s = s[:-1]
        return s + ']'


class InstructionPointer:
    def __init__(self, fungespace, *, pos=(0, 0), delta=(1, 0), stack=None):
        self.fungespace = fungespace
        self.stack = deepcopy(stack) or Stack()

        self.x, self.y = pos
        self.dx, self.dy = delta
        self.x_soffset, self.y_soffset = 0, 0

        self.stringmode = False
        self.alive = True

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def wrap(self):
        # turn around and move back in bounds
        self.reflect()
        self.move()
        # keep going until you're out of bounds, but on the opposite
        # side of the fungespace
        while self.fungespace.in_bounds_rect(self.x, self.y):
            self.move()
        # turn around again, and move back in bounds
        self.reflect()
        self.move()

    def move_try_wrap(self):
        self.move()
        if not self.fungespace.in_bounds_rect(self.x, self.y):
            self.wrap()

    def skip_spaces(self):
        while self.fungespace.get(self.x, self.y) == 32:
            self.move_try_wrap()

    def skip_non_semicolons(self):
        while self.fungespace.get(self.x, self.y) != ord(';'):
            self.move_try_wrap()

    def reflect(self):
        self.dx *= -1
        self.dy *= -1

    def turn_left(self):
        self.dx, self.dy = self.dy, -self.dx

    def turn_right(self):
        self.dx, self.dy = -self.dy, self.dx

    def find_next_instruction(self):
        while True:
            v = self.fungespace.get(self.x, self.y)
            if v == 32:
                self.skip_spaces()
            elif v == ord(';'):
                self.skip_non_semicolons()
                self.move_try_wrap()
            else:
                return v

    def tick(self):
        skip_move = False

        cell_value = self.fungespace.get(self.x, self.y)
        cell_char = chr(cell_value)

        # stringmode is processed separately, skips remainder of the
        # function if applicable
        if self.stringmode:
            if cell_char == '"':
                self.stringmode = False
            elif cell_char == ' ':
                self.stack.push(cell_value)
                self.skip_spaces()
                skip_move = True
            else:
                self.stack.push(cell_value)
        else:
            skip_move = self.execute_instruction(cell_value, cell_char)

        if not skip_move:
            self.move_try_wrap()

    def execute_instruction(self, cell_value, cell_char):
        ######################
        # DIRECTION CHANGING #
        ######################

        if cell_char == '>':
            self.dx, self.dy = (1, 0)

        elif cell_char == '<':
            self.dx, self.dy = (-1, 0)

        elif cell_char == '^':
            self.dx, self.dy = (0, -1)

        elif cell_char == 'v':
            self.dx, self.dy = (0, 1)

        elif cell_char == '?':
            self.dx, self.dy = choice([(1, 0), (-1, 0), (0, -1), (0, 1)])

        elif cell_char == ']':
            self.turn_right()

        elif cell_char == '[':
            self.turn_left()

        elif cell_char == 'r':
            self.reflect()

        elif cell_char == 'x':
            dy = self.stack.pop()
            dx = self.stack.pop()
            self.dx, self.dy = dx, dy

        ################
        # FLOW CONTROL #
        ################

        elif cell_char == '#':
            self.move_try_wrap()

        elif cell_char == '@':
            self.alive = False

        elif cell_char == ';':
            self.move_try_wrap()
            self.skip_non_semicolons()

        elif cell_char == 'j':
            v = self.stack.pop()

            turn_around = False
            if v < 0:
                self.reflect()
                turn_around = True

            for _ in range(abs(v)):
                self.move_try_wrap()
            if turn_around:
                self.reflect()

        elif cell_char == 'q':
            v = self.stack.pop()
            exit(v)

        elif cell_char == 'k':
            v = self.stack.pop()

            saved_pos = (self.x, self.y)
            self.move_try_wrap()
            i = self.find_next_instruction()
            if v != 0:
                self.x, self.y = saved_pos

            for _ in range(0, v):
                self.execute_instruction(i, chr(i))

        ###################
        # DECISION MAKING #
        ###################

        elif cell_char == '!':
            v = self.stack.pop()
            self.stack.push(1 if v == 0 else 0)

        elif cell_char == '`':
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.push(0 if b > a else 1)

        elif cell_char == '_':
            v = self.stack.pop()
            self.dx, self.dy = (1, 0) if v == 0 else (-1, 0)

        elif cell_char == '|':
            v = self.stack.pop()
            self.dx, self.dy = (0, 1) if v == 0 else (0, -1)

        elif cell_char == 'w':
            b = self.stack.pop()
            a = self.stack.pop()
            if a > b:
                self.turn_right()
            elif b > a:
                self.turn_left()

        ########################
        # DATA: CELL CRUNCHING #
        ########################

        elif cell_char in '0123456789abcdef':
            self.stack.push(int(cell_char, 16))

        elif cell_char == '+':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.push(b + a)

        elif cell_char == '*':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.push(b * a)

        elif cell_char == '-':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.push(b - a)

        elif cell_char == '/':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.push(0 if a == 0 else b // a)

        elif cell_char == '%':
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.push(0 if a == 0 else b % a)

        ###########
        # STRINGS #
        ###########

        elif cell_char == '"':
            self.stringmode = True

        elif cell_char == '\'':
            saved_pos = (self.x, self.y)
            self.move_try_wrap()
            self.stack.push(self.fungespace.get(self.x, self.y))

        elif cell_char == 's':
            saved_pos = (self.x, self.y)
            self.move_try_wrap()
            self.fungespace.put(self.x, self.y, self.stack.pop())

        ######################
        # STACK MANIPULATION #
        ######################

        elif cell_char == '$':
            self.stack.pop()

        elif cell_char == ':':
            v = self.stack.pop()
            self.stack.push(v)
            self.stack.push(v)

        elif cell_char == '\\':
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.push(b)
            self.stack.push(a)

        elif cell_char == 'n':
            self.stack.clear()

        ############################
        # STACK STACK MANIPULATION #
        ############################

        elif cell_char == '{':
            self.stack.begin_block(self.x_soffset, self.y_soffset)
            self.x_soffset = self.x + self.dx
            self.y_soffset = self.y + self.dy

        elif cell_char == '}':
            reflect, xso, yso = self.stack.end_block()
            if reflect:
                self.reflect()
            else:
                self.x_soffset, self.y_soffset = xso, yso

        elif cell_char == 'u':
            reflect = self.stack.stack_under_stack()
            if reflect:
                self.reflect()

        #######################
        # FUNGE-SPACE STORAGE #
        #######################

        elif cell_char == 'g':
            dy = self.stack.pop() + self.y_soffset
            dx = self.stack.pop() + self.x_soffset
            self.stack.push(self.fungespace.get(dx, dy))

        elif cell_char == 'p':
            dy = self.stack.pop() + self.y_soffset
            dx = self.stack.pop() + self.x_soffset
            v = self.stack.pop()
            self.fungespace.put(dx, dy, v)

        #########################
        # STANDARD INPUT/OUTPUT #
        #########################

        elif cell_char == '.':
            print(self.stack.pop(), end='')

        elif cell_char == ',':
            print(chr(self.stack.pop()), end='')

        elif cell_char == '&':
            self.reflect()  # TODO: decimal input

        elif cell_char == '~':
            self.reflect()  # TODO: char input

        #####################
        # FILE INPUT/OUTPUT #
        #####################

        elif cell_char == 'i':
            self.reflect()  # TODO: file input

        elif cell_char == 'o':
            self.reflect()  # TODO: file output

        ####################
        # SYSTEM EXECUTION #
        ####################

        elif cell_char == '=':
            self.reflect()  # TODO: system execution

        ################################
        # SYSTEM INFORMATION RETRIEVAL #
        ################################

        elif cell_char == 'y':
            v = self.stack.pop()

            info = self.get_sys_info()
            self.stack.push_all(info)

            if v > 0:
                tmp = self.stack.pick(v)
                for _ in range(len(info)):
                    self.stack.pop()
                self.stack.push(tmp)

        ################
        # FINGERPRINTS #
        ################

        # TODO: implement some fingerprints

        elif cell_char == '(':
            _ = self.build_fingerprint()
            self.reflect()

        elif cell_char == ')':
            _ = self.build_fingerprint()
            self.reflect()

        #################
        # MISCELLANEOUS #
        #################

        # skip spaces in zero ticks
        elif cell_char == ' ':
            self.skip_spaces()
            return True

        # noop
        elif cell_char == 'z':
            pass

        # unknown character
        else:
            self.reflect()

        return False

    def build_fingerprint(self):
        v = self.stack.pop()

        fingerprint = 0
        for _ in range(v):
            fingerprint *= 256
            fingerprint += self.stack.pop()

        return fingerprint

    def get_sys_info(self):
        info = []

        info.append(0b00000)  # flag cell

        info.append(math.inf)  # bytes per cell

        info.append(0)  # handprint (N/A)
        info.append(10)  # version

        info.append(0)  # os execution paradigm
        info.append(ord('/'))  # path separator

        info.append(2)  # scalar per vector (befunge)

        info.append(0)  # id of this ip
        info.append(0)  # team number (N/A)

        info.append(self.y)  # ip y
        info.append(self.x)  # ip x
        info.append(self.dy)  # ip dy
        info.append(self.dx)  # ip dx
        info.append(self.y_soffset)  # ip y storage offset
        info.append(self.x_soffset)  # ip x storage offset

        info.extend(reversed(self.fungespace.least_point()))  # least p
        info.extend(reversed(self.fungespace.greatest_point()))  # greatest p

        now = datetime.now()
        date = ((now.year - 1900) * 256 * 256) + (now.month * 256) + now.day
        time = (now.hour * 256 * 256) + (now.minute * 256) + now.second
        info.append(date)  # the date
        info.append(time)  # the time

        info.append(len(self.stack.stacks))  # number of stacks
        for s in self.stack.stacks:
            info.append(len(s))  # length of stacks from top to bottom

        info.extend([0, 0])  # TODO: the command line arguments
        info.extend([0, 0])  # TODO: the environment variables

        return info


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python main.py <file>')
        exit(1)

    fungespace = FungeSpace(sys.argv[1])
    print(fungespace)

    ips = []
    ips.append(InstructionPointer(fungespace))

    while ips:
        tmp = []
        while ips:
            ip = ips.pop()
            ip.tick()
            if ip.alive:
                tmp.append(ip)
        while tmp:
            ips.append(tmp.pop())
