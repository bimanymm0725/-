import pyclipper
from VtkAdaptor import *
from Polyline import *


def test_clipper_offset():
    """测试Clipper库的轮廓偏置功能"""
    # 创建"回"字型轮廓
    outerPoly = [(0, 0), (100, 0), (100, 100), (0, 100)]  # 外轮廓，逆时针
    innerPoly = [(30, 30), (30, 70), (70, 70), (70, 30)]  # 内轮廓，顺时针

    # 测试三种衔接类型
    join_types = [
        (pyclipper.JT_ROUND, "Round"),
        (pyclipper.JT_SQUARE, "Square"),
        (pyclipper.JT_MITER, "Miter")
    ]

    vtkAdaptor = VtkAdaptor()

    # 显示原始轮廓
    outer_poly = Polyline()
    for pt in outerPoly:
        outer_poly.addPoint(Point3D(pt[0], pt[1], 0))
    outer_poly.addPoint(outer_poly.startPoint())

    inner_poly = Polyline()
    for pt in innerPoly:
        inner_poly.addPoint(Point3D(pt[0], pt[1], 0))
    inner_poly.addPoint(inner_poly.startPoint())

    vtkAdaptor.drawPolyline(outer_poly).GetProperty().SetColor(0, 0, 0)
    vtkAdaptor.drawPolyline(inner_poly).GetProperty().SetColor(0, 0, 0)

    # 测试不同衔接类型的偏置
    colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]  # 红、绿、蓝
    offsets = [-5, -10, -15]  # 向内偏置

    for i, (join_type, join_name) in enumerate(join_types):
        pco = pyclipper.PyclipperOffset()
        pco.AddPath(outerPoly, join_type, pyclipper.ET_CLOSEDPOLYGON)
        pco.AddPath(innerPoly, join_type, pyclipper.ET_CLOSEDPOLYGON)

        for j, offset_dist in enumerate(offsets):
            solution = pco.Execute(offset_dist)

            print(f"{join_name} offset {offset_dist}: {len(solution)} contours")

            color = colors[i]
            # 稍微调整颜色以区分不同偏置距离
            adjusted_color = (color[0] * (0.7 + 0.1 * j),
                              color[1] * (0.7 + 0.1 * j),
                              color[2] * (0.7 + 0.1 * j))

            for path in solution:
                poly = Polyline()
                for pt in path:
                    poly.addPoint(Point3D(pt[0], pt[1], 0))
                if len(path) > 0:
                    poly.addPoint(Point3D(path[0][0], path[0][1], 0))

                actor = vtkAdaptor.drawPolyline(poly)
                actor.GetProperty().SetColor(adjusted_color[0], adjusted_color[1], adjusted_color[2])
                actor.GetProperty().SetLineWidth(2)

    vtkAdaptor.display()


if __name__ == '__main__':
    test_clipper_offset()