import math
import pyclipper
from Polyline import *


class ClipperAdaptor:
    def __init__(self, digits=7):
        self.f = math.pow(10, digits)  # 数值精度，默认为7位小数
        self.arcTolerance = 0.005  # 图像精度，默认为0.005mm

    def toPath(self, poly):
        """将Polyline转化为Path"""
        path = []
        for pt in poly.points:
            # 将坐标放大并转为整数
            x_int = int(round(pt.x * self.f))
            y_int = int(round(pt.y * self.f))
            path.append((x_int, y_int))
        return path

    def toPaths(self, polys):
        """将Polyline列表转化为Path列表"""
        paths = []
        for poly in polys:
            paths.append(self.toPath(poly))
        return paths

    def toPoly(self, path, z=0, closed=True):
        """将Path转化为Polyline"""
        poly = Polyline()
        for pt in path:
            # 将坐标缩小回原始精度
            x = pt[0] / self.f
            y = pt[1] / self.f
            poly.addPoint(Point3D(x, y, z))

        if len(path) > 0 and closed:
            # 封闭轮廓：添加起点
            first_pt = path[0]
            poly.addPoint(Point3D(first_pt[0] / self.f, first_pt[1] / self.f, z))

        return poly

    def toPolys(self, paths, z=0, closed=True):
        """将Path列表转化为Polyline列表"""
        polys = []
        for path in paths:
            polys.append(self.toPoly(path, z, closed))
        return polys

    def offset(self, polys, delta, jt=pyclipper.JT_SQUARE):
        """偏置函数，输入Polyline列表"""
        if not polys:
            return []

        pco = pyclipper.PyclipperOffset()
        pco.ArcTolerance = self.arcTolerance * self.f  # 指定图像精度，放大

        # 添加所有轮廓
        paths = self.toPaths(polys)
        for path in paths:
            pco.AddPath(path, jt, pyclipper.ET_CLOSEDPOLYGON)

        # 执行偏置，偏置距离按比例放大
        solution = pco.Execute(delta * self.f)

        if not solution:
            return []

        # 使用第一个多边形的z坐标
        z_coord = polys[0].point(0).z if polys[0].count() > 0 else 0
        return self.toPolys(solution, z_coord, True)