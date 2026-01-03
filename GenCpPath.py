import pyclipper
from ClipperAdaptor import ClipperAdaptor
from PolyPerSeeker import seekPolyPer
from Polyline import *
import math


class GenCpPath:
    def __init__(self, boundaries, interval, shellThk):
        self.boundaries = boundaries
        self.interval = interval
        self.shellThk = shellThk
        self.arcTolerance = 0.005
        self.joinType = pyclipper.JT_SQUARE

        self.offsetPolyses = []
        self.paths = []

        self.offset()
        self.linkLocalOffsets()

    def offset(self):
        """连续偏置路径生成函数 (增加面积过滤)"""
        ca = ClipperAdaptor()
        ca.arcTolerance = self.arcTolerance

        # 最小面积阈值，过滤噪点
        MIN_AREA = 1.0

        delta = self.interval / 2

        # 首次偏置
        raw_polys = ca.offset(self.boundaries, -delta, self.joinType)
        valid_polys = [p for p in raw_polys if abs(p.getArea()) > MIN_AREA]

        if valid_polys:
            self.offsetPolyses.append(valid_polys)
        else:
            return

        # 循环偏置
        while math.fabs(delta) < self.shellThk:
            delta += self.interval
            raw_polys = ca.offset(self.boundaries, -delta, self.joinType)

            if not raw_polys: break

            valid_polys = [p for p in raw_polys if abs(p.getArea()) > MIN_AREA]
            if not valid_polys: break

            self.offsetPolyses.append(valid_polys)

    def linkToParent(self, child):
        """将子曲线连接到父曲线上 (增加孤岛检测)"""
        parent = child.parent
        if not parent: return child

        pt = child.startPoint()
        dMin, iAtdMin = float('inf'), 0
        for i in range(parent.count()):
            d = pt.distanceSquare(parent.point(i))
            if d < dMin:
                dMin, iAtdMin = d, i

        # 【核心修复】如果最近距离超过 3倍 路径间距，视为独立岛屿，不连接
        if math.sqrt(dMin) > self.interval * 3.0:
            return None

        newPoly = Polyline()
        for i in range(iAtdMin + 1): newPoly.addPoint(parent.point(i).clone())
        if newPoly.count() > 0: newPoly.points[-1].w = 1
        for i in range(child.count()): newPoly.addPoint(child.point(i).clone())
        if newPoly.count() > 0: newPoly.points[-1].w = 1
        for i in range(iAtdMin, parent.count()): newPoly.addPoint(parent.point(i).clone())
        return newPoly

    def linkLocalOffsets(self):
        """连接偏置曲线"""
        if not self.offsetPolyses: return

        try:
            seekPolyPer(self.offsetPolyses)
        except:
            for ps in self.offsetPolyses: self.paths.extend(ps)
            return

        merged_children = set()
        for i in range(len(self.offsetPolyses) - 1, 0, -1):
            childs = self.offsetPolyses[i]
            for j in range(len(childs)):
                child = childs[j]
                if hasattr(child, 'parent') and child.parent:
                    newPoly = self.linkToParent(child)
                    if newPoly:
                        child.parent.points = newPoly.points
                        merged_children.add(child)

        for path in self.offsetPolyses[0]:
            self.paths.append(path)

        for i in range(1, len(self.offsetPolyses)):
            for path in self.offsetPolyses[i]:
                if path not in merged_children:
                    self.paths.append(path)

        self.offsetPolyses.clear()


def genCpPath(boundaries, interval, shellThk):
    return GenCpPath(boundaries, interval, shellThk).paths