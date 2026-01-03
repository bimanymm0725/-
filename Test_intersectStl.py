import time
import os
from SliceAlgo import *
from StlModel import *


def comprehensive_test():
    """全面测试所有STL文件"""
    stl_folder = "./STL"

    # 获取所有STL文件
    stl_files = []
    for file in os.listdir(stl_folder):
        if file.lower().endswith('.stl'):
            stl_files.append(os.path.join(stl_folder, file))

    if not stl_files:
        print("在指定文件夹中未找到STL文件！")
        return

    print(f"找到 {len(stl_files)} 个STL文件")

    # 按文件大小排序
    stl_files.sort(key=lambda x: os.path.getsize(x))

    # 测试不同层厚
    layerThks = [2.0, 1.0, 0.5]

    results = []

    for stl_file in stl_files:
        file_basename = os.path.basename(stl_file)
        file_size = os.path.getsize(stl_file) / 1024  # KB

        print(f"\n{'=' * 80}")
        print(f"测试文件: {file_basename} ({file_size:.0f} KB)")
        print(f"{'=' * 80}")

        stlModel = StlModel()
        if stlModel.readStlFile(stl_file):
            facet_count = stlModel.getFacetNumber()
            bounds = stlModel.getBounds()
            height = bounds[5] - bounds[4]

            file_result = {
                'filename': file_basename,
                'file_size_kb': file_size,
                'facet_count': facet_count,
                'height': height,
                'layer_results': []
            }

            print(f"面片数量: {facet_count}, 模型高度: {height:.2f}mm")

            for layerThk in layerThks:
                expected_layers = max(1, int(height / layerThk))
                print(f"\n--- 层厚: {layerThk}mm (预计{expected_layers}层) ---")

                layer_result = {
                    'layer_thk': layerThk,
                    'expected_layers': expected_layers
                }

                try:
                    # 扫描平面法
                    start = time.time()
                    layers1 = intersectStl_sweep(stlModel, layerThk)
                    sweep_time = time.time() - start
                    actual_layers1 = len(layers1)
                    print(f"  扫描平面法: {sweep_time:.3f}秒, 实际层数: {actual_layers1}")
                    layer_result['sweep_time'] = sweep_time
                    layer_result['sweep_layers'] = actual_layers1

                    # 层高匹配法
                    start = time.time()
                    layers2 = intersectStl_match(stlModel, layerThk)
                    match_time = time.time() - start
                    actual_layers2 = len(layers2)
                    print(f"  层高匹配法: {match_time:.3f}秒, 实际层数: {actual_layers2}")
                    layer_result['match_time'] = match_time
                    layer_result['match_layers'] = actual_layers2

                    # 暴力法（只对小文件运行）
                    run_brutal = (facet_count <= 100 and file_size < 100)
                    if run_brutal:
                        start = time.time()
                        layers3 = intersectStl_brutal(stlModel, layerThk)
                        brutal_time = time.time() - start
                        actual_layers3 = len(layers3)
                        print(f"  暴力法: {brutal_time:.3f}秒, 实际层数: {actual_layers3}")
                        layer_result['brutal_time'] = brutal_time
                        layer_result['brutal_layers'] = actual_layers3

                        # 计算加速比
                        if brutal_time > 0:
                            sweep_speedup = brutal_time / sweep_time if sweep_time > 0 else 0
                            match_speedup = brutal_time / match_time if match_time > 0 else 0
                            print(f"  扫描平面法加速比: {sweep_speedup:.2f}x")
                            print(f"  层高匹配法加速比: {match_speedup:.2f}x")
                            layer_result['sweep_speedup'] = sweep_speedup
                            layer_result['match_speedup'] = match_speedup
                    else:
                        print("  暴力法: 跳过（文件较大）")
                        layer_result['brutal_time'] = None

                except Exception as e:
                    print(f"  计算过程中出现错误: {e}")
                    continue

                file_result['layer_results'].append(layer_result)

            results.append(file_result)

            # 释放内存
            del stlModel

    # 生成详细报告
    print("\n" + "=" * 100)
    print("测试结果汇总报告")
    print("=" * 100)

    for result in results:
        print(f"\n模型: {result['filename']}")
        print(
            f"  文件大小: {result['file_size_kb']:.0f} KB, 面片数: {result['facet_count']}, 高度: {result['height']:.2f}mm")

        for layer_result in result['layer_results']:
            print(f"  层厚 {layer_result['layer_thk']}mm:")
            print(
                f"    扫描平面法: {layer_result.get('sweep_time', 'N/A'):.3f}s ({layer_result.get('sweep_layers', 'N/A')}层)")
            print(
                f"    层高匹配法: {layer_result.get('match_time', 'N/A'):.3f}s ({layer_result.get('match_layers', 'N/A')}层)")
            if layer_result.get('brutal_time'):
                print(f"    暴力法: {layer_result['brutal_time']:.3f}s ({layer_result.get('brutal_layers', 'N/A')}层)")
                print(f"    扫描平面法加速比: {layer_result.get('sweep_speedup', 'N/A'):.2f}x")
                print(f"    层高匹配法加速比: {layer_result.get('match_speedup', 'N/A'):.2f}x")


def performance_analysis():
    """性能分析：比较不同算法在不同规模模型上的表现"""
    stl_folder = "./STL"

    # 选择代表性的测试文件
    test_files = [
        "cube.STL",  # 小模型
        "cylinder.STL",  # 中小模型
        "3DP.STL",  # 中等模型
        "bunny.stl"  # 大模型（如果存在）
    ]

    layerThk = 1.0  # 固定层厚

    print("性能分析报告")
    print("=" * 50)

    for filename in test_files:
        stl_file = os.path.join(stl_folder, filename)
        if not os.path.exists(stl_file):
            print(f"文件不存在: {filename}")
            continue

        print(f"\n分析文件: {filename}")
        print("-" * 30)

        stlModel = StlModel()
        if stlModel.readStlFile(stl_file):
            facet_count = stlModel.getFacetNumber()
            bounds = stlModel.getBounds()
            height = bounds[5] - bounds[4]

            print(f"面片数: {facet_count}, 高度: {height:.2f}mm")

            # 测试三种算法
            times = {}

            # 扫描平面法
            start = time.time()
            layers1 = intersectStl_sweep(stlModel, layerThk)
            times['sweep'] = time.time() - start

            # 层高匹配法
            start = time.time()
            layers2 = intersectStl_match(stlModel, layerThk)
            times['match'] = time.time() - start

            # 暴力法（只对小模型）
            if facet_count <= 1000:
                start = time.time()
                layers3 = intersectStl_brutal(stlModel, layerThk)
                times['brutal'] = time.time() - start
            else:
                times['brutal'] = None

            # 输出结果
            print(f"扫描平面法: {times['sweep']:.3f}s ({len(layers1)}层)")
            print(f"层高匹配法: {times['match']:.3f}s ({len(layers2)}层)")

            if times['brutal']:
                print(f"暴力法: {times['brutal']:.3f}s ({len(layers3)}层)")
                # 计算加速比
                if times['brutal'] > 0:
                    sweep_speedup = times['brutal'] / times['sweep']
                    match_speedup = times['brutal'] / times['match']
                    print(f"扫描平面法加速比: {sweep_speedup:.2f}x")
                    print(f"层高匹配法加速比: {match_speedup:.2f}x")

            del stlModel


if __name__ == "__main__":
    # 运行全面测试
    comprehensive_test()

    # 运行性能分析
    performance_analysis()