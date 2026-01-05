import math
import pyclipper
from Layer import Layer
from ClipperAdaptor import ClipperAdaptor
from GeomBase import *


# ==============================================================================
# 1. 核心算法类
# ==============================================================================
class HollowingAlgo:
    def __init__(self, wall_thickness, z_min=None, z_max=None):
        self.w = wall_thickness
        # 兼容旧接口，允许不传 z_min/z_max (默认为无穷大范围)
        self.z_min = z_min if z_min is not None else float('-inf')
        self.z_max = z_max if z_max is not None else float('inf')
        self.ca = ClipperAdaptor()

    def generate_hollow_layers(self, layers):
        print(f"正在进行3D均匀抽壳 (壁厚: {self.w}mm)...")

        hollowed_layers = []
        total = len(layers)

        for i in range(total):
            if i % 10 == 0:
                print(f"  处理进度: {i}/{total}", end="\r")

            current_layer = layers[i]
            z_i = current_layer.z

            # 如果这一层因为破面导致外轮廓完全丢失，直接跳过
            if not current_layer.contours:
                hollowed_layers.append(Layer(z_i))
                continue

            # === 边界蒙皮检查 (Top/Bottom Skin) ===
            # 如果距离顶底小于壁厚，强制实心
            dist_to_top = self.z_max - z_i
            dist_to_bottom = z_i - self.z_min

            if dist_to_top < self.w - 0.01 or dist_to_bottom < self.w - 0.01:
                # 强制实心
                new_layer = Layer(z_i)
                for p in current_layer.contours:
                    new_layer.contours.append(p.clone())
                hollowed_layers.append(new_layer)
                continue

            # === Park 算法逻辑 ===
            # 1. 确定搜索范围
            start_idx = i
            while start_idx > 0 and (z_i - layers[start_idx - 1].z) < self.w:
                start_idx -= 1

            end_idx = i
            while end_idx < total - 1 and (layers[end_idx + 1].z - z_i) < self.w:
                end_idx += 1

            void_candidates = []
            is_solid = False

            # 2. 遍历邻居层
            for j in range(start_idx, end_idx + 1):
                neighbor_layer = layers[j]
                if not neighbor_layer.contours: continue

                dz = abs(z_i - neighbor_layer.z)

                if dz >= self.w - 1e-5:
                    offset_dist = 0
                else:
                    offset_dist = math.sqrt(self.w ** 2 - dz ** 2)

                # 向内偏置
                offset_polys = self.ca.offset(neighbor_layer.contours, -offset_dist, pyclipper.JT_ROUND)

                if not offset_polys:
                    # 只要有一个邻居限制为空，说明此处无法容纳空腔，强制实心
                    is_solid = True
                    break

                void_candidates.append(offset_polys)

            # 3. 求交集
            final_void = []
            if not is_solid and void_candidates:
                final_void = void_candidates[0]
                for k in range(1, len(void_candidates)):
                    final_void = self.ca.clip(final_void, void_candidates[k], pyclipper.CT_INTERSECTION)
                    if not final_void: break

            # 4. 生成结果
            new_layer = Layer(z_i)

            if not final_void:
                # 实心层：复制外轮廓
                for p in current_layer.contours:
                    new_layer.contours.append(p.clone())
            else:
                # 空心层：外轮廓 - 内腔
                hollow_polys = self.ca.clip(current_layer.contours, final_void, pyclipper.CT_DIFFERENCE)
                new_layer.contours = hollow_polys

            hollowed_layers.append(new_layer)

        print(f"  处理完成: {total}/{total}        ")
        return hollowed_layers


# ==============================================================================
# 2. 全局接口函数 (您缺失的部分)
# ==============================================================================
def perform_hollowing(stlModel, layerThk, wallThickness):
    """
    执行抽壳的全局接口函数：集成切片、拼接、修复和抽壳
    """
    # 延迟导入以避免循环依赖
    from SliceAlgo import intersectStl_sweep, adjustPolygonDirs
    # 必须直接导入类，而不是函数
    from LinkSegs_dlook import LinkSegs_dlook
    from ClipperAdaptor import ClipperAdaptor

    # 获取高度范围 (用于顶底实心判断)
    bounds = stlModel.getBounds()
    zMin, zMax = bounds[4], bounds[5]

    print("1. 基础切片...")
    raw_layers = intersectStl_sweep(stlModel, layerThk)

    print("2. 轮廓拼接 (启用强力修复)...")
    ca = ClipperAdaptor()

    total_healed = 0
    for layer in raw_layers:
        if layer.segments:
            # 使用字典查询法拼接类
            linker = LinkSegs_dlook(layer.segments)

            valid_contours = linker.contours

            # 强力修复：检查未闭合的废料
            if linker.polys:
                for open_poly in linker.polys:
                    if open_poly.count() > 2:
                        # 强制闭合
                        open_poly.addPoint(open_poly.startPoint())
                        valid_contours.append(open_poly)
                        total_healed += 1

            if valid_contours:
                # 拓扑清洗：去除自相交和噪点
                clean_polys = ca.simplify_and_clean(valid_contours, clean_dist=0.02)
                adjustPolygonDirs(clean_polys)
                layer.contours = clean_polys
            else:
                layer.contours = []

            # 清理内存
            layer.segments = []

    if total_healed > 0:
        print(f"   [提示] 强制修复了 {total_healed} 个破损轮廓。")

    print("3. 执行抽壳...")
    # 传入 zMin, zMax 以启用顶底强制实心逻辑
    hollower = HollowingAlgo(wallThickness, zMin, zMax)
    return hollower.generate_hollow_layers(raw_layers)