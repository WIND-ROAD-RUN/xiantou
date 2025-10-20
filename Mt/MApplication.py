from maix import touchscreen, app, time, display, image
from Mt.MWidget import MWidget
from Mt.Clock import GameClock

class MApplication:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MApplication, cls).__new__(cls)
        return cls._instance

    def __init__(self, img_width=None, img_height=None, fit=image.Fit.FIT_CONTAIN):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.ts = touchscreen.TouchScreen()
        self.disp = display.Display()
        self.fit = fit
        self.img_width = img_width or self.disp.width()
        self.img_height = img_height or self.disp.height()
        self.img = image.Image(self.img_width, self.img_height)
        self.main_window = None
        self.widgets = []  # 新增：所有需要事件分发的控件
        self.active_dialog = None  # 当前活动对话框
        self._initialized = True
        self.pre_frame_callback = None   # 帧前回调
        self.post_frame_callback = None  # 帧后回调
        # 引擎时钟：fixed_dt_ms 可选，例如 16 ms 固定步进
        self.game_clock = GameClock().instance(fixed_dt_ms=16)
        self._last_tick = time.ticks_ms()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = MApplication()
        return cls._instance

    def setMainWindow(self, window):
        self.main_window = window
        window._set_app_env(self.img, self.disp, self.img_width, self.img_height, self.fit)

    def register_widget(self, widget):
        if widget not in self.widgets:
            self.widgets.append(widget)

    def unregister_widget(self, widget):
        if widget in self.widgets:
            self.widgets.remove(widget)
    def showDialog(self, dialog):
        self.active_dialog = dialog
        dialog.setVisible(True)
        main_win = self.main_window
        if dialog not in main_win.children:
            main_win.addWidget(dialog)

    def closeDialog(self, dialog):
        if self.active_dialog == dialog:
            self.active_dialog = None
        dialog.setVisible(False)

    def setPreFrameCallback(self, func):
        self.pre_frame_callback = func

    def setPostFrameCallback(self, func):
        self.post_frame_callback = func

    def exec(self, interval_ms=10):
        if not self.main_window:
            raise RuntimeError("No main window set")
        while not app.need_exit():
            now = time.ticks_ms()
            last = getattr(self, "_last_tick", now)
            # 使用 time.ticks_diff（若不可用则退回到普通减法）
            try:
                dt = time.ticks_diff(now, last)
            except Exception:
                dt = now - last
            self._last_tick = now
            # 先驱动引擎时钟（帧前时钟）
            self.game_clock.update(dt)
            # 帧前回调
            if self.pre_frame_callback:
                try:
                    self.pre_frame_callback()
                except Exception:
                    pass
            # 读取触摸并分发（保持现有逻辑）
            x, y, is_pressed = self.ts.read()
            tx, ty = x, y
            if self.img_width and self.img_height and self.disp:
                tx, ty = image.resize_map_pos_reverse(
                    self.img_width, self.img_height,
                    self.disp.width(), self.disp.height(),
                    self.fit, x, y
                )
            if self.active_dialog and self.active_dialog.isVisible():
                self.active_dialog.hit_test(tx, ty, is_pressed)
            else:
                self.main_window.hit_test(tx, ty, is_pressed)
            # 绘制
            self.main_window.repaint()
            # 帧后回调
            if self.post_frame_callback:
                try:
                    self.post_frame_callback()
                except Exception:
                    pass
            # sleep 保持 loop 节奏
            time.sleep_ms(interval_ms)
    
    def _process_event_and_repaint(self, dialog=None, interval_ms=10):
        if dialog is not None:
            x, y, is_pressed = self.ts.read()
            tx, ty = x, y
            if self.img_width and self.img_height and self.disp:
                tx, ty = image.resize_map_pos_reverse(
                    self.img_width, self.img_height,
                    self.disp.width(), self.disp.height(),
                    self.fit, x, y
                )
            # 递归命中检测，能命中dialog的子控件
            hit_widget = dialog.hit_test(tx, ty) if is_pressed else None
            if is_pressed and not getattr(dialog, "_pressed", False) and hit_widget:
                dialog._last_pressed_widget = hit_widget
                dialog._pressed = True
            elif not is_pressed and getattr(dialog, "_pressed", False):
                if dialog._last_pressed_widget and dialog._last_pressed_widget.hit_test(tx, ty):
                    if hasattr(dialog._last_pressed_widget, "clicked"):
                        dialog._last_pressed_widget.clicked.emit()
                    if hasattr(dialog._last_pressed_widget, "on_click"):
                        dialog._last_pressed_widget.on_click()
                dialog._last_pressed_widget = None
                dialog._pressed = False
            # 绘制主窗口和对话框
            self.img.draw_rect(0, 0, self.img.width(), self.img.height(), image.Color.from_rgb(255,255,255), thickness=-1)
            self.main_window.draw(self.img)
            dialog.draw(self.img)
            self.disp.show(self.img, fit=self.fit)
            time.sleep_ms(interval_ms)
        else:
            self.main_window._process_event(self.ts)
            self.main_window.repaint()
            time.sleep_ms(interval_ms)

    def exit(self):
        app.set_exit_flag(True)