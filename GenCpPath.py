import pyclipper

from ClipperAdaptor import ClipperAdaptor
from PolyPerSeeker import seekPolyPer
from Polyline import *
import math

class GenCpPath:
    def __init__(self, boundaries, interval, shellThk):
        self.boundaries = boundaries  # 打印区域边界轮廓
        self.interval = interval  # 工艺参数：偏置距离（喷头直径）
        self.shellThk = shellThk  # 工艺参数：填充带宽（外壳厚度）
        self.arcTolerance = 0.005  # 工艺参数：圆弧精度
        self.joinType = pyclipper.JT_SQUARE  # 工艺参数：衔接类型

        self.offsetPolyses = []  # 临时存储的中间偏置曲线列表
        self.paths = []  # 最终输出的轮廓行路径列表

        self.offset()  # 调用连续偏置路径生成函数
        self.linkLocalOffsets()  # 调用路径连接函数

    def offset(self):
        """连续偏置路径生成函数"""
        ca = ClipperAdaptor()
        ca.arcTolerance = self.arcTolerance

        delta = self.interval / 2  # 首次偏置距离

        # 首次偏置
        polys = ca.offset(self.boundaries, -delta, self.joinType)
        if polys:
            self.offsetPolyses.append(polys)

        # 循环偏置直至偏置距离大于填充带宽
        while math.fabs(delta) < self.shellThk:
            delta += self.interval
            polys = ca.offset(self.boundaries, -delta, self.joinType)

            if not polys or len(polys) == 0:
                break  # 已到偏置区域中心，则退出

            self.offsetPolyses.append(polys)

    def linkToParent(self, child):
        """将子曲线连接到父曲线上"""
        parent = child.parent
        if not parent:
            return child

        pt = child.startPoint()  # 获取子曲线起点pt

        # 寻找父曲线上距离最近的点
        dMin, iAtdMin = float('inf'), 0
        for i in range(parent.count()):
            d = pt.distanceSquare(parent.point(i))
            if d < dMin:
                dMin, iAtdMin = d, i

        # 构建新的连接曲线
        newPoly = Polyline()

        # 添加父曲线的前半部分（到最近点）
        for i in range(iAtdMin + 1):
            newPoly.addPoint(parent.point(i).clone())

        # 标记连接进点
        if newPoly.count() > 0:
            newPoly.points[-1].w = 1

        # 添加子曲线
        for i in range(child.count()):
            newPoly.addPoint(child.point(i).clone())

        # 标记连接出点
        if newPoly.count() > 0:
            newPoly.points[-1].w = 1

        # 添加父曲线的后半部分（从最近点到结束）
        for i in range(iAtdMin, parent.count()):
            newPoly.addPoint(parent.point(i).clone())

        return newPoly

    def linkLocalOffsets(self):
        """连接偏置曲线"""
        if not self.offsetPolyses:
            return

        # 确定所有曲线的父子关系
        all_polys = seekPolyPer(self.offsetPolyses)

        # 从最内层开始，逐层连接到父曲线
        for i in range(len(self.offsetPolyses) - 1, 0, -1):
            childs = self.offsetPolyses[i]
            for j in range(len(childs) - 1, -1, -1):
                child = childs[j]
                if hasattr(child, 'parent') and child.parent:
                    newPoly = self.linkToParent(child)
                    parent = child.parent
                    parent.points = newPoly.points  # 用新曲线替换原父曲线
                    del childs[j]  # 删除已连接的子曲线

        # 将剩余的最外层曲线添加到输出路径
        for path in self.offsetPolyses[0]:
            self.paths.append(path)

        self.offsetPolyses.clear()  # 清空临时列表


def genCpPath(boundaries, interval, shellThk):
    """生成轮廓路径全局接口函数"""
    return GenCpPath(boundaries, interval, shellThk).paths