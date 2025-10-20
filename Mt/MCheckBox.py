from maix import image
from Mt.MWidget import MWidget
from Mt.MSignal import MSignal

class MCheckBox(MWidget):
    def __init__(self, text, x, y, w=24, h=24, checked=False, parent=None):
        super().__init__(x, y, w, h, parent)
        self._text = text
        self.checked = checked
        self.box_size = min(w, h, 24)
        self.bg_color = image.Color.from_rgb(255,255,255)
        self.border_color = image.Color.from_rgb(180,180,180)
        self.check_color = image.Color.from_rgb(33,150,243)
        self.text_color = image.Color.from_rgb(0,0,0)
        self.toggled = MSignal()
    def setChecked(self, checked):
        self.checked = checked
    def isChecked(self):
        return self.checked
    def setText(self, text):
        self._text = text
    def text(self):
        return self._text
    def paintEvent(self, img):
        if not self.isVisible():
            return
        img.draw_rect(self.x, self.y, self.box_size, self.box_size, self.bg_color, thickness=-1)
        img.draw_rect(self.x, self.y, self.box_size, self.box_size, self.border_color, thickness=2)
        if self.checked:
            bx, by, bs = self.x, self.y, self.box_size
            img.draw_line(bx+4, by+bs//2, bx+bs//2, by+bs-5, self.check_color, 2)
            img.draw_line(bx+bs//2, by+bs-5, bx+bs-5, by+5, self.check_color, 2)
        img.draw_string(self.x + self.box_size + 8, self.y + (self.box_size//2 - 8), self._text, self.text_color)
    def hit_test(self, x, y, pressed=None):
        if not self.isVisible():
            return None
        if self.x <= x < self.x + self.box_size and self.y <= y < self.y + self.box_size:
            if pressed is not None:
                if pressed and not getattr(self, "_pressed", False):
                    self._pressed = True
                elif not pressed and getattr(self, "_pressed", False):
                    self._pressed = False
                    self.checked = not self.checked
                    self.toggled.emit(self.checked)
                    return self
                return None
            else:
                return self
        else:
            self._pressed = False
        return None