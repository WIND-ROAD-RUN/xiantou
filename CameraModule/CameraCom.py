from maix import camera, image

class CameraCom:
    def __init__(self, width=640, height=480, fps=60, fmt=image.Format.FMT_RGB888, buff_num=2):
        """
        初始化摄像头
        :param width: 图像宽度
        :param height: 图像高度
        :param fps: 帧率
        :param fmt: 图像格式
        :param buff_num: 缓存数量
        """
        self.cam = camera.Camera(width, height, fmt, fps=fps, buff_num=buff_num)

    def set_resolution(self, width, height):
        """设置分辨率"""
        self.cam.set_resolution(width=width, height=height)

    def set_fps(self, fps):
        """设置帧率"""
        self.cam.set_fps(fps)

    def skip_frames(self, n=30):
        """跳过开头的n帧"""
        self.cam.skip_frames(n)

    def set_exposure(self, value):
        """设置曝光时间（us）"""
        self.cam.exposure(value)

    def set_gain(self, value):
        """设置增益"""
        self.cam.gain(value)

    def set_awb_manual(self, gains):
        """
        设置手动白平衡
        :param gains: [r, gr, gb, b] 增益值列表
        """
        self.cam.awb_mode(camera.AwbMode.Manual)
        self.cam.set_wb_gain(gains)

    def set_awb_auto(self):
        """设置自动白平衡"""
        self.cam.awb_mode(camera.AwbMode.Auto)

    def set_luma(self, value):
        """设置亮度"""
        self.cam.luma(value)

    def set_contrast(self, value):
        """设置对比度"""
        self.cam.constrast(value)

    def set_saturation(self, value):
        """设置饱和度"""
        self.cam.saturation(value)

    def read(self):
        """读取一帧图像"""
        return self.cam.read()

    def read_raw(self):
        """读取原始raw图像"""
        return self.cam.read_raw()

    def lens_corr(self, img, strength=1.5):
        """图像畸变矫正"""
        return img.lens_corr(strength=strength)