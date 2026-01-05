from StlModel import StlModel
from IntersectStl_match import IntersectStl_match
from SliceAlgo import linkSegs_brutal
import time
import os
import glob
import LinkPoint

try:
    from LinkSegs_dorder import LinkSegs_dorder
    from LinkSegs_dlook import LinkSegs_dlook


    # 创建对应的包装函数
    def linkSegs_dorder_local(segs):
        processor = LinkSegs_dorder(segs)
        return processor.contours


    def linkSegs_dlook_local(segs):
        processor = LinkSegs_dlook(segs)
        return processor.contours


    OPTIMIZED_ALGOS_AVAILABLE = True

except ImportError as e:
    print(f"警告: 无法导入优化算法类: {e}")
    OPTIMIZED_ALGOS_AVAILABLE = False


def diagnose_linkage_issues(segs, algorithm_name):
    """诊断链接问题"""
    print(f"\n=== {algorithm_name} 诊断 ===")

    # 统计点信息
    all_points = []
    for seg in segs:
        all_points.append(LinkPoint(seg.A))
        all_points.append(LinkPoint(seg.B))

    # 找出重复的点
    point_groups = {}
    for point in all_points:
        key = (round(point.x, 6), round(point.y, 6))
        if key not in point_groups:
            point_groups[key] = []
        point_groups[key].append(point)

    # 输出有多个点的位置
    multi_point_locations = {k: v for k, v in point_groups.items() if len(v) > 2}
    print(f"多重点位置数量: {len(multi_point_locations)}")

    for key, points in list(multi_point_locations.items())[:5]:  # 只显示前5个
        print(f"  位置 {key}: {len(points)} 个点")

    # 检查线段连接性
    connected_count = 0
    disconnected_count = 0

    for i, seg1 in enumerate(segs):
        connected = False
        for j, seg2 in enumerate(segs):
            if i != j:
                if (seg1.B.isCoincide(seg2.A) or seg1.B.isCoincide(seg2.B) or
                        seg1.A.isCoincide(seg2.A) or seg1.A.isCoincide(seg2.B)):
                    connected = True
                    break
        if connected:
            connected_count += 1
        else:
            disconnected_count += 1

    print(f"连接的线段: {connected_count}, 孤立的线段: {disconnected_count}")


