import os
import sys
import vtk

sys.path.append('.')

try:
    from SliceAlgo import readSlcFile
    from VtkAdaptor import VtkAdaptor
    from GeomBase import *
except ImportError as e:
    print(f"环境错误: {e}")
    sys.exit(1)


class HollowingViewer:
    def __init__(self, slc_path):
        self.slc_path = slc_path

        print(f"正在读取: {slc_path}")
        self.layers = readSlcFile(slc_path)
        if not self.layers:
            print("读取失败或文件为空")
            sys.exit(1)

        self.total = len(self.layers)

        self.va = VtkAdaptor()
        self.va.setBackgroundColor(1.0, 1.0, 1.0)  # 白色背景

        # 默认显示中间层
        self.idx = min(int(self.total * 0.4), self.total - 1)
        self.mode = "SINGLE"

        self.actors = []
        self._init_actors()

        self.va.interactor.AddObserver("KeyPressEvent", self.on_key)

        print("\n" + "=" * 60)
        print("【 抽壳效果透视查看 】")
        print("  蓝色线 = 外表面 (Outer Shell)")
        print("  红色线 = 内表面 (Inner Wall)")
        print("-" * 30)
        print("  [S] 单层切片模式")
        print("  [A] 3D 透视模式")
        print("  [↑/↓] 切换层级")
        print("=" * 60)

        # 初始化时强制刷新并重置相机
        self._update(reset_camera=True)
        self.va.display()

    def _init_actors(self):
        print("正在构建显示对象...")
        for i in range(self.total):
            layer = self.layers[i]
            z = layer.z
            group = []

            if layer.contours:
                for poly in layer.contours:
                    # 判断顺逆时针 (内孔/外壁)
                    is_inner = not poly.isCCW()

                    # 转换为VTK
                    pts = vtk.vtkPoints()
                    lines = vtk.vtkCellArray()
                    lines.InsertNextCell(poly.count() + 1)
                    for j in range(poly.count()):
                        p = poly.point(j)
                        pts.InsertNextPoint(p.x, p.y, z)  # 使用真实Z高度
                        lines.InsertCellPoint(j)
                    lines.InsertCellPoint(0)  # 闭合

                    pd = vtk.vtkPolyData()
                    pd.SetPoints(pts);
                    pd.SetLines(lines)
                    map = vtk.vtkPolyDataMapper()
                    map.SetInputData(pd)
                    act = vtk.vtkActor()
                    act.SetMapper(map)

                    if is_inner:
                        # 内壁 -> 红色，加粗
                        act.GetProperty().SetColor(1, 0, 0)
                        act.GetProperty().SetLineWidth(2)
                    else:
                        # 外壳 -> 蓝色
                        act.GetProperty().SetColor(0, 0, 1)
                        act.GetProperty().SetOpacity(0.5)
                        act.GetProperty().SetLineWidth(1)

                    act.SetVisibility(False)
                    self.va.renderer.AddActor(act)
                    group.append(act)

            self.actors.append(group)

    def on_key(self, obj, event):
        key = obj.GetKeySym()
        refresh = False
        reset_cam = False  # 标记是否需要重置相机

        if key in ["s", "S"]:
            self.mode = "SINGLE"
            refresh = True
            reset_cam = True  # 切换模式时重置相机
        elif key in ["a", "A"]:
            self.mode = "ALL"
            refresh = True
            reset_cam = True  # 切换模式时重置相机
        elif key == "Up" and self.idx < self.total - 1:
            self.idx += 1
            refresh = True
        elif key == "Down" and self.idx > 0:
            self.idx -= 1
            refresh = True
            # reset_cam = True

        if refresh:
            print(f"\r模式: {self.mode} | 层: {self.idx + 1}/{self.total}   ", end="")
            self._update(reset_camera=reset_cam)

    def _update(self, reset_camera=False):
        # 1. 切换可见性
        has_visible_actor = False
        for i, g in enumerate(self.actors):
            vis = (self.mode == "ALL") or (i == self.idx)
            for a in g:
                a.SetVisibility(vis)
                if vis: has_visible_actor = True

        cam = self.va.renderer.GetActiveCamera()

        # 2. 设置相机模式
        if self.mode == "SINGLE":
            cam.ParallelProjectionOn()  # 平行投影
            if reset_camera:
                cam.SetViewUp(0, 1, 0)
                self.va.renderer.ResetCamera()
                fp = cam.GetFocalPoint()
                cam.SetPosition(fp[0], fp[1], fp[2] + 500)

        else:
            cam.ParallelProjectionOff()  # 透视投影
            if reset_camera:
                self.va.renderer.ResetCamera()

        # 3. 渲染
        self.va.window.Render()


if __name__ == "__main__":
    slc_file = "./STL/monk_hollow_result.slc"
    if not os.path.exists(slc_file):
        print(f"错误：找不到 {slc_file}")
    else:
        HollowingViewer(slc_file)