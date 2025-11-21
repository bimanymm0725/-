class Layer:
    def __init__(self, z):
        self.z = z # 当前层高度值
        self.segments = [] # 截交线段列表
        self.contours = [] # 多边形轮廓列表（封闭截交线）