from VtkAdaptor import *
from GenHatch import *
from Polyline import *
from Utility import *
import vtk


def create_u_shape_poly(offset_x=0):
    """创建一个凹U形多边形，用于展示线段顺序差异"""
    poly = Polyline()
    # 逆时针定义
    points = [
        (0, 0), (100, 0), (100, 100), (70, 100),
        (70, 30), (30, 30), (30, 100), (0, 100)
    ]
    for x, y in points:
        poly.addPoint(Point3D(x + offset_x, y, 0))
    # 闭合
    poly.addPoint(Point3D(points[0][0] + offset_x, points[0][1], 0))
    return poly


def draw_labeled_segments(va, segs, color):
    """绘制线段并在起点处标记序号"""
    for i, seg in enumerate(segs):
        # 绘制线段
        actor = va.drawSegment(seg)
        actor.GetProperty().SetColor(color)
        actor.GetProperty().SetLineWidth(2)

        # 绘制序号文本
        textSrc = vtk.vtkVectorText()
        textSrc.SetText(f"{i}")
        textMapper = vtk.vtkPolyDataMapper()
        textMapper.SetInputConnection(textSrc.GetOutputPort())
        textActor = vtk.vtkFollower()  # 使用Follower使文字始终朝向相机
        textActor.SetMapper(textMapper)
        textActor.SetScale(4, 4, 4)  # 调整文字大小
        textActor.GetProperty().SetColor(0, 0, 0)  # 黑色文字

        # 设置位置 (稍微偏移一点以免遮挡)
        textActor.SetPosition(seg.A.x, seg.A.y, seg.A.z + 1)
        textActor.SetCamera(va.renderer.GetActiveCamera())

        va.renderer.AddActor(textActor)


def test_compare_hatch_distribution():
    va = VtkAdaptor()
    interval = 5.0
    angle = degToRad(0)  # 0度水平填充

    print("=== 对比测试开始 ===")

    # --- 左侧：Clipper 裁剪法 ---
    print("生成 Clipper 填充线 (红色)...")
    poly_clip = create_u_shape_poly(offset_x=-120)  # 向左偏移
    va.drawPolyline(poly_clip).GetProperty().SetColor(0, 0, 0)

    # 增加文本标签说明
    textL = vtk.vtkVectorText();
    textL.SetText("Clipper (Clip)")
    actL = va.drawPdSrc(textL);
    actL.SetPosition(-100, -20, 0);
    actL.SetScale(5)
    actL.GetProperty().SetColor(1, 0, 0)

    segs_clip = genClipHatches([poly_clip], interval, angle)
    draw_labeled_segments(va, segs_clip, (1, 0, 0))  # 红色

    # --- 右侧：扫描线法 ---
    print("生成 Sweep 填充线 (蓝色)...")
    poly_sweep = create_u_shape_poly(offset_x=20)  # 向右偏移
    va.drawPolyline(poly_sweep).GetProperty().SetColor(0, 0, 0)

    # 增加文本标签说明
    textR = vtk.vtkVectorText();
    textR.SetText("SweepLine (Scan)")
    actR = va.drawPdSrc(textR);
    actR.SetPosition(40, -20, 0);
    actR.SetScale(5)
    actR.GetProperty().SetColor(0, 0, 1)

    segs_sweep = genSweepHatches([poly_sweep], interval, angle)
    draw_labeled_segments(va, segs_sweep, (0, 0, 1))  # 蓝色

    print(f"Clipper 线段数: {len(segs_clip)}")
    print(f"Sweep   线段数: {len(segs_sweep)}")

    va.renderer.ResetCamera()
    va.display()


if __name__ == '__main__':
    test_compare_hatch_distribution()