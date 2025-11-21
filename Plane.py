from GeomBase import *
from Line import *


class Plane:
    def __init__(self, P, N):
        self.P = P.clone()
        self.N = N.clone().normalized()

    def __str__(self):
        A, B, C, D = self.toFormula()
        return "Plane\n%s\n%s\n" % (str(self.P),str(self.N))

    def toFormula(self):
        A = self.N.dx
        B = self.N.dy
        C = self.N.dz
        D = -(A * self.P.x + B * self.P.y + C * self.P.z)
        return A, B, C, D

    @staticmethod
    def zPlane(z):
        P = Point3D(0, 0, z)
        N = Vector3D(0, 0, 1)
        return Plane(P, N)

    def intersect(self, other):
        n1 = self.N
        n2 = other.N

        direction = n1.crossProduct(n2)

        if direction.lengthSquare() < epsilonSquare:
            return None

        A1, B1, C1, D1 = self.toFormula()
        A2, B2, C2, D2 = other.toFormula()

        det = A1 * B2 - A2 * B1
        if abs(det) > epsilon:
            x = (B1 * D2 - B2 * D1) / det
            y = (A2 * D1 - A1 * D2) / det
            point = Point3D(x, y, 0)
        else:
            det = A1 * C2 - A2 * C1
            if abs(det) > epsilon:
                x = (C1 * D2 - C2 * D1) / det
                z = (A2 * D1 - A1 * D2) / det
                point = Point3D(x, 0, z)
            else:
                det = B1 * C2 - B2 * C1
                if abs(det) > epsilon:
                    y = (C1 * D2 - C2 * D1) / det
                    z = (B2 * D1 - B1 * D2) / det
                    point = Point3D(0, y, z)
                else:
                    return None
        return Line(point, direction)

    def clone(self):
        return Plane(self.P, self.N)