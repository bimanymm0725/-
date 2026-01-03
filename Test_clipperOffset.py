import pyclipper
from VtkAdaptor import *
from Polyline import *


def draw_offset_polygon(vtkAdaptor, path, offset_x, offset_y, color, line_width=2, z=0):
    """绘制带偏移的多边形"""
    poly = Polyline()
    for pt in path:
        poly.addPoint(Point3D(pt[0] + offset_x, pt[1] + offset_y, z))
    if len(path) > 0:
        poly.addPoint(Point3D(path[0][0] + offset_x, path[0][1] + offset_y, z))  # 封闭轮廓

    actor = vtkAdaptor.drawPolyline(poly)
    actor.GetProperty().SetColor(color[0], color[1], color[2])
    actor.GetProperty().SetLineWidth(line_width)
    return actor


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

    # 定义三种衔接类型的显示偏移量
    # 每种类型在水平方向分开，垂直方向相同
    x_offsets = [0, 150, 300]  # 水平偏移量

    vtkAdaptor = VtkAdaptor()

    # 定义颜色和偏置距离
    colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]  # 红、绿、蓝
    offsets = [-5, -10, -15]  # 向内偏置

    # 为每种衔接类型绘制原始轮廓和偏置结果
    for i, (join_type, join_name) in enumerate(join_types):
        x_offset = x_offsets[i]

        # 绘制原始轮廓（带偏移）
        draw_offset_polygon(vtkAdaptor, outerPoly, x_offset, 0, (0, 0, 0), 1)
        draw_offset_polygon(vtkAdaptor, innerPoly, x_offset, 0, (0, 0, 0), 1)

        # 创建PyclipperOffset对象并添加路径
        pco = pyclipper.PyclipperOffset()
        pco.AddPath(outerPoly, join_type, pyclipper.ET_CLOSEDPOLYGON)
        pco.AddPath(innerPoly, join_type, pyclipper.ET_CLOSEDPOLYGON)

        # 测试不同偏置距离
        for j, offset_dist in enumerate(offsets):
            # 执行偏置操作
            solution = pco.Execute(offset_dist)
            # 为同一衔接类型的不同偏置距离使用相同颜色，但调整亮度
            base_color = colors[i]
            # 偏置距离越大（-15比-5更深），颜色越深
            brightness = 0.8 - 0.1 * j  # -5: 0.8, -10: 0.7, -15: 0.6
            adjusted_color = (base_color[0] * brightness,
                              base_color[1] * brightness,
                              base_color[2] * brightness)

            # 绘制偏置结果
            for path in solution:
                draw_offset_polygon(vtkAdaptor, path, x_offset, 0, adjusted_color, 2)

    print("  左侧：圆角连接 (JT_ROUND) - 红色")
    print("  中间：方角连接 (JT_SQUARE) - 绿色")
    print("  右侧：斜接连接 (JT_MITER) - 蓝色")

    vtkAdaptor.display()


if __name__ == '__main__':
    test_clipper_offset()