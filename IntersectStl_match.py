from GeomBase import *
from Triangle import *
from StlModel import *
from Layer import *
from GeomAlgo import *


class IntersectStl_match:
    def __init__(self, stlModel, layerThk):
        self.stlModel = stlModel
        self.layerThk = layerThk
        self.layers = []
        self.intersect()

    def matchFacetZs_brutal(self, zs):
        """暴力法层高匹配函数"""
        for tri in self.stlModel.triangles:
            zMin, zMax = tri.zMinPnt().z, tri.zMaxPnt().z
            for z in zs:
                if z > zMax:
                    break
                if z >= zMin and z <= zMax:
                    tri.zs.append(z)

    def matchFacetZs_bisection(self, zs):
        """二分法层高匹配函数"""
        n = len(zs)
        for tri in self.stlModel.triangles:
            zMin, zMax = tri.zMinPnt().z, tri.zMaxPnt().z

            # 1. 二分法寻找下限序号
            low, up, mid = 0, n - 1, 0
            while up - low > 1:
                mid = int((low + up) / 2)
                if zs[mid] < zMin:
                    low = mid
                else:
                    up = mid

            start = up
            if zs[low] == zMin:
                start = low

            # 2. 二分法寻找上限序号
            low, up = 0, n - 1
            while up - low > 1:
                mid = int((low + up) / 2)
                if zs[mid] < zMax:
                    low = mid
                else:
                    up = mid

            stop = low
            if zs[up] == zMax:
                stop = up

            # 3. 将匹配的层高添加到面片
            for i in range(start, stop + 1):
                tri.zs.append(zs[i])

    def genLayerHeights(self):
        """生成切片层高列表和层字典"""
        xMin, xMax, yMin, yMax, zMin, zMax = self.stlModel.getBounds()
        zs = []
        layerDic = {}
        z = zMin + self.layerThk
        while z < zMax:
            zs.append(z)
            layerDic[z] = Layer(z)
            z += self.layerThk
        return zs, layerDic

    def intersect(self):
        """层高匹配截交核心函数"""
        # 生成层高列表和层字典
        zs, layerDic = self.genLayerHeights()

        # 使用二分法进行层高匹配
        self.matchFacetZs_bisection(zs)

        # 遍历所有三角面片进行截交计算
        for triangle in self.stlModel.triangles:
            for z in triangle.zs:
                seg = intersectTriangleZPlane(triangle, z)
                if seg is not None:
                    layerDic[z].segments.append(seg)

        # 将层字典转换为层列表
        for layer in layerDic.values():
            self.layers.append(layer)