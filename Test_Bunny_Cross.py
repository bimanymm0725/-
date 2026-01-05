import os
import vtk
import time
import math
import sys

sys.path.append('.')

try:
    from StlModel import StlModel
    from SliceAlgo import intersectStl_sweep
    from GenSptPath import genSptPath, SptFillType
    from Utility import degToRad
    from VtkAdaptor import VtkAdaptor
    from GeomBase import *
    from Segment import Segment
    from LinkSegs_dlook import LinkSegs_dlook
    from ClipperAdaptor import ClipperAdaptor
    import GeomAlgo
except ImportError as e:
    print(f"环境错误: {e}")
    sys.exit(1)


def fixed_pointInPolygon(p, polygon):
    n = polygon.count()
    for i in range(n):
        A = polygon.point(i)
        B = polygon.point((i + 1) % n)
        if A.distance(B) < 1e-7: continue
        if GeomAlgo.distance(p, Segment(A, B)) < 1e-7: return -1
    count = 0
    for i in range(n):
        A = polygon.point(i)
        B = polygon.point((i + 1) % n)
        if A.distance(B) < 1e-7: continue
        if (A.y > p.y and B.y > p.y) or (A.y < p.y and B.y < p.y): continue
        if abs(A.y - p.y) < 1e-7 and abs(B.y - p.y) < 1e-7: continue
        if abs(B.y - A.y) > 1e-7:
            x = A.x + (p.y - A.y) * (B.x - A.x) / (B.y - A.y)
            if x > p.x:
                if not (abs(A.y - p.y) < 1e-7 and A.x > p.x) and not (abs(B.y - p.y) < 1e-7 and B.x > p.x): count += 1
    return 1 if count % 2 == 1 else 0


GeomAlgo.pointInPolygon = fixed_pointInPolygon
try:
    import PolyPerSeeker;

    PolyPerSeeker.pointInPolygon = fixed_pointInPolygon
    import SliceAlgo;

    SliceAlgo.pointInPolygon = fixed_pointInPolygon
except:
    pass


def fixed_adjustPolygonDirs(polygons):
    for i in range(len(polygons)):
        pt = polygons[i].startPoint()
        insideCount = 0
        for j in range(len(polygons)):
            if j == i: continue
            if GeomAlgo.pointInPolygon(pt, polygons[j]) == 1:
                insideCount += 1
        if insideCount % 2 == 0:
            polygons[i].makeCCW()
        else:
            polygons[i].makeCW()


def test_bunny_cross():
    print("=" * 60)
    print(" Bunny支撑生成测试")
    print("=" * 60)

    # 1. 路径
    stl_path = "./STL/bunny.stl"
    if not os.path.exists(stl_path):
        print("未找到 bunny.stl")
        return

    # 2. 读取与切片
    src = vtk.vtkSTLReader()
    src.SetFileName(stl_path)
    src.Update()
    stl_model = StlModel()
    stl_model.extractFromVtkStlReader(src)

    LAYER_THK = 2.0
    layers = intersectStl_sweep(stl_model, LAYER_THK)

    # 3. 轮廓拼接
    t0 = time.time()

    ca = ClipperAdaptor()
    total_healed = 0

    for i, layer in enumerate(layers):
        if layer.segments:
            linker = LinkSegs_dlook(layer.segments)

            contours = linker.contours

            if linker.polys:
                for open_poly in linker.polys:
                    if open_poly.count() > 2:
                        open_poly.addPoint(open_poly.startPoint())
                        contours.append(open_poly)
                        total_healed += 1

            if contours:
                try:
                    layer.contours = ca.simplify_and_clean(contours, clean_dist=0.02)
                    fixed_adjustPolygonDirs(layer.contours)
                except:
                    layer.contours = contours
            else:
                layer.contours = []

    # 4. 生成支撑
    genSptPath(stl_model, layers,
               pathInvl=1.5,
               gridSize=2.0,
               crAngle=degToRad(60),
               fillType=SptFillType.cross,
               fillAngle=0,
               xyGap=0.5)

    # 5. 可视化
    va = VtkAdaptor()
    va.setBackgroundColor(1.0, 1.0, 1.0)

    # 模型 (灰)
    actor_model = va.drawPdSrc(src)
    actor_model.GetProperty().SetColor(0.8, 0.8, 0.8)
    actor_model.GetProperty().SetOpacity(0.15)

    has_spt = False
    for i, layer in enumerate(layers):
        z = layer.z
        # 轮廓 (黑)
        for poly in layer.contours:
            d = poly.clone()
            for p in d.points: p.z = z
            act = va.drawPolyline(d)
            act.GetProperty().SetColor(0, 0, 0)
            act.GetProperty().SetLineWidth(2)  # 加粗一点看得清楚

        # 支撑 (红/绿)
        if hasattr(layer, 'sptDpPaths') and layer.sptDpPaths:
            has_spt = True
            for poly in layer.sptDpPaths:
                d = poly.clone()
                for p in d.points: p.z = z
                act = va.drawPolyline(d)
                col = (1, 0, 0) if i % 2 == 0 else (0, 0.8, 0)
                act.GetProperty().SetColor(col)
                act.GetProperty().SetLineWidth(1)

        # 支撑边界 (蓝)
        if hasattr(layer, 'sptContours'):
            for poly in layer.sptContours:
                d = poly.clone()
                for p in d.points: p.z = z
                act = va.drawPolyline(d)
                act.GetProperty().SetColor(0, 0, 1)

    cam = va.renderer.GetActiveCamera()
    cam.ParallelProjectionOn()
    va.renderer.ResetCamera()
    cam.SetViewUp(0, 1, 0)

    va.display()


if __name__ == '__main__':
    test_bunny_cross()