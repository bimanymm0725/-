import os
import sys
import time
import math

# 添加当前目录到Python路径
sys.path.append('.')

try:
    from GeomBase import *
    from StlModel import StlModel
    from SliceAlgo import *
    from IntersectStl_sweep import IntersectStl_sweep
    from VtkAdaptor import VtkAdaptor
    import pyclipper
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖文件都在当前目录")
    sys.exit(1)


class ClipperAdaptor:
    """Clipper库适配器"""

    def __init__(self, digits=7):
        self.f = math.pow(10, digits)
        self.arcTolerance = 0.005

    def toPath(self, poly):
        """将Polyline转化为Path"""
        path = []
        for pt in poly.points:
            x_int = int(round(pt.x * self.f))
            y_int = int(round(pt.y * self.f))
            path.append((x_int, y_int))
        return path

    def toPaths(self, polys):
        """将Polyline列表转化为Path列表"""
        paths = []
        for poly in polys:
            paths.append(self.toPath(poly))
        return paths

    def toPoly(self, path, z=0, closed=True):
        """将Path转化为Polyline"""
        poly = Polyline()
        for pt in path:
            x = pt[0] / self.f
            y = pt[1] / self.f
            poly.addPoint(Point3D(x, y, z))

        if len(path) > 0 and closed:
            first_pt = path[0]
            poly.addPoint(Point3D(first_pt[0] / self.f, first_pt[1] / self.f, z))

        return poly

    def toPolys(self, paths, z=0, closed=True):
        """将Path列表转化为Polyline列表"""
        polys = []
        for path in paths:
            polys.append(self.toPoly(path, z, closed))
        return polys

    def offset(self, polys, delta, jt=pyclipper.JT_SQUARE):
        """偏置函数"""
        if not polys:
            return []

        pco = pyclipper.PyclipperOffset()
        pco.ArcTolerance = self.arcTolerance * self.f

        paths = self.toPaths(polys)
        for path in paths:
            pco.AddPath(path, jt, pyclipper.ET_CLOSEDPOLYGON)

        solution = pco.Execute(delta * self.f)

        if not solution:
            return []

        z_coord = polys[0].point(0).z if polys[0].count() > 0 else 0
        return self.toPolys(solution, z_coord, True)


def generate_slc_file():
    """生成SLC测试文件"""
    print("=== 生成SLC测试文件 ===")

    # 使用cube.STL进行测试
    stl_paths = [
        "D:/Projects/STL/cube.STL",
        "D:/Projects/STL/cube.stl",
        "./cube.STL"
    ]

    stl_path = None
    for path in stl_paths:
        if os.path.exists(path):
            stl_path = path
            break

    if not stl_path:
        print("未找到STL文件，创建测试立方体...")
        # 创建简单的测试立方体
        stlModel = StlModel()
        vertices = [
            Point3D(0, 0, 0), Point3D(50, 0, 0), Point3D(50, 50, 0), Point3D(0, 50, 0),
            Point3D(0, 0, 30), Point3D(50, 0, 30), Point3D(50, 50, 30), Point3D(0, 50, 30)
        ]

        # 创建立方体的三角形面
        triangles = [
            (0, 1, 2), (0, 2, 3),  # 底面
            (4, 5, 6), (4, 6, 7),  # 顶面
            (0, 1, 5), (0, 5, 4),  # 前面
            (2, 3, 7), (2, 7, 6),  # 后面
            (0, 3, 7), (0, 7, 4),  # 左面
            (1, 2, 6), (1, 6, 5)  # 右面
        ]

        for tri in triangles:
            stlModel.triangles.append(Triangle(vertices[tri[0]], vertices[tri[1]], vertices[tri[2]]))
    else:
        print(f"读取STL文件: {stl_path}")
        stlModel = StlModel()
        if not stlModel.readStlFile(stl_path):
            print("STL文件读取失败")
            return None

    print(f"模型面片数: {len(stlModel.triangles)}")

    # 切片参数
    layerThk = 5.0  # 使用较大的层厚减少层数

    # 使用扫描平面法切片
    print("开始切片...")
    slicer = IntersectStl_sweep(stlModel, layerThk)
    layers = slicer.layers
    print(f"生成 {len(layers)} 层切片")

    # 处理轮廓（跳过复杂的方向调整）
    for layer in layers:
        if layer.segments:
            layer.contours = linkSegs_brutal(layer.segments)

    # 保存SLC文件
    output_path = "./test_model.slc"
    if writeSlcFile(layers, output_path):
        print(f"SLC文件已保存: {output_path}")
        return output_path
    else:
        print("SLC文件保存失败")
        return None


