from math import floor
from utils import linspace


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
        self.running = False
        self.temperature = 0
        self.aX = 0
        self.aY = 0
        self.speed = 0
        self.remainingByProduct = 0
        self.oxygen = 100
        self.last_power = 0
        self.last_f1 = 0
        self.last_f2 = 0
        self.last_f3 = 0
        self.last_f4 = 0

        # constants
        self.speedDecay = 0.95
        self.f1f2Temperaturef4 = [0, 2, 5, 7, 8]
        self.f1f2TemperaturePower = [8, 5, 3, 2, 1]
        self.f3f4TemperaturePower = [2, 3, 5, 7, 8]
        self.f3f4TemperatureByproduct = [8, 7, 5, 3, 1]

    def update(self, dt) -> int:
        f1c = []
        f2c = []
        f3c = []
        f1f2cf4 = []
        f1f2cPower = []
        f3f4cPower = []
        f3f4cBp = []
        for out, inc in zip((f1c, f2c, f3c, f1f2cf4, f1f2cPower, f3f4cPower, f3f4cBp),
                            (self.f1Curve, self.f2Curve, self.f3Curve, self.f1f2Temperaturef4, self.f1f2TemperaturePower,
                            self.f3f4TemperaturePower, self.f3f4TemperatureByproduct)):
            for i in range(4):
                out += list(linspace(inc[i], inc[i + 1], 15))
            out += [inc[-1]]

        power = 0
        calcPower = self.power
        byproducts = 0
        if not self.running:
            self.temperature *= 0.9
        else:
            # with open('log.txt', 'a') as file:
            #     file.write(str(f1c) + '\n')
            f1 = f1c[int(calcPower * 4.3 * 65 // 100)] * dt
            f2 = f2c[int(calcPower * 4.3 * 65 // 100)] * dt
            f3 = f3c[int(calcPower * 4.3 * 65 // 100)] * dt

            self.f1Stock -= f1 * 0.15
            self.f2Stock -= f2 * 0.15
            self.f3Stock -= f3 * 0.15

            # reaction 1
            mini = min((f1, f2))
            f4 = mini * (f1f2cf4[int(calcPower * 4.3 * 65 // 100)])
            power += mini * (f1f2cPower[int(calcPower * 4.3 * 65 // 100)] + 1)
            f1 -= mini
            f2 -= mini

            # reaction 2
            mini = min((f3, f4))
            power += mini * (f3f4cPower[int(calcPower * 4.3 * 65 // 100)]) * 3
            byproducts += mini * (f3f4cBp[int(calcPower * 4.3 * 65 // 100)]) // 2
            f3 -= mini
            f4 -= mini

            # remaining reagents
            self.oxygen -= f4
            byproducts += f1
            byproducts += f3
            self.last_f1 = f1 * 10
            self.last_f2 = f2 * 10
            self.last_f3 = f3 * 10
            self.last_f4 = f4 * 10
            self.temperature -= f2 * 2.5
            self.temperature += f3
            self.speed -= f3

        self.last_power = self.power
        self.power = power
        self.aX = self.power * 45
        self.aY = self.aX
        self.speed += self.power
        self.speed *= self.speedDecay
        self.shipPosition += self.speed * 0.002
        self.temperature += self.power * 0.2

        byproducts += self.remainingByProduct
        self.remainingByProduct = byproducts - floor(byproducts)

        # securities
        if self.power > 15:
            self.power = 15
        if self.power < 0:
            self.power = 0
        if self.temperature > 200:
            self.stop('args')
            self.status = 'Staled'
        return int(byproducts // 2)

    def linspace(self, start, stop, count):
        step = (stop - start) / float(count)
        return [start + i * step for i in range(count)]

    def start(self, args):
        self.status = 'Running'
        self.running = True

    def stop(self, args):
        self.status = 'Idle'
        self.running = False

    def set_curve(self, args):
        if args[1] == 'full' or args[1] == 'f':
            if len(args) != 7:
                return
            newCurve = [int(x) for x in args[2:]]
            if [0 <= x <= 8 for x in newCurve] != [True for x in range(len(self.f1Curve))]:
                return
            if args[0] == 'f1':
                self.f1Curve = newCurve
            if args[0] == 'f2':
                self.f2Curve = newCurve
            if args[0] == 'f3':
                self.f3Curve = newCurve

        if not args[1] in ('0', '25', '50', '75', '100'):
            return args[1] + ' should be either 0, 25, 50, 75 or 100'

        if not args[2] in ('0', '1', '2', '3', '4', '5', '6', '7', '8'):
            return args[2] + ' should be an integer between 0 and 8'

        if args[0] == 'f1':
            self.f1Curve[('0', '25', '50', '75', '100').index(args[1])] = int(args[2])

        if args[0] == 'f2':
            self.f2Curve[('0', '25', '50', '75', '100').index(args[1])] = int(args[2])

        if args[0] == 'f3':
            self.f3Curve[('0', '25', '50', '75', '100').index(args[1])] = int(args[2])
