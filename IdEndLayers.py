import pyclipper
import math
from Layer import Layer
from ClipperAdaptor import ClipperAdaptor
from GeomBase import *


# ==========================================
# 核心功能函数
# ==========================================

def clean_contours(ca, contours, precision=0.05):
    """
    轮廓整形函数：消除锯齿和噪点
    """
    if not contours: return []

    # 1. 向外膨胀 (消除凹陷/重叠)
    # 修正：移除 limit 参数，使用默认值
    expanded = ca.offset(contours, precision, jt=pyclipper.JT_MITER)

    # 2. 向内收缩 (恢复尺寸)
    cleaned = ca.offset(expanded, -precision, jt=pyclipper.JT_MITER)

    return cleaned


def pickFfRegions(layer1, layer2, shellThk):
    c1, c2 = layer1.contours, layer2.contours
    ca = ClipperAdaptor()

    # === 1. 计算外壳内边界 c2oi ===
    # 向内偏置，得到稀疏填充的边界
    # 使用 JT_ROUND 稍微圆滑一点，避免内部出现奇怪的尖角
    c2oi = ca.offset(c2, -shellThk, jt=pyclipper.JT_ROUND)
    if len(c2oi) == 0:
        return False

    layer2.shellContours = c2oi

    # === 2. 识别端面 (关键逻辑) ===
    # 如果 c1(参考层) 为空，说明 c2 全是悬空端面
    if len(c1) == 0:
        d = c2
    else:
        # 关键修正：c1 向外膨胀 "安全距离"，确保能覆盖住垂直对齐的 c2
        # 如果不膨胀，切片误差会导致垂直墙壁被识别为端面(留下一圈皮)
        # 0.1mm 的膨胀量通常足够覆盖切片误差
        c1_safe = ca.offset(c1, 0.1, jt=pyclipper.JT_SQUARE)

        # d = c2 - c1_safe
        # 过滤掉面积小于 1.0 的碎屑，防止噪点
        d = ca.clip(c2, c1_safe, pyclipper.CT_DIFFERENCE, minArea=1.0)

    if len(d) == 0:
        return False

    # === 3. 生成密实填充区域 f ===
    # 端面 d 向内延伸 shellThk (为了与外壳结合牢固)
    doo = ca.offset(d, shellThk, jt=pyclipper.JT_ROUND)

    # f = doo ∩ c2oi (限制在模型内部)
    z = c2[0].point(0).z if c2 else 0
    f = ca.clip(doo, c2oi, pyclipper.CT_INTERSECTION, z, minArea=1.0)

    layer2.ffContours = f
    return len(f) > 0


def splitFfRegions(layers, shellThk, endLayerNum):
    if not layers: return

    # 插入辅助空层，以便处理第一层的端面
    layers.insert(0, Layer(0))

    i = 0  # 参考层索引
    j = 1  # 目标层索引

    while True:
        if j >= len(layers):
            break

        # 尝试识别 layer[j] 是否相对于 layer[i] 有端面
        is_end = pickFfRegions(layers[i], layers[j], shellThk)

        if is_end:
            # 如果 layer[j] 是端面层，我们需要向上继续标记 endLayerNum 层
            # 这里的逻辑是：只要发现端面，就保持参考层 i 不变，
            # 让后续的 j, j+1... 都跟 i 比，从而都识别出端面区域
            # 这样可以生成一定厚度的实心底/顶
            count = 0
            while is_end and count < endLayerNum:
                j += 1
                count += 1
                if j >= len(layers): break
                # 继续用 i 层作为参考，判断 j 层是否有端面区域
                is_end = pickFfRegions(layers[i], layers[j], shellThk)

            # 一组端面处理完，更新参考层位置
            i = j - 1
        else:
            # 不是端面（垂直生长），正常推进
            i += 1
            j += 1

    del layers[0]