def test_stl_model(stl_file_path, layer_thk=1.0):
    """测试单个STL模型的拼接算法性能"""
    print(f"\n{'=' * 60}")
    print(f"测试模型: {os.path.basename(stl_file_path)}")
    print(f"{'=' * 60}")

    if not os.path.exists(stl_file_path):
        print(f"错误: 文件不存在 - {stl_file_path}")
        return

    try:
        # 1. 读取STL模型
        print("1. 读取STL模型...")
        start_time = time.time()
        stl_model = StlModel()
        success = stl_model.readStlFile(stl_file_path)
        load_time = time.time() - start_time

        if not success:
            print(f"错误: 无法读取STL文件 - {stl_file_path}")
            return

        xMin, xMax, yMin, yMax, zMin, zMax = stl_model.getBounds()
        print(f"模型边界: X({xMin:.2f}, {xMax:.2f}), Y({yMin:.2f}, {yMax:.2f}), Z({zMin:.2f}, {zMax:.2f})")
        print(f"面片数量: {len(stl_model.triangles)}")
        print(f"加载时间: {load_time:.2f}秒")

        # 2. 切片处理
        print("2. 进行切片处理...")
        start_time = time.time()
        intersect_processor = IntersectStl_match(stl_model, layer_thk)
        slice_time = time.time() - start_time
        print(f"切片层数: {len(intersect_processor.layers)}")
        print(f"切片时间: {slice_time:.2f}秒")

        # 3. 统计总线段数
        total_segments = 0
        for layer in intersect_processor.layers:
            total_segments += len(layer.segments)
        print(f"总截交线段数: {total_segments}")

        if total_segments == 0:
            print("警告: 没有截交线段，跳过拼接测试")
            return

        # 4. 选择一层进行详细测试（通常选择中间层）
        test_layer_index = len(intersect_processor.layers) // 2
        if test_layer_index >= len(intersect_processor.layers):
            test_layer_index = 0

        test_layer = intersect_processor.layers[test_layer_index]
        print(f"\n测试层: 第{test_layer_index}层 (高度: {test_layer.z:.2f}mm)")
        print(f"测试层线段数: {len(test_layer.segments)}")

        # 5. 测试三种拼接算法
        print("\n3. 测试拼接算法性能:")
        print("-" * 40)

        # 字典序排序法
        dorder_time = float('inf')
        if OPTIMIZED_ALGOS_AVAILABLE:
            print("字典序排序法测试...")
            start_time = time.time()
            try:
                contours_dorder = linkSegs_dorder_local(test_layer.segments)
                dorder_time = time.time() - start_time
                print(f"✓ 字典序排序法: {dorder_time:.3f}秒, 轮廓数: {len(contours_dorder)}")
            except Exception as e:
                print(f"✗ 字典序排序法失败: {e}")
        else:
            print("跳过字典序排序法 (未找到实现)")

        # 字典查询法
        dlook_time = float('inf')
        if OPTIMIZED_ALGOS_AVAILABLE:
            print("字典查询法测试...")
            start_time = time.time()
            try:
                contours_dlook = linkSegs_dlook_local(test_layer.segments)
                dlook_time = time.time() - start_time
                print(f"✓ 字典查询法: {dlook_time:.3f}秒, 轮廓数: {len(contours_dlook)}")
            except Exception as e:
                print(f"✗ 字典查询法失败: {e}")
        else:
            print("跳过字典查询法 (未找到实现)")

        # 暴力法（只在线段数较少时测试）
        brutal_time = float('inf')
        if len(test_layer.segments) <= 1000:  # 只在线段数较少时测试暴力法
            print("暴力法测试...")
            start_time = time.time()
            try:
                contours_brutal = linkSegs_brutal(test_layer.segments)
                brutal_time = time.time() - start_time
                print(f"✓ 暴力法: {brutal_time:.3f}秒, 轮廓数: {len(contours_brutal)}")
            except Exception as e:
                print(f"✗ 暴力法失败: {e}")
        else:
            print(f"跳过暴力法测试 (线段数 {len(test_layer.segments)} > 1000)")

        # 6. 性能比较
        print("\n4. 性能比较:")
        print("-" * 40)
        if dorder_time != float('inf') and dlook_time != float('inf') and dlook_time > 0:
            speedup = dorder_time / dlook_time
            print(f"字典查询法比字典序排序法快: {speedup:.2f}倍")

        if brutal_time != float('inf') and dlook_time != float('inf') and dlook_time > 0:
            speedup = brutal_time / dlook_time
            print(f"字典查询法比暴力法快: {speedup:.2f}倍")
        elif brutal_time != float('inf') and dorder_time != float('inf') and dorder_time > 0:
            speedup = brutal_time / dorder_time
            print(f"字典序排序法比暴力法快: {speedup:.2f}倍")

    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


def find_stl_files():
    """查找STL文件"""
    stl_dirs = [
        "./STL/",
    ]

    stl_files = []
    for directory in stl_dirs:
        if os.path.exists(directory):
            # 查找所有.stl文件
            pattern = os.path.join(directory, "*.stl")
            files = glob.glob(pattern)
            # 查找所有.STL文件（大写扩展名）
            pattern_upper = os.path.join(directory, "*.STL")
            files_upper = glob.glob(pattern_upper)

            stl_files.extend(files)
            stl_files.extend(files_upper)

    return stl_files


def test_all_models():
    """测试所有STL模型"""
    print("开始查找STL模型文件...")
    stl_files = find_stl_files()

    if not stl_files:
        print("未找到任何STL文件!")
        print("请确保STL文件位于以下目录:")
        print("./STL/")
        return

    print(f"找到 {len(stl_files)} 个STL文件:")
    for file in stl_files:
        print(f"  - {file}")

    if not OPTIMIZED_ALGOS_AVAILABLE:
        print("\n警告: 优化算法（字典序排序法和字典查询法）不可用")
        print("将只测试暴力法")

    print("\n开始测试拼接算法性能...")
    print("=" * 60)

    # 设置切片厚度
    layer_thickness = 1.0  # mm

    for stl_file in stl_files:
        test_stl_model(stl_file, layer_thickness)

    print("\n" + "=" * 60)
    print(f"所有模型测试完成! 共测试了 {len(stl_files)} 个模型")


if __name__ == "__main__":
    test_all_models()