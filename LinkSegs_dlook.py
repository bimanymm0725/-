from GeomBase import *
from LinkPoint import LinkPoint
from Polyline import Polyline


class LinkSegs_dlook:
    def __init__(self, segs):
        self.segs = segs
        self.contours = []
        self.polys = []
        self.link()

    def createPointDict(self):
        """构建点字典"""
        point_dict = {}

        for seg in self.segs:
            lp1 = LinkPoint(seg.A)
            lp2 = LinkPoint(seg.B)
            lp1.other = lp2
            lp2.other = lp1

            # 使用坐标作为键
            key1 = (lp1.x, lp1.y, lp1.z)
            key2 = (lp2.x, lp2.y, lp2.z)

            if key1 not in point_dict:
                point_dict[key1] = []
            point_dict[key1].append(lp1)

            if key2 not in point_dict:
                point_dict[key2] = []
            point_dict[key2].append(lp2)

        return point_dict

    def findUnusedPoint(self, point_dict):
        """在字典中寻找未使用的点"""
        for point_list in point_dict.values():
            for point in point_list:
                if not point.used:
                    return point
        return None

    def findNextPoint(self, current_point, point_dict, start_point):
        """寻找下一个连接点"""
        # 获取当前线段的另一端
        other_end = current_point.other

        # 在字典中寻找与另一端重合的点
        other_key = (other_end.x, other_end.y, other_end.z)

        if other_key not in point_dict:
            return None

        candidates = point_dict[other_key]

        # 寻找未使用的点（不能是自身）
        for candidate in candidates:
            if not candidate.used and candidate != other_end:
                return candidate

        # 检查是否可以闭合到起点
        for candidate in candidates:
            if candidate.isCoincident(start_point):
                return start_point

        return None

    def link(self):
        """字典查询法拼接核心函数 - 简化版本"""
        point_dict = self.createPointDict()

        debug_mode = len(point_dict) < 100

        while True:
            # 寻找未使用的点
            start_point = self.findUnusedPoint(point_dict)
            if start_point is None:
                break

            poly = Polyline()
            current = start_point
            iteration_count = 0
            max_iterations = len(point_dict) * 2

            while iteration_count < max_iterations:
                iteration_count += 1

                # 添加当前点到轮廓
                poly.addPoint(current.toPoint3D())
                current.used = True

                # 标记另一端点为已使用
                if current.other and not current.other.used:
                    current.other.used = True

                # 寻找下一个点
                next_point = self.findNextPoint(current, point_dict, start_point)

                if next_point is None:
                    # 检查当前线段的另一端是否可以闭合轮廓
                    if poly.count() > 2 and current.other.isCoincident(start_point):
                        poly.addPoint(start_point.toPoint3D())
                    break

                # 检查是否回到起点
                if next_point.isCoincident(start_point):
                    poly.addPoint(start_point.toPoint3D())
                    break

                current = next_point

            # 保存轮廓
            if poly.count() >= 3:
                if poly.isClosed():
                    self.contours.append(poly)
                else:
                    self.polys.append(poly)

        return self.contours