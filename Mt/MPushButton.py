from maix import image
from Mt.MWidget import MWidget
from Mt.MSignal import MSignal

class MPushButton(MWidget):
    def __init__(self, text, x, y, w, h, parent=None):
        super().__init__(x, y, w, h, parent)
        self._text = text
        self.bg_color = image.Color.from_rgb(240,240,240)
        self.border_color = image.Color.from_rgb(180,180,180)
        self.text_color = image.Color.from_rgb(0,0,0)
        self.clicked = MSignal()
    def setText(self, text):
        self._text = text
    def text(self):
        return self._text
    def paintEvent(self, img):
        if not self.isVisible():
            return
        img.draw_rect(self.x, self.y, self.w, self.h, self.bg_color, thickness=-1)
        img.draw_rect(self.x, self.y, self.w, self.h, self.border_color, thickness=2)
        img.draw_string(self.x+8, self.y+12, self._text, self.text_color)
    def hit_test(self, x, y, pressed=None):
        if not self.isVisible():
            return None
        if self.x <= x < self.x + self.w and self.y <= y < self.y + self.h:
            if pressed is not None:
                if pressed and not getattr(self, "_pressed", False):
                    self._pressed = True
                elif not pressed and getattr(self, "_pressed", False):
                    self._pressed = False
                    self.clicked.emit()
                    return self
                return None
            else:
                return self
        else:
            self._pressed = False
        return None