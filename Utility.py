import math

def makeListLinear(lists):
    """将多维列表转化为一维列表"""
    outList = []
    _makeListLinear(lists, outList)
    return outList

def _makeListLinear(inList, outList):
    """makeListLinear的依赖函数（递归实现）"""
    for a in inList:
        if type(a) != list:
            outList.append(a)
        else:
            _makeListLinear(a, outList)


def degToRad(deg):
    """角度转弧度"""
    return deg * math.pi / 180.0

def radToDeg(rad):
    """弧度转角度"""
    return rad * 180.0 / math.pi