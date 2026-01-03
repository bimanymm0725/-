import math
from GeomBase import *
from Polyline import *
from Line import *
from Ray import *
from Segment import *
from Plane import *
from Polyline import *
from Triangle import *

def nearZero(x):
    return math.fabs(x) < epsilon

def distance(obj1, obj2):
    if isinstance(obj1, Point3D) and isinstance(obj2, Line):  # Point Line
        P, Q, V = obj2.P, obj1, obj2.V
        t = P.pointTo(Q).dotProduct(V)
        R = P + V.amplified(t)
        return Q.distance(R)

    elif isinstance(obj1, Point3D) and isinstance(obj2, Ray):  # Point Ray
        P, Q, V = obj2.P, obj1, obj2.V
        t = P.pointTo(Q).dotProduct(V)
        if t >= 0:
            R = P + V.amplified(t)
            return Q.distance(R)
        return Q.distance(P)

    elif isinstance(obj1, Point3D) and isinstance(obj2, Segment):  # Point Segment
        Q, P, P1, V = obj1, obj2.A, obj2.B, obj2.direction().normalized()
        L = obj2.length()
        t = P.pointTo(Q).dotProduct(V)
        if t <= 0:
            return Q.distance(P)
        elif t <= L:
            R = P + V.amplified(t)
            return Q.distance(R)
        return Q.distance(P1)

    elif isinstance(obj1, Point3D) and isinstance(obj2, Plane):  # Point Plane
        P = obj2.P
        N = obj2.N
        PQ = obj1 - P
        if PQ.length() < epsilon:
            return 0.0
        cos_theta = PQ.dotProduct(N) / (PQ.length() * N.length())
        return abs(PQ.length() * cos_theta)
    elif isinstance(obj1, Line) and isinstance(obj2, Line):  # Line Line
        P1 = obj1.P
        V1 = obj1.V
        P2 = obj2.P
        V2 = obj2.V
        n = V1.crossProduct(V2)
        if n.lengthSquare() < epsilonSquare:
            return P1.distance(V2)
        else:
            P1P2 = P2-P1
            if P1P2.length() < epsilon:
                return 0.0
            cos_theta = P1P2.dotProduct(n) / (P1P2.length() * n.length())
            return abs(P1P2.length() * cos_theta)

    elif isinstance(obj1, Line) and isinstance(obj2, Plane):  # Line Plane
        if abs(obj1.V.dotProduct(obj2.N)) < epsilon:
            return obj1.P.distance(obj2)
        else:
            return 0.0
    elif isinstance(obj1, Ray) and isinstance(obj2, Plane):  # Ray Plane
        if abs(obj1.V.dotProduct(obj2.N)) < epsilon:
            return obj1.P.distance(obj2)
        else:
            A, B, C, D = obj2.toFormula()
            numerator = -(A * obj1.P.x + B * obj1.P.y + C * obj1.P.z + D)
            denominator = A * obj1.V.dx + B * obj1.V.dy + C * obj1.V.dz
            t = numerator / denominator

            if t >= 0:
                return 0.0
            else:
                return obj1.P.distance(obj2)
    elif isinstance(obj1, Segment) and isinstance(obj2, Plane):  # Segment Plane
        A = obj1.A
        B = obj1.B
        P = obj2.P
        N = obj2.N

        f_A = N.dx * (A.x - P.x) + N.dy * (A.y - P.y) + N.dz * (A.z - P.z)
        f_B = N.dx * (B.x - P.x) + N.dy * (B.y - P.y) + N.dz * (B.z - P.z)

        if f_A * f_B <= 0:
            return 0.0
        else:
            dA = distance(A, obj2)
            dB = distance(B, obj2)
            return min(dA, dB)
    return None


def intersectLine(line1, line2):
    """
    计算两条直线的交点
    返回: 交点P, t1, t2
    注意: 交点P可能为None（当直线平行或不相交时）
    """

    P1 = line1.P
    V1 = line1.V
    P2 = line2.P
    V2 = line2.V
    P1P2 = P2 - P1

    # 检查两条直线是否平行
    cross = V1.crossProduct(V2)
    if cross.lengthSquare() < epsilonSquare:
        if abs(P1P2.crossProduct(V2).lengthSquare()) < epsilonSquare:
            return P1.clone(), 0, P1P2.dotProduct(V2)
        else:
            return None, 0, 0

    denominator = V1.dx * V2.dy - V1.dy * V2.dx
    if abs(denominator) > epsilon:
        t1 = (P1P2.dx * V2.dy - P1P2.dy * V2.dx) / denominator
        t2 = (P1P2.dx * V1.dy - P1P2.dy * V1.dx) / denominator
    else:
        denominator = V1.dy * V2.dz - V1.dz * V2.dy
        if abs(denominator) > epsilon:
            t1 = (P1P2.dy * V2.dz - P1P2.dz * V2.dy) / denominator
            t2 = (P1P2.dy * V1.dz - P1P2.dz * V1.dy) / denominator
        else:
            denominator = V1.dx * V2.dz - V1.dz * V2.dx
            if abs(denominator) > epsilon:
                t1 = (P1P2.dx * V2.dz - P1P2.dz * V2.dx) / denominator
                t2 = (P1P2.dx * V1.dz - P1P2.dz * V1.dx) / denominator
            else:
                return None, 0, 0

    intersection = P1 + V1.amplified(t1)

    return intersection, t1, t2


