from copy import deepcopy
import sys


class FungeSpace:
    SPACE = ord(' ')

    def __init__(self, path):
        with open(path) as f:
            lines = list(map(lambda l: l.strip(), f.readlines()))

        self.cells = []
        for l in lines:
            self.cells.append(list(map(lambda c: ord(c), l)))

        self.x_offset, self.y_offset = 0, 0

    def in_bounds(self, x, y):
        return (y in range(0, len(self.cells)) and
                x in range(0, len(self.cells[y])))

    def get(self, x, y):
        return self.cells[y][x] if self.in_bounds(x, y) else self.SPACE

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
        elif y >= len(self.cells):
            while (y > len(self.cells)):
                self.cells.append([])
        if x < 0:
            for row in self.cells:
                if len(row) == 0:
                    continue
                for _ in range(abs(x)):
                    row.insert(0, self.SPACE)
            self.x_offset += abs(x)

        # recalculate the coordinates and pad them in the positive
        # direction so whatever is being set can be set (this may
        # not actually apply)
        x = ox + self.x_offset
        y = oy + self.y_offset
        while y >= len(self.cells):
            self.cells.append([])
        while x >= len(self.cells[y]):
            self.cells[y].append(self.SPACE)

        self.cells[y][x] = ord(v)

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

    def pop(self):
        return self.stacks[0].pop()


class InstructionPointer:
    def __init__(self, fungespace, *, pos=(0, 0), delta=(1, 0), stack=None):
        self.fungespace = fungespace
        self.stack = deepcopy(stack) or Stack()

        self.x, self.y = pos
        self.delta = list(delta)
        self.stringmode = False

        self.alive = True

    def move(self):
        self.x += self.delta[0]
        self.y += self.delta[1]

    def reflect(self):
        self.delta[0] *= -1
        self.delta[1] *= -1

    def tick(self):
        d = self.fungespace.get(self.x, self.y)
        c = chr(d)

        # basic numbers
        if c == '0':
            self.stack.push(0)
        elif c == '1':
            self.stack.push(1)
        elif c == '2':
            self.stack.push(2)
        elif c == '3':
            self.stack.push(3)
        elif c == '4':
            self.stack.push(4)
        elif c == '5':
            self.stack.push(5)
        elif c == '6':
            self.stack.push(6)
        elif c == '7':
            self.stack.push(7)
        elif c == '8':
            self.stack.push(8)
        elif c == '9':
            self.stack.push(9)
        elif c == 'a':
            self.stack.push(10)
        elif c == 'b':
            self.stack.push(11)
        elif c == 'c':
            self.stack.push(12)
        elif c == 'd':
            self.stack.push(13)
        elif c == 'e':
            self.stack.push(14)
        elif c == 'f':
            self.stack.push(15)

        # movement
        elif c == '<':
            self.delta = [-1, 0]
        elif c == '>':
            self.delta = [1, 0]
        elif c == '^':
            self.delta = [0, -1]
        elif c == 'v':
            self.delta = [0, 1]
        elif c == '#':
            self.move()

        # stack
        elif c == '$':
            self.stack.pop()

        # output
        elif c == '.':
            print(self.stack.pop(), end='')
        elif c == ',':
            print(chr(self.stack.pop()), end='')

        # end program
        elif c == '@':
            self.alive = False
            return

        # unknown instruction, so reflect            
        elif c != ' ':
            self.reflect()
        
        self.move()


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
