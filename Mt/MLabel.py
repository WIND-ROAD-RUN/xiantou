from maix import image
from Mt.MWidget import MWidget

class MLabel(MWidget):
    def __init__(self, text, x=0, y=0, w=None, h=None, color=None, parent=None):
        if w is None or h is None:
            size = image.string_size(text)
            w = w or (size.width() + 4)
            h = h or (size.height() + 4)
        super().__init__(x, y, w, h, parent)
        self._text = text
        self.color = color or image.Color.from_rgb(0, 0, 0)
        self._image = None   # 新增：用于保存要绘制的图片

    def setText(self, text):
        self._text = text

    def text(self):
        return self._text

    # 新增：设置要显示的图片（传入 maix.image.Image 对象）
    def setImage(self, img):
        self._image = img
        # 可选：如果标签未指定宽高，则自动根据图片大小调整
        if (self.w == 0 or self.h == 0) and hasattr(img, "width") and hasattr(img, "height"):
            try:
                iw = img.width()
                ih = img.height()
                if iw and ih:
                    self.w = iw
                    self.h = ih
            except Exception:
                pass

    def clearImage(self):
        self._image = None

    def paintEvent(self, img):
        if not self.isVisible():
            return
        # 如果设置了图片，则绘制图片；否则绘制文本
        if self._image is not None:
            try:
                # 优先尝试图片对象的 resize 方法
                scaled = None
                try:
                    if hasattr(self._image, "resize"):
                        scaled = self._image.resize(self.w, self.h)
                    # 其次尝试模块级的 resize 接口
                    elif hasattr(image, "resize"):
                        scaled = image.resize(self._image, self.w, self.h)
                    else:
                        scaled = self._image
                except Exception:
                    scaled = self._image

                if scaled is None:
                    scaled = self._image

                # 绘制缩放后的图片，兼容 draw_image / draw_picture
                try:
                    img.draw_image(self.x, self.y, scaled)
                except Exception:
                    try:
                        img.draw_picture(self.x, self.y, scaled)
                    except Exception:
                        # 最后兜底：直接不绘制图片，改为绘制文本以免抛错
                        img.draw_string(self.x + 2, self.y + 2, self._text, self.color)
            except Exception:
                img.draw_string(self.x + 2, self.y + 2, self._text, self.color)
        else:
            img.draw_string(self.x + 2, self.y + 2, self._text, self.color)
        
    def hit_test(self, x, y, pressed=None):
        if not self.isVisible():
            return None
        if self.x <= x < self.x + self.w and self.y <= y < self.y + self.h:
            return self
        return None