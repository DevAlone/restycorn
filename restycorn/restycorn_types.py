class uint(int):
    def __new__(cls, value, *args, **kwargs):
        value = int(value)
        if value < 0:
            raise ValueError("Value of uint type cannot be negative")
        return super(uint, cls).__new__(cls, value)

    def __add__(self, other):
        return uint(super(uint, self).__add__(other))

    def __sub__(self, other):
        return uint(super(uint, self).__sub__(other))

    def __mul__(self, other):
        return uint(super(uint, self).__mul__(other))

    def __mod__(self, other):
        return uint(super(uint, self).__mod__(other))

    def __truediv__(self, other):
        return uint(super(uint, self).__truediv__(other))

    def __lt__(self, other):
        return super(uint, self).__lt__(other)

    def __le__(self, other):
        return super(uint, self).__le__(other)

    def __eq__(self, other):
        return super(uint, self).__eq__(other)

    def __ne__(self, other):
        return super(uint, self).__ne__(other)

    def __gt__(self, other):
        return super(uint, self).__gt__(other)

    def __ge__(self, other):
        return super(uint, self).__ge__(other)

    def __hash__(self):
        return super(uint, self).__hash__()
