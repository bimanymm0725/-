from GeomBase import *
from GeomBase import Point3D
from IntersectStl_sweep import SweepPlane
from Layer import Layer
from Polyline import Polyline
from Segment import Segment
from GeomAlgo import adjustPolygonDirs


class TVertex:
    def __init__(self, pnt3d, digits=7):  # 从 Point3D 对象转化，保留固定小数位数
        self.x = round(pnt3d.x, digits)  # 顶点的x、y、z坐标
        self.y = round(pnt3d.y, digits)
        self.z = round(pnt3d.z, digits)
        self.faces = []

    def toTuple(self):  # 将顶点转化为元组
        return self.x, self.y, self.z

    def toPoint3D(self):  # 将顶点转化为Point3D对象
        return Point3D(self.x, self.y, self.z)

    def isSmaller(self, other):  # 比较两个点大小，字典序
        if self.x < other.x:
            return True
        elif self.x == other.x and self.y < other.y:
            return True
        elif self.x == other.x and self.y == other.y and self.z < other.z:
            return True
        return False


class TEdge:  # 定义TEdge类
    def __init__(self, tA, tB):  # 从两个TVertex点初始化
        self.A, self.B = tA, tB  # 两个顶点引用 A、B
        self.F = None  # 所从属的面片引用 F
        self.OE = None  # 对边引用 OE

    def toTuple(self):  # 将边转化为元组（6维）
        if self.A.isSmaller(self.B):
            return self.A.x, self.A.y, self.A.z, self.B.x, self.B.y, self.B.z
        else:
            return self.B.x, self.B.y, self.B.z, self.A.x, self.A.y, self.A.z

    def intersect(self, z):  # 边和z平面求交，返回交点
        if min(self.A.z, self.B.z) > z or max(self.A.z, self.B.z) < z:
            return None  # 如果边高于或低于z，无交点
        elif self.A.z == self.B.z == z:
            return None  # 如果边位于z平面，无交点
        else:
            if z == self.A.z:
                return self.A.toPoint3D()
            else:
                ratio = (z - self.A.z) / (self.B.z - self.A.z)  # 根据z比例计算
                vec = self.A.toPoint3D().pointTo(self.B.toPoint3D()).amplified(ratio)
                pnt = self.A.toPoint3D() + vec
                return pnt


class TFace():  # 定义TFace类
    def __init__(self, tA, tB, tC, te1, te2, te3):  # 初始化函数
        self.A, self.B, self.C = tA, tB, tC  # 顶点引用A、B、C
        self.E1, self.E2, self.E3 = te1, te2, te3  # 半边引用 E1、E2、E3
        self.used = False  # 面片是否被使用过

    def zMin(self):
        return min(self.A.z, self.B.z, self.C.z)  # 获取面片Z方向最低点

    def zMax(self):
        return max(self.A.z, self.B.z, self.C.z)  # 获取面片Z方向最高点

    def intersect(self, z):  # 面片和截平面求交
        if self.zMin() > z or self.zMax() < z:
            return None, None, None  # 如果面片高于或低于截平面，无交点
        elif self.A.z == self.B.z == self.C.z == z:
            return None, None, None  # 如果面片和截平面重合，无交点

        # 计算三条半边与截平面的交点
        c1 = self.E1.intersect(z)
        c2 = self.E2.intersect(z)
        c3 = self.E3.intersect(z)

        # 情况1：两个交点都在半边上
        if c1 is not None and c2 is not None and c3 is None:
            if not c1.isCoincide(c2):
                segment = Segment(c1, c2)
                return segment, [self.E1, self.E2], None
        elif c1 is not None and c3 is not None and c2 is None:
            if not c1.isCoincide(c3):
                segment = Segment(c1, c3)
                return segment, [self.E1, self.E3], None
        elif c2 is not None and c3 is not None and c1 is None:
            if not c2.isCoincide(c3):
                segment = Segment(c2, c3)
                return segment, [self.E2, self.E3], None

        # 情况2：一个交点在半边上，一个交点在顶点上
        # 检查顶点是否在截平面上
        vertex_on_plane = None
        if abs(self.A.z - z) < epsilon:
            vertex_on_plane = self.A
        elif abs(self.B.z - z) < epsilon:
            vertex_on_plane = self.B
        elif abs(self.C.z - z) < epsilon:
            vertex_on_plane = self.C

        if vertex_on_plane is not None:
            # 找到与顶点相连且与平面相交的半边
            edge_with_intersection = None
            edge_intersection_point = None

            if c1 is not None and not c1.isCoincide(vertex_on_plane.toPoint3D()):
                edge_with_intersection = self.E1
                edge_intersection_point = c1
            elif c2 is not None and not c2.isCoincide(vertex_on_plane.toPoint3D()):
                edge_with_intersection = self.E2
                edge_intersection_point = c2
            elif c3 is not None and not c3.isCoincide(vertex_on_plane.toPoint3D()):
                edge_with_intersection = self.E3
                edge_intersection_point = c3

            if edge_with_intersection is not None:
                segment = Segment(edge_intersection_point, vertex_on_plane.toPoint3D())
                return segment, [edge_with_intersection], vertex_on_plane

        return None, None, None


