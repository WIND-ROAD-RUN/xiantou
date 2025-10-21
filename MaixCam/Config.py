import json
import os

class Config:
    def __init__(self):
        # 基本配置
        self.baojingshijian = 1000        # 报警时间，单位 ms，默认 1000
        self.ng_baojingshu = 3            # NG 报警数，单位 个，默认 3
        self.ng_yuzhi = 2                 # NG 阈值，单位 个，默认 2

        # 相机配置（新增）
        self.camera_exposure_us = 10000   # 相机曝光，单位 us，默认 10000
        self.camera_gain = 1              # 相机增益，单位 倍，默认 1

    def save(self, path):
        """
        将当前配置保存到文件 path（JSON 格式）。
        返回 True 表示成功，失败返回 False。
        """
        try:
            d = {
                "baojingshijian": self.baojingshijian,
                "ng_baojingshu": self.ng_baojingshu,
                "ng_yuzhi": self.ng_yuzhi,
                "camera_exposure_us": self.camera_exposure_us,
                "camera_gain": self.camera_gain,
            }
            dirn = os.path.dirname(path)
            if dirn and not os.path.exists(dirn):
                os.makedirs(dirn)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def load(self, path):
        """
        从文件 path 加载配置（JSON 格式）。
        返回 True 表示成功，失败返回 False（文件不存在或解析错误）。
        """
        try:
            if not os.path.exists(path):
                return False
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if "baojingshijian" in d: self.baojingshijian = d["baojingshijian"]
            if "ng_baojingshu" in d: self.ng_baojingshu = d["ng_baojingshu"]
            if "ng_yuzhi" in d: self.ng_yuzhi = d["ng_yuzhi"]
            if "camera_exposure_us" in d: self.camera_exposure_us = d["camera_exposure_us"]
            if "camera_gain" in d: self.camera_gain = d["camera_gain"]
            return True
        except Exception:
            return False

