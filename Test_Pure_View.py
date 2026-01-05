import sys
import vtk

sys.path.append('.')
try:
    from SliceAlgo import readSlcFile
    from VtkAdaptor import VtkAdaptor
except ImportError as e:
    print(f"环境错误: {e}")
    sys.exit(1)


def view_slc_only(filename):
    print("=" * 60)
    print("SLC 查看器")
    print("=" * 60)

    # 读取文件
    print(f"正在读取: {filename}")
    layers = readSlcFile(filename)

    if not layers:
        print("错误：文件为空或读取失败。")
        return

    print(f"成功读取 {len(layers)} 层。")
    print("正在渲染...")

    # 启动 VTK
    va = VtkAdaptor()
    va.setBackgroundColor(1.0, 1.0, 1.0)  # 白色背景

    # 只绘制读取到的内容
    for layer in layers:
        for poly in layer.contours:
            # 绘制外轮廓 (蓝色)
            act = va.drawPolyline(poly)
            act.GetProperty().SetColor(0, 0, 1)
            act.GetProperty().SetLineWidth(1)

    print("窗口已打开。")
    va.display()


if __name__ == "__main__":
    view_slc_only("./STL/monk_at_1.0mm.slc")