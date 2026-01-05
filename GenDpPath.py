import math
from GeomBase import *
from Polyline import *
from GeomAlgo import rotatePolygons
from SplitRegion import splitRegion
from GenHatch import genHatches
from Utility import degToRad


class GenDpPath:
    def __init__(self, polygons, interval, angle):
        self.polygons = polygons
        self.interval = interval
        self.angle = angle
        self.splitPolys = []

    def genScanYs(self, polygons):
        # 1. 获取所有多边形的整体 Y 范围
        yMin, yMax = float('inf'), float('-inf')
        has_points = False
        for poly in polygons:
            for i in range(poly.count()):
                pt = poly.point(i)
                if pt.y < yMin: yMin = pt.y
                if pt.y > yMax: yMax = pt.y
                has_points = True

        if not has_points: return []
        grid_start_idx = math.floor((yMin - 1e-5) / self.interval)
        start_y = grid_start_idx * self.interval

        ys = []
        idx = 0
        while True:
            curr_y = start_y + idx * self.interval

            # 超过最大范围则停止
            if curr_y > yMax + 1e-5:
                break

            # 只保留实际上穿过模型的线
            if curr_y >= yMin - 1e-5:
                ys.append(curr_y)

            idx += 1

        return ys

    def linkLocalHatches(self, segs):
        """Zig-Zag 连接函数"""
        poly = Polyline()
        if not segs: return poly


        segs.sort(key=lambda s: (round(s.A.y, 4), s.A.x))

        for i, seg in enumerate(segs):
            # 偶数行：A -> B
            if i % 2 == 0:
                poly.addPoint(seg.A)
                poly.addPoint(seg.B)
            # 奇数行：B -> A
            else:
                poly.addPoint(seg.B)
                poly.addPoint(seg.A)

            # 标记连接线段（跳刀）
            if i < len(segs) - 1:
                if poly.count() > 0:
                    poly.points[-1].w = 1.0

        return poly

    def generate(self):
        # 1. 旋转多边形至水平方向 (-angle)
        center = Point3D(0, 0, 0)
        rotPolys = rotatePolygons(self.polygons, -self.angle, center)

        # 2. 分区生成单连通区域
        self.splitPolys = splitRegion(rotPolys)

        # 3. 计算一次全局 ys
        ys = self.genScanYs(rotPolys)

        paths = []
        # 4. 对每个单连通区域生成并连接路径
        for poly in self.splitPolys:
            # 传入全局 ys，确保每个区域都在同一套网格上切分
            segs = genHatches([poly], ys)

            if len(segs) > 0:
                path = self.linkLocalHatches(segs)
                paths.append(path)

        # 5. 将路径旋转回原始角度 (+angle)
        return rotatePolygons(paths, self.angle, center)

    def generateEx(self, ys=None, center=None):
        rotPolys = rotatePolygons(self.polygons, -self.angle, center)
        if ys is None: ys = self.genScanYs(rotPolys)
        self.splitPolys = splitRegion(rotPolys)
        paths = []
        for poly in self.splitPolys:
            segs = genHatches([poly], ys)
            if len(segs) > 0:
                path = self.linkLocalHatches(segs)
                paths.append(path)
        return rotatePolygons(paths, self.angle, center)


# 全局接口
def genDpPath(polygons, interval, angle):
    return GenDpPath(polygons, interval, angle).generate()


def genDpPathEx(polygons, interval, angle, ys=None, center=None):
    return GenDpPath(polygons, interval, angle).generateEx(ys, center)