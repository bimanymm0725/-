import math
from GenSptPath import SptFillType, genSptPath
from SliceAlgo import intersectStl_sweep
from IdEndLayers import idEndLayers
from GenCpPath import genCpPath
from GenDpPath import genDpPath
from GeomBase import *


class PrintParams:
    """打印工艺参数类"""

    def __init__(self, stlModel):
        self.stlModel = stlModel
        self.layerThk, self.shellThk, self.endThk = 0.2, 2.0, 2.0
        self.sfRate, self.fillAngle = 0.2, 0.0
        self.sptOn = False
        self.sptCrAngle = math.radians(60.0)
        self.sptGridSize = 2.0
        self.sptSfRate, self.sptFillAngle = 0.15, 0.0
        self.sptFillType = SptFillType.cross
        self.sptXyGap = 1.0
        self.g0Speed, self.g1Speed = 5000, 1000
        self.startCode = "; Start code...\nG28\n"
        self.endCode = "; End code...\nM104 S0\n"
        self.nozzleSize, self.filamentSize = 0.4, 1.75  # 常用默认值


def genAllPaths(pp: PrintParams):
    """所有路径生成函数"""
    sfInvl = pp.nozzleSize / pp.sfRate
    sptSfInvl = pp.nozzleSize / pp.sptSfRate

    layers = intersectStl_sweep(pp.stlModel, pp.layerThk)

    endLayerNum = int(pp.endThk / pp.layerThk) + 1
    idEndLayers(layers, pp.shellThk, endLayerNum)

    for i, layer in enumerate(layers):
        layer.cpPaths, layer.ffPaths, layer.sfPaths = [], [], []

        # 轮廓路径
        layer.cpPaths = genCpPath(layer.contours, pp.nozzleSize, pp.shellThk)

        delta = 0 if i % 2 == 0 else math.pi / 2

        # 密实填充
        if len(layer.ffContours) > 0:
            layer.ffPaths = genDpPath(layer.ffContours, pp.nozzleSize, pp.fillAngle + delta)

        # 稀疏填充
        if len(layer.sfContours) > 0:
            layer.sfPaths = genDpPath(layer.sfContours, sfInvl, pp.fillAngle + delta)

    if pp.sptOn:
        genSptPath(pp.stlModel, layers, sptSfInvl, pp.sptGridSize,
                   pp.sptCrAngle, pp.sptFillType, pp.sptFillAngle, pp.sptXyGap)

    return layers


def pathToCode(path, pp, e, e_per_mm):
    """
    将一条路径转化为NC代码
    path: 路径
    pp: 参数
    e: 当前累计挤出量
    e_per_mm: 单位长度(mm)需要的挤出量
    """
    code = ""
    for i, p in enumerate(path.points):
        if i == 0:
            # 移动到起点 (G0)
            code += "G0 F%d X%.3f Y%.3f Z%.3f\n" % (pp.g0Speed, p.x, p.y, p.z)
        else:
            # 打印移动 (G1)
            dist = p.distance(path.points[i - 1])

            # 检查是否为空走 (w=1表示连接线段，不挤出)
            # 在GenCpPath中我们用w=1标记了空走连接线
            if path.points[i - 1].w == 1:
                # 空走，无挤出
                code += "G0 F%d X%.3f Y%.3f\n" % (pp.g0Speed, p.x, p.y)
            else:
                # 正常打印
                e += dist * e_per_mm
                code += "G1 F%d X%.3f Y%.3f E%.5f\n" % (pp.g1Speed, p.x, p.y, e)

    return code, e


def postProcess(layers, pp):
    """后处理生成G代码"""
    code = pp.startCode
    e = 0.0

    # 打印线条体积 = 长度 * 线宽(喷嘴直径) * 层高
    # 耗材体积 = 长度 * pi * (耗材直径/2)^2
    # E_per_mm = (nozzle * layer_height) / (pi * (filament/2)^2)

    filament_area = math.pi * (pp.filamentSize / 2) ** 2
    line_area = pp.nozzleSize * pp.layerThk
    e_per_mm = line_area / filament_area

    for i, layer in enumerate(layers):
        code += "; Layer %d Z=%.3f\n" % (i, layer.z)

        # 支撑
        if hasattr(layer, 'sptCpPaths'):
            for path in layer.sptCpPaths:
                block, e = pathToCode(path, pp, e, e_per_mm)
                code += block
        if hasattr(layer, 'sptDpPaths'):
            for path in layer.sptDpPaths:
                block, e = pathToCode(path, pp, e, e_per_mm)
                code += block

        # 实体路径
        for path in layer.cpPaths:
            block, e = pathToCode(path, pp, e, e_per_mm)
            code += block
        for path in layer.ffPaths:
            block, e = pathToCode(path, pp, e, e_per_mm)
            code += block
        for path in layer.sfPaths:
            block, e = pathToCode(path, pp, e, e_per_mm)
            code += block

    code += pp.endCode
    return code


def genNcCode(pp: PrintParams):
    layers = genAllPaths(pp)
    return postProcess(layers, pp)