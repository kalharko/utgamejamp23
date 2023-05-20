from math import floor


class Engine():
    def __init__(self) -> None:
        self.power = 0
        self.shipPosition = 0
        self.f1Curve = [0, 0, 0, 0, 0]
        self.f2Curve = [0, 0, 0, 0, 0]
        self.f3Curve = [0, 0, 0, 0, 0]
        self.f1Stock = 100
        self.f2Stock = 100
        self.f3Stock = 100
        self.status = 'Shut off'
        self.running = True
        self.temperature = 20
        self.aX = 1000
        self.aY = 0
        self.speed = 0
        self.lastPowers = []
        self.remainingByProduct = 0
        self.oxygen = 100

        # constants
        self.speedDecay = 0.6

    def update(self, dt) -> int:
        if self.running is False:
            return

        f1c = []
        f2c = []
        f3c = []
        for out, inc in zip((f1c, f2c, f3c), (self.f1Curve, self.f2Curve, self.f3Curve)):
            for i in range(3):
                out += list(self.linspace(inc[i], inc[i + 1], 10))
            out += [inc[-1]]

        f1 = f1c[int(self.power * 31 // 100)] * dt
        f2 = f2c[int(self.power * 31 // 100)] * dt
        f3 = f3c[int(self.power * 31 // 100)] * dt

        # reaction 1
        f4 = min((f1, f3))
        f1 -= min((f1, f3))
        f3 -= min((f1, f3))

        # reaction 2
        power = min((f1, f2))
        byproducts = min((f1, f2))
        f3 += min((f1, f2))
        f1 -= min((f1, f2))
        f2 -= min((f1, f2))

        # reaction 3
        power += min((f3, f4))
        f3 -= min((f3, f4))
        f4 -= min((f3, f4))

        # restock
        self.f1Stock += f1
        self.f2Stock += f2
        self.f3Stock += f3
        byproducts += f4

        self.power = power
        self.speed += self.power
        self.speed *= self.speedDecay
        self.shipPosition += self.speed

        byproducts += self.remainingByProduct
        self.remainingByProduct = byproducts - floor(byproducts)
        return floor(byproducts)

    def linspace(self, start, stop, count):
        step = (stop - start) / float(count)
        return [start + i * step for i in range(count)]

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def set_curve(self, args):
        if not args[1] in ('0', '25', '50', '75', '100'):
            return args[1] + ' should be either 0, 25, 50, 75 or 100'

        if not args[2] in ('0', '1', '2', '3', '4', '5', '6', '7', '8'):
            return args[2] + ' should be an integer between 0 and 8'

        if self.args[0].lower() == 'f1':
            self.f1Curve[int(args[1])] = int(args[2])

        if self.args[0].lower() == 'f2':
            self.f2Curve[int(args[1])] = int(args[2])

        if self.args[0].lower() == 'f3':
            self.f3Curve[int(args[1])] = int(args[2])
