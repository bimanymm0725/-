from GeomBase import *
from Triangle import *
from StlModel import *
from Layer import *
from GeomAlgo import *
import struct
import os
from IntersectStl_sweep import IntersectStl_sweep
from IntersectStl_match import IntersectStl_match
from LinkSegs_dorder import LinkSegs_dorder
from LinkSegs_dlook import LinkSegs_dlook

def intersectStl_brutal(stlModel, layerThk):
    """STL模型截交函数 - 暴力法"""
    layers = []  # 保存层对象列表

    # 获取模型边界
    xMin, xMax, yMin, yMax, zMin, zMax = stlModel.getBounds()

    # 从最低点开始切片，每次增加层厚
    z = zMin + layerThk
    while z < zMax:  # 截交主循环
        layer = Layer(z)

        # 对当前高度，遍历所有三角形
        for tri in stlModel.triangles:
            # 计算三角形和平面交线
            seg = intersectTriangleZPlane(tri, z)
            if seg is not None:
                layer.segments.append(seg)  # 将交线保存在layer中

        layers.append(layer)
        z += layerThk

    return layers  # 返回层列表


def linkSegs_brutal(segs):
    """暴力拼接函数，将截交线段整理成封闭轮廓"""
    segs = segs[:]  # 创建副本，避免修改原列表
    contours = []  # 保存拼接后的轮廓

    while len(segs) > 0:
        contour = Polyline()  # 创建新的轮廓

        # 从线段集中取出一条线段作为起始线段
        start_seg = segs.pop(0)
        contour.addPoint(start_seg.A)
        contour.addPoint(start_seg.B)

        found_segment = True
        while found_segment and len(segs) > 0:
            found_segment = False

            # 遍历剩余线段，寻找可以连接的线段
            for i in range(len(segs)):
                seg = segs[i]

                # 检查线段是否与轮廓的起点或终点重合
                if contour.startPoint().isCoincide(seg.A):
                    contour.raddPoint(seg.B)  # 在起点前添加
                    segs.pop(i)
                    found_segment = True
                    break
                elif contour.startPoint().isCoincide(seg.B):
                    contour.raddPoint(seg.A)  # 在起点前添加
                    segs.pop(i)
                    found_segment = True
                    break
                elif contour.endPoint().isCoincide(seg.A):
                    contour.addPoint(seg.B)  # 在终点后添加
                    segs.pop(i)
                    found_segment = True
                    break
                elif contour.endPoint().isCoincide(seg.B):
                    contour.addPoint(seg.A)  # 在终点后添加
                    segs.pop(i)
                    found_segment = True
                    break

            # 如果轮廓封闭，退出当前轮廓的拼接
            if contour.isClosed():
                break

        # 如果轮廓不封闭，但无法找到更多连接线段，也保存该轮廓
        contours.append(contour)

    return contours


def writeSlcFile(layers, path):
    """写SLC文件"""
    f = None
    try:
        f = open(path, 'wb')  # 打开（或创建）一个二进制文件

        # 写入Header区
        header = "-SLCVER 2.0 -UNIT MM -PACKAGE PythonSlicer -EXTENTS 0,0,0,0,0,0"
        header_bytes = header.encode('utf-8')
        f.write(header_bytes)

        # Header结尾3字节
        f.write(bytes([0x0d, 0x0a, 0x1a]))

        # 填充Header到2048字节
        header_padding = 2048 - len(header_bytes) - 3
        if header_padding > 0:
            f.write(bytes([0x20] * header_padding))  # 用空格填充

        # 写入Reserved区256个0x00
        f.write(bytes([0x00] * 256))

        # 写入Sampling Table区
        # 通道数量为1
        f.write(struct.pack('B', 1))

        # 每个通道4个float字段：起始高度、切片厚度、线宽补偿、保留字段
        if layers:
            start_z = layers[0].z
            layer_thk = layers[1].z - layers[0].z if len(layers) > 1 else 1.0
        else:
            start_z = 0.0
            layer_thk = 1.0

        f.write(struct.pack('4f', start_z, layer_thk, 0.0, 0.0))

        # 写入Contour Data区
        for layer in layers:
            # 写入层高和轮廓数量
            f.write(struct.pack('fI', layer.z, len(layer.contours)))

            for contour in layer.contours:
                # 写入顶点数和gap数（这里gap数设为0）
                f.write(struct.pack('II', contour.count(), 0))

                # 写入顶点坐标（只写入x,y，z由层高决定）
                for i in range(contour.count()):
                    pt = contour.point(i)
                    f.write(struct.pack('2f', pt.x, pt.y))

        # 写入文件结尾
        if layers:
            max_z = layers[-1].z
        else:
            max_z = 0.0
        f.write(struct.pack('fI', max_z, 0xFFFFFFFF))

        return True

    except Exception as ex:
        print("writeSlcFile exception:", ex)  # 打印异常
        return False
    finally:
        if f:
            f.close()


def readSlcFile(path):
    """读SLC文件"""
    f = None
    try:
        f = open(path, 'rb')
        layers = []

        # 读取Header区（跳过2048字节）
        f.read(2048)

        # 读取Reserved区（跳过256字节）
        f.read(256)

        # 读取Sampling Table区
        num_channels = struct.unpack('B', f.read(1))[0]

        # 读取通道数据（这里只处理第一个通道）
        if num_channels > 0:
            channel_data = struct.unpack('4f', f.read(16))
            start_z, layer_thk, compensation, reserved = channel_data

        # 读取Contour Data区
        while True:
            # 读取层高和轮廓数量
            layer_header = f.read(8)  # 4字节float + 4字节uint
            if len(layer_header) < 8:
                break

            z, num_contours = struct.unpack('fI', layer_header)

            # 检查文件结束标记
            if num_contours == 0xFFFFFFFF:
                break

            layer = Layer(z)

            # 读取当前层的所有轮廓
            for _ in range(num_contours):
                # 读取顶点数和gap数
                contour_header = f.read(8)  # 2个4字节uint
                if len(contour_header) < 8:
                    break

                num_points, num_gaps = struct.unpack('II', contour_header)

                # 读取顶点坐标
                contour = Polyline()
                for _ in range(num_points):
                    point_data = f.read(8)  # 2个4字节float
                    if len(point_data) < 8:
                        break
                    x, y = struct.unpack('2f', point_data)
                    contour.addPoint(Point3D(x, y, z))

                layer.contours.append(contour)

            layers.append(layer)

        return layers

    except Exception as ex:
        print("readSlcFile exception:", ex)
        return None
    finally:
        if f:
            f.close()

def processLayers(layers):
    """处理所有层：拼接线段并调整轮廓方向"""
    for layer in layers:
        if layer.segments:
            layer.contours = linkSegs_brutal(layer.segments)
            adjustPolygonDirs(layer.contours)

    return layers

def intersectStl_sweep(stlModel, layerThk):
    """扫描平面法STL模型截交函数"""
    return IntersectStl_sweep(stlModel, layerThk).layers

def intersectStl_match(stlModel, layerThk):
    """层高匹配法STL模型截交函数"""
    return IntersectStl_match(stlModel, layerThk).layers

def linkSegs_dorder(segs):
    """字典序排序线段链接，全局函数"""
    return LinkSegs_dorder(segs).contours

def linkSegs_dlook(segs):
    """字典查询法线段链接，全局函数"""
    return LinkSegs_dlook(segs).contours