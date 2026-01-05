import math
from enum import Enum
from GeomBase import Point3D
from FindSptRegion import findSptRegion
from GenDpPath import genDpPathEx


class SptFillType(Enum):
    line = 1
    cross = 2


def genSptPath(stlModel, layers, pathInvl, gridSize, crAngle, fillType, fillAngle=0, xyGap=1):
    # 1. 生成支撑区域
    print("正在计算支撑区域...")
    findSptRegion(stlModel, layers, gridSize, crAngle, xyGap)

    # 2. 计算全局 ys 和 center
    xMin, xMax, yMin, yMax, zMin, zMax = stlModel.getBounds()
    center = Point3D((xMin + xMax) / 2, (yMin + yMax) / 2, 0)  # 旋转中心 Z 可以是 0
    corner = Point3D(xMax, yMax, 0)
    radius = center.distance(corner)

    ys = []
    # 扩大一点范围，确保覆盖旋转后的模型
    y = center.y - radius * 1.5
    end_y = center.y + radius * 1.5
    while y <= end_y:
        ys.append(y)
        y += pathInvl

    print(f"正在生成支撑路径 (Total layers: {len(layers)})...")
    # 3. 遍历每层
    for i, layer in enumerate(layers):
        # 确保清空旧数据
        layer.sptDpPaths = []
        layer.sptCpPaths = []

        if not hasattr(layer, 'sptContours') or not layer.sptContours:
            continue

        angle = fillAngle
        if fillType == SptFillType.cross and i % 2 == 1:
            angle = fillAngle + math.pi / 2

        # 生成路径
        # 这里传入的 ys 是全局统一的，保证了上下层路径对齐
        layer.sptDpPaths = genDpPathEx(layer.sptContours, pathInvl, angle, ys, center)
        layer.sptCpPaths = layer.sptContours


if __name__ == '__main__':
    from StlModel import StlModel
    from SliceAlgo import intersectStl_sweep, readSlcFile
    from VtkAdaptor import VtkAdaptor
    from Utility import degToRad
    import vtk

    print("正在处理...")
    src, stlModel = vtk.vtkSTLReader(), StlModel()
    src.SetFileName("D:\\Projects\\STL\\monk.stl")
    stlModel.extractFromVtkStlReader(src)

    layers = readSlcFile ("D:\\Projects\\STL\\monk_at_2.0mm.slc")

    genSptPath(stlModel, layers, 2, 2, degToRad(60), SptFillType.line)

    va = VtkAdaptor()
    va.drawPdSrc(src).GetProperty().SetOpacity(0.1)

    for layer in layers:
        if hasattr(layer, 'sptDpPaths'):
            for poly in layer.sptDpPaths:
                if poly: va.drawPolyline(poly).GetProperty().SetColor(1, 0, 0)
        if hasattr(layer, 'sptCpPaths'):
            for poly in layer.sptCpPaths:
                if poly: va.drawPolyline(poly).GetProperty().SetColor(0, 0, 1)

    va.display()