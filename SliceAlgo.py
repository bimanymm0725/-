import struct
import math
from GeomBase import Point3D
from Polyline import Polyline
from Layer import Layer
from Segment import Segment
from IntersectStl_sweep import IntersectStl_sweep
from IntersectStl_match import IntersectStl_match
from LinkSegs_dorder import LinkSegs_dorder
from LinkSegs_dlook import LinkSegs_dlook
from GeomAlgo import adjustPolygonDirs, intersectTriangleZPlane


def heal_and_organize(layer, tolerance=0.5):

    linker = LinkSegs_dlook(layer.segments)
    closed_contours = linker.contours
    open_polys = linker.polys

    # 尝试修复开放轮廓
    for poly in open_polys:
        if poly.count() < 2: continue

        start = poly.startPoint()
        end = poly.endPoint()

        dist = start.distance(end)
        if dist < tolerance:
            poly.addPoint(start)
            if poly.count() >= 3:
                closed_contours.append(poly)

    # 过滤极小轮廓
    valid_contours = []
    for cont in closed_contours:
        # 简单面积判断，太小的不要
        if abs(cont.getArea()) > 0.01:
            valid_contours.append(cont)

    layer.contours = valid_contours

    # 调整方向
    adjustPolygonDirs(layer.contours)


def intersectStl_sweep(stlModel, layerThk):
    """扫描平面法STL模型截交函数"""
    return IntersectStl_sweep(stlModel, layerThk).layers


def slice_combine(stlModel, layerThk):
    # 1. 截交
    slicer = IntersectStl_sweep(stlModel, layerThk)
    layers = slicer.layers

    # 2. 拼接与修复
    total_healed = 0
    for layer in layers:
        if len(layer.segments) > 0:
            heal_and_organize(layer, tolerance=0.5)  # 0.5mm 容差
            layer.segments = []
    return layers

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


def writeSlcFile(layers, path):
    f = None
    try:
        f = open(path, 'wb')
        header = "-SLCVER 2.0 -UNIT MM -PACKAGE PythonSlicer -EXTENTS 0,0,0,0,0,0"
        header_bytes = header.encode('utf-8')
        f.write(header_bytes)
        f.write(bytes([0x0d, 0x0a, 0x1a]))
        header_padding = 2048 - len(header_bytes) - 3
        if header_padding > 0: f.write(bytes([0x20] * header_padding))
        f.write(bytes([0x00] * 256))
        f.write(struct.pack('B', 1))

        start_z = layers[0].z if layers else 0.0
        layer_thk = layers[1].z - layers[0].z if len(layers) > 1 else 1.0
        f.write(struct.pack('4f', start_z, layer_thk, 0.0, 0.0))

        for layer in layers:
            f.write(struct.pack('fI', layer.z, len(layer.contours)))
            for contour in layer.contours:
                f.write(struct.pack('II', contour.count(), 0))
                for i in range(contour.count()):
                    pt = contour.point(i)
                    f.write(struct.pack('2f', pt.x, pt.y))

        max_z = layers[-1].z if layers else 0.0
        f.write(struct.pack('fI', max_z, 0xFFFFFFFF))
        return True
    except Exception as ex:
        print("writeSlcFile exception:", ex)
        return False
    finally:
        if f: f.close()


def readSlcFile(path):
    f = None
    try:
        f = open(path, 'rb')
        layers = []
        f.read(2048 + 256)
        num_channels = struct.unpack('B', f.read(1))[0]
        if num_channels > 0: f.read(16)

        while True:
            layer_header = f.read(8)
            if len(layer_header) < 8: break
            z, num_contours = struct.unpack('fI', layer_header)
            if num_contours == 0xFFFFFFFF: break

            layer = Layer(z)
            for _ in range(num_contours):
                contour_header = f.read(8)
                if len(contour_header) < 8: break
                num_points, _ = struct.unpack('II', contour_header)
                contour = Polyline()
                for _ in range(num_points):
                    point_data = f.read(8)
                    if len(point_data) < 8: break
                    x, y = struct.unpack('2f', point_data)
                    contour.addPoint(Point3D(x, y, z))
                layer.contours.append(contour)
            layers.append(layer)
        return layers
    except Exception as ex:
        print("readSlcFile exception:", ex)
        return None
    finally:
        if f: f.close()


def intersectStl_match(stlModel, layerThk):
    return IntersectStl_match(stlModel, layerThk).layers


def linkSegs_dorder(segs):
    return LinkSegs_dorder(segs).contours


def linkSegs_dlook(segs):
    return LinkSegs_dlook(segs).contours


def linkSegs_brutal(segs):
    segs = segs[:]
    contours = []
    while len(segs) > 0:
        contour = Polyline()
        start_seg = segs.pop(0)
        contour.addPoint(start_seg.A)
        contour.addPoint(start_seg.B)
        found_segment = True
        while found_segment and len(segs) > 0:
            found_segment = False
            for i in range(len(segs)):
                seg = segs[i]
                if contour.startPoint().isCoincide(seg.A):
                    contour.raddPoint(seg.B)
                    segs.pop(i);
                    found_segment = True;
                    break
                elif contour.startPoint().isCoincide(seg.B):
                    contour.raddPoint(seg.A)
                    segs.pop(i);
                    found_segment = True;
                    break
                elif contour.endPoint().isCoincide(seg.A):
                    contour.addPoint(seg.B)
                    segs.pop(i);
                    found_segment = True;
                    break
                elif contour.endPoint().isCoincide(seg.B):
                    contour.addPoint(seg.A)
                    segs.pop(i);
                    found_segment = True;
                    break
            if contour.isClosed(): break
        contours.append(contour)
    return contours