import math

epsilon = 1.0e-7
epsilonSquare = epsilon * epsilon
pi=3.1415927

class Point3D:
    def __init__(self,x=0.0,y=0.0,z=0.0,w=1.0):
        self.x,self.y,self.z,self.w=x,y,z,w

    def __str__(self):
        return f'Point3D:({self.x},{self.y},{self.z})'

    def clone(self):
        return Point3D(self.x,self.y,self.z,self.w)

    def pointTo(self,other):
        return Vector3D(other.x-self.x,other.y-self.y,other.z-self.z)

    def translate(self,vec):
        self.x += vec.dx
        self.y += vec.dy
        self.z += vec.dz

    def translated(self,vec):
        return Point3D(self.x+vec.dx,self.y+vec.dy,self.z+vec.dz)

    def distance(self,other):
        return math.sqrt(self.distanceSquare(other))

    def distanceSquare(self,other):
        return self.pointTo(other).lengthSquare()

    def middle(self,other):
        return Point3D((self.x+other.x)/2.0,(self.y+other.y)/2.0,(self.z+other.z)/2.0)

    def isCoincide(self,other):
        return self.distanceSquare(other)<epsilonSquare

    def isIdentical(self,other):
        return self.x==other.x and self.y==other.y and self.z==other.z

    def multiplied(self,m):
        x = self.x * m.a[0][0] + self.y * m.a[1][0] + self.z * m.a[2][0] + self.w * m.a[3][0]
        y = self.x * m.a[0][1] + self.y * m.a[1][1] + self.z * m.a[2][1] + self.w * m.a[3][1]
        z = self.x * m.a[0][2] + self.y * m.a[1][2] + self.z * m.a[2][2] + self.w * m.a[3][2]
        return Point3D(x, y, z)

    def __add__(self, vec): #+
        return self.translated(vec)

    def __sub__(self,other): #-
        if isinstance(other,Point3D):
            return other.pointTo(self)
        elif isinstance(other,Vector3D):
            return self + other.reversed()
        else:
            print("error")

    def __mul__(self, m): #*
        return self.multiplied(m)

    pass

class Vector3D:
    def __init__(self,dx=0.0,dy=0.0,dz=0.0,dw=0.0):
        self.dx,self.dy,self.dz,self.dw=dx,dy,dz,dw

    def __str__(self):
        return f'Vector3D:({self.dx},{self.dy},{self.dz})'

    def reverse(self):
        self.dx = -self.dx
        self.dy = -self.dy
        self.dz = -self.dz

    def reversed(self):
        return Vector3D(-self.dx, -self.dy, -self.dz)

    def clone(self):
        return Vector3D(self.dx,self.dy,self.dz,self.dw)

    def dotProduct(self,other):
        return self.dx*other.dx + self.dy*other.dy + self.dz*other.dz

    def crossProduct(self, other):
        return Vector3D(self.dy*other.dz-other.dy*self.dz,-(self.dx*other.dz-other.dx*self.dz),self.dx*other.dy-other.dx*self.dy)

    def amplify(self, f):
        self.dx *= f
        self.dy *= f
        self.dz *= f

    def amplified(self, f):
        return Vector3D(self.dx*f,self.dy*f,self.dz*f)

    def length(self):
        return math.sqrt(self.lengthSquare())

    def lengthSquare(self):
        return self.dx*self.dx + self.dy*self.dy + self.dz*self.dz

    def normalize(self):
        if self.length()!=0 :
            self.dx /= math.sqrt(self.length())
            self.dy /= math.sqrt(self.length())
            self.dz /= math.sqrt(self.length())
        else:
            print("error: cannot normalize zero vector")

    def normalized(self):
        if self.length()!=0 :
            return Vector3D(self.dx/math.sqrt(self.length()),self.dy/math.sqrt(self.length()),self.dz/math.sqrt(self.length()))
        else:
            print("error: cannot normalize zero vector")
            return Vector3D()

    def isZeroVector(self) -> bool:
        return self.lengthSquare() <epsilonSquare

    def multiplied(self, m):
        dx=self.dx * m.a[0][0] + self.dy * m.a[1][0] + self.dz * m.a[2][0] + self.dw * m.a[3][0]
        dy=self.dx * m.a[0][1] + self.dy * m.a[1][1] + self.dz * m.a[2][1] + self.dw * m.a[3][1]
        dz=self.dx * m.a[0][2] + self.dy * m.a[1][2] + self.dz * m.a[2][2] + self.dw * m.a[3][2]
        dw=self.dx * m.a[0][3] + self.dy * m.a[1][3] + self.dz * m.a[2][3] + self.dw * m.a[3][3]
        return Vector3D(dx, dy, dz, dw)

    def isParallel(self, other):
        return self.crossProduct(other).isZeroVector()

    def getAngle(self, vec):  # 0 ~PI
        if self.isZeroVector() or vec.isZeroVector():
            return 0.0
        cos=self.dotProduct(vec)/(self.length()*vec.length())
        return math.acos(cos)

    def getAngle2D(self):  # 0 ~ 2PI, On XY Plane
        if self.isZeroVector():
            return 0.0
        angle= math.atan2(self.dy, self.dx)
        return angle if angle>=0 else angle+2*pi

    def getOrthoVector2D(self):  # On XY Plane
        return Vector3D(-self.dy, self.dx, 0.0)

    def __add__(self, other):
        return Vector3D(self.dx + other.dx, self.dy + other.dy, self.dz + other.dz)

    def __sub__(self, other):
        return Vector3D(self.dx - other.dx, self.dy - other.dy, self.dz - other.dz)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self.amplified(other)
        elif isinstance(other, Matrix3D):
            return self.multiplied(other)
        else:
            print("error: unsupported multiplication")
            return None

class Matrix3D:
    def __init__(self):
        self.a =[[1.0,0.0,0.0,0.0],
                 [0.0,1.0,0.0,0.0],
                 [0.0,0.0,1.0,0.0],
                 [0.0,0.0,0.0,1.0]]

    def __str__(self):
        result = ''
        for i in range(4):
            result += f"[{self.a[i][0]:.1f}, {self.a[i][1]:.1f}, {self.a[i][2]:.1f}, {self.a[i][3]:.1f}]\n"
        return result

    def makeIdentical(self):
        self.a = [[1.0, 0.0, 0.0, 0.0],
                  [0.0, 1.0, 0.0, 0.0],
                  [0.0, 0.0, 1.0, 0.0],
                  [0.0, 0.0, 0.0, 1.0]]

    def multiplied(self, other):
        result = Matrix3D()
        for i in range(4):
            for j in range(4):
                result.a[i][j] = (self.a[i][0] * other.a[0][j] +
                                  self.a[i][1] * other.a[1][j] +
                                  self.a[i][2] * other.a[2][j] +
                                  self.a[i][3] * other.a[3][j])
        return result

    def getDeterminant(self):
        a = self.a
        det = (a[0][0] * (a[1][1] * (a[2][2] * a[3][3] - a[2][3] * a[3][2]) -
               a[1][2] * (a[2][1] * a[3][3] - a[2][3] * a[3][1]) +
               a[1][3] * (a[2][1] * a[3][2] - a[2][2] * a[3][1])) -
              a[0][1] * (a[1][0] * (a[2][2] * a[3][3] - a[2][3] * a[3][2]) -
               a[1][2] * (a[2][0] * a[3][3] - a[2][3] * a[3][0]) +
               a[1][3] * (a[2][0] * a[3][2] - a[2][2] * a[3][0])) +
              a[0][2] * (a[1][0] * (a[2][1] * a[3][3] - a[2][3] * a[3][1]) -
               a[1][1] * (a[2][0] * a[3][3] - a[2][3] * a[3][0]) +
               a[1][3] * (a[2][0] * a[3][1] - a[2][1] * a[3][0])) -
              a[0][3] * (a[1][0] * (a[2][1] * a[3][2] - a[2][2] * a[3][1]) -
               a[1][1] * (a[2][0] * a[3][2] - a[2][2] * a[3][0]) +
               a[1][2] * (a[2][0] * a[3][1] - a[2][1] * a[3][0])))
        return det

    def getReverseMatrix(self):
        det = self.getDeterminant()
        if abs(det) < epsilon:
            print("error: matrix is singular")
            return None

        result = Matrix3D()
        a = self.a

        result.a[0][0] = (a[1][1] * (a[2][2] * a[3][3] - a[2][3] * a[3][2]) -
                          a[1][2] * (a[2][1] * a[3][3] - a[2][3] * a[3][1]) +
                          a[1][3] * (a[2][1] * a[3][2] - a[2][2] * a[3][1])) / det

        result.a[0][1] = (-(a[0][1] * (a[2][2] * a[3][3] - a[2][3] * a[3][2]) -
                            a[0][2] * (a[2][1] * a[3][3] - a[2][3] * a[3][1]) +
                            a[0][3] * (a[2][1] * a[3][2] - a[2][2] * a[3][1]))) / det

        result.a[0][2] = (a[0][1] * (a[1][2] * a[3][3] - a[1][3] * a[3][2]) -
                          a[0][2] * (a[1][1] * a[3][3] - a[1][3] * a[3][1]) +
                          a[0][3] * (a[1][1] * a[3][2] - a[1][2] * a[3][1])) / det

        result.a[0][3] = (-(a[0][1] * (a[1][2] * a[2][3] - a[1][3] * a[2][2]) -
                            a[0][2] * (a[1][1] * a[2][3] - a[1][3] * a[2][1]) +
                            a[0][3] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]))) / det

        result.a[1][0] = (-(a[1][0] * (a[2][2] * a[3][3] - a[2][3] * a[3][2]) -
                            a[1][2] * (a[2][0] * a[3][3] - a[2][3] * a[3][0]) +
                            a[1][3] * (a[2][0] * a[3][2] - a[2][2] * a[3][0]))) / det

        result.a[1][1] = (a[0][0] * (a[2][2] * a[3][3] - a[2][3] * a[3][2]) -
                          a[0][2] * (a[2][0] * a[3][3] - a[2][3] * a[3][0]) +
                          a[0][3] * (a[2][0] * a[3][2] - a[2][2] * a[3][0])) / det

        result.a[1][2] = (-(a[0][0] * (a[1][2] * a[3][3] - a[1][3] * a[3][2]) -
                            a[0][2] * (a[1][0] * a[3][3] - a[1][3] * a[3][0]) +
                            a[0][3] * (a[1][0] * a[3][2] - a[1][2] * a[3][0]))) / det

        result.a[1][3] = (a[0][0] * (a[1][2] * a[2][3] - a[1][3] * a[2][2]) -
                          a[0][2] * (a[1][0] * a[2][3] - a[1][3] * a[2][0]) +
                          a[0][3] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])) / det

        result.a[2][0] = (a[1][0] * (a[2][1] * a[3][3] - a[2][3] * a[3][1]) -
                          a[1][1] * (a[2][0] * a[3][3] - a[2][3] * a[3][0]) +
                          a[1][3] * (a[2][0] * a[3][1] - a[2][1] * a[3][0])) / det

        result.a[2][1] = (-(a[0][0] * (a[2][1] * a[3][3] - a[2][3] * a[3][1]) -
                            a[0][1] * (a[2][0] * a[3][3] - a[2][3] * a[3][0]) +
                            a[0][3] * (a[2][0] * a[3][1] - a[2][1] * a[3][0]))) / det

        result.a[2][2] = (a[0][0] * (a[1][1] * a[3][3] - a[1][3] * a[3][1]) -
                          a[0][1] * (a[1][0] * a[3][3] - a[1][3] * a[3][0]) +
                          a[0][3] * (a[1][0] * a[3][1] - a[1][1] * a[3][0])) / det

        result.a[2][3] = (-(a[0][0] * (a[1][1] * a[2][3] - a[1][3] * a[2][1]) -
                            a[0][1] * (a[1][0] * a[2][3] - a[1][3] * a[2][0]) +
                            a[0][3] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))) / det

        result.a[3][0] = (-(a[1][0] * (a[2][1] * a[3][2] - a[2][2] * a[3][1]) -
                            a[1][1] * (a[2][0] * a[3][2] - a[2][2] * a[3][0]) +
                            a[1][2] * (a[2][0] * a[3][1] - a[2][1] * a[3][0]))) / det

        result.a[3][1] = (a[0][0] * (a[2][1] * a[3][2] - a[2][2] * a[3][1]) -
                          a[0][1] * (a[2][0] * a[3][2] - a[2][2] * a[3][0]) +
                          a[0][2] * (a[2][0] * a[3][1] - a[2][1] * a[3][0])) / det

        result.a[3][2] = (-(a[0][0] * (a[1][1] * a[3][2] - a[1][2] * a[3][1]) -
                            a[0][1] * (a[1][0] * a[3][2] - a[1][2] * a[3][0]) +
                            a[0][2] * (a[1][0] * a[3][1] - a[1][1] * a[3][0]))) / det

        result.a[3][3] = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) -
                          a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0]) +
                          a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])) / det

        return result

    @staticmethod
    def createTranslateMatrix(dx, dy, dz):
        m = Matrix3D()
        m.a[3][0] = dx
        m.a[3][1] = dy
        m.a[3][2] = dz
        return m

    @staticmethod
    def createScaleMatrix(sx, sy, sz):
        m = Matrix3D()
        m.a[0][0] = sx
        m.a[1][1] = sy
        m.a[2][2] = sz
        return m

    @staticmethod
    def createRotateMatrix(axis, angle):
        m = Matrix3D()
        axis = axis.normalized()
        x, y, z = axis.dx, axis.dy, axis.dz
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        one_minus_cos = 1 - cos_a

        m.a[0][0] = cos_a + x * x * one_minus_cos
        m.a[0][1] = x * y * one_minus_cos - z * sin_a
        m.a[0][2] = x * z * one_minus_cos + y * sin_a

        m.a[1][0] = y * x * one_minus_cos + z * sin_a
        m.a[1][1] = cos_a + y * y * one_minus_cos
        m.a[1][2] = y * z * one_minus_cos - x * sin_a

        m.a[2][0] = z * x * one_minus_cos - y * sin_a
        m.a[2][1] = z * y * one_minus_cos + x * sin_a
        m.a[2][2] = cos_a + z * z * one_minus_cos

        return m

    @staticmethod
    def createMirrorMatrix(point, normal):
        m = Matrix3D()
        normal = normal.normalized()
        a, b, c = normal.dx, normal.dy, normal.dz
        d = - (a * point.x + b * point.y + c * point.z)

        m.a[0][0] = 1 - 2 * a * a
        m.a[0][1] = -2 * a * b
        m.a[0][2] = -2 * a * c
        m.a[0][3] = -2 * a * d

        m.a[1][0] = -2 * a * b
        m.a[1][1] = 1 - 2 * b * b
        m.a[1][2] = -2 * b * c
        m.a[1][3] = -2 * b * d

        m.a[2][0] = -2 * a * c
        m.a[2][1] = -2 * b * c
        m.a[2][2] = 1 - 2 * c * c
        m.a[2][3] = -2 * c * d

        m.a[3][3] = 1

        return m

    def __mul__(self, other):
        if isinstance(other, Matrix3D):
            return self.multiplied(other)
        else:
            print("error: unsupported multiplication")
            return None

    def __add__(self, other):
        if isinstance(other, Matrix3D):
            result = Matrix3D()
            for i in range(4):
                for j in range(4):
                    result.a[i][j] = self.a[i][j] + other.a[i][j]
            return result
        else:
            print("error: unsupported addition")
            return None

    def __sub__(self, other):
        if isinstance(other, Matrix3D):
            result = Matrix3D()
            for i in range(4):
                for j in range(4):
                    result.a[i][j] = self.a[i][j] - other.a[i][j]
            return result
        else:
            print("error: unsupported subtraction")
            return None

if __name__=='__main__':
    pt= Point3D(1.0,2.0,3.0)
    m=Matrix3D()
    print(m)