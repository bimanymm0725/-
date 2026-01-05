import math
import pyclipper
from Polyline import *
from GeomBase import Point3D


class ClipperAdaptor:
    def __init__(self, digits=7):
        self.f = math.pow(10, digits)  # 数值精度放大倍数
        self.arcTolerance = 0.005  # 圆弧离散精度

    def toPath(self, poly):
        """将Polyline转化为Path (浮点 -> 整数)"""
        path = []
        for pt in poly.points:
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
        """将Path转化为Polyline (整数 -> 浮点)"""
        poly = Polyline()
        for pt in path:
            x = pt[0] / self.f
            y = pt[1] / self.f
            poly.addPoint(Point3D(x, y, z))

        if len(path) > 0 and closed:
            first_pt = path[0]
            if path[-1] != first_pt:
                poly.addPoint(Point3D(first_pt[0] / self.f, first_pt[1] / self.f, z))
        return poly

    def toPolys(self, paths, z=0, closed=True):
        """将Path列表转化为Polyline列表"""
        polys = []
        for path in paths:
            if len(path) < 3: continue
            polys.append(self.toPoly(path, z, closed))
        return polys

    def simplify_and_clean(self, polys, clean_dist=0.02):
        """
        对轮廓进行简化和清洗，去除微小锯齿和自相交。
        这是处理“脏”几何数据的核心工具。
        """
        if not polys: return []

        paths = self.toPaths(polys)

        try:
            simplified = pyclipper.SimplifyPolygons(paths, pyclipper.PFT_NONZERO)
        except:
            return polys

        cleaned = pyclipper.CleanPolygons(simplified, clean_dist * self.f)

        # 获取Z高度
        z = polys[0].point(0).z if polys and polys[0].count() > 0 else 0

        return self.toPolys(cleaned, z, True)

    def offset(self, polys, delta, jt=pyclipper.JT_SQUARE):
        """偏置函数"""
        if not polys: return []

        pco = pyclipper.PyclipperOffset()
        pco.ArcTolerance = self.arcTolerance * self.f

        paths = self.toPaths(polys)
        for path in paths:
            pco.AddPath(path, jt, pyclipper.ET_CLOSEDPOLYGON)

        # 执行偏置
        try:
            solution = pco.Execute(delta * self.f)
        except:
            return []

        if not solution: return []

        z_coord = polys[0].point(0).z if polys[0].count() > 0 else 0
        return self.toPolys(solution, z_coord, True)

    def clip(self, subjPolys, clipPolys, clipType, z=0, minArea=0.01):
        """通用布尔运算"""
        clipper = pyclipper.Pyclipper()

        p_subj = self.toPaths(subjPolys)
        p_clip = self.toPaths(clipPolys)

        if not p_subj: return []

        clipper.AddPaths(p_subj, pyclipper.PT_SUBJECT, True)
        if p_clip:
            clipper.AddPaths(p_clip, pyclipper.PT_CLIP, True)

        try:
            sln = clipper.Execute(clipType, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        except:
            return []

        slnPolys = self.toPolys(sln, z)

        # 过滤微小面积
        resultPolys = []
        for poly in slnPolys:
            if math.fabs(poly.getArea()) >= minArea:
                resultPolys.append(poly)

        return resultPolys