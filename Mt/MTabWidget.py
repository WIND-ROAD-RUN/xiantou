from Mt.MWidget import MWidget
from Mt.MSignal import MSignal
from maix import image

class MTabPage(MWidget):
    def __init__(self, x=0, y=0, w=0, h=0, parent=None):
        super().__init__(x, y, w, h, parent)
    def addWidget(self, widget):
        self.add_child(widget)

class MTabWidget(MWidget):
    def __init__(self, x, y, w, h, parent=None):
        super().__init__(x, y, w, h, parent)
        self.tabs = []  # [(title, page)]
        self.current_index = 0
        self.tab_height = 32
        self.tab_bg_color = image.Color.from_rgb(240, 240, 240)
        self.tab_active_color = image.Color.from_rgb(220, 220, 220)
        self.tab_border_color = image.Color.from_rgb(180, 180, 180)
        self.text_color = image.Color.from_rgb(0, 0, 0)
        self.tab_changed = MSignal()
        self._tab_bar_visible = True

    def setTabBarVisible(self, visible: bool):
        self._tab_bar_visible = visible

    def isTabBarVisible(self):
        return self._tab_bar_visible

    def addTab(self, page, title):
        # page 必须是 MTabPage 或 MWidget
        page.x = self.x
        page.y = self.y + (self.tab_height if self._tab_bar_visible else 0)
        page.w = self.w
        page.h = self.h - (self.tab_height if self._tab_bar_visible else 0)
        self.tabs.append((title, page))
        page.setVisible(len(self.tabs) == 1)
        self.add_child(page)

    def setCurrentIndex(self, index):
        if 0 <= index < len(self.tabs):
            self.tabs[self.current_index][1].setVisible(False)
            self.current_index = index
            self.tabs[self.current_index][1].setVisible(True)
            self.tab_changed.emit(index)

    def currentIndex(self):
        return self.current_index

    def paintEvent(self, img):
        if not self.isVisible():
            return
        tab_y = self.y
        tab_h = self.tab_height if self._tab_bar_visible else 0
        # 绘制tab栏
        if self._tab_bar_visible:
            tab_w = self.w // max(1, len(self.tabs))
            for i, (title, _) in enumerate(self.tabs):
                x0 = self.x + i * tab_w
                color = self.tab_active_color if i == self.current_index else self.tab_bg_color
                img.draw_rect(x0, tab_y, tab_w, self.tab_height, color, thickness=-1)
                img.draw_rect(x0, tab_y, tab_w, self.tab_height, self.tab_border_color, thickness=1)
                img.draw_string(x0 + 8, tab_y + 8, title, self.text_color)
        # 绘制tab内容区边框
        img.draw_rect(self.x, tab_y + tab_h, self.w, self.h - tab_h, self.tab_border_color, thickness=1)

    def hit_test(self, x, y, pressed=None):
        if not self.isVisible():
            return None
        tab_y = self.y
        tab_h = self.tab_height if self._tab_bar_visible else 0
        # 检查tab栏点击
        if self._tab_bar_visible and self.x <= x < self.x + self.w and tab_y <= y < tab_y + self.tab_height:
            tab_w = self.w // max(1, len(self.tabs))
            idx = (x - self.x) // tab_w
            if 0 <= idx < len(self.tabs):
                self.setCurrentIndex(idx)
            return self
        # 只让当前tab内容区的控件响应
        if self.tabs:
            return self.tabs[self.current_index][1].hit_test(x, y, pressed)
        return None