def intersectSegmentPlane(seg, plane):
    """计算线段和平面的交点，返回交点P或None"""

    A = seg.A
    B = seg.B
    AB = B - A

    if AB.lengthSquare() < epsilonSquare:
        if pointOnPlane(A, plane):
            return A
        else:
            return None

    dot = AB.dotProduct(plane.N)

    if abs(dot) < epsilon:
        if pointOnPlane(A, plane):
            return A
        else:
            return None

    t = -plane.N.dotProduct(A - plane.P) / dot

    if 0 <= t <= 1:
        intersection = A + AB.amplified(t)
        return intersection
    else:
        return None


def intersect(obj1, obj2):
    """计算两个几何对象的交点"""
    if isinstance(obj1, Line) and isinstance(obj2, Line):
        intersection, t1, t2 = intersectLine(obj1, obj2)
        return intersection

    elif isinstance(obj1, Segment) and isinstance(obj2, Segment):
        V1 = obj1.direction().normalized()
        V2 = obj2.direction().normalized()
        line1 = Line(obj1.A, V1)
        line2 = Line(obj2.A, V2)

        intersection, t1, t2 = intersectLine(line1, line2)

        if intersection and 0 <= t1 <= obj1.length() and 0 <= t2 <= obj2.length():
            return intersection
        else:
            return None

    elif isinstance(obj1, Line) and isinstance(obj2, Segment):
        V2 = obj2.direction().normalized()
        line2 = Line(obj2.A, V2)
        intersection, t1, t2 = intersectLine(obj1, line2)

        if intersection and 0 <= t2 <= obj2.length():
            return intersection
        else:
            return None

    elif isinstance(obj1, Line) and isinstance(obj2, Ray):
        intersection, t1, t2 = intersectLine(obj1, Line(obj2.P, obj2.V))

        if intersection and t2 >= 0:
            return intersection
        else:
            return None

    elif isinstance(obj1, Ray) and isinstance(obj2, Segment):
        V2 = obj2.direction().normalized()
        intersection, t1, t2 = intersectLine(Line(obj1.P, obj1.V), Line(obj2.A, V2))

        if intersection and t1 >= 0 and 0 <= t2 <= obj2.length():
            return intersection
        else:
            return None

    elif isinstance(obj1, Ray) and isinstance(obj2, Ray):
        intersection, t1, t2 = intersectLine(Line(obj1.P, obj1.V), Line(obj2.P, obj2.V))

        if intersection and t1 >= 0 and t2 >= 0:
            return intersection
        else:
            return None

    elif isinstance(obj1, Line) and isinstance(obj2, Plane):
        dot = obj1.V.dotProduct(obj2.N)

        if nearZero(dot):
            if pointOnPlane(obj1.P, obj2):
                return obj1.P
            else:
                return None

        numerator = -obj2.N.dotProduct(obj1.P - obj2.P)
        t = numerator / dot

        intersection = obj1.P + obj1.V.amplified(t)
        return intersection

    elif isinstance(obj1, Ray) and isinstance(obj2, Plane):
        line = Line(obj1.P, obj1.V)
        intersection = intersect(line, obj2)

        if intersection and pointOnRay(intersection, obj1):
            return intersection
        else:
            return None

    elif isinstance(obj1, Segment) and isinstance(obj2, Plane):
        return intersectSegmentPlane(obj1, obj2)

    return None

def pointOnPlane(point, plane):
    """判断点是否在平面上"""
    PQ = point - plane.P
    distance = abs(PQ.dotProduct(plane.N))
    return distance < epsilon

def pointOnRay(p, ray):
    """判断点是否在射线上"""
    PR = ray.P - p
    if PR.lengthSquare() < epsilonSquare:
        return True

    cross = ray.V.crossProduct(PR)
    if cross.lengthSquare() < epsilonSquare and ray.V.dotProduct(PR) > 0:
        return True

    return False

