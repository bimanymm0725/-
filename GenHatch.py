import math
import pyclipper
from GeomBase import *
from Polyline import *
from Segment import *
from Line import *
from GeomAlgo import intersect
from ClipperAdaptor import ClipperAdaptor


class SweepLine:
    def __init__(self):
        self.segs = []

    def intersect(self, y):
        ips = []

        # 获取当前层的正确 Z 高度
        current_z = 0.0
        if len(self.segs) > 0:
            current_z = self.segs[0].A.z

        yLine = Line(Point3D(0, y, current_z), Vector3D(1, 0, 0))

        for seg in self.segs:
            # 检查端点重合
            if abs(seg.A.y - y) < epsilon:
                ips.append(seg.A.clone())
            elif abs(seg.B.y - y) < epsilon:
                ips.append(seg.B.clone())
            else:
                ip = intersect(yLine, seg)
                if ip is not None:
                    ips.append(ip)

        # 按X排序
        ips.sort(key=lambda p: p.x)

        # 移除重合点
        i = len(ips) - 1
        while i > 0:
            if ips[i].distanceSquare(ips[i - 1]) < epsilonSquare:
                del ips[i]
                del ips[i - 1]
                i -= 2
            else:
                i -= 1
        return ips


def calcHatchPoints(polygons, ys):
    segs = []
    # 收集所有边
    for poly in polygons:
        cnt = poly.count()
        for i in range(cnt):
            p1 = poly.point(i)
            p2 = poly.point((i + 1) % cnt)
            # 忽略极短边
            if p1.distance(p2) < epsilon: continue

            seg = Segment(p1, p2)
            seg.yMin = min(p1.y, p2.y)
            seg.yMax = max(p1.y, p2.y)
            segs.append(seg)

    segs.sort(key=lambda s: s.yMin)

    k = 0
    sweep = SweepLine()
    ipsec = []

    for y in ys:
        # 移除
        for i in range(len(sweep.segs) - 1, -1, -1):
            if sweep.segs[i].yMax < y - epsilon:
                del sweep.segs[i]

        # 添加
        for i in range(k, len(segs)):
            seg = segs[i]
            # yMin < y <= yMax (半开区间，防止顶点重复计算)
            if seg.yMin < y - epsilon <= seg.yMax:
                sweep.segs.append(seg)
            elif seg.yMin >= y - epsilon:
                k = i
                break

        if len(sweep.segs) > 0:
            ipsec.append(sweep.intersect(y))
        else:
            ipsec.append([])

    return ipsec


def genHatches(polygons, ys):
    segs = []
    ipsec = calcHatchPoints(polygons, ys)
    for ips in ipsec:
        for i in range(0, len(ips), 2):
            if i + 1 < len(ips):
                segs.append(Segment(ips[i], ips[i + 1]))
    return segs


def genSweepHatches(polygons, interval, angle):
    mt = Matrix3D.createRotateMatrix(Vector3D(0, 0, 1), -angle)
    mb = Matrix3D.createRotateMatrix(Vector3D(0, 0, 1), angle)
    rotPolys = [p.multiplied(mt) for p in polygons]

    yMin, yMax = float('inf'), float('-inf')
    for poly in rotPolys:
        for pt in poly.points:
            yMin = min(yMin, pt.y)
            yMax = max(yMax, pt.y)

    ys = []
    y = yMin + interval
    while y < yMax:
        ys.append(y)
        y += interval

    segs = genHatches(rotPolys, ys)
    for seg in segs:
        seg.multiply(mb)
    return segs


def genClipHatches(polygons, interval, angle):
    if not polygons: return []
    xMin, xMax = float('inf'), float('-inf')
    yMin, yMax = float('inf'), float('-inf')
    z = polygons[0].startPoint().z

    for poly in polygons:
        for pt in poly.points:
            xMin = min(xMin, pt.x);
            xMax = max(xMax, pt.x)
            yMin = min(yMin, pt.y);
            yMax = max(yMax, pt.y)

    center = Point3D((xMin + xMax) / 2, (yMin + yMax) / 2, z)
    R = math.sqrt((xMax - xMin) ** 2 + (yMax - yMin) ** 2) / 2.0
    v = Vector3D(math.cos(angle), math.sin(angle), 0)
    n = Vector3D(math.cos(angle + math.pi / 2), math.sin(angle + math.pi / 2), 0)

    parallels = []
    start_base = center - n.amplified(R)
    num_lines = int(2 * R / interval) + 2

    for i in range(num_lines):
        base_pt = start_base + n.amplified(interval * i)
        p_start = base_pt - v.amplified(R * 1.5)
        p_end = base_pt + v.amplified(R * 1.5)
        line = Polyline()
        line.addPoint(p_start)
        line.addPoint(p_end)
        parallels.append(line)

    ca = ClipperAdaptor()
    pc = pyclipper.Pyclipper()
    pc.AddPaths(ca.toPaths(polygons), pyclipper.PT_CLIP, True)
    pc.AddPaths(ca.toPaths(parallels), pyclipper.PT_SUBJECT, False)

    solution = pc.Execute2(pyclipper.CT_INTERSECTION)
    hatchSegs = []

    def extract_paths(node):
        for child in node.Childs:
            if len(child.Contour) > 0:
                poly = ca.toPoly(child.Contour, z, closed=False)
                if poly.count() >= 2:
                    hatchSegs.append(Segment(poly.startPoint(), poly.endPoint()))
            extract_paths(child)

    extract_paths(solution)
    return hatchSegs