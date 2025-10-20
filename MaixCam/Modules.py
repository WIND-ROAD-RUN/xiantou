from CameraModule.CameraCom import CameraCom
from ImgProModule.Utility import AIVisionCreateConfig,ClassIDWithName
from ImgProModule.Yolov11Coms.DetectImgProCom import DetectImgProCom
from ImgProModule.ImgProComs.ImgProCom import ImgProCom
from maix import  display, image, app
from Mt.KeyMonitor import KeyMonitor
from MaixCam.Config import Config
from MaixCam.Utilty import UtiltyPath
from Mt.GPIOBlink import GPIOBlink
import os

class Modules:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Modules, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.data = {}
        self._initialized = True
        self.ini()

    def defineVar(self):
        classIDWithName=ClassIDWithName()
        classIDWithName[0]=r"线头"
        return classIDWithName
    
    def readConfig(self):
        self.paths=UtiltyPath()
        cfg_path = self.paths.config_path
        cfg_dir = os.path.dirname(cfg_path)

        # 确保目录存在
        if cfg_dir and not os.path.exists(cfg_dir):
            try:
                os.makedirs(cfg_dir)
            except Exception:
                pass

        # 创建 Config 实例
        self.config = Config()

        # 如果文件存在则尝试加载，加载失败则覆盖写入默认配置
        if os.path.exists(cfg_path):
            try:
                ok = self.config.load(cfg_path)
                if not ok:
                    # load 返回 False（解析或内容问题），保存当前默认配置
                    try:
                        self.config.save(cfg_path)
                    except Exception:
                        pass
            except Exception:
                try:
                    self.config.save(cfg_path)
                except Exception:
                    pass
        else:
            try:
                self.config.save(cfg_path)
            except Exception:
                pass

    def ini(self):
        self.readConfig()

        engineConfig=AIVisionCreateConfig()
        engineConfig.model_path=Modules().paths.model_path
        print("model_path:",engineConfig.model_path)
        
        self.engineCom=DetectImgProCom(engineConfig)
        self.imgProCom=ImgProCom(self.engineCom)
        #self.camera=CameraCom(width=self.engineCom.engine.input_width(),height=self.engineCom.engine.input_height(),fmt=self.engineCom.engine.input_format())
        self.camera=CameraCom(width=640,height=480,fmt=self.engineCom.engine.input_format(),buff_num=1)
        self.camera.set_exposure(100)
        self.camera.set_gain(0)

        self.imgProCom.context.classIDWithName=self.defineVar()
        self.disDebug=None
        self.disRelease=None
        self.countLabel=None

        self.warning = GPIOBlink(pin_name=self.paths.pin_name, gpio_name=self.paths.gpio_name, initial=0)
        self.warning.setLow()


        self.keyMonotor=KeyMonitor.instance()


    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = Modules()
        return cls._instance