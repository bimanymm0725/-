import vtk
import os
from StlModel import StlModel
from SliceAlgo import intersectStl_sweep
from FindSptRegion import findSptRegion
from Utility import degToRad, radToDeg
from VtkAdaptor import VtkAdaptor
from GeomBase import Point3D


def stl_to_vtk_actor(stl_model):
    points = vtk.vtkPoints()
    cells = vtk.vtkCellArray()

    # 遍历所有三角形，构建 VTK 数据
    for tri in stl_model.triangles:
        # 插入三个顶点
        id1 = points.InsertNextPoint(tri.A.x, tri.A.y, tri.A.z)
        id2 = points.InsertNextPoint(tri.B.x, tri.B.y, tri.B.z)
        id3 = points.InsertNextPoint(tri.C.x, tri.C.y, tri.C.z)

        # 构建三角形单元
        triangle = vtk.vtkTriangle()
        triangle.GetPointIds().SetId(0, id1)
        triangle.GetPointIds().SetId(1, id2)
        triangle.GetPointIds().SetId(2, id3)
        cells.InsertNextCell(triangle)

    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetPolys(cells)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly_data)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor


def show_perfect_match():
    # 1. 路径设置
    stl_path = ".\\STL\\man head.stl"

    print(f"读取原始模型: {stl_path}")
    src = vtk.vtkSTLReader()
    src.SetFileName(stl_path)
    src.Update()

    stlModel = StlModel()
    stlModel.extractFromVtkStlReader(src)

    # 2. 应用最优旋转角度
    best_x = 85.14
    best_y = 0
    print(f"应用最优角度: X={best_x}, Y={best_y}")

    # 在内存中生成旋转后的模型对象 optModel
    # 所有的计算（切片、支撑）都将基于这个对象
    optModel = stlModel.rotated(degToRad(best_x), degToRad(best_y), 0)

    # 3. 切片 (2.0mm)
    print("正在切片 (2.0mm)...")
    layers = intersectStl_sweep(optModel, 2.0)

    # 4. 生成支撑 (网格1.5mm)
    print("正在生成支撑 (网格1.5mm)...")
    findSptRegion(optModel, layers, 1.5, degToRad(60), 1.0)

    # 5. 可视化
    print("正在构建场景...")
    va = VtkAdaptor()
    va.setBackgroundColor(1, 1, 1)  # 白色背景

    print("转换模型用于显示...")
    actor_opt = stl_to_vtk_actor(optModel)
    actor_opt.GetProperty().SetColor(0.7, 0.7, 0.7)  # 灰色
    actor_opt.GetProperty().SetOpacity(0.3)  # 半透明
    va.drawActor(actor_opt)

    # 绘制结果
    print("绘制切片和支撑...")
    for i, layer in enumerate(layers):
        # 黑色：模型切片轮廓
        for poly in layer.contours:
            va.drawPolyline(poly).GetProperty().SetColor(0, 0, 0)

        # 蓝色：生成的支撑轮廓
        if hasattr(layer, 'sptContours'):
            for poly in layer.sptContours:
                act = va.drawPolyline(poly)
                act.GetProperty().SetColor(0, 0, 1)
                act.GetProperty().SetLineWidth(2)

    va.renderer.ResetCamera()

    va.display()


if __name__ == '__main__':
    show_perfect_match()