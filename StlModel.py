from GeomBase import *
from Triangle import Triangle
import vtk
import struct
import os
import math


class StlModel:
    def __init__(self):
        self.triangles = []  # 三角面片列表
        self.xMin = self.xMax = self.yMin = self.yMax = self.zMin = self.zMax = 0

    def getFacetNumber(self):
        """获取STL模型中的面片数"""
        return len(self.triangles)

    def _calculateBounds(self):
        """计算模型边界"""
        if not self.triangles:
            self.xMin = self.xMax = self.yMin = self.yMax = self.zMin = self.zMax = 0
            return

        # 初始化边界值
        self.xMin = self.xMax = self.triangles[0].A.x
        self.yMin = self.yMax = self.triangles[0].A.y
        self.zMin = self.zMax = self.triangles[0].A.z

        # 遍历所有三角形更新边界
        for tri in self.triangles:
            for vertex in [tri.A, tri.B, tri.C]:
                self.xMin = min(self.xMin, vertex.x)
                self.xMax = max(self.xMax, vertex.x)
                self.yMin = min(self.yMin, vertex.y)
                self.yMax = max(self.yMax, vertex.y)
                self.zMin = min(self.zMin, vertex.z)
                self.zMax = max(self.zMax, vertex.z)

    def getCoords(self, line):
        """从文本中提取坐标，被readStlFile调用"""
        # 移除多余的空格和换行符
        line = line.strip()
        # 按空格分割
        parts = line.split()
        if len(parts) >= 4:
            try:
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                return x, y, z
            except ValueError:
                return None
        return None

    def readStlFile(self, filepath):
        """读取STL文件，输入文件路径"""
        print(f"尝试读取文件: {filepath}")

        # 首先检测文件格式
        file_type = self._detectStlFormat(filepath)
        print(f"检测到文件格式: {file_type}")

        if file_type == "binary":
            success = self._readStlFileBinary(filepath)
            if success:
                print(f"二进制读取成功，三角形数量: {len(self.triangles)}")
            else:
                print("二进制读取失败，尝试文本格式")
                success = self._readStlFileText(filepath)
                if success:
                    print(f"文本读取成功，三角形数量: {len(self.triangles)}")
            return success
        elif file_type == "ascii":
            success = self._readStlFileText(filepath)
            if success:
                print(f"文本读取成功，三角形数量: {len(self.triangles)}")
            else:
                print("文本读取失败，尝试二进制格式")
                success = self._readStlFileBinary(filepath)
                if success:
                    print(f"二进制读取成功，三角形数量: {len(self.triangles)}")
            return success
        else:
            # 如果无法确定，先尝试文本格式，再尝试二进制格式
            success = self._readStlFileText(filepath)
            if success:
                print(f"文本读取成功，三角形数量: {len(self.triangles)}")
                return True
            success = self._readStlFileBinary(filepath)
            if success:
                print(f"二进制读取成功，三角形数量: {len(self.triangles)}")
            return success

    def _detectStlFormat(self, filepath):
        """检测STL文件格式"""
        try:
            file_size = os.path.getsize(filepath)

            with open(filepath, 'rb') as f:
                # 读取前200个字节
                header = f.read(200)

            # 检查是否是ASCII STL（包含"solid"关键字）
            try:
                header_text = header.decode('ascii', errors='ignore').lower()
                if 'solid' in header_text:
                    # 进一步检查是否包含STL关键字
                    if 'facet' in header_text or 'vertex' in header_text:
                        return "ascii"
                    else:
                        # 如果有solid但没有facet/vertex，可能是二进制文件的头部恰好有solid这个词
                        pass
            except:
                pass

            # 检查是否是二进制STL
            # 二进制STL：80字节头部 + 4字节三角形数量 + 每个三角形50字节
            if file_size >= 84:
                # 读取三角形数量
                try:
                    num_triangles = struct.unpack('<I', header[80:84])[0]
                    expected_size = 84 + num_triangles * 50

                    # 如果计算的文件大小与实际文件大小匹配，很可能是二进制格式
                    if expected_size == file_size:
                        return "binary"
                except:
                    pass

            return "unknown"

        except Exception as e:
            print(f"检测文件格式时出错: {e}")
            return "unknown"

    def _readStlFileText(self, filepath):
        """读取文本STL文件"""
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'latin-1', 'cp1252', 'gbk', 'ascii']

            for encoding in encodings:
                try:
                    print(f"尝试使用编码 {encoding} 读取文本STL")
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()

                    lines = content.splitlines()
                    self.triangles = []

                    i = 0
                    triangle_count = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        i += 1

                        if 'facet normal' in line.lower():
                            # 读取法向量
                            coords = self.getCoords(line)
                            if coords:
                                N = Vector3D(coords[0], coords[1], coords[2])
                            else:
                                N = Vector3D(0, 0, 0)

                            # 寻找 "outer loop"
                            found_outer = False
                            while i < len(lines) and not found_outer:
                                if 'outer loop' in lines[i].lower():
                                    found_outer = True
                                i += 1

                            if not found_outer:
                                continue

                            # 读取三个顶点
                            vertices = []
                            vertices_read = 0
                            while i < len(lines) and vertices_read < 3:
                                vertex_line = lines[i].strip()
                                i += 1
                                if 'vertex' in vertex_line.lower():
                                    vertex_coords = self.getCoords(vertex_line)
                                    if vertex_coords:
                                        vertex = Point3D(vertex_coords[0], vertex_coords[1], vertex_coords[2])
                                        # 检查坐标是否合理
                                        if self._isReasonableCoordinate(vertex):
                                            vertices.append(vertex)
                                            vertices_read += 1
                                        else:
                                            print(f"警告: 发现不合理的坐标: {vertex}")

                            # 创建三角形
                            if len(vertices) == 3:
                                triangle = Triangle(vertices[0], vertices[1], vertices[2], N)
                                self.triangles.append(triangle)
                                triangle_count += 1

                            # 寻找 "endfacet"
                            found_endfacet = False
                            while i < len(lines) and not found_endfacet:
                                if 'endfacet' in lines[i].lower():
                                    found_endfacet = True
                                i += 1

                    print(f"使用编码 {encoding} 读取到 {triangle_count} 个三角形")

                    if len(self.triangles) > 0:
                        self._calculateBounds()
                        return True

                except UnicodeDecodeError:
                    print(f"编码 {encoding} 解码错误")
                    continue
                except Exception as e:
                    print(f"文本格式读取失败 (编码 {encoding}): {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            return False

        except Exception as ex:
            print(f"读取文本STL文件时出错: {ex}")
            import traceback
            traceback.print_exc()
            return False

    def _readStlFileBinary(self, filepath):
        """读取二进制STL文件"""
        try:
            with open(filepath, 'rb') as f:
                # 跳过80字节的头文件
                header = f.read(80)

                # 读取三角形数量
                num_triangles_data = f.read(4)
                if len(num_triangles_data) < 4:
                    return False

                # 尝试小端和大端字节序
                try:
                    num_triangles = struct.unpack('<I', num_triangles_data)[0]
                except:
                    num_triangles = struct.unpack('>I', num_triangles_data)[0]

                # 验证三角形数量是否合理
                file_size = os.path.getsize(filepath)
                expected_size = 84 + num_triangles * 50

                print(
                    f"二进制STL - 三角形数量: {num_triangles}, 期望文件大小: {expected_size}, 实际文件大小: {file_size}")

                if abs(expected_size - file_size) > 100:  # 允许100字节的误差
                    print(f"警告: 文件大小不匹配，可能不是有效的二进制STL文件")
                    # 但仍然尝试读取

                self.triangles = []
                valid_triangles = 0

                for i in range(num_triangles):
                    # 读取法向量（12字节）
                    normal_data = f.read(12)
                    if len(normal_data) < 12:
                        break

                    # 尝试小端和大端字节序读取顶点
                    vertices = []
                    valid_vertices = 0

                    for j in range(3):
                        vertex_data = f.read(12)
                        if len(vertex_data) < 12:
                            break

                        # 尝试小端字节序
                        try:
                            x, y, z = struct.unpack('<3f', vertex_data)
                            vertex = Point3D(x, y, z)
                            if self._isReasonableCoordinate(vertex):
                                vertices.append(vertex)
                                valid_vertices += 1
                            else:
                                # 尝试大端字节序
                                x, y, z = struct.unpack('>3f', vertex_data)
                                vertex = Point3D(x, y, z)
                                if self._isReasonableCoordinate(vertex):
                                    vertices.append(vertex)
                                    valid_vertices += 1
                        except:
                            continue

                    # 跳过属性字节计数（2字节）
                    f.read(2)

                    # 创建三角形
                    if len(vertices) == 3:
                        triangle = Triangle(vertices[0], vertices[1], vertices[2])
                        self.triangles.append(triangle)
                        valid_triangles += 1

                print(f"成功读取的三角形数量: {valid_triangles}")

                if valid_triangles > 0:
                    self._calculateBounds()
                    return True
                else:
                    return False

        except Exception as ex:
            print(f"读取二进制STL文件时出错: {ex}")
            import traceback
            traceback.print_exc()
            return False

    def _isReasonableCoordinate(self, point):
        """检查坐标是否合理（避免天文数字）"""
        # 合理的3D打印模型坐标通常在 -1000 到 1000 mm 范围内
        reasonable_range = 10000.0  # 10米范围应该足够大了
        return (abs(point.x) < reasonable_range and
                abs(point.y) < reasonable_range and
                abs(point.z) < reasonable_range and
                not math.isnan(point.x) and not math.isinf(point.x) and
                not math.isnan(point.y) and not math.isinf(point.y) and
                not math.isnan(point.z) and not math.isinf(point.z))

    def extractFromVtkStlReader(self, vtkStlReader):
        """从VTK Reader提取数据 """
        try:
            vtkStlReader.Update()

            poly_data = vtkStlReader.GetOutput()
            if poly_data is None:
                print("Error: VTK Output is None")
                return False

            points = poly_data.GetPoints()
            if points is None:
                print("Error: VTK Points is None (可能是空文件或路径错误)")
                return False

            polys = poly_data.GetPolys()
            polys.InitTraversal()
            self.triangles = []
            id_list = vtk.vtkIdList()

            while polys.GetNextCell(id_list):
                if id_list.GetNumberOfIds() == 3:
                    pt0 = points.GetPoint(id_list.GetId(0))
                    pt1 = points.GetPoint(id_list.GetId(1))
                    pt2 = points.GetPoint(id_list.GetId(2))
                    A = Point3D(pt0[0], pt0[1], pt0[2])
                    B = Point3D(pt1[0], pt1[1], pt1[2])
                    C = Point3D(pt2[0], pt2[1], pt2[2])

                    # 计算法向量
                    AB = A.pointTo(B)
                    AC = A.pointTo(C)
                    # 处理共线三角形导致的零向量问题
                    cross = AB.crossProduct(AC)
                    if cross.length() > 1e-6:
                        normal = cross.normalized()
                    else:
                        normal = Vector3D(0, 0, 1)

                    self.triangles.append(Triangle(A, B, C, normal))

            self._calculateBounds()
            return True
        except Exception as e:
            print(f"从VTK提取数据出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def getBounds(self):
        """获取模型6个方向边界极值"""
        return self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax

    def multiplied(self, m):
        """根据矩阵进行几何变换"""
        model = StlModel()
        for t in self.triangles:
            # 变换三角形顶点和法向量
            newA = t.A.multiplied(m)
            newB = t.B.multiplied(m)
            newC = t.C.multiplied(m)
            newN = t.N.multiplied(m)
            triangle = Triangle(newA, newB, newC, newN)
            model.triangles.append(triangle)

        model._calculateBounds()
        return model

    def rotated(self, a, b, c):
        """指定角度对模型旋转变换 (a,b,c 分别为绕 X,Y,Z 轴的弧度)"""
        mx = Matrix3D.createRotateMatrix(Vector3D(1, 0, 0), a)
        my = Matrix3D.createRotateMatrix(Vector3D(0, 1, 0), b)
        mz = Matrix3D.createRotateMatrix(Vector3D(0, 0, 1), c)

        m = mx * my * mz
        return self.multiplied(m)