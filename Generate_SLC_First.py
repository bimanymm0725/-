# Generate_SLC_First.py
from SliceAlgo import *
from StlModel import StlModel
from IntersectStl_sweep import IntersectStl_sweep
import os
import time


def generate_multiple_slc():
    """
    读取monk.stl并生成不同层厚的SLC文件
    层厚: 0.2mm, 0.5mm, 1.0mm, 2.0mm
    """

    # 配置路径
    stl_dir = "./STL"
    stl_filename = "monk.stl"
    stl_path = os.path.join(stl_dir, stl_filename)

    # 需要生成的层厚列表
    layer_thicknesses = [0.2, 0.5, 1.0, 2.0]

    # 1. 检查文件是否存在
    if not os.path.exists(stl_path):
        print(f"错误: STL文件不存在: {stl_path}")
        return

    # 2. 读取STL模型 (只读取一次)
    print(f"正在读取STL文件: {stl_path} ...")
    start_load = time.time()
    stlModel = StlModel()

    if not stlModel.readStlFile(stl_path):
        print("STL文件读取失败")
        return

    print(f"读取成功! 面片数: {len(stlModel.triangles)}")
    print(f"加载耗时: {time.time() - start_load:.2f} 秒")

    bounds = stlModel.getBounds()
    print(f"模型高度范围: Z({bounds[4]:.2f}, {bounds[5]:.2f})")
    print("=" * 50)

    # 3. 循环处理不同的层厚
    for thk in layer_thicknesses:
        print(f"\n开始处理层厚: {thk} mm")
        step_start = time.time()

        # A. 切片 (使用扫描平面法)
        print("  1. 正在切片(扫描平面法)...")
        # 计时切片
        t1 = time.time()
        slicer = IntersectStl_sweep(stlModel, thk)
        layers = slicer.layers
        t2 = time.time()
        print(f"     生成层数: {len(layers)} (耗时: {t2 - t1:.2f}s)")

        # B. 轮廓拼接 (优化点)
        print("  2. 正在拼接轮廓(优化算法: linkSegs_dlook)...")
        contour_count = 0
        t3 = time.time()

        for layer in layers:
            if layer.segments:
                layer.contours = linkSegs_dlook(layer.segments)
                contour_count += len(layer.contours)

        t4 = time.time()
        print(f"     总轮廓数: {contour_count} (耗时: {t4 - t3:.2f}s)")

        # C. 保存SLC文件
        output_filename = f"monk_at_{thk}mm.slc"
        output_path = os.path.join(stl_dir, output_filename)

        print(f"  3. 保存文件: {output_path}")
        if writeSlcFile(layers, output_path):
            print(f"     [成功] 文件已保存")
        else:
            print(f"     [失败] 文件保存出错")

        print(f"  当前层厚总耗时: {time.time() - step_start:.2f} 秒")
        print("-" * 50)

    print("\n所有任务完成!")


if __name__ == '__main__':
    generate_multiple_slc()