class TModel:
    def __init__(self, stlModel):
        self.vxDic, self.egDic = {}, {}
        self.faces = []
        self.stlModel = stlModel
        self.createTModel()

    def createTModel(self):
        for t in self.stlModel.triangles:
            A, B, C = TVertex(t.A), TVertex(t.B), TVertex(t.C)

            # 确保顶点在字典中
            a_key = A.toTuple()
            b_key = B.toTuple()
            c_key = C.toTuple()

            if a_key not in self.vxDic:
                self.vxDic[a_key] = A
            if b_key not in self.vxDic:
                self.vxDic[b_key] = B
            if c_key not in self.vxDic:
                self.vxDic[c_key] = C

            tA = self.vxDic[a_key]
            tB = self.vxDic[b_key]
            tC = self.vxDic[c_key]

            e1, e2, e3 = TEdge(tA, tB), TEdge(tB, tC), TEdge(tC, tA)

            # 建立边字典
            e1_key = e1.toTuple()
            e2_key = e2.toTuple()
            e3_key = e3.toTuple()

            if e1_key not in self.egDic:
                self.egDic[e1_key] = []
            self.egDic[e1_key].append(e1)

            if e2_key not in self.egDic:
                self.egDic[e2_key] = []
            self.egDic[e2_key].append(e2)

            if e3_key not in self.egDic:
                self.egDic[e3_key] = []
            self.egDic[e3_key].append(e3)

            f = TFace(tA, tB, tC, e1, e2, e3)

            tA.faces.append(f)
            tB.faces.append(f)
            tC.faces.append(f)

            e1.F = f
            e2.F = f
            e3.F = f

            self.faces.append(f)

        # 建立对边关系
        for edge_list in self.egDic.values():
            if len(edge_list) == 2:
                edge_list[0].OE = edge_list[1]
                edge_list[1].OE = edge_list[0]


