from GeomBase import*

class Triangle:
    def __init__(self,A, B, C, N = Vector3D(0,0,0)):
        self.A, self.B, self.C, self.N = A.clone(), B.clone(), C.clone(), N.clone()
        self.zs=[]

    def __str__(self):
        return f"Triangle\nA: {self.A}\nB: {self.B}\nC: {self.C}\nN: {self.N}"

    def zMinPnt(self): # 3个顶点中的Z方向最低点
        min_z = min(self.A.z, self.B.z, self.C.z)
        if self.A.z == min_z:
            return self.A
        elif self.B.z == min_z:
            return self.B
        else:
            return self.C

    def zMaxPnt(self): # 3个顶点中的Z方向最高点
        max_z = max(self.A.z, self.B.z, self.C.z)
        if self.A.z == max_z:
            return self.A
        elif self.B.z == max_z:
            return self.B
        else:
            return self.C

    def calcNormal(self): # 计算面片法向量
        AB = self.A.pointTo(self.B)
        AC = self.A.pointTo(self.C)
        normal = AB.crossProduct(AC).normalized()
        self.N = normal
        return normal