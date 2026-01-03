import pyclipper
from VtkAdaptor import *
from Polyline import *


def tuplesToPoly(tuples, offset_x=0, offset_y=0, z=0):
    """将元组序列转化为Polyline，支持偏移"""
    poly = Polyline()
    for pt in tuples:
        poly.addPoint(Point3D(pt[0] + offset_x, pt[1] + offset_y, z))
    if len(tuples) > 0:
        # 封闭轮廓
        poly.addPoint(Point3D(tuples[0][0] + offset_x, tuples[0][1] + offset_y, z))
    return poly


def draw_with_offset(vtkAdaptor, path, offset_x, offset_y, color, line_width=3):
    """绘制带偏移的轮廓"""
    poly = tuplesToPoly(path, offset_x, offset_y)
    actor = vtkAdaptor.drawPolyline(poly)
    actor.GetProperty().SetColor(color[0], color[1], color[2])
    actor.GetProperty().SetLineWidth(line_width)
    return actor


def test_clipper_operations():
    """测试Clipper库的布尔运算"""
    # 创建subject轮廓（正方形）
    subject = [(0, 0), (100, 0), (100, 70), (0, 70)]

    # 创建clip轮廓（长方形）
    clip = [(30, 50), (70, 50), (70, 100), (30, 100)]

    # 定义四种布尔运算
    operations = [
        (pyclipper.CT_INTERSECTION, "Intersection"),
        (pyclipper.CT_UNION, "Union"),
        (pyclipper.CT_DIFFERENCE, "Difference"),
        (pyclipper.CT_XOR, "Xor")
    ]

    # 定义每个运算的显示偏移量
    offsets = [
        (0, 0),  # 左上角：交集
        (150, 0),  # 右上角：并集
        (0, 120),  # 左下角：差集
        (150, 120)  # 右下角：异或
    ]

    # 定义颜色
    colors = [
        (1, 0, 0),  # 红色：交集
        (0, 1, 0),  # 绿色：并集
        (0, 0, 1),  # 蓝色：差集
        (1, 1, 0)  # 黄色：异或
    ]

    vtkAdaptor = VtkAdaptor()

    for i, ((op_type, op_name), (offset_x, offset_y)) in enumerate(zip(operations, offsets)):
        print(f"Processing {op_name} at offset ({offset_x}, {offset_y})")

        # 创建裁剪器并添加多边形
        clipper = pyclipper.Pyclipper()
        clipper.AddPath(subject, pyclipper.PT_SUBJECT, True)
        clipper.AddPath(clip, pyclipper.PT_CLIP, True)

        # 执行布尔运算
        solution = clipper.Execute(op_type)
        print(f"  {op_name}: {len(solution)} contours")

        # 绘制原始轮廓（带偏移）
        draw_with_offset(vtkAdaptor, subject, offset_x, offset_y, (0, 0, 0), 1)
        draw_with_offset(vtkAdaptor, clip, offset_x, offset_y, (0, 0, 0), 1)

        # 绘制布尔运算结果
        for path in solution:
            draw_with_offset(vtkAdaptor, path, offset_x, offset_y, colors[i])
    vtkAdaptor.display()


if __name__ == '__main__':
    test_clipper_operations()