from maix import nn
from ImgProModule.Utility import AIVisionCreateConfig, DetectionRectangleInfo, Point

class DetectImgProCom:
    def __init__(self, config=None):
        self.config = config if config else AIVisionCreateConfig()
        self.engine = nn.YOLOv5(model=self.config.model_path,dual_buff=self.config.dual_buff)

    def processImg(self, img):
        bboxes = self.engine.detect(img, conf_th=self.config.conf_threshold, iou_th=self.config.nms_threshold)
        results = []
        for obj in bboxes:
            left = obj.x
            top = obj.y
            right = obj.x + obj.w
            bottom = obj.y + obj.h
            score = obj.score
            class_id = obj.class_id
            leftTop = Point(left, top)
            rightTop = Point(right, top)
            rightBottom = Point(right, bottom)
            leftBottom = Point(left, bottom)
            area = obj.w * obj.h
            width= obj.w
            height=obj.h
            detection_info = DetectionRectangleInfo(
                leftTop, rightTop, rightBottom, leftBottom, score, class_id, area, centralX= (left + right) // 2, centralY= (top + bottom) // 2, width=width, height=height)
            results.append(detection_info)
        return results
