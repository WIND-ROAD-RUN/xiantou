from enum import Enum, auto
from ImgProModule.Utility import DetectionRectangleInfo
from maix import  image

class Color:
    Red     = (255, 0, 0)
    Green   = (0, 255, 0)
    Blue    = (0, 0, 255)
    Yellow  = (255, 255, 0)
    Cyan    = (0, 255, 255)
    Magenta = (255, 0, 255)
    Black   = (0, 0, 0)
    White   = (255, 255, 255)
    Gray    = (128, 128, 128)
    Orange  = (255, 165, 0)
    Purple  = (128, 0, 128)
    Brown   = (165, 42, 42)
    Pink    = (255, 192, 203)
    Lime    = (0, 255, 128)
    Navy    = (0, 0, 128)
    Teal    = (0, 128, 128)
    Olive   = (128, 128, 0)
    Maroon  = (128, 0, 0)
    Silver  = (192, 192, 192)
    Gold    = (255, 215, 0)

class TextLocate(Enum):
    LeftTopIn = auto()
    LeftTopOut = auto()
    RightTopIn = auto()
    RightTopOut = auto()
    LeftBottomIn = auto()
    LeftBottomOut = auto()
    RightBottomIn = auto()
    RightBottomOut = auto()
    CenterIn = auto()

class ConfigDrawRect:
    def __init__(self):
        self.thickness = 1
        self.rectColor = Color.Green
        self.text = ""
        self.textColor = Color.Green
        self.fontSize = 3
        self.textLocate = TextLocate.LeftTopOut
        self.isRegion = False
        self.alpha = 0.3
        self.thresh = 0.5
        self.maxVal = 1.0
        self.hasFrame = True
        self.isDashed = False

class ImgPainterCom:
    def __init__(self):
        pass
    
    @staticmethod
    def drawRectOnImg(img:image,detectionRectangleInfo:DetectionRectangleInfo,cfg:ConfigDrawRect ):
        rectColor=image.Color.from_rgb(cfg.rectColor[0], cfg.rectColor[1], cfg.rectColor[2])
        textColor=image.Color.from_rgb(cfg.textColor[0], cfg.textColor[1], cfg.textColor[2])
        img.draw_rect(detectionRectangleInfo.leftTop.x, detectionRectangleInfo.leftTop.y, detectionRectangleInfo.width, detectionRectangleInfo.height, color = rectColor)
        img.draw_string(detectionRectangleInfo.centralX, detectionRectangleInfo.centralY, cfg.text, color = textColor)



