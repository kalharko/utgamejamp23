

def linspace(start, stop, count):
    step = (stop - start) / float(count)
    return [start + i * step for i in range(count)]
