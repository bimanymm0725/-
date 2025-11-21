from GeomBase import *
from LinkPoint import LinkPoint
from Polyline import Polyline
import functools


def cmp_pntSmaller(lp1, lp2):
    """字典序比较两个链接点大小"""
    if lp1.x < lp2.x:
        return -1
    elif lp1.x == lp2.x and lp1.y < lp2.y:
        return -1
    elif lp1.x == lp2.x and lp1.y == lp2.y and lp1.z < lp2.z:
        return -1
    elif lp1.x == lp2.x and lp1.y == lp2.y and lp1.z == lp2.z:
        return 0
    else:
        return 1


class LinkSegs_dorder:
    def __init__(self, segs):
        self.segs = segs
        self.contours = []
        self.polys = []
        self.link()

    def createLpList(self):
        """根据输入线段构建链接点列表"""
        lpnts = []

        for seg in self.segs:
            lp1 = LinkPoint(seg.A)
            lp2 = LinkPoint(seg.B)
            lp1.other = lp2
            lp2.other = lp1
            lpnts.append(lp1)
            lpnts.append(lp2)

        # 对点进行字典序排序
        lpnts.sort(key=functools.cmp_to_key(cmp_pntSmaller))
        return lpnts

    def findUnusedPnt(self, lpnts):
        """从列表中找出未使用的点"""
        for lp in lpnts:
            if not lp.used:
                return lp
        return None

    def findCoincidentPoint(self, target_point, lpnts):
        """在排序列表中寻找与目标点重合的未使用点"""
        for lp in lpnts:
            if lp.isCoincident(target_point) and not lp.used and lp != target_point:
                return lp
        return None

    def link(self):
        """字典序拼接核心函数 - 简化版本"""
        lpnts = self.createLpList()

        debug_mode = len(lpnts) < 1000

        while True:
            # 寻找未使用的点
            start_point = self.findUnusedPnt(lpnts)
            if start_point is None:
                break

            poly = Polyline()
            current = start_point
            start_point_coords = (start_point.x, start_point.y, start_point.z)

            if debug_mode:
                print(f"开始新轮廓，起始点: ({current.x}, {current.y}, {current.z})")

            iteration_count = 0
            max_iterations = len(lpnts) * 2

            while iteration_count < max_iterations:
                iteration_count += 1

                # 添加当前点到轮廓
                poly.addPoint(current.toPoint3D())
                current.used = True

                # 标记另一端点为已使用
                if current.other and not current.other.used:
                    current.other.used = True

                # 获取当前线段的另一端
                other_end = current.other

                # 寻找与另一端重合的下一个点
                next_point = self.findCoincidentPoint(other_end, lpnts)

                if next_point is None:
                    # 检查是否可以闭合轮廓
                    if poly.count() > 2 and other_end.isCoincident(start_point):
                        poly.addPoint(start_point.toPoint3D())
                        if debug_mode:
                            print(f"轮廓闭合，总点数: {poly.count()}")
                    break

                # 检查是否回到起点
                if next_point.isCoincident(start_point):
                    poly.addPoint(start_point.toPoint3D())
                    if debug_mode:
                        print(f"轮廓闭合，总点数: {poly.count()}")
                    break

                current = next_point

            # 保存轮廓
            if poly.count() >= 3:
                if poly.isClosed():
                    self.contours.append(poly)
                else:
                    self.polys.append(poly)

        return self.contours