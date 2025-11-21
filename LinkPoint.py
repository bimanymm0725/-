from GeomBase import Point3D

class LinkPoint:
    def __init__(self, pnt3d, digits=7):
        self.x = round(pnt3d.x, digits)
        self.y = round(pnt3d.y, digits)
        self.z = round(pnt3d.z, digits)
        self.other = None  # 指向线段另一个端点
        self.used = False  # 点是否已经被使用
        self.index = 0  # 点在列表中的序号
        self.segments = []

    def __str__(self):
        return f"LinkPoint({self.x}, {self.y}, {self.z}), used: {self.used}"

    def toPoint3D(self):
        return Point3D(self.x, self.y, self.z)

    def isCoincident(self, other, tolerance=1e-5):
        """判断两个点是否重合"""
        return (abs(self.x - other.x) < tolerance and
                abs(self.y - other.y) < tolerance and
                abs(self.z - other.z) < tolerance)