def splitSfRegions(layers):
    ca = ClipperAdaptor()
    for layer in layers:
        # 如果有外壳
        if len(layer.shellContours) > 0:
            # 如果没有密实区，整个内部都是稀疏区
            if len(layer.ffContours) == 0:
                layer.sfContours = layer.shellContours
            else:
                # s = c2oi - f
                s = ca.clip(layer.shellContours, layer.ffContours, pyclipper.CT_DIFFERENCE, layer.z)
                layer.sfContours = s


def idEndLayers(layers, shellThk, endLayerNum):
    # 1. 下端面识别 (自下而上)
    # 这会填充 layers 中的 ffContours
    splitFfRegions(layers, shellThk, endLayerNum)

    # 2. 上端面识别 (自上而下)
    # 我们需要先把下端面的结果存起来，以免被覆盖
    lower_ff = [layer.ffContours for layer in layers]

    # 清空 ffContours 以便计算上端面
    for layer in layers: layer.ffContours = []

    # 反转列表计算上端面
    reversed_layers = layers[::-1]
    splitFfRegions(reversed_layers, shellThk, endLayerNum)

    # 3. 合并上下端面结果
    # ff = lower_ff U upper_ff
    ca = ClipperAdaptor()
    for i, layer in enumerate(layers):
        upper = layer.ffContours
        lower = lower_ff[i]

        if len(upper) > 0 and len(lower) > 0:
            # 合并
            merged = ca.clip(upper, lower, pyclipper.CT_UNION, layer.z)
            layer.ffContours = merged
        elif len(lower) > 0:
            layer.ffContours = lower
        # else: 保持 upper

    # 4. 最后生成稀疏区域 (sf = shell - ff)
    splitSfRegions(layers)


if __name__ == '__main__':
    import os
    import vtk
    from StlModel import StlModel
    from SliceAlgo import intersectStl_sweep, linkSegs_dlook
    from VtkAdaptor import VtkAdaptor

    stl_path = "./STL/multiEnds.stl"
    if not os.path.exists(stl_path):
        stl_path = "./STL/monk.stl"
        print(f"Warning: multiEnds.stl not found, using {stl_path}")

    if not os.path.exists(stl_path):
        print("Error: No model file found.")
        exit()

    print(f"读取模型: {stl_path} ...")
    src = vtk.vtkSTLReader()
    src.SetFileName(stl_path)
    src.Update()

    stlModel = StlModel()
    stlModel.extractFromVtkStlReader(src)

    layerThk = 1.0
    shellThk = 2.0
    endThk = 3.0
    endLayerNum = int(endThk / layerThk) + 1

    print("Slicing...")
    layers = intersectStl_sweep(stlModel, layerThk)

    print("Linking contours & Cleaning...")
    ca = ClipperAdaptor()
    for layer in layers:
        if layer.segments:
            raw_conts = linkSegs_dlook(layer.segments)
            # 关键：全局清洗，消除锯齿
            # 修正：移除 limit 参数
            layer.contours = clean_contours(ca, raw_conts, precision=0.02)

    print("Identifying end layers...")
    idEndLayers(layers, shellThk, endLayerNum)

    print("Visualizing...")
    va = VtkAdaptor()
    va.setBackgroundColor(1, 1, 1)

    act_model = va.drawPdSrc(src)
    act_model.GetProperty().SetOpacity(0.05)
    act_model.GetProperty().SetColor(0, 0, 0)

    for layer in layers:
        # 模型轮廓 (黑)
        for poly in layer.contours:
            act = va.drawPolyline(poly)
            act.GetProperty().SetColor(0, 0, 0)
            act.GetProperty().SetLineWidth(1)

        # 密实端面 (红)
        for poly in layer.ffContours:
            act = va.drawPolyline(poly)
            act.GetProperty().SetColor(1, 0, 0)
            act.GetProperty().SetLineWidth(3)

        # 稀疏内部 (绿)
        for poly in layer.sfContours:
            act = va.drawPolyline(poly)
            act.GetProperty().SetColor(0, 1, 0)
            act.GetProperty().SetLineWidth(1)

    va.renderer.ResetCamera()
    va.display()