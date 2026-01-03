import time
import os
import vtk
from VtkAdaptor import VtkAdaptor
from SliceAlgo import readSlcFile
from GenDpPath import genDpPath
from Utility import degToRad


class InteractiveViewer:
    """交互式查看器类"""

    def __init__(self, layers, pathses, interval):
        self.layers = layers
        self.pathses = pathses
        self.interval = interval
        self.total_layers = len(layers)

        # 初始化 VTK
        self.va = VtkAdaptor()
        self.va.setBackgroundColor(1.0, 1.0, 1.0)  # 白色背景

        # 状态变量
        self.current_idx = 43  # 默认看第43层
        self.view_mode = "ALL"  # "ALL" (全貌) 或 "SINGLE" (单层)

        # 存储 Actor 以便快速切换显隐
        self.actors = []  # 结构: [{'contours': [actors], 'paths': [actors]}, ...]

        print("\n正在构建 3D 场景，请稍候...")
        self._build_actors()
        self._setup_input()
        self._update_visibility()

        # 打印操作指南
        print("\n" + "=" * 60)
        print("【 交互操作指南 】")
        print(f"  当前层厚文件包含 {self.total_layers} 层")
        print("  [S] 键 : 切换到【单层模式】查看具体线路 (推荐)")
        print("  [A] 键 : 切换到【全貌模式】 (PPT风格)")
        print("  [↑] 键 : 上一层")
        print("  [↓] 键 : 下一层")
        print("  [Q] 键 : 退出程序")
        print("=" * 60)

        # 开启正交投影，消除透视变形，方便观察间距
        self.va.renderer.GetActiveCamera().ParallelProjectionOn()
        self.va.renderer.ResetCamera()
        self.va.display()

    def _build_actors(self):
        """预先创建所有层的所有Actor，后续只控制开关"""
        for i in range(self.total_layers):
            layer_group = {'contours': [], 'paths': []}
            z = self.layers[i].z

            # 1. 创建轮廓 Actor (黑色)
            if self.layers[i].contours:
                for poly in self.layers[i].contours:
                    # 强制Z值
                    for pt in poly.points: pt.z = z
                    act = self.va.drawPolyline(poly)
                    act.GetProperty().SetColor(0, 0, 0)  # 黑色
                    act.GetProperty().SetLineWidth(1)
                    layer_group['contours'].append(act)

            # 2. 创建路径 Actor (红色)
            if i < len(self.pathses) and self.pathses[i]:
                for path in self.pathses[i]:
                    # 强制Z值
                    for pt in path.points: pt.z = z
                    act = self.va.drawPolyline(path)
                    act.GetProperty().SetColor(1, 0, 0)  # 红色
                    act.GetProperty().SetLineWidth(1.5)
                    layer_group['paths'].append(act)

            self.actors.append(layer_group)

    def _setup_input(self):
        """绑定键盘事件"""
        self.va.interactor.AddObserver("KeyPressEvent", self.on_key)

    def on_key(self, obj, event):
        key = obj.GetKeySym()

        if key in ["s", "S"]:
            self.view_mode = "SINGLE"
            print(f"模式切换 -> 单层模式 (层: {self.current_idx})")
            self._update_visibility()

        elif key in ["a", "A"]:
            self.view_mode = "ALL"
            print(f"模式切换 -> 全貌模式")
            self._update_visibility()

        elif key == "Up":
            if self.current_idx < self.total_layers - 1:
                self.current_idx += 1
                if self.view_mode == "SINGLE":
                    print(f"切换至第 {self.current_idx} 层")
                    self._update_visibility()

        elif key == "Down":
            if self.current_idx > 0:
                self.current_idx -= 1
                if self.view_mode == "SINGLE":
                    print(f"切换至第 {self.current_idx} 层")
                    self._update_visibility()

    def _update_visibility(self):
        """根据模式和当前层，设置Actor可见性"""
        for i, group in enumerate(self.actors):
            # 判断是否可见
            visible = False
            if self.view_mode == "ALL":
                visible = True
            elif self.view_mode == "SINGLE":
                visible = (i == self.current_idx)

            # 应用可见性
            for act in group['contours']:
                act.SetVisibility(visible)
            for act in group['paths']:
                act.SetVisibility(visible)

        # 如果是单层模式，自动将相机对准该层
        if self.view_mode == "SINGLE":
            # 简单的相机跟随逻辑，保持视角不变，只变中心
            cam = self.va.renderer.GetActiveCamera()
            fp = cam.GetFocalPoint()
            current_z = self.layers[self.current_idx].z
            cam.SetFocalPoint(fp[0], fp[1], current_z)

        self.va.window.Render()


def run_test():
    # === 1. 性能统计 (保留原功能) ===
    base_dir = "./STL"
    files = ["monk_at_2.0mm.slc", "monk_at_1.0mm.slc", "monk_at_0.5mm.slc", "monk_at_0.2mm.slc"]

    interval = 1.5  # 间距
    base_angle = 0  # 初始角度

    vis_data = {}  # 存储用于可视化的数据 (只存2.0mm的，为了流畅)

    print(f"{'=' * 65}")
    print(f"平行路径生成性能统计 (间距: {interval}mm)")
    print(f"{'=' * 65}")
    print(f"{'文件名':<20} | {'层数':<6} | {'耗时(s)':<10} | {'路径总数'}")
    print("-" * 65)

    for fname in files:
        fpath = os.path.join(base_dir, fname)
        if not os.path.exists(fpath):
            print(f"{fname:<20} | 文件不存在")
            continue

        layers = readSlcFile(fpath)
        if not layers: continue

        pathses = []
        count = 0
        t_start = time.time()

        for i, layer in enumerate(layers):
            if not layer.contours:
                pathses.append([])
                continue
            # 正交角度
            theta = degToRad(base_angle if i % 2 == 0 else base_angle + 90)
            # 生成
            paths = genDpPath(layer.contours, interval, theta)
            pathses.append(paths)
            count += len(paths)

        t_end = time.time()
        print(f"{fname:<20} | {len(layers):<6} | {t_end - t_start:<10.4f} | {count}")

        # 缓存 2.0mm 的数据用于展示
        if "2.0mm" in fname:
            vis_data['layers'] = layers
            vis_data['pathses'] = pathses

    # === 2. 交互可视化 ===
    if 'layers' in vis_data:
        InteractiveViewer(vis_data['layers'], vis_data['pathses'], interval)
    else:
        print("未找到 2.0mm 文件用于可视化。")


if __name__ == '__main__':
    run_test()