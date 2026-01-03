import math
from random import random, uniform
from FindSptRegion import FindSptRegion
import os


def fitness(stlModel, a, b, gridSize, crAngle):
    """定义适应度函数: 计算支撑体积"""
    sptLength = 0.0
    # 1. 旋转模型
    newModel = stlModel.rotated(a, b, 0)

    # 2. 计算模型支撑点 (不需要layers参数)
    fsr = FindSptRegion(newModel, None, gridSize, crAngle)
    gridDic = fsr.calcModelSptPoints()

    # 3. 累加支撑线段长度
    for key in gridDic:
        zas = gridDic[key]
        for i in range(0, len(zas), 2):
            if i + 1 <= len(zas) - 1:
                za0, za1 = zas[i], zas[i + 1]
                if za1[1] < crAngle:
                    sptLength += (za1[0] - za0[0])

    # 4. 体积 = 总长度 * 网格面积
    return sptLength * fsr.ax * fsr.ay


amax = 2 * math.pi


class Particle:
    """粒子类"""

    def __init__(self, a=None, b=None, f=None):
        self.a = uniform(0, amax) if a is None else a
        self.b = uniform(0, amax) if b is None else b
        self.f = float('inf') if f is None else f

    def clone(self):
        return Particle(self.a, self.b, self.f)

    def fitness(self, stlModel, gridSize, crAngle):
        val = fitness(stlModel, self.a, self.b, gridSize, crAngle)
        self.f = val

    def evolve(self, LP, GP, wL, wG):
        r1, r2, r3 = random(), random(), random()
        sum_w = r1 + wL * r2 + wG * r3
        p = r1 / sum_w
        q = wL * r2 / sum_w
        r = wG * r3 / sum_w

        self.a = p * self.a + q * LP.a + r * GP.a
        self.b = p * self.b + q * LP.b + r * GP.b

    def vary(self, prob, LP, GP):
        if random() < prob:
            a = uniform(0, amax)
            if a < min(self.a, LP.a, GP.a) or a > max(self.a, LP.a, GP.a):
                self.b = uniform(0, amax)
            else:
                if random() < 0.5:
                    self.b = uniform(0, min(self.b, LP.b, GP.b))
                else:
                    self.b = uniform(max(self.b, LP.b, GP.b), amax)
            self.a = a


def pso(stlModel, gridSize, crAngle, popu, iter_num, prob, wL, wG):
    """粒子群优化函数"""
    P, LP = [], []
    GP = Particle()

    # 步骤 1: 初始化
    for i in range(popu):
        p = Particle()
        P.append(p)
        LP.append(p.clone())

    for k in range(iter_num):
        print(f"迭代 {k + 1}/{iter_num}, 当前最优支撑体积: {GP.f:.2f}")

        # 步骤 2: 计算适应度
        for i in range(popu):
            P[i].fitness(stlModel, gridSize, crAngle)

        # 步骤 3 & 4: 更新极值
        for i in range(popu):
            if P[i].f < LP[i].f:
                LP[i] = P[i].clone()
            if P[i].f < GP.f:
                GP = P[i].clone()

        # 步骤 5: 变异和进化
        for i in range(popu):
            P[i].vary(prob, LP[i], GP)
            P[i].evolve(LP[i], GP, wL, wG)

        if GP.f < 1.0:
            print("找到近似零支撑解，提前结束。")
            break

    return GP


if __name__ == '__main__':
    from StlModel import StlModel
    from SliceAlgo import intersectStl_sweep
    from FindSptRegion import findSptRegion
    from Utility import degToRad, radToDeg
    from VtkAdaptor import VtkAdaptor
    import vtk
    import time

    # 1. 设置模型路径
    stl_path = ".\\STL\\cube.stl"

    print(f"读取模型: {stl_path}")
    src = vtk.vtkSTLReader()
    src.SetFileName(stl_path)
    src.Update()

    stlModel = StlModel()
    if stlModel.extractFromVtkStlReader(src):
        print(f"模型读取成功，面片数: {stlModel.getFacetNumber()}")

        # 2. PSO 参数设置
        # gridSize: 设为 25.0mm
        # popu: 50 (种群数)
        # iter: 30 (迭代次数)
        grid_size = 25.0
        population = 50
        max_iter = 30

        print(f"开始PSO优化 | 网格: {grid_size}mm | 种群: {population} | 迭代: {max_iter}")

        start_time = time.time()

        # 运行 PSO
        best = pso(stlModel, grid_size, degToRad(60), population, max_iter, 0.01, 4, 4)

        end_time = time.time()
        print(f"优化完成! 总耗时: {end_time - start_time:.2f} 秒")
        print(f"最优角度 (度): X={radToDeg(best.a):.2f}, Y={radToDeg(best.b):.2f}, 体积={best.f:.2f}")