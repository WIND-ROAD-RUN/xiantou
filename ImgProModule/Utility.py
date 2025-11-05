class AIVisionCreateConfig:
    def __init__(self):
        self.model_path = "/root/models/yolo11n.mud"
        self.conf_threshold = 0.3
        self.nms_threshold = 0.1
        self.dual_buff = True

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class DetectionRectangleInfo:
    def __init__(self, leftTop: Point,
                 rightTop: Point,
                 rightBottom: Point,
                 leftBottom: Point,
                 score: float,
                 classid: int,
                 area: int,
                 centralX:int,
                 centralY:int,
                 width:int,
                 height:int):
        self.leftTop = leftTop
        self.rightTop = rightTop
        self.rightBottom = rightBottom
        self.leftBottom = leftBottom
        self.score = score
        self.classid = classid
        self.area = area
        self.centralX=centralX
        self.centralY=centralY
        self.width=width
        self.height=height

    def __str__(self):
        return (f"DetectionRectangleInfo("
                f"classid={self.classid}, score={self.score:.2f}, area={self.area}, "
                f"center=({self.centralX},{self.centralY}), size=({self.width}x{self.height}), "
                f"leftTop=({self.leftTop.x},{self.leftTop.y}), "
                f"rightTop=({self.rightTop.x},{self.rightTop.y}), "
                f"rightBottom=({self.rightBottom.x},{self.rightBottom.y}), "
                f"leftBottom=({self.leftBottom.x},{self.leftBottom.y}))")

    __repr__ = __str__

    
ProcessResult=list[DetectionRectangleInfo]

ProcessResultIndexMap=dict[int,list[int]]

ClassIDWithName=dict[int,str]

