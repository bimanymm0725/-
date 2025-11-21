from GeomBase import *
from Triangle import *
from StlModel import *
from Layer import *
from GeomAlgo import *


class SweepPlane:
    def __init__(self):
        self.triangles = []  # 修正：移除不需要的参数


class IntersectStl_sweep:
    def __init__(self, stlModel, layerThk):
        self.stlModel = stlModel
        self.layerThk = layerThk
        self.layers = []
        self.intersect()

    def genLayerHeights(self):
        """生成切片层高列表函数"""
        xMin, xMax, yMin, yMax, zMin, zMax = self.stlModel.getBounds()  # 模型边界
        zs = []
        z = zMin + self.layerThk
        while z < zMax:  # 根据切片厚度均匀生成层高
            zs.append(z)
            z += self.layerThk
        return zs

    def intersect(self):
        """扫描平面法截交实现函数"""
        triangles = self.stlModel.triangles  # 赋值，保存引用，简化写法

        # 检查是否有三角形
        if len(triangles) == 0:
            print("警告: 没有三角形数据，跳过截交计算")
            return

        # 对三角形按最低点进行排序
        triangles.sort(key=lambda t: t.zMinPnt().z)

        zs = self.genLayerHeights()  # 生成层高列表
        k = 0  # 添加面片遍历过程起始序号
        sweep = SweepPlane()  # 扫描平面对象

        for z in zs:  # 遍历层高列表循环
            # 1. 移除扫描平面面片列表中不和扫描平面相关的面片
            for i in range(len(sweep.triangles) - 1, -1, -1):
                if z > sweep.triangles[i].zMaxPnt().z:
                    del sweep.triangles[i]

            # 2. 向扫描平面面片列表添加面片
            for i in range(k, len(triangles)):
                tri = triangles[i]
                if z >= tri.zMinPnt().z and z <= tri.zMaxPnt().z:
                    sweep.triangles.append(tri)
                elif tri.zMinPnt().z > z:
                    k = i  # 记录位置，下次从i开始遍历
                    break

            # 3. 面片列表和扫描平面求交
            layer = Layer(z)
            for triangle in sweep.triangles:
                seg = intersectTriangleZPlane(triangle, z)
                if seg is not None:
                    layer.segments.append(seg)  # 截交线段保存至layer.segments中

            self.layers.append(layer)