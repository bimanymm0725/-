import os
import vtk
import time
import math
from StlModel import StlModel
from SliceAlgo import intersectStl_sweep, linkSegs_dlook
from GenSptPath import genSptPath, SptFillType
from Utility import degToRad
from VtkAdaptor import VtkAdaptor
from GeomBase import *
from Segment import Segment
# 导入 GeomAlgo 是为了使用它的全局 distance 函数
import GeomAlgo


def fixed_pointInPolygon(p, polygon):
    """
    判断点与多边形的位置关系 (本地修复版)
    修复了“cannot normalize zero vector”报错问题
    返回: -1:边界, 1:内部, 0:外部
    """
    n = polygon.count()
    # 1. 检查点是否在多边形边界上
    for i in range(n):
        A = polygon.point(i)
        B = polygon.point((i + 1) % n)

        # === 关键修复：如果线段两端点重合（长度为0），直接跳过 ===
        # 避免 Segment 计算方向时报错
        if A.distance(B) < epsilon:
            continue

        seg = Segment(A, B)

        # 调用 GeomAlgo.distance 全局函数
        if GeomAlgo.distance(p, seg) < epsilon:
            return -1

    # 2. 射线法判断内外
    count = 0
    for i in range(n):
        A = polygon.point(i)
        B = polygon.point((i + 1) % n)

        # 同样忽略重合的边，虽然后面的逻辑也能处理，但跳过更安全
        if A.distance(B) < epsilon:
            continue

        if (A.y > p.y and B.y > p.y) or (A.y < p.y and B.y < p.y):
            continue

        if abs(A.y - p.y) < epsilon and abs(B.y - p.y) < epsilon:
            if (A.x <= p.x <= B.x) or (B.x <= p.x <= A.x):
                return -1
            continue

        if abs(B.y - A.y) > epsilon:
            x_intersect = A.x + (p.y - A.y) * (B.x - A.x) / (B.y - A.y)
            if x_intersect > p.x:
                # 排除顶点重合的特殊情况
                if not (abs(A.y - p.y) < epsilon and A.x > p.x) and \
                        not (abs(B.y - p.y) < epsilon and B.x > p.x):
                    count += 1

    if count % 2 == 1:
        return 1
    else:
        return 0


def fixed_adjustPolygonDirs(polygons):
    """
    调整多边形方向 (本地修复版)
    """
    for i in range(len(polygons)):
        pt = polygons[i].startPoint()  # 取轮廓起点作为测试点
        insideCount = 0

        for j in range(len(polygons)):
            if j == i: continue
            restPoly = polygons[j]
            # 调用修复后的函数
            if fixed_pointInPolygon(pt, restPoly) == 1:
                insideCount += 1

        # 偶数层(0, 2...)是外轮廓->逆时针，奇数层(1, 3...)是内孔->顺时针
        if insideCount % 2 == 0:
            polygons[i].makeCCW()
        else:
            polygons[i].makeCW()


# ==============================================================================


def test_bunny_cross():
    # === 1. 参数配置 ===
    stl_path = ".\\STL\\bunny.STL"
    if not os.path.exists(stl_path):
        stl_path = ".\\STL\\bunny.stl"
        if not os.path.exists(stl_path):
            print(f"错误: 找不到文件 {stl_path}")
            return

    layer_thk = 2.0
    spt_interval = 1.5
    grid_size = 2.0
    cr_angle = 60

    # === 2. 读取与切片 ===
    print(f"正在读取 {stl_path} ...")
    src = vtk.vtkSTLReader()
    src.SetFileName(stl_path)
    src.Update()

    stl_model = StlModel()
    stl_model.extractFromVtkStlReader(src)

    print(f"正在切片 (层厚 {layer_thk}mm)...")
    layers = intersectStl_sweep(stl_model, layer_thk)

    # === 3. 轮廓处理 (调用本地修复函数) ===
    print("正在拼接轮廓并调整方向...")
    t0 = time.time()
    for layer in layers:
        if layer.segments:
            # 1. 拼接
            layer.contours = linkSegs_dlook(layer.segments)
            # 2. 调整方向 (使用本地修复版，消除报错)
            fixed_adjustPolygonDirs(layer.contours)

    print(f"轮廓处理完成，耗时: {time.time() - t0:.2f}秒")

    # === 4. 生成支撑 ===
    print("正在生成支撑路径 (模式: Cross/交叉填充)...")
    genSptPath(stl_model, layers,
               pathInvl=spt_interval,
               gridSize=grid_size,
               crAngle=degToRad(cr_angle),
               fillType=SptFillType.cross,
               fillAngle=0,
               xyGap=0.5)

    # === 5. 可视化 ===
    print("正在构建可视化场景...")
    va = VtkAdaptor()
    va.setBackgroundColor(1.0, 1.0, 1.0)

    actor_model = va.drawPdSrc(src)
    actor_model.GetProperty().SetColor(0.8, 0.8, 0.8)
    actor_model.GetProperty().SetOpacity(0.15)

    has_support = False
    for i, layer in enumerate(layers):
        # 绘制模型轮廓
        for poly in layer.contours:
            act = va.drawPolyline(poly)
            act.GetProperty().SetColor(0, 0, 0)
            act.GetProperty().SetLineWidth(1)

        # 绘制支撑路径 (红绿交替)
        if hasattr(layer, 'sptDpPaths') and layer.sptDpPaths:
            has_support = True
            for poly in layer.sptDpPaths:
                act = va.drawPolyline(poly)
                act.GetProperty().SetLineWidth(1.5)
                if i % 2 == 0:
                    act.GetProperty().SetColor(1.0, 0.0, 0.0)
                else:
                    act.GetProperty().SetColor(0.0, 0.8, 0.0)

                    # 绘制支撑边界
        if hasattr(layer, 'sptContours'):
            for poly in layer.sptContours:
                act = va.drawPolyline(poly)
                act.GetProperty().SetColor(0, 0, 1)
                act.GetProperty().SetLineWidth(1)

    if not has_support:
        print("警告: 未生成支撑。")

    cam = va.renderer.GetActiveCamera()
    cam.ParallelProjectionOn()
    va.renderer.ResetCamera()
    cam.SetViewUp(0, 1, 0)

    fp = cam.GetFocalPoint()
    pos = cam.GetPosition()
    cam.SetPosition(fp[0], fp[1], pos[2])

    print("窗口已打开。")
    va.display()


if __name__ == '__main__':
    test_bunny_cross()