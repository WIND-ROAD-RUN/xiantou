from Mt.MWidget import MWidget
from maix import image
from Mt.MApplication import MApplication

class MDialog(MWidget):
    def __init__(self, x, y, w, h, parent=None):
        super().__init__(x, y, w, h, parent)
        self._visible = False
        self.bg_color = image.Color.from_rgb(255, 255, 255)
        self.border_color = image.Color.from_rgb(180, 180, 180)
        self.result = None
        self._modal = False

    def exec(self):
        self._modal = True
        self.setVisible(True)
        app = MApplication.instance()
        # 模态循环，阻塞主程序，直到 accept/reject
        while self.isVisible():
            app._process_event_and_repaint(dialog=self)
        return self.result
    
    def addWidget(self, widget):
        self.add_child(widget)
    
    def show(self):
        MApplication.instance().showDialog(self)

    def accept(self):
        self.result = True
        MApplication.instance().closeDialog(self)

    def reject(self):
        self.result = False
        MApplication.instance().closeDialog(self)

    def paintEvent(self, img):
        if not self.isVisible():
            return
        if self._modal:
            # 只在模态时绘制遮罩
            img.draw_rect(0, 0, img.width(), img.height(), image.Color.from_rgb(0, 0, 0), thickness=-1)
        # 对话框本体
        img.draw_rect(self.x, self.y, self.w, self.h, self.bg_color, thickness=-1)
        img.draw_rect(self.x, self.y, self.w, self.h, self.border_color, thickness=2)
        # 可在此绘制标题、内容等