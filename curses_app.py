# -*- coding: utf-8 -*-

import curses as curses
import locale as locale
import time as time
from math import floor
from engine import Engine
from random import choice
import pymunk as pymunk
from utils import linspace


class CursesApp():
    def __init__(self, stdscr):
        # encoding
        self.code = locale.getpreferredencoding()
        curses.curs_set(0)

        # constants
        self.TARGET_FPS = 15
        self.MIN_HEIGHT = 40
        self.MIN_WIDTH = 150
        self.ALPHA = tuple([ord(x) for x in 'abcdefghijklmnopqrstuvwxyz 1234567890['])
        self.BG = []
        with open('Assets/background.txt', 'r', encoding='utf-8') as file:
            for line in file.readlines():
                self.BG.append(line.rstrip('\n'))

        # color pairs
        curses.init_pair(1, curses.COLOR_WHITE, 0)  # white
        curses.init_pair(2, curses.COLOR_BLUE, 0)  # blue
        curses.init_pair(3, curses.COLOR_GREEN, 0)  # green
        curses.init_pair(4, curses.COLOR_RED, 0)  # red
        curses.init_pair(5, 8, 0)  # black
        curses.init_pair(6, curses.COLOR_YELLOW, 0)  # yellow

        # display
        self.screen = stdscr
        self.screen.nodelay(1)

        # controls
        self.user_input = ''
        self.cursor_position = 0
        self.app_is_running = True
        self.engine = Engine()
        self.commands = {
            'q': self.quit,
            'exit': self.quit,
            'quit': self.quit,
            'start': self.engine.start,
            'stop': self.engine.stop,
            'f1': self.engine.set_curve,
            'f2': self.engine.set_curve,
            'f3': self.engine.set_curve,
        }

        # byproducts
        self.space = pymunk.Space()
        self.space.gravity = (0, 40)

        self.staticLines = []
        for pos in [((-1, 0), (-1, 40)),
                    ((0, -1), (156, -1)),
                    ((0, 41), (156, 41)),
                    ((157, 0), (157, 40)),
                    ((0, 15), (71, 15))]:
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            shape = pymunk.Segment(self.space.static_body, pos[0], pos[1], 2)
            shape.friction = 0.1
            shape.elasticity = 0.9
            self.space.add(body, shape)
            self.staticLines.append((body, shape))

        self.byproducts = []
        self.bpRepresentation = []

        # check screen size
        self.size_adjust()

        # main loop
        self.main_loop()

        # exit
        self.screen.erase()
        self.screen.refresh()
        curses.endwin()

    def main_loop(self):
        last_frame_date = time.time()
        with open('log.txt', 'w') as file:
            file.write('===' + '\n')

        while self.app_is_running:
            # frame rate control
            if (delta := time.time() - last_frame_date) < 1 / self.TARGET_FPS:
                for i in range(4):
                    time.sleep((1 / self.TARGET_FPS - delta) / 4)
                    self.space.step((1 / self.TARGET_FPS - delta) / 4)
            delta = time.time() - last_frame_date
            last_frame_date = time.time()

            # update
            if (err := self.update(delta)) is not None:
                exit('\n' + err + '\n')
            self.display()

            # input
            if self.input() is not None:
                continue

    def size_adjust(self) -> None:
        last_frame_date = time.time()
        while self.screen.getmaxyx()[0] < self.MIN_HEIGHT or self.screen.getmaxyx()[1] < self.MIN_WIDTH:
            # frame rate control
            if (delta := time.time() - last_frame_date) < 1 / self.TARGET_FPS:
                time.sleep(1 / self.TARGET_FPS - delta)
            last_frame_date = time.time()

            # display
            self.screen.clear()
            self.screen.addstr(4, 5, f"Adjust your terminal size until it is at least ({self.MIN_HEIGHT}, {self.MIN_WIDTH})")
            self.screen.addstr(5, 5, str(self.screen.getmaxyx()))
            self.screen.refresh()

    def update(self, dt):
        # engine
        nb_new_byproducts = self.engine.update(dt)
        for i in range(nb_new_byproducts):
            self.add_byproduct((9, 5))

        # byproducts
        for bp in self.byproducts:
            bp.body.apply_force_at_local_point((self.engine.aX, self.engine.aY))

        # end game
        if self.engine.oxygen < 0:
            return 'You ran out of oxygen, game over'
        if self.engine.shipPosition >= 94:
            if self.engine.speed < 50:
                return 'You reached your destination, you are able to repair your ship and continue on your journey'
            elif self.engine.shipPosition > 110:
                return 'You over shot your destination because your speed was too great, you will now drift in space until the end of times'

    def input(self):
        key = self.screen.getch()
        if key == -1:
            return -1
        unKey = curses.unctrl(key)
        strKey = str(unKey).lstrip("b'").rstrip("'")

        # text input
        if key in self.ALPHA:
            self.user_input = self.user_input[:self.cursor_position] + strKey + self.user_input[self.cursor_position:]
            self.cursor_position += 1
        elif strKey == '^H':  # backspace
            if self.cursor_position > 0:
                self.user_input = self.user_input[:self.cursor_position - 1] + self.user_input[self.cursor_position:]
                self.cursor_position -= 1
        elif strKey == '\\x02':  # down arrow
            self.cursor_position = len(self.user_input)
        elif strKey == '\\x03':  # up arrow
            self.cursor_position = 0
        elif strKey == '\\x04':  # left arrow
            if self.cursor_position > 0:
                self.cursor_position -= 1
        elif strKey == '\\x05':  # right arrow
            if self.cursor_position < len(self.user_input):
                self.cursor_position += 1

        # input validation
        elif strKey == '^J':  # cariage return
            args = [x.lower() for x in self.user_input.split(' ')]
            if args[0] in self.commands:
                self.commands[args[0]](args)
            self.user_input = ''
            self.cursor_position = 0
        else:
            with open('log.txt', 'a') as file:
                file.write(strKey + '\n')

    def display(self):
        self.screen.erase()

        # background
        for y, line in enumerate(self.BG):
            self.screen.addstr(y, 0, line)

        # input
        self.screen.addstr(38, 5, self.user_input[:self.cursor_position] + '|' + self.user_input[self.cursor_position:])

        # power
        for y in range(int(self.engine.power * 6.6 * 34 // 100)):
            self.screen.addstr(36 - y, 151, '▇▇')

        for y in range(9):
            self.screen.addstr(34 - y, int(4 + self.engine.power * 4.3 * 65 // 100), '╮', curses.color_pair(5))
        for y in range(9):
            self.screen.addstr(22 - y, int(4 + self.engine.power * 4.3 * 65 // 100), '╮', curses.color_pair(5))
        for y in range(9):
            self.screen.addstr(22 - y, int(76 + self.engine.power * 4.3 * 65 // 100), '╮', curses.color_pair(5))

        # stocks
        for y in range(int(self.engine.f1Stock * 8 // 100)):
            self.screen.addstr(10 - y, 109, '▇▇')
        for y in range(int(self.engine.f2Stock * 8 // 100)):
            self.screen.addstr(10 - y, 119, '▇▇')
        for y in range(int(self.engine.f3Stock * 8 // 100)):
            self.screen.addstr(10 - y, 129, '▇▇')
        for y in range(int(self.engine.oxygen * 8 // 100)):
            self.screen.addstr(10 - y, 138, '▇▇')

        # informations
        self.screen.addstr(7, 88, str(round(self.engine.temperature, 3)))
        self.screen.addstr(6, 90, self.engine.status)
        self.screen.addstr(27, 126, str(round(self.engine.speed, 4)))

        # debug
        self.screen.addstr(2, 59, str(round(self.engine.last_f1, 4)))
        self.screen.addstr(3, 59, str(round(self.engine.last_f2, 4)))
        self.screen.addstr(4, 59, str(round(self.engine.last_f3, 4)))
        self.screen.addstr(5, 59, str(round(self.engine.last_f4, 4)))

        # curve f1
        f1c = []
        f2c = []
        f3c = []
        for out, inc in zip((f1c, f2c, f3c), (self.engine.f1Curve, self.engine.f2Curve, self.engine.f3Curve)):
            for i in range(4):
                out += list(linspace(inc[i], inc[i + 1], 16))
            out += [inc[-1]]
        for yStart, xRange, curve in zip((35, 23, 23), (list(range(4, 69)), list(range(4, 69)), list(range(76, 141))), (f1c, f2c, f3c)):
            for x, y in zip(xRange, curve):
                self.screen.addstr(yStart - int(y), int(x), '◦')

        for x, y in zip((4, 20, 36, 52, 68), self.engine.f1Curve):
            self.screen.addstr(35 - y, x, 'o')

        # curve f2
        for x, y in zip((4, 20, 36, 52, 68), self.engine.f2Curve):
            self.screen.addstr(23 - y, x, 'o')

        # curve f2
        for x, y in zip((4, 20, 36, 52, 68), self.engine.f3Curve):
            self.screen.addstr(23 - y, x + 72, 'o')

        # byproducts
        for bp, representation in zip(self.byproducts, self.bpRepresentation):
            self.screen.addstr(floor(bp.body.position[1]), floor(bp.body.position[0]), representation[0], curses.color_pair(representation[1]))

        # map
        progress = self.engine.shipPosition * 61 // 100
        self.screen.addstr(int(27 + progress // 7), int(79 + progress), '▶', curses.color_pair(4))

        # refresh
        self.screen.refresh()

    def add_byproduct(self, position):
        body = pymunk.Body(10, 100)
        body.position = position
        shape = pymunk.Circle(body, 1, (0, 0))
        shape.friction = 0.1
        shape.elasticity = 0.6
        shape.collision_type = 2
        self.space.add(body, shape)
        self.byproducts.append(shape)
        self.bpRepresentation.append((choice(('▤', '▣', '◉', '◬', '◍')), choice((1, 2, 3, 4, 5))))

    def quit(self, args):
        self.app_is_running = False
