import os
import sys
import math

sys.path.append('.')

try:
    import GeomAlgo
    from Segment import Segment
    from StlModel import StlModel
    from HollowingAlgo import perform_hollowing
    from SliceAlgo import writeSlcFile
    import GeomAlgo
except ImportError as e:
    print(f"环境错误: {e}")
    sys.exit(1)


def fixed_pointInPolygon(p, polygon):
    n = polygon.count()
    # 1. 边界检查
    for i in range(n):
        A = polygon.point(i)
        B = polygon.point((i + 1) % n)
        if A.distance(B) < 1e-7: continue

        # 【关键修复】使用全局 distance 函数
        if GeomAlgo.distance(p, Segment(A, B)) < 1e-7:
            return -1

    # 2. 射线法
    count = 0
    for i in range(n):
        A = polygon.point(i)
        B = polygon.point((i + 1) % n)
        if A.distance(B) < 1e-7: continue

        if (A.y > p.y and B.y > p.y) or (A.y < p.y and B.y < p.y): continue
        if abs(A.y - p.y) < 1e-7 and abs(B.y - p.y) < 1e-7: continue

        if abs(B.y - A.y) > 1e-7:
            x_intersect = A.x + (p.y - A.y) * (B.x - A.x) / (B.y - A.y)
            if x_intersect > p.x:
                if not (abs(A.y - p.y) < 1e-7 and A.x > p.x) and \
                        not (abs(B.y - p.y) < 1e-7 and B.x > p.x):
                    count += 1
    return 1 if count % 2 == 1 else 0


GeomAlgo.pointInPolygon = fixed_pointInPolygon
try:
    import PolyPerSeeker

    PolyPerSeeker.pointInPolygon = fixed_pointInPolygon
    import SliceAlgo

    SliceAlgo.pointInPolygon = fixed_pointInPolygon
except:
    pass


def main():
    print("=" * 60)
    print(" 3D 均匀抽壳数据生成")
    print("=" * 60)

    # 1. 路径设置
    stl_path = "./STL/monk.stl"
    if not os.path.exists(stl_path):
        print(f"错误: 找不到 {stl_path}")
        return

    # 2. 读取模型
    print(f"读取模型: {stl_path}")
    stl_model = StlModel()
    if not stl_model.readStlFile(stl_path):
        print("读取失败")
        return

    # 3. 设置参数
    # 层厚 1.0mm, 壁厚 3.0mm
    LAYER_THK = 1.0
    WALL_THICKNESS = 3.0

    print(f"执行抽壳 (层厚:{LAYER_THK}mm, 壁厚:{WALL_THICKNESS}mm)...")

    # 4. 核心计算
    hollowed_layers = perform_hollowing(stl_model, LAYER_THK, WALL_THICKNESS)

    # 5. 保存结果
    out_slc = f"./STL/monk_hollow_result.slc"
    print(f"\n正在保存切片数据至: {out_slc}")

    if writeSlcFile(hollowed_layers, out_slc):
        print("[成功] 文件已生成！请运行可视化脚本查看。")
    else:
        print("[失败] 文件保存失败。")


if __name__ == "__main__":
    main()