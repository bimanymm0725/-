from SliceAlgo import *
from StlModel import StlModel
import os


def generate_test_slc_fixed():
    # 配置参数
    modelName = "monk"
    layerThk = 2.0

    stl_path = "./STL/monk.stl"

    if not os.path.exists(stl_path):
        print(f"STL文件不存在: {stl_path}")
        return

    print(f"读取STL文件: {stl_path}")
    stlModel = StlModel()

    # 读取STL文件
    if stlModel.readStlFile(stl_path):
        print(f"成功读取STL文件，面片数: {len(stlModel.triangles)}")

        # 获取模型边界信息
        bounds = stlModel.getBounds()
        print(
            f"模型边界: X({bounds[0]:.1f}, {bounds[1]:.1f}), Y({bounds[2]:.1f}, {bounds[3]:.1f}), Z({bounds[4]:.1f}, {bounds[5]:.1f})")

        # 使用扫描平面法进行切片
        try:
            print("开始切片处理...")
            from IntersectStl_sweep import IntersectStl_sweep
            slicer = IntersectStl_sweep(stlModel, layerThk)
            layers = slicer.layers

            print(f"切片完成，共 {len(layers)} 层")

            # 简化处理：只进行线段拼接，跳过方向调整
            print("处理轮廓...")
            for i, layer in enumerate(layers):
                if layer.segments:
                    print(f"处理第 {i + 1} 层，线段数: {len(layer.segments)}")
                    try:
                        # 只进行线段拼接
                        layer.contours = linkSegs_brutal(layer.segments)
                        print(f"  生成轮廓数: {len(layer.contours)}")
                    except Exception as e:
                        print(f"  第 {i + 1} 层轮廓处理失败: {e}")
                        layer.contours = []
                else:
                    layer.contours = []

            # 保存SLC文件
            output_path = f"D:/{modelName}_at_{layerThk}mm_fixed.slc"
            success = writeSlcFile(layers, output_path)

            if success:
                print(f"SLC文件已生成并保存: {output_path}")

                # 统计信息
                total_contours = 0
                valid_layers = 0
                for i, layer in enumerate(layers):
                    if layer.contours:
                        total_contours += len(layer.contours)
                        valid_layers += 1
                        print(f"层 {i + 1}: 高度={layer.z:.1f}, 轮廓数={len(layer.contours)}")

                print(f"有效层数: {valid_layers}/{len(layers)}")
                print(f"总轮廓数: {total_contours}")
            else:
                print("SLC文件保存失败")

        except Exception as e:
            print(f"切片过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("STL文件读取失败")


if __name__ == '__main__':
    generate_test_slc_fixed()