class TopoSlicer:
    def __init__(self, stlModel, layerThk):
        self.stlModel = stlModel
        self.layerThk = layerThk
        self.topModel = TModel(stlModel)
        self.layers = []
        self.current_face = None  # 用于追踪当前面片
        self.slice()

    def findSeedFace(self, faces):
        """从扫描平面收集的面片中寻找种子面片"""
        for face in faces:
            if not face.used:
                return face
        return None

    def findNextFace(self, edges, node):
        """寻找目标邻面"""
        # 情况1：两个交点都在半边上
        if edges and len(edges) == 2 and node is None:
            # 按照课件第48页的优化策略，先检查 e1 的邻面
            if edges[1].OE is not None and edges[1].OE.F is not None:
                next_face = edges[1].OE.F
                if not next_face.used:
                    return next_face

            # 再检查 e0 的邻面
            if edges[0].OE is not None and edges[0].OE.F is not None:
                next_face = edges[0].OE.F
                if not next_face.used:
                    return next_face

        # 情况2：一个交点在半边上，一个交点在顶点上
        elif edges and len(edges) == 1 and node is not None:
            # 首先检查半边的对边所在面片
            if edges[0].OE is not None and edges[0].OE.F is not None:
                next_face = edges[0].OE.F
                if not next_face.used:
                    return next_face

            # 如果对边面片已使用，则在顶点相邻面片中寻找（课件第41页情况b）
            if node is not None and hasattr(node, 'faces'):
                for adjacent_face in node.faces:
                    if adjacent_face.used or adjacent_face == self.current_face:
                        continue

                    # 检查相邻面片是否与截平面相交
                    seg, adj_edges, adj_node = adjacent_face.intersect(node.z)
                    if seg is not None:
                        return adjacent_face

        return None

    def createLayerContours(self, z, faces):
        """拓扑对当前高度截平面做截交，输出 layer（切片轮廓）"""
        layer = Layer(z)

        # 重置所有面片的使用状态
        for face in faces:
            face.used = False

        # 外层循环：寻找种子面片
        while True:
            seed_face = self.findSeedFace(faces)
            if seed_face is None:
                break  # 没有更多种子面片，退出

            contour = Polyline()
            current_face = seed_face
            self.current_face = current_face  # 设置当前面片

            # 内层循环：追踪轮廓
            iteration_count = 0
            max_iterations = len(faces) * 10  # 防止无限循环

            while iteration_count < max_iterations:
                iteration_count += 1

                # 计算当前面片与截平面的交线
                seg, edges, node = current_face.intersect(z)

                # 标记当前面片为已使用
                current_face.used = True

                # 检查退出条件
                if seg is None:
                    break  # 当前面片与截平面不相交

                # 将线段添加到轮廓
                contour.appendSegment(seg)

                # 检查轮廓是否封闭
                if contour.isClosed():
                    break

                # 寻找下一个面片
                next_face = self.findNextFace(edges, node)
                if next_face is None:
                    break  # 无法找到下一个面片

                current_face = next_face
                self.current_face = current_face  # 更新当前面片

            # 保存有效的轮廓
            if contour.count() >= 3:
                layer.contours.append(contour)

        return layer

    def getLayerHeights(self):
        """生成切片层高列表"""
        xMin, xMax, yMin, yMax, zMin, zMax = self.stlModel.getBounds()
        zs = []
        z = zMin + self.layerThk
        while z < zMax:
            zs.append(z)
            z += self.layerThk
        return zs

    def adjustContourDirections(self, contours):
        """调整轮廓方向：外轮廓逆时针，内轮廓顺时针"""
        adjustPolygonDirs(contours)

    def slice(self):
        """在扫描平面法框架下切片"""
        # 对拓扑面片按最低点排序
        self.topModel.faces.sort(key=lambda face: face.zMin())

        # 生成层高列表
        zs = self.getLayerHeights()

        # 初始化扫描平面
        k = 0  # 面片遍历起始序号
        sweep = SweepPlane()

        # 遍历所有层高
        for z in zs:
            # 1. 移除扫描平面中不再相关的面片
            for i in range(len(sweep.triangles) - 1, -1, -1):
                if z > sweep.triangles[i].zMax():
                    del sweep.triangles[i]

            # 2. 向扫描平面添加新的相关面片
            for i in range(k, len(self.topModel.faces)):
                face = self.topModel.faces[i]
                if face.zMin() <= z <= face.zMax():
                    sweep.triangles.append(face)
                elif face.zMin() > z:
                    k = i  # 记录位置，下次从这里开始遍历
                    break

            # 3. 创建当前层的切片轮廓
            layer = self.createLayerContours(z, sweep.triangles)

            # 4. 调整轮廓方向（外轮廓逆时针，内轮廓顺时针）
            if layer.contours:
                self.adjustContourDirections(layer.contours)

            self.layers.append(layer)