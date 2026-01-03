import math
import pyclipper
from GeomBase import *
from Polyline import *
from GeomAlgo import adjustPolygonDirs
from GenHatch import calcHatchPoints  # 复用扫描线求交逻辑
from ClipperAdaptor import ClipperAdaptor


class SplitRegion:
    def __init__(self, polygons, adjustPolyDirs=False):
        self.polygons = polygons
        # 步骤1：确保方向符合“外逆内顺”
        if adjustPolyDirs:
            adjustPolygonDirs(self.polygons)

        # 执行分区
        self.splitPolygons = self.split()

    def findTurnPoints(self):
        """步骤2：寻找凹峰点"""
        vx = Vector3D(1, 0, 0)
        turnPts = []
        for poly in self.polygons:
            cnt = poly.count()
            if cnt < 3: continue

            pts = poly.points
            for i in range(cnt):  # 遍历每个顶点
                # 获取前后点，处理闭合索引
                prev_pt = pts[i - 1]
                curr_pt = pts[i]
                next_pt = pts[(i + 1) % cnt]

                v1 = prev_pt.pointTo(curr_pt)
                v2 = curr_pt.pointTo(next_pt)

                # 判断峰点: (v1 x vx) * (v2 x vx) <= 0 (式 9-12)
                # 即两邻边在扫描线方向(vx)的异侧
                if v1.crossProduct(vx).dz * v2.crossProduct(vx).dz <= 0:
                    # 判断凹点: v1 x v2 < 0 (式 9-9)
                    if v1.crossProduct(v2).dz < 0:
                        turnPts.append(curr_pt)
        return turnPts

    def findLRPoints(self, pt, ptses):
        """寻找凹峰点两侧最近的交点"""
        # ptses 是 calcHatchPoints 返回的二维列表 [层][点]
        for pts in ptses:
            # 找到高度相同的那一层
            if len(pts) > 0 and abs(pts[0].y - pt.y) < epsilon:
                # 遍历该层所有交点，找到夹住 pt 的两个点
                for i in range(len(pts) - 1):
                    # 因为 pts 已经按 x 排序
                    if pts[i].x < pt.x - epsilon and pts[i + 1].x > pt.x + epsilon:
                        return pts[i], pts[i + 1]
        return None, None

    def createSplitter(self, p1, p2, delta=1.0e-4):
        """创建切分矩形（瘦矩形）"""
        vx = Vector3D(1, 0, 0)
        vy = Vector3D(0, 1, 0)
        splitter = Polyline()

        # 构造微小矩形 (公式 9-14 ~ 9-17)
        # P1 = A - d*vx - d*vy
        splitter.addPoint(p1 - vx.amplified(delta) - vy.amplified(delta))
        # P2 = B + d*vx - d*vy
        splitter.addPoint(p2 + vx.amplified(delta) - vy.amplified(delta))
        # P3 = B + d*vx + d*vy
        splitter.addPoint(p2 + vx.amplified(delta) + vy.amplified(delta))
        # P4 = A - d*vx + d*vy
        splitter.addPoint(p1 - vx.amplified(delta) + vy.amplified(delta))

        splitter.addPoint(splitter.startPoint())  # 闭合
        return splitter

    def split(self):
        """分区核心函数"""
        # 1. 获取所有凹峰点
        turnPts = self.findTurnPoints()
        if not turnPts:
            return self.polygons  # 没有凹峰点，直接返回原多边形

        # 2. 收集扫描高度 ys
        ys = []
        for pt in turnPts:
            ys.append(pt.y)
        ys.sort()

        # 去除重复高度 (epsilon)
        unique_ys = []
        if len(ys) > 0:
            unique_ys.append(ys[0])
            for i in range(1, len(ys)):
                if abs(ys[i] - ys[i - 1]) > epsilon:
                    unique_ys.append(ys[i])

        # 3. 计算所有凹峰点高度处的交点
        hatchPtses = calcHatchPoints(self.polygons, unique_ys)

        splitters = []
        # 4. 对每个凹峰点构造切分器
        for turnPt in turnPts:
            lPt, rPt = self.findLRPoints(turnPt, hatchPtses)
            if lPt is not None and rPt is not None:
                splitter = self.createSplitter(lPt, rPt)
                splitters.append(splitter)

        if not splitters:
            return self.polygons

        # 5. 执行布尔差运算 (Difference)
        clipper = pyclipper.Pyclipper()
        ca = ClipperAdaptor()

        # 添加主体 (Subject)
        clipper.AddPaths(ca.toPaths(self.polygons), pyclipper.PT_SUBJECT, True)
        # 添加切分器 (Clip)
        clipper.AddPaths(ca.toPaths(splitters), pyclipper.PT_CLIP, True)

        # 执行差集
        solution = clipper.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)

        # 还原结果
        z = turnPts[0].z if turnPts else 0
        return ca.toPolys(solution, z)


def splitRegion(polygons, adjustPolyDirs=False):
    """SplitRegion 类的全局接口函数"""
    return SplitRegion(polygons, adjustPolyDirs).splitPolygons