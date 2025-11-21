# Generate_SLC_First.py
from SliceAlgo import *
from StlModel import StlModel
import os


def generate_slc_for_test():
    """为Test_genCpPath生成SLC文件"""

    # 使用小模型测试（cube.STL）
    stl_path = "D:/Projects/STL/cube.STL"
    layerThk = 1.0

    if not os.path.exists(stl_path):
        print(f"STL文件不存在: {stl_path}")
        return False

    print(f"读取STL文件: {stl_path}")
    stlModel = StlModel()

    if stlModel.readStlFile(stl_path):
        print(f"成功读取，面片数: {len(stlModel.triangles)}")

        bounds = stlModel.getBounds()
        print(f"模型边界: Z({bounds[4]:.1f}, {bounds[5]:.1f})")
        print(f"使用层厚: {layerThk}mm")

        # 使用扫描平面法切片
        from IntersectStl_sweep import IntersectStl_sweep
        slicer = IntersectStl_sweep(stlModel, layerThk)
        layers = slicer.layers

        print(f"生成 {len(layers)} 层")

        # 处理轮廓
        for layer in layers:
            if layer.segments:
                layer.contours = linkSegs_brutal(layer.segments)

        # 保存SLC文件到Test_genCpPath.py期望的路径
        output_path = "D:/monk_at_1.0mm.slc"
        success = writeSlcFile(layers, output_path)

        if success:
            print(f"SLC文件已生成: {output_path}")
            return True
        else:
            print("SLC文件保存失败")
            return False
    else:
        print("STL文件读取失败")
        return False


if __name__ == '__main__':
    generate_slc_for_test()