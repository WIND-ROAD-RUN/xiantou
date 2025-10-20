from Mt.MWidget import MWidget
from maix import image

class MMainWindow(MWidget):
    def __init__(self, x=0, y=0, w=0, h=0):
        super().__init__(x, y, w, h)
        self.img = None
        self.disp = None
        self.img_width = None
        self.img_height = None
        self.fit = None
        self.is_visible = False

    def _set_app_env(self, img, disp, img_width, img_height, fit):
        self.img = img
        self.disp = disp
        self.img_width = img_width
        self.img_height = img_height
        self.fit = fit

    def repaint(self):
        if not self.is_visible:
            return
        if self.img is None or self.disp is None:
            return
        self.img.draw_rect(0, 0, self.img.width(), self.img.height(), image.Color.from_rgb(255,255,255), thickness=-1)
        self.draw(self.img)
        self.disp.show(self.img, fit=self.fit)

    def show(self):
        self.is_visible = True

    def addWidget(self, widget):
        self.add_child(widget)