def pointInPolygon(p, polygon):
    """
    判断点与多边形的位置关系
    返回:
        -1 : 在多边形边界上
        1  : 在多边形内部
        0  : 在多边形外部
    """
    n = polygon.count()
    for i in range(n):
        A = polygon.point(i)
        B = polygon.point((i + 1) % n)

        seg = Segment(A, B)
        if p.distance(seg) < epsilon:
            return -1


    count = 0
    for i in range(n):
        A = polygon.point(i)
        B = polygon.point((i + 1) % n)

        if (A.y > p.y and B.y > p.y) or (A.y < p.y and B.y < p.y):
            continue

        if nearZero(A.y - p.y) and nearZero(B.y - p.y):
            if (A.x <= p.x <= B.x) or (B.x <= p.x <= A.x):
                return -1
            continue

        if not nearZero(B.y - A.y):
            x_intersect = A.x + (p.y - A.y) * (B.x - A.x) / (B.y - A.y)

            if x_intersect > p.x:
                if not (nearZero(A.y - p.y) and A.x > p.x) and not (nearZero(B.y - p.y) and B.x > p.x):
                    count += 1

    if count % 2 == 1:
        return 1
    else:
        return 0


def intersectTrianglePlane(triangle, plane):
    """空间三角形和平面求交函数"""
    # 输入为Triangle和Plane对象
    AB = Segment(triangle.A, triangle.B)  # 三角形3条边
    AC = Segment(triangle.A, triangle.C)
    BC = Segment(triangle.B, triangle.C)

    c1 = intersectSegmentPlane(AB, plane)  # 3条边和平面交点
    c2 = intersectSegmentPlane(AC, plane)
    c3 = intersectSegmentPlane(BC, plane)

    # 分类讨论，枚举各种情况
    if c1 is None:
        if c2 is not None and c3 is not None:  # 存在2个交点的情况
            if c2.distance(c3) != 0.0:
                return Segment(c2, c3)
    elif c2 is None:
        if c1 is not None and c3 is not None:  # 存在2个交点的情况
            if c1.distance(c3) != 0.0:
                return Segment(c1, c3)
    elif c3 is None:
        if c1 is not None and c2 is not None:  # 存在2个交点的情况
            if c1.distance(c2) != 0.0:
                return Segment(c1, c2)
    elif c1 is not None and c2 is not None and c3 is not None:  # 存在3个交点的情况
        return Segment(c1, c3) if c1.isIdentical(c2) else Segment(c1, c2)

    return None  # 如果都不满足，返回None

def intersectTriangleZPlane(triangle, z):
    """计算三角形与Z平面的交线"""
    if triangle.zMinPnt().z>z:
        return None
    if triangle.zMaxPnt().z<z:
        return None
    plane = Plane.zPlane(z)
    return intersectTrianglePlane(triangle, plane)

def adjustPolygonDirs(polygons):
    """调整多边形的方向（统一外边界为逆时针，内边界为顺时针）"""
    for i in range(len(polygons)):
        pt = polygons[i].startPoint()  # 取出待检测轮廓上的起点
        insideCount = 0  # 点在几个多边形内部计数

        for j in range(len(polygons)):
            if j == i:  # 如果两个多边形一样则跳过
                continue
            restPoly = polygons[j]
            if pointInPolygon(pt, restPoly) == 1:  # 点在另一多边形内部，则加1
                insideCount += 1

        # 判断点在内部次数是否为偶数
        if insideCount % 2 == 0:
            polygons[i].makeCCW()  # 调整多边形方向为逆时针
        else:
            polygons[i].makeCW()  # 调整多边形方向为顺时针


def rotatePolygons(polygons, angle, center=None):
    """旋转多边形集合，返回新的多边形列表（不修改原对象）"""
    if not polygons:
        return []

    # 确定旋转中心
    dx = 0 if center is None else center.x
    dy = 0 if center is None else center.y

    # 构造变换矩阵：平移到原点 -> 旋转 -> 平移回原处
    mt = Matrix3D.createTranslateMatrix(-dx, -dy, 0)
    mr = Matrix3D.createRotateMatrix(Vector3D(0, 0, 1), angle)
    mb = Matrix3D.createTranslateMatrix(dx, dy, 0)

    m = mt * mr * mb

    newPolys = []
    for poly in polygons:
        # 使用 multiplied 生成新对象，而不是 multiply
        newPolys.append(poly.multiplied(m))

    return newPolys