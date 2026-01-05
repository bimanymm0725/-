import os
import vtk
import time
from StlModel import StlModel
from VtkAdaptor import VtkAdaptor


def test_stl_viewer():
    stl_filename = "monk.stl"
    stl_path = os.path.join(".", "STL", stl_filename)

    if not os.path.exists(stl_path):
        print(f"[错误] 无法找到文件: {stl_path}")
        print("请确保在当前代码目录下创建 'STL' 文件夹并将 'monk.stl' 放入其中。")
        return

    start_time = time.time()

    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_path)
    reader.Update()  # 触发读取

    stl_model = StlModel()
    success = stl_model.extractFromVtkStlReader(reader)

    load_time = time.time() - start_time

    if success:
        facet_count = stl_model.getFacetNumber()
        bounds = stl_model.getBounds()  # (xMin, xMax, yMin, yMax, zMin, zMax)

        print(f"模型统计信息:")
        print(f"  - 三角面片数量: {facet_count}")
        print(f"  - X 轴范围: {bounds[0]:.2f} ~ {bounds[1]:.2f} mm")
        print(f"  - Y 轴范围: {bounds[2]:.2f} ~ {bounds[3]:.2f} mm")
        print(f"  - Z 轴范围: {bounds[4]:.2f} ~ {bounds[5]:.2f} mm")
        print(f"  - 模型高度: {bounds[5] - bounds[4]:.2f} mm")

        va = VtkAdaptor(bgClr=(0.95, 0.95, 0.95))  # 浅灰色背景

        actor = va.drawPdSrc(reader)
        actor.GetProperty().SetColor(0.7, 0.7, 0.7)
        actor.GetProperty().SetOpacity(1.0)

        va.display()

    else:
        print("[失败] 无法解析 STL 模型数据。")


if __name__ == '__main__':
    test_stl_viewer()