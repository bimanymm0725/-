from GeomBase import *

class Polyline:
    def __init__(self):
        self.points = []  # 存储多段线的顶点列表

    def __str__(self):
        if len(self.points) == 0:
            return "Polyline: empty"
        elif len(self.points) == 1:
            return f"Polyline: 1 point at {self.points[0]}"
        else:
            return f"Polyline: {len(self.points)} points from {self.startPoint()} to {self.endPoint()}"

    def clone(self):
        new_polyline = Polyline()
        for pt in self.points:
            new_polyline.addPoint(pt.clone())
        return new_polyline

    def count(self):
        return len(self.points)

    def addPoint(self, pt):
        self.points.append(pt.clone())

    def addTuple(self, tuple):
        if len(tuple) >= 3:
            self.points.append(Point3D(tuple[0], tuple[1], tuple[2]))

    def raddPoint(self, pt):
        self.points.insert(0, pt.clone())

    def removePoint(self, index):
        if 0 <= index < len(self.points):
            return self.points.pop(index)
        return None

    def point(self, index):
        if 0 <= index < len(self.points):
            return self.points[index]
        return None

    def startPoint(self):
        if len(self.points) > 0:
            return self.points[0]
        return None

    def endPoint(self):
        if len(self.points) > 0:
            return self.points[-1]
        return None

    def isClosed(self):
        if len(self.points) < 3:
            return False
        return self.startPoint().isCoincide(self.endPoint())

    def reverse(self):
        self.points.reverse()

    def getArea(self):
        if len(self.points) < 3:
            return 0.0

        area = 0.0
        n = len(self.points)

        for i in range(n):
            j = (i + 1) % n
            area += self.points[i].x * self.points[j].y
            area -= self.points[j].x * self.points[i].y

        return abs(area) / 2.0

    def makeCCW(self):
        if self.isCCW():
            return
        self.reverse()

    def makeCW(self):
        if not self.isCCW():
            return
        self.reverse()

    def isCCW(self):
        if len(self.points) < 3:
            return True

        area = 0.0
        n = len(self.points)

        for i in range(n):
            j = (i + 1) % n
            area += (self.points[j].x - self.points[i].x) * (self.points[j].y + self.points[i].y)

        return area < 0

    def translate(self, vec):
        for pt in self.points:
            pt.translate(vec)

    def translated(self, vec):
        new_polyline = self.clone()
        new_polyline.translate(vec)
        return new_polyline

    def appendSegment(self, seg):
        if len(self.points) == 0:
            self.addPoint(seg.A)
        self.addPoint(seg.B)

    def multiply(self, m):
        for i in range(len(self.points)):
            self.points[i] = self.points[i].multiplied(m)

    def multiplied(self, m):
        new_polyline = self.clone()
        new_polyline.multiply(m)
        return new_polyline

def writePolyline(path, polyline: Polyline):
    f = None
    try:
        f = open(path, 'w')
        f.write('%s\n' % polyline.count())
        for pt in polyline.points:
            txt = "%s, %s, %s\n" % (pt.x, pt.y, pt.z)
            f.write(txt)
    except Exception as ex:
        print(ex)
    finally:
        if f:
            f.close()


def readPolyline(path):
    f = None
    try:
        f = open(path, 'r')
        poly = Polyline()
        number = int(f.readline())
        for i in range(number):
            txt = f.readline()
            txts = txt.split(',')
            x, y, z = float(txts[0]), float(txts[1]), float(txts[2])
            poly.addPoint(Point3D(x, y, z))
        return poly
    except Exception as ex:
        print(ex)
        return None
    finally:
        if f:
            f.close()