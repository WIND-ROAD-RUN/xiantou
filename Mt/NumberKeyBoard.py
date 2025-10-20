from Mt.MDialog import MDialog
from Mt.MPushButton import MPushButton
from Mt.MLabel import MLabel
from Mt.MApplication import MApplication
from maix import image

class NumberKeyBoard(MDialog):
    """
    数字键盘对话框（继承 MDialog）。
    用法：
        kb = NumberKeyBoard(x, y, w, h, max_len=6)
        res = kb.exec()   # 模态，返回字符串或 None
    或非模态：
        kb.show()
        v = kb.getValue()
    """
    def __init__(self, x, y, w, h, parent=None, max_len=6):
        super().__init__(x, y, w, h, parent)
        self.max_len = max_len
        self._buf = ""
        self._margin = 12
        self._gap = 8
        self.result = None

        # 改动：增加顶部“行高”，确保顶部的取消按钮和显示区域有足够高度
        # 使用对话框高度的一个比例或最小值作为显示区高度
        self.display_h = max(40, int(h * 0.18))

        # 按钮区列数和行数（1..9 三行 + 最后一行）
        self.cols = 3
        self.rows = 4

        # 先按宽度计算按钮宽度
        total_gap_w = (self.cols - 1) * self._gap
        btn_w = max(10, (self.w - 2 * self._margin - total_gap_w) // self.cols)

        # 按高度计算按钮高度，确保不超出 dialog 高度
        total_gap_h = (self.rows - 1) * self._gap
        avail_h_for_buttons = self.h - 2 * self._margin - self.display_h
        # 如果可用高度过小，尝试压缩 display_h，但保留一个较大最小值
        if avail_h_for_buttons <= 0:
            self.display_h = max(28, self.h - 2 * self._margin - (self.rows * 20 + total_gap_h))
            avail_h_for_buttons = self.h - 2 * self._margin - self.display_h

        btn_h_candidate = (avail_h_for_buttons - total_gap_h) // self.rows
        if btn_h_candidate <= 0:
            # 兜底，保证至少 12 像素
            btn_h = max(12, min(btn_w, (self.h - 2 * self._margin - total_gap_h) // self.rows))
        else:
            # 按钮高度不超过宽度（保持方形或接近）
            btn_h = min(btn_w, btn_h_candidate)

        # 如果按钮高度太小且 display_h 很大，压缩 display_h 以腾出空间
        required_buttons_h = self.rows * btn_h + total_gap_h
        if required_buttons_h > (self.h - 2 * self._margin - 16):
            self.display_h = max(24, self.h - 2 * self._margin - required_buttons_h)
            avail_h_for_buttons = self.h - 2 * self._margin - self.display_h
            btn_h_candidate = (avail_h_for_buttons - total_gap_h) // self.rows
            if btn_h_candidate > 0:
                btn_h = min(btn_w, btn_h_candidate)

        # 显示标签（放在 dialog 顶部）
        disp_x = self.x + self._margin
        disp_y = self.y + self._margin
        disp_w = self.w - 2 * self._margin
        self.display_label = MLabel(self._buf, disp_x, disp_y, disp_w, self.display_h)
        self.addWidget(self.display_label)

        # 生成数字键 1..9
        start_y = disp_y + self.display_h + self._gap
        nums = ["1","2","3","4","5","6","7","8","9"]
        for idx, ch in enumerate(nums):
            col = idx % self.cols
            row = idx // self.cols
            bx = self.x + self._margin + col * (btn_w + self._gap)
            by = start_y + row * (btn_h + self._gap)
            b = MPushButton(ch, bx, by, btn_w, btn_h, parent=self)
            b.clicked.connect(self._make_digit_handler(ch))
            self.addWidget(b)

        # 第四行：OK, 0, Back
        row4_y = start_y + 3 * (btn_h + self._gap)
        # 防止超出底部：如果 row4_y + btn_h 超出，则上移 start_y
        overflow = (row4_y + btn_h) - (self.y + self.h - self._margin)
        if overflow > 0:
            start_y -= overflow
            row4_y -= overflow
            row4_y = min(row4_y, self.y + self.h - self._margin - btn_h)

        # OK 按钮（左）
        ok_w = btn_w
        ok_x = self.x + self._margin
        ok_btn = MPushButton("确定", ok_x, row4_y, ok_w, btn_h, parent=self)
        ok_btn.clicked.connect(self._on_ok)
        self.addWidget(ok_btn)
        # 0 按钮（中）
        zero_x = self.x + self._margin + 1 * (btn_w + self._gap)
        zero_btn = MPushButton("0", zero_x, row4_y, btn_w, btn_h, parent=self)
        zero_btn.clicked.connect(self._make_digit_handler("0"))
        self.addWidget(zero_btn)
        # Back 按钮（右）
        back_x = self.x + self._margin + 2 * (btn_w + self._gap)
        back_btn = MPushButton("←", back_x, row4_y, btn_w, btn_h, parent=self)
        back_btn.clicked.connect(self._on_back)
        self.addWidget(back_btn)

        # 右上角放置取消按钮（小），调整尺寸以适配放大的顶部行高
        c_w = min(80, self.w // 3)
        # 让取消按钮高度接近按钮高度或不小于一个较大的最小值
        c_h = max(28, min(btn_h, int(self.display_h * 0.7)))
        c_x = self.x + self.w - c_w - self._margin
        # 将取消按钮垂直居中放到显示区内
        c_y = disp_y + max(0, (self.display_h - c_h) // 2)
        cancel_btn = MPushButton("取消", c_x, c_y, c_w, c_h, parent=self)
        cancel_btn.clicked.connect(self._on_cancel)
        self.addWidget(cancel_btn)

    def _make_digit_handler(self, ch):
        def handler():
            if len(self._buf) < self.max_len:
                self._buf += ch
                self._update_display()
        return handler

    def _on_back(self):
        if self._buf:
            self._buf = self._buf[:-1]
            self._update_display()

    def _on_ok(self):
        # 设置结果并关闭（调用父类 accept）
        self.value = self._buf
        self.accept()

    def _on_cancel(self):
        self.reject()

    def _update_display(self):
        # 更新标签文本
        self.display_label.setText(self._buf if self._buf else "")

    # 新增接口：获取当前值（优先返回 exec 的结果，其次返回当前缓冲）
    def getValue(self):
        return self.value if self.value is not None else self._buf

    # 可选：清除当前缓冲与结果
    def clearValue(self):
        self._buf = ""
        self.value = None
        self._update_display()