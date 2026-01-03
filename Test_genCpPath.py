import os
import sys
import math
import vtk

# ==============================================================================
# 区域 1: 基础环境与热修复
# ==============================================================================
try:
    import GeomAlgo
    from Segment import Segment
    # 只导入类，不依赖外部的函数定义
    from GenCpPath import GenCpPath
    from ClipperAdaptor import ClipperAdaptor
    from PolyPerSeeker import seekPolyPer
    from Polyline import Polyline
    from SliceAlgo import readSlcFile, writeSlcFile, linkSegs_brutal
    from StlModel import StlModel
    from IntersectStl_sweep import IntersectStl_sweep
    from VtkAdaptor import VtkAdaptor
    import pyclipper
except ImportError as e:
    sys.path.append('.')
    try:
        import GeomAlgo
        from Segment import Segment
        from GenCpPath import GenCpPath
        from ClipperAdaptor import ClipperAdaptor
        from PolyPerSeeker import seekPolyPer
        from Polyline import Polyline
        from SliceAlgo import readSlcFile, writeSlcFile, linkSegs_brutal
        from StlModel import StlModel
        from IntersectStl_sweep import IntersectStl_sweep
        from VtkAdaptor import VtkAdaptor
        import pyclipper
    except ImportError as e2:
        print(f"环境错误: 缺少必要文件 ({e2})")
        sys.exit(1)


# --- 修复 1: 修复 GeomAlgo.pointInPolygon ---
def fixed_pointInPolygon(p, polygon):
    n = polygon.count()
    for i in range(n):
        A = polygon.point(i)
        B = polygon.point((i + 1) % n)
        if A.distance(B) < 1e-7: continue
        if GeomAlgo.distance(p, Segment(A, B)) < 1e-7: return -1
    count = 0
    for i in range(n):
        A = polygon.point(i)
        B = polygon.point((i + 1) % n)
        if A.distance(B) < 1e-7: continue
        if (A.y > p.y and B.y > p.y) or (A.y < p.y and B.y < p.y): continue
        if abs(A.y - p.y) < 1e-7 and abs(B.y - p.y) < 1e-7: continue
        if abs(B.y - A.y) > 1e-7:
            x = A.x + (p.y - A.y) * (B.x - A.x) / (B.y - A.y)
            if x > p.x:
                if not (abs(A.y - p.y) < 1e-7 and A.x > p.x) and not (abs(B.y - p.y) < 1e-7 and B.x > p.x):
                    count += 1
    return 1 if count % 2 == 1 else 0


GeomAlgo.pointInPolygon = fixed_pointInPolygon
try:
    import PolyPerSeeker

    PolyPerSeeker.pointInPolygon = fixed_pointInPolygon
except:
    pass


# ==============================================================================
# 区域 2: 注入优化逻辑
# ==============================================================================

# 定义新的 offset 函数：增加面积过滤
def patched_offset(self):
    ca = ClipperAdaptor()
    ca.arcTolerance = self.arcTolerance
    MIN_AREA = 0.5  # 调小阈值，保留合理的中心结构，去除极小噪点

    delta = self.interval / 2

    raw_polys = ca.offset(self.boundaries, -delta, self.joinType)
    valid_polys = [p for p in raw_polys if abs(p.getArea()) > MIN_AREA]

    if valid_polys:
        self.offsetPolyses.append(valid_polys)
    else:
        return

    while math.fabs(delta) < self.shellThk:
        delta += self.interval
        raw_polys = ca.offset(self.boundaries, -delta, self.joinType)
        if not raw_polys: break

        valid_polys = [p for p in raw_polys if abs(p.getArea()) > MIN_AREA]
        if not valid_polys: break

        self.offsetPolyses.append(valid_polys)


# 定义新的 linkToParent 函数：增加距离检测
def patched_linkToParent(self, child):
    parent = child.parent
    if not parent: return child

    pt = child.startPoint()
    dMin, iAtdMin = float('inf'), 0
    for i in range(parent.count()):
        d = pt.distanceSquare(parent.point(i))
        if d < dMin:
            dMin, iAtdMin = d, i

    # 【核心修复】如果内外圈距离超过 3 倍间距，视为独立岛屿，不连接
    # 这就是消除 PPT 中那种“乱连线”的关键
    if math.sqrt(dMin) > self.interval * 3.0:
        return None

    newPoly = Polyline()
    for i in range(iAtdMin + 1): newPoly.addPoint(parent.point(i).clone())
    if newPoly.count() > 0: newPoly.points[-1].w = 1
    for i in range(child.count()): newPoly.addPoint(child.point(i).clone())
    if newPoly.count() > 0: newPoly.points[-1].w = 1
    for i in range(iAtdMin, parent.count()): newPoly.addPoint(parent.point(i).clone())
    return newPoly


# 定义新的 linkLocalOffsets 函数
def patched_linkLocalOffsets(self):
    if not self.offsetPolyses: return
    try:
        seekPolyPer(self.offsetPolyses)
    except:
        for ps in self.offsetPolyses: self.paths.extend(ps)
        return

    merged_children = set()
    for i in range(len(self.offsetPolyses) - 1, 0, -1):
        childs = self.offsetPolyses[i]
        for j in range(len(childs)):
            child = childs[j]
            if hasattr(child, 'parent') and child.parent:
                newPoly = self.linkToParent(child)
                if newPoly:
                    child.parent.points = newPoly.points
                    merged_children.add(child)

    for path in self.offsetPolyses[0]:
        self.paths.append(path)
    for i in range(1, len(self.offsetPolyses)):
        for path in self.offsetPolyses[i]:
            if path not in merged_children:
                self.paths.append(path)
    self.offsetPolyses.clear()


# === 应用补丁 ===
print("[系统] 正在注入智能优化算法 (去噪 + 孤岛识别)...")
GenCpPath.offset = patched_offset
GenCpPath.linkToParent = patched_linkToParent
GenCpPath.linkLocalOffsets = patched_linkLocalOffsets


# ==============================================================================
# 区域 3: 本地接口函数 (解决 NameError 的关键)
# ==============================================================================
def local_genCpPath(boundaries, interval, shellThk):
    """
    本地定义的接口函数，确保调用的是打过补丁的 GenCpPath 类。
    """
    generator = GenCpPath(boundaries, interval, shellThk)
    return generator.paths


# ==============================================================================
# 区域 4: 主逻辑
# ==============================================================================

def find_data_file(stl_dir, model_name, layer_thk):
    slc_name = f"{model_name}_at_{layer_thk}mm.slc"
    slc_path = os.path.join(stl_dir, slc_name)
    if os.path.exists(slc_path): return slc_path
    return None


def show_clean_contours():
    print("=" * 60)
    print(" 轮廓平行路径生成 (PPT效果复现版)")
    print("=" * 60)

    STL_DIR = "./STL"
    # 使用 1.0mm 切片观察
    SLC_PATH = find_data_file(STL_DIR, "monk", 1.0)

    if not SLC_PATH:
        print(f"未找到文件: {SLC_PATH}")
        print("请先确保 ./STL/monk_at_1.0mm.slc 存在")
        return

    print(f"[1] 读取: {SLC_PATH}")
    layers = readSlcFile(SLC_PATH)

    # 选取第 48 层 (对应Z约-76.6mm)
    target_idx = min(len(layers) - 1, 48)
    layer = layers[target_idx]

    print(f"[2] 处理第 {target_idx} 层 (Z={layer.z:.1f}mm)")

    # 参数设置：为了让线条明显，间距设为 0.6mm，壁厚设大以便填满
    INTERVAL = 0.6
    SHELL_THK = 10.0

    print(f"[3] 生成路径 (间距:{INTERVAL}mm)...")

    if layer.contours:
        # === 关键：调用本地定义的函数 ===
        paths = local_genCpPath(layer.contours, INTERVAL, SHELL_THK)
        print(f"    - 生成路径数: {len(paths)}")
    else:
        paths = []
        print("警告：该层没有轮廓！")

    # 可视化
    print("[4] 渲染视图...")
    va = VtkAdaptor(bgClr=(1.0, 1.0, 1.0))  # 白色背景

    # 1. 原始轮廓 (黑色加粗)
    for c in layer.contours:
        p = c.clone()
        for pt in p.points: pt.z = 0  # 拍平
        act = va.drawPolyline(p)
        act.GetProperty().SetColor(0, 0, 0)
        act.GetProperty().SetLineWidth(3)

    # 2. 填充路径 (红色)
    for p in paths:
        draw_p = p.clone()
        for pt in draw_p.points: pt.z = 0
        act = va.drawPolyline(draw_p)
        act.GetProperty().SetColor(1, 0, 0)
        act.GetProperty().SetLineWidth(1.5)

    # 3. 相机设置 (顶视 + 平行投影)
    cam = va.renderer.GetActiveCamera()
    cam.ParallelProjectionOn()
    cam.SetParallelScale(65)  # 调整视野大小
    va.renderer.ResetCamera()
    # 稍微调整一下初始视角，保证看全
    va.renderer.GetActiveCamera().Zoom(1.1)

    print("\n窗口已打开。")
    va.display()


if __name__ == "__main__":
    show_clean_contours()