import math
import pyclipper
from GeomBase import *
from Line import Line
from Plane import Plane
from Polyline import Polyline
from GeomAlgo import intersect
from ClipperAdaptor import ClipperAdaptor
from SliceAlgo import readSlcFile
from StlModel import StlModel
from Utility import degToRad
import vtk
from VtkAdaptor import VtkAdaptor


class FindSptRegion:
    def __init__(self, stlModel, layers, gridSize, crAngle, xyGap=1):
        self.digit = 3  # 计算精度
        self.stlModel = stlModel
        self.layers = layers
        self.gridSize = gridSize  # 预设网格边长
        self.ax, self.ay = 0, 0  # 调整后的网格边长
        self.crAngle = crAngle  # 支撑临界角 (弧度)
        self.xyGap = xyGap  # 支撑横向间隙

    def execute(self):
        """类的核心函数"""
        # 1. 计算模型支撑点 (竖直方向)
        gridDic = self.calcModelSptPoints()

        # 2. 遍历每一层切片，生成平面支撑区域
        if self.layers:
            for layer in self.layers:
                layer.sptContours = []  # 初始化支撑轮廓列表
                # 计算当前高度的切片支撑点
                pts = self.calcLayerSptPoints(gridDic, layer.z)
                # 如果有支撑点，生成支撑区域
                if len(pts) > 0:
                    layer.sptContours = self.genSptRegions(pts, layer)

    def initGrids(self):
        """底面网格生成函数"""
        xMin, xMax, yMin, yMax, zMin, zMax = self.stlModel.getBounds()

        # 根据公式(10-1)和(10-2)计算调整后的网格边长
        if self.gridSize <= 0: self.gridSize = 1.0  # 防止除零

        self.ax = (xMax - xMin) / (int((xMax - xMin) / self.gridSize) + 1)
        self.ay = (yMax - yMin) / (int((yMax - yMin) / self.gridSize) + 1)

        xs, ys = [], []
        gridDic = {}

        # 生成X方向网格坐标序列
        x = xMin
        while x <= xMax:
            xs.append(round(x, self.digit))
            x += self.ax

        # 生成Y方向网格坐标序列
        y = yMin
        while y <= yMax:
            ys.append(round(y, self.digit))
            y += self.ay

        # 初始化网格字典，预存底面点 (zMin, 0度)
        for x_val in xs:
            for y_val in ys:
                gridDic[(x_val, y_val)] = [(round(zMin, self.digit), 0)]

        return xs, ys, gridDic

    def area(self, A, B, C):
        """计算由三点确定的三角形面积"""
        return 0.5 * math.fabs(A.x * B.y + B.x * C.y + C.x * A.y - A.x * C.y - B.x * A.y - C.x * B.y)

    def pointInTriangle(self, pt, tri, err=1.0e-7):
        """判断点是否在三角形投影内部 (面积法)"""
        A, B, C = tri.A, tri.B, tri.C
        S = self.area(A, B, C)
        S1 = self.area(pt, A, B)
        S2 = self.area(pt, B, C)
        S3 = self.area(pt, A, C)

        if math.fabs(S1 + S2 + S3 - S) < err:
            return True
        return False

    def getValidGrids(self, tri, xs, ys):
        """寻找 tri 对应的有效网格节点"""
        A, B, C = tri.A, tri.B, tri.C
        # 面片包络矩形
        xMin, xMax = min(A.x, B.x, C.x), max(A.x, B.x, C.x)
        yMin, yMax = min(A.y, B.y, C.y), max(A.y, B.y, C.y)

        sub_xs, sub_ys = [], []

        # 筛选潜在的X、Y坐标子序列
        for x in xs:
            if xMin <= x <= xMax:
                sub_xs.append(x)
            elif x > xMax:
                break
        for y in ys:
            if yMin <= y <= yMax:
                sub_ys.append(y)
            elif y > yMax:
                break

        grids = []
        # 精确判断
        for x in sub_xs:
            for y in sub_ys:
                if self.pointInTriangle(Point3D(x, y, 0), tri):
                    grids.append((x, y))
        return grids

    def getFacetAngle(self, tri):
        """计算面片倾角 (法向量与Z轴夹角)"""
        angle = tri.N.getAngle(Vector3D(0, 0, 1))  # 结果为弧度
        angle = round(angle, self.digit)
        # 保证倾角在 0~90 度 (0~pi/2) 范围内
        return (math.pi - angle) if angle > math.pi / 2 else angle

    def calcModelSptPoints(self):
        """计算模型支撑点"""
        xs, ys, gridDic = self.initGrids()

        for tri in self.stlModel.triangles:
            validGrids = self.getValidGrids(tri, xs, ys)
            for vg in validGrids:
                ln = Line(Point3D(vg[0], vg[1], 0), Vector3D(0, 0, 1))
                pln = Plane(tri.A, tri.N)
                pt = intersect(ln, pln)
                if pt is not None:
                    z = round(pt.z, self.digit)
                    a = self.getFacetAngle(tri)
                    gridDic[vg].append((z, a))

        # 对每组交点按z值从小到大排序
        for k in gridDic:
            gridDic[k].sort(key=lambda t: t[0])

        return gridDic

    def hasSptPoint(self, zas, z):
        """判断网格上是否有切片支撑点"""
        for i in range(0, len(zas), 2):
            if i + 1 <= len(zas) - 1:
                za0, za1 = zas[i], zas[i + 1]
                if za0[0] <= z <= za1[0] and za1[1] <= self.crAngle:
                    return True
        return False

    def calcLayerSptPoints(self, gridDic, z):
        """计算切片支撑点"""
        pts = []
        for key in gridDic.keys():
            zas = gridDic[key]
            if self.hasSptPoint(zas, z):
                pts.append(Point3D(key[0], key[1], z))
        return pts

    def pointToRect(self, pt, lx, ly):
        """将点转化为平面矩形"""
        vx, vy = Vector3D(lx / 2, 0, 0), Vector3D(0, ly / 2, 0)
        rect = Polyline()
        rect.addPoint(pt - vx - vy)
        rect.addPoint(pt + vx - vy)
        rect.addPoint(pt + vx + vy)
        rect.addPoint(pt - vx + vy)
        rect.addPoint(pt - vx - vy)  # 闭合
        return rect

    def genRawSptRegions(self, pts):
        """支撑点转化为初始支撑区域 (布尔并)"""
        rects = []
        for pt in pts:
            rects.append(self.pointToRect(pt, 1.1 * self.ax, 1.1 * self.ay))

        clipper, ca = pyclipper.Pyclipper(), ClipperAdaptor()
        clipper.AddPaths(ca.toPaths(rects), pyclipper.PT_SUBJECT, True)
        sln = clipper.Execute(pyclipper.CT_UNION, pyclipper.PFT_POSITIVE, pyclipper.PFT_POSITIVE)
        return ca.toPolys(sln, pts[0].z)

    def genSptRegions(self, pts, layer):
        """生成最终支撑区域 (修正初始区域，避开模型) - 增强鲁棒性版"""
        # 1. 生成初始区域
        rawRegions = self.genRawSptRegions(pts)
        if not rawRegions:
            return []

        clipper, ca = pyclipper.Pyclipper(), ClipperAdaptor()

        # 2. 对模型轮廓进行偏置 (xyGap)
        model_contours_offset = []
        try:
            if layer.contours:
                model_contours_offset = ca.offset(layer.contours, self.xyGap)
        except Exception:
            model_contours_offset = []

        # 3. 检查偏置后的路径是否有效
        valid_clips = []
        if model_contours_offset:
            for poly in model_contours_offset:
                # 过滤掉点数太少的退化多边形
                if poly.count() >= 3:
                    valid_clips.append(poly)

        # 4. 设置布尔运算路径
        clipper.AddPaths(ca.toPaths(rawRegions), pyclipper.PT_SUBJECT, True)

        # 只有当裁剪路径有效时才添加
        if valid_clips:
            try:
                clipper.AddPaths(ca.toPaths(valid_clips), pyclipper.PT_CLIP, True)
            except pyclipper.ClipperException:
                # 如果Clipper依然报错，说明路径可能有自相交等严重问题，跳过裁剪
                print(f"警告: Layer Z={layer.z} 裁剪路径无效，跳过避让修正。")
                return rawRegions

        # 5. 执行布尔减
        try:
            sln = clipper.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        except pyclipper.ClipperException:
            print(f"警告: Layer Z={layer.z} 布尔运算失败，返回初始区域。")
            return rawRegions

        return ca.toPolys(sln, layer.z)


def findSptRegion(stlModel, layers, gridSize, crAngle, xyGap=1):
    """支撑生成全局函数"""
    FindSptRegion(stlModel, layers, gridSize, crAngle, xyGap).execute()


if __name__ == '__main__':
    # 简单测试代码
    pass