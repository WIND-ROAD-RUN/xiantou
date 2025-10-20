import json
import os

class Config:
    def __init__(self):
        self.jiange = 0
        self.yanshichufashijian = 0
        self.chufashijian = 0
        self.xiaodouyici = 0
        self.dadouyici = 0
        self.zongshu = 0

    def save(self, path):
        """
        将当前配置保存到文件 path（JSON 格式）。
        返回 True 表示成功，失败返回 False。
        """
        try:
            d = {
                "jiange": self.jiange,
                "yanshichufashijian": self.yanshichufashijian,
                "chufashijian": self.chufashijian,
                "xiaodouyici": self.xiaodouyici,
                "dadouyici": self.dadouyici,
                "zongshu": self.zongshu,
            }
            # 确保目录存在
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
            # 仅设置已知字段，避免注入未知属性
            if "jiange" in d: self.jiange = d["jiange"]
            if "yanshichufashijian" in d: self.yanshichufashijian = d["yanshichufashijian"]
            if "chufashijian" in d: self.chufashijian = d["chufashijian"]
            if "xiaodouyici" in d: self.xiaodouyici = d["xiaodouyici"]
            if "dadouyici" in d: self.dadouyici = d["dadouyici"]
            if "zongshu" in d: self.zongshu = d["zongshu"]
            return True
        except Exception:
            return False

