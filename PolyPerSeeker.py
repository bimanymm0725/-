from GeomAlgo import pointInPolygon
from Utility import makeListLinear
import math


class PolyPerSeeker:
    def __init__(self, polys):
        self.polys = makeListLinear(polys)  # 将输入列表转为线性列表
        self.seek()

    def seek(self):
        """寻找父子关系的核心函数"""
        polys = self.polys

        # 初始化动态属性
        for poly in polys:
            poly.area = math.fabs(poly.getArea())  # 面积为绝对值
            poly.parent = None  # 父曲线
            poly.childs = []  # 子曲线列表
            poly.depth = 0  # 深度值

        # 根据面积对曲线排序（从小到大）
        polys.sort(key=lambda t: t.area)

        # 寻找父子关系
        for i in range(0, len(polys) - 1):
            for j in range(i + 1, len(polys)):
                pt = polys[i].startPoint()  # 取第i条曲线的起点为测试点
                if pointInPolygon(pt, polys[j]) == 1:  # 点在多边形内部
                    polys[i].parent = polys[j]  # 指定父曲线
                    polys[j].childs.append(polys[i])  # 添加子曲线
                    break

        # 计算每条曲线的深度值
        for poly in polys:
            self.findPolyDepth(poly)

        # 依据曲线深度值对polys排序
        polys.sort(key=lambda t: t.depth)

    def findPolyDepth(self, poly):
        """曲线深度值计算函数"""
        crtPoly = poly
        while crtPoly.parent is not None:
            crtPoly = crtPoly.parent
            poly.depth += 1


def seekPolyPer(polys):
    """全局接口函数"""
    return PolyPerSeeker(polys).polys