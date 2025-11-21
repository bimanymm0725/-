from GeomBase import *

class Segment:
    def __init__(self, A, B):
        self.A = A.clone()
        self.B = B.clone()

    def multiply(self, m):  # m 为矩阵
        self.A = self.A.multiplied(m)
        self.B = self.B.multiplied(m)

    def multiplied(self, m):
        return Segment(self.A.multiplied(m), self.B.multiplied(m))

    def __str__(self):
        return "Segment\nA %s\nB %s\n" % (str(self.A), str(self.B))

    def length(self):
        return self.A.distance(self.B)

    def direction(self):
        return self.A.pointTo(self.B)

    def swap(self):
        self.A, self.B = self.B, self.A