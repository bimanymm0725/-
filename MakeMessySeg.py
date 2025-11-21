from GeomBase import *
from Segment import Segment
import math
import random


def makeMessySegs(circleNum=10, segNumPerCircle=100000, radius=100.0):
    """生成平面上大规模的散乱线段"""
    segs = []  # 定义线段列表
    r = radius  # 以半径递增的方式生成同心圆

    for i in range(circleNum):  # 遍历，生成指定circleNum个同心圆
        pnts = []  # 点列表，用于收集图上的点

        for j in range(segNumPerCircle):  # 按细分分段划分圆
            theta = j / segNumPerCircle * 2 * math.pi  # 角度theta
            x = r * math.cos(theta)  # 图上点x、y坐标，图心在原点
            y = r * math.sin(theta)
            pnt = Point3D(x, y)
            pnts.append(pnt)

        pnts.append(pnts[0])  # 在pnts添加起点，以封闭轮廓

        for j in range(len(pnts) - 1):  # 将点依次整理为线段，添加至segs
            seg = Segment(pnts[j], pnts[j + 1])
            segs.append(seg)

        r += 10.0  # 同心圆半径递增

    print('segment count', len(segs))  # 打印seg中线段总数

    if len(segs) > 0:
        min_length = segs[0].A.distance(segs[0].B)
        for seg in segs:
            length = seg.A.distance(seg.B)
            if length < min_length:
                min_length = length
        print('min segment length', min_length)  # 打印seg中最短的线段

    # 对seg中线段数优化处理（打乱顺序）
    for i in range(len(segs)):
        rd = random.randint(0, len(segs) - 1)  # 生成一个随机序号
        segs[i], segs[rd] = segs[rd], segs[i]  # 当前线段和随机序号线段交换

    return segs