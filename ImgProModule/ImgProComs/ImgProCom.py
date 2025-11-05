from ImgProModule.Yolov11Coms import DetectImgProCom
from ImgProModule.Utility import ProcessResult,ProcessResultIndexMap,ClassIDWithName
from ImgProModule.ImgProComs.ImgPainterCom import ImgPainterCom,ConfigDrawRect

class ImgProContext:
    def __init__(self):
        self.processResult = ProcessResult()
        self.processResultIndexMap = ProcessResultIndexMap()
        self.classIDWithName=ClassIDWithName()

class ImgProCom:
    def __init__(self, DetectImgProCom: DetectImgProCom):
        self.detector = DetectImgProCom
        self.context = ImgProContext()
    
    def run(self, img):
        self.context.processResult = self.processImg(img)
        self.context.processResultIndexMap = self.getProcessResultIndexMap(self.context.processResult)
        return self.context
    
    def processImg(self, img):
     return self.detector.processImg(img)

    def getProcessResultIndexMap(self, results :ProcessResult):
        index_map = ProcessResultIndexMap()
        for idx, rect in enumerate(results):
            if rect.classid not in index_map:
                index_map[rect.classid] = []
            index_map[rect.classid].append(idx)
        return index_map
    
    def getMaskImg(self,img):
        processResult=self.context.processResult
        for obj in processResult:
            cfg=ConfigDrawRect()
            if obj.classid in self.context.classIDWithName:
                cfg.text=self.context.classIDWithName[obj.classid]
            else:
                cfg.text=str(obj.classid)
            ImgPainterCom.drawRectOnImg(img,obj,cfg)

        return img
    
    def getMaskImgWithountText(self,img):
        processResult=self.context.processResult
        for obj in processResult:
            cfg=ConfigDrawRect()
            ImgPainterCom.drawRectOnImg(img,obj,cfg)

        return img
