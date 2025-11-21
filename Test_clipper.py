import pyclipper
from VtkAdaptor import *
from Polyline import *


def tuplesToPoly(tuples, z=0):
    """将元组序列转化为Polyline"""
    poly = Polyline()
    for pt in tuples:
        poly.addPoint(Point3D(pt[0], pt[1], z))
    if len(tuples) > 0:
        poly.addPoint(Point3D(tuples[0][0], tuples[0][1], z))  # 封闭轮廓
    return poly


def test_clipper_operations():
    """测试Clipper库的布尔运算"""
    # 创建subject轮廓（正方形）
    subject = [(0, 0), (100, 0), (100, 70), (0, 70)]

    # 创建clip轮廓（长方形）
    clip = [(30, 50), (70, 50), (70, 100), (30, 100)]

    # 测试四种布尔运算
    operations = [
        (pyclipper.CT_INTERSECTION, "Intersection"),
        (pyclipper.CT_UNION, "Union"),
        (pyclipper.CT_DIFFERENCE, "Difference"),
        (pyclipper.CT_XOR, "Xor")
    ]

    vtkAdaptor = VtkAdaptor()

    for i, (op_type, op_name) in enumerate(operations):
        clipper = pyclipper.Pyclipper()
        clipper.AddPath(subject, pyclipper.PT_SUBJECT, True)
        clipper.AddPath(clip, pyclipper.PT_CLIP, True)

        solution = clipper.Execute(op_type)

        print(f"{op_name}: {len(solution)} contours")

        # 可视化显示
        color = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0)][i]
        for path in solution:
            poly = tuplesToPoly(path)
            actor = vtkAdaptor.drawPolyline(poly)
            actor.GetProperty().SetColor(color[0], color[1], color[2])
            actor.GetProperty().SetLineWidth(3)

    # 显示原始轮廓
    subject_poly = tuplesToPoly(subject)
    clip_poly = tuplesToPoly(clip)

    vtkAdaptor.drawPolyline(subject_poly).GetProperty().SetColor(0, 0, 0)
    vtkAdaptor.drawPolyline(clip_poly).GetProperty().SetColor(0, 0, 0)

    vtkAdaptor.display()


if __name__ == '__main__':
    test_clipper_operations()