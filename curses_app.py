# -*- coding: utf-8 -*-

import curses as curses
import locale as locale
import time as time
from math import floor
from engine import Engine
from random import choice
import pymunk as pymunk


class CursesApp():
    def __init__(self, stdscr):
        # encoding
        locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        self.code = locale.getpreferredencoding()
        curses.curs_set(0)

        # constants
        self.TARGET_FPS = 15
        self.MIN_HEIGHT = 40
        self.MIN_WIDTH = 150
        self.ALPHA = tuple([ord(x) for x in 'abcdefghijklmnopqrstuvwxyz 1234567890'])
        self.BG = []
        with open('Assets/background.txt', 'r', encoding='utf-8') as file:
            for line in file.readlines():
                self.BG.append(line.rstrip('\n'))
        self.BASE_MASK = [[False for x in range(156)] for y in range(40)]
        with open('Assets/mask_base.txt', 'r', encoding='utf-8') as file:
            for y, line in enumerate(file.readlines()):
                for x, character in enumerate(line.rstrip('\n')):
                    if character != ' ':
                        self.BASE_MASK[y][x] = True

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
        }

        # byproducts
        self.space = pymunk.Space()
        self.space.gravity = (0, 40)

        self.staticLines = []
        for pos in [((0, 0), (0, 40)),
                    ((0, 0), (156, 0)),
                    ((0, 40), (156, 40)),
                    ((156, 0), (156, 40)),
                    ((0, 14), (71, 14))]:
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            shape = pymunk.Segment(self.space.static_body, pos[0], pos[1], 1)
            shape.friction = 0.2
            self.space.add(body, shape)
            self.staticLines.append((body, shape))

        self.byproducts = []
        self.bpRepresentation = []
        self.add_byproduct((9, 5))
        self.add_byproduct((9, 5))
        self.add_byproduct((9, 5))
        self.add_byproduct((9, 5))
        self.add_byproduct((9, 5))
        self.add_byproduct((9, 5))
        self.add_byproduct((9, 5))

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
                time.sleep((1 / self.TARGET_FPS - delta) / 3)
                self.space.step((1 / self.TARGET_FPS - delta) / 3)
                time.sleep((1 / self.TARGET_FPS - delta) / 3)
                self.space.step((1 / self.TARGET_FPS - delta) / 3)
                time.sleep((1 / self.TARGET_FPS - delta) / 3)
                self.space.step((1 / self.TARGET_FPS - delta) / 3)
            last_frame_date = time.time()

            # update
            self.update(delta)
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
        self.engine.update(dt)

        # byproducts
        for bp in self.byproducts:
            bp.body.apply_force_at_local_point((self.engine.aX, self.engine.aY))

        # simulation
        # self.space.step(dt)

    def input(self):
        key = self.screen.getch()
        unKey = curses.unctrl(key)
        strKey = str(unKey).lstrip("b'").rstrip("'")
        if key == -1:
            return -1

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
            args = self.user_input.split(' ')
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
        for y in range(int(self.engine.power * 34 // 100)):
            self.screen.addstr(36 - y, 151, '▇▇')

        # stocks
        for y in range(int(self.engine.f1Stock * 8 // 100)):
            self.screen.addstr(10 - y, 109, '▇▇')
        for y in range(int(self.engine.f2Stock * 8 // 100)):
            self.screen.addstr(10 - y, 119, '▇▇')
        for y in range(int(self.engine.f3Stock * 8 // 100)):
            self.screen.addstr(10 - y, 129, '▇▇')
        for y in range(int(self.engine.oxygen * 8 // 100)):
            self.screen.addstr(10 - y, 138, '▇▇')

        # curve f1
        for x, y in zip((4, 20, 36, 52, 68), self.engine.f1Curve):
            self.screen.addstr(35 - y, x, 'o')

        # curve f2
        for x, y in zip((4, 20, 36, 52, 68), self.engine.f2Curve):
            self.screen.addstr(23 - y, x, 'o')

        # curve f2
        for x, y in zip((4, 20, 36, 52, 68), self.engine.f3Curve):
            self.screen.addstr(23 - y, x + 72, 'o')

        # map
        progress = self.engine.shipPosition * 63 // 100
        self.screen.addstr(int(27 + progress // 9), int(79 + progress), '▶', curses.color_pair(4))

        self.screen.refresh()

        # byproducts
        for bp, representation in zip(self.byproducts, self.bpRepresentation):
            self.screen.addstr(floor(bp.body.position[1]), floor(bp.body.position[0]), representation[0], curses.color_pair(representation[1]))
            # with open('log.txt', 'a') as file:
            #     file.write(str(floor(bp.body.position[1])) + ' ' + str(floor(bp.body.position[0])) + '\n')

    def add_byproduct(self, position):
        body = pymunk.Body(10, 100)
        body.position = position
        shape = pymunk.Circle(body, 1, (0, 0))
        shape.friction = 0.5
        shape.collision_type = 2
        self.space.add(body, shape)
        self.byproducts.append(shape)
        self.bpRepresentation.append((choice(('▤', '▣', '◉', '◬', '◍')), choice((1, 2, 3, 4, 5))))

    def quit(self):
        self.app_is_running = False