def generate_contour_paths(layers, interval=2.0, shell_thk=8.0):
    """生成轮廓平行填充路径"""
    print("=== 生成轮廓平行填充路径 ===")
    print(f"参数: 路径间距={interval}mm, 外壳厚度={shell_thk}mm")

    ca = ClipperAdaptor()
    all_paths = []

    # 只处理前3层以节省时间
    max_layers = min(3, len(layers))

    for layer_idx in range(max_layers):
        layer = layers[layer_idx]
        print(f"处理第 {layer_idx + 1} 层，轮廓数: {len(layer.contours)}")

        if not layer.contours:
            print("  该层没有轮廓，跳过")
            all_paths.append([])
            continue

        layer_paths = []
        current_distance = interval / 2  # 首次偏置距离

        # 生成多层偏置路径
        while abs(current_distance) <= shell_thk:
            try:
                offset_polys = ca.offset(layer.contours, -current_distance, pyclipper.JT_SQUARE)

                if offset_polys:
                    layer_paths.extend(offset_polys)
                    print(f"  偏置距离 {current_distance:.1f}: 生成 {len(offset_polys)} 条路径")
                else:
                    break  # 没有更多偏置路径，停止

            except Exception as e:
                print(f"  偏置距离 {current_distance:.1f} 时出错: {e}")
                break

            current_distance += interval

        all_paths.append(layer_paths)
        print(f"  该层总共生成 {len(layer_paths)} 条路径")

    return all_paths


def visualize_results(layers, contour_paths):
    """可视化显示结果"""
    print("=== 可视化显示 ===")

    try:
        va = VtkAdaptor()

        # 显示原始轮廓（黑色）
        for layer_idx, layer in enumerate(layers):
            if layer_idx >= len(contour_paths):
                break

            for contour in layer.contours:
                # 每层在Z方向偏移以便观察
                offset_contour = contour.clone()
                offset_contour.translate(Vector3D(0, 0, layer_idx * 20))
                actor = va.drawPolyline(offset_contour)
                actor.GetProperty().SetColor(0, 0, 0)
                actor.GetProperty().SetLineWidth(2)

        # 显示生成的路径（彩色）
        colors = [
            (1, 0, 0),  # 红色
            (0, 1, 0),  # 绿色
            (0, 0, 1),  # 蓝色
            (1, 1, 0),  # 黄色
            (1, 0, 1),  # 紫色
        ]

        for layer_idx, paths in enumerate(contour_paths):
            for path_idx, path in enumerate(paths):
                # 同样的Z偏移
                offset_path = path.clone()
                offset_path.translate(Vector3D(0, 0, layer_idx * 20))

                # 使用渐变色
                color_idx = path_idx % len(colors)
                color = colors[color_idx]

                actor = va.drawPolyline(offset_path)
                actor.GetProperty().SetColor(color[0], color[1], color[2])
                actor.GetProperty().SetLineWidth(1)

        print("显示可视化窗口...")
        print("提示: 在窗口中可以:")
        print("  - 鼠标左键拖拽旋转视图")
        print("  - 鼠标右键拖拽平移视图")
        print("  - 鼠标滚轮缩放")
        print("  - 按'q'键退出")

        va.display()

    except Exception as e:
        print(f"可视化失败: {e}")


def main():
    """主函数"""
    print("轮廓平行填充路径生成测试")
    print("=" * 50)

    # 步骤1: 检查或生成SLC文件
    slc_file = "./test_model.slc"
    if not os.path.exists(slc_file):
        print("未找到SLC文件，开始生成...")
        slc_file = generate_slc_file()
        if not slc_file:
            print("SLC文件生成失败，程序退出")
            return

    # 步骤2: 读取SLC文件
    print(f"\n读取SLC文件: {slc_file}")
    layers = readSlcFile(slc_file)
    if not layers:
        print("SLC文件读取失败")
        return

    print(f"成功读取 {len(layers)} 层")

    # 步骤3: 生成轮廓路径
    start_time = time.time()
    contour_paths = generate_contour_paths(layers)
    end_time = time.time()

    total_paths = sum(len(paths) for paths in contour_paths)
    print(f"\n路径生成完成，总共 {total_paths} 条路径")
    print(f"生成时间: {end_time - start_time:.2f} 秒")

    # 步骤4: 可视化显示
    visualize_results(layers, contour_paths)

    print("\n测试完成!")


if __name__ == '__main__':
    main()