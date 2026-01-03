class Layer:
    def __init__(self, z):
        self.z = z # 当前层高度值
        self.segments = [] # 截交线段列表
        self.contours = [] # 多边形轮廓列表（封闭截交线）

        self.shellContours = []  # 轮廓填充内边界轮廓
        self.ffContours = []  # 密实填充区域轮廓 (Full Fill)
        self.sfContours = []  # 稀疏填充区域轮廓 (Sparse Fill)

        self.cpPaths = []  # 轮廓填充路径
        self.ffPaths = []  # 密实填充路径
        self.sfPaths = []  # 稀疏填充路径
        self.sptContours = []  # 支撑区域轮廓
        self.sptCpPaths = []  # 支撑轮廓路径
        self.sptDpPaths = []  # 支撑填充路径