from Mt.MMainWindow import MMainWindow
from Mt.MTabWidget import MTabWidget,MTabPage
from Mt.MLabel import MLabel
from Mt.MPushButton import MPushButton
from Mt.MWidget import MWidget
from Mt.MApplication import MApplication
from MaixCam.RunningInfo import RunningInfo, RunMode
from MaixCam.Modules import Modules
from Mt.NumberKeyBoard import NumberKeyBoard

from maix import image

class MaixCamMainWindow(MMainWindow):
  
    def __init__(self, x, y, width, height, margin=0):
        super().__init__(x, y, width, height)
        self.width = width
        self.height = height
        self.margin = margin

        self.buildUI()

        Modules.instance().disDebug=self.labelDisImgDebug
        Modules.instance().countLabel=self.countButton

    def buildUI(self):
        self.tabWidget = MTabWidget(self.margin, self.margin, self.width - self.margin*2, self.height -  self.margin*2)
        self.tabWidget.setTabBarVisible(False)

        self.build_Menu()
        self.build_Debug()
        self.build_Config()

        self.addWidget(self.tabWidget)

    def build_Menu(self):
        # 创建一个页面容器
        self.menuContainer = MTabPage(0, 0, self.tabWidget.w, self.tabWidget.h)

        # 创建Title并居中
        self.titleLabel = MLabel(text="请选择运行模式", x=0, y=0)
        self.titleLabel.x = (self.menuContainer.w - self.titleLabel.w) // 2
        self.titleLabel.y = self.margin + 5

        # 按钮参数
        btn_count = 2  # 仅保留 Debug 和 配置
        btn_width = int(self.menuContainer.w * 0.5)
        btn_height = int(self.menuContainer.h * 0.12)
        btn_gap = int((self.menuContainer.h - self.titleLabel.y - self.titleLabel.h - btn_count * btn_height) / (btn_count + 1))
        btn_x = (self.menuContainer.w - btn_width) // 2
        btn_y_start = self.titleLabel.y + self.titleLabel.h + btn_gap

        # 分别创建并命名按钮（竖直排列）
        self.btn_startRun = MPushButton(text="开始运行", x=btn_x, y=btn_y_start, w=btn_width, h=btn_height)
        self.btn_config = MPushButton(text="配置修改", x=btn_x, y=btn_y_start + (btn_height + btn_gap), w=btn_width, h=btn_height)

        btn_w = 150
        btn_h = 50
        btn_margin = 10
        btn_x = self.menuContainer.w - btn_w - btn_margin 
        btn_y = btn_margin
        self.btn_exit= MPushButton(text="退出程序",x=btn_margin, y=btn_y, w=btn_w, h=btn_h)

        # 连接槽函数
        self.btn_startRun.clicked.connect(self.on_startRun_clicked)
        # 已移除 release 的连接
        self.btn_config.clicked.connect(self.on_config_clicked)
        self.btn_exit.clicked.connect(self.on_exit_clicked)

        self.menuContainer.add_child(self.titleLabel)
        self.menuContainer.add_child(self.btn_startRun)
        self.menuContainer.add_child(self.btn_config)
        self.menuContainer.add_child(self.btn_exit)

        # 添加到tab
        self.tabWidget.addTab(self.menuContainer, "菜单")

    def build_Debug(self):
        self.debugContainer = MTabPage(0, 0, self.tabWidget.w, self.tabWidget.h)

        self.labelDisImgDebug= MLabel(text="Debug模式下显示图像", x=self.margin, y=self.margin,w=self.width-self.margin*2,h=self.height*2)
        self.debugContainer.add_child(self.labelDisImgDebug)

        btn_w = 100
        btn_h = 50
        btn_margin = 10
        btn_x = self.debugContainer.w - btn_w - btn_margin  # 右上角
        btn_y = btn_margin
        self.exit_debug_btn = MPushButton(text="退出", x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        self.exit_debug_btn.clicked.connect(self.on_exit_to_menu)
        self.debugContainer.add_child(self.exit_debug_btn)

        btn_y += 70
        self.countButton=MPushButton(text="当前识别数量:0",x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        self.debugContainer.add_child(self.countButton)

        self.tabWidget.addTab(self.debugContainer, "Debug")

    def build_Config(self):
        self.configContainer = MTabPage(0, 0, self.tabWidget.w, self.tabWidget.h)

        btn_w = 100
        btn_h = 50
        btn_margin = 10
        btn_x = self.configContainer.w - btn_w - btn_margin  # 右上角
        btn_y = btn_margin

        self.exit_config_btn = MPushButton(text="退出", x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        self.exit_config_btn.clicked.connect(self.on_exit_to_menu)
        self.configContainer.add_child(self.exit_config_btn)

        cfg = Modules.instance().config

        # 两列布局参数
        left_label_x = 50
        left_btn_x = 210
        left_unit_x = left_btn_x + 120

        right_col_start = self.configContainer.w // 2 + 20
        right_label_x = right_col_start
        right_btn_x = right_label_x + 160
        right_unit_x = right_btn_x + 120

        row_y = [100, 220, 340]  # 三行高度，可根据需要调整

        # 第一列（左）
        # 报警时间 设置 (ms) - 左上
        self.lb_baojingshijian = MLabel(text="报警时间:", x=left_label_x, y=row_y[0])
        self.configContainer.add_child(self.lb_baojingshijian)

        self.btn_baojingshijian = MPushButton(text=str(getattr(cfg, "baojingshijian", 1000)), x=left_btn_x, y=row_y[0], w=100, h=50)
        self.btn_baojingshijian.clicked.connect(self.on_baojingshijian_clicked)
        self.configContainer.add_child(self.btn_baojingshijian)

        self.lb_baojingshijianUnit = MLabel(text="ms", x=left_btn_x, y=row_y[0] + 60)
        self.configContainer.add_child(self.lb_baojingshijianUnit)

        # NG 报警数 设置 (个) - 左中
        self.lb_ng_baojingshu = MLabel(text="NG报警数:", x=left_label_x, y=row_y[1])
        self.configContainer.add_child(self.lb_ng_baojingshu)

        self.btn_ng_baojingshu = MPushButton(text=str(getattr(cfg, "ng_baojingshu", 1)), x=left_btn_x, y=row_y[1], w=100, h=50)
        self.btn_ng_baojingshu.clicked.connect(self.on_ng_baojingshu_clicked)
        self.configContainer.add_child(self.btn_ng_baojingshu)

        self.lb_ng_baojingshuUnit = MLabel(text="个", x=left_btn_x, y=row_y[1] + 60)
        self.configContainer.add_child(self.lb_ng_baojingshuUnit)

        # NG 阈值 设置 (个) - 左下
        self.lb_ng_yuzhi = MLabel(text="NG阈值:", x=left_label_x, y=row_y[2])
        self.configContainer.add_child(self.lb_ng_yuzhi)

        self.btn_ng_yuzhi = MPushButton(text=str(getattr(cfg, "ng_yuzhi", 1)), x=left_btn_x, y=row_y[2], w=100, h=50)
        self.btn_ng_yuzhi.clicked.connect(self.on_ng_yuzhi_clicked)
        self.configContainer.add_child(self.btn_ng_yuzhi)

        self.lb_ng_yuzhiUnit = MLabel(text="个", x=left_btn_x, y=row_y[2] + 60)
        self.configContainer.add_child(self.lb_ng_yuzhiUnit)

        # 第二列（右）
        # 相机曝光 设置 (us) - 右上
        self.lb_camera_exposure = MLabel(text="相机曝光:", x=right_label_x, y=row_y[0])
        self.configContainer.add_child(self.lb_camera_exposure)

        self.btn_camera_exposure = MPushButton(text=str(getattr(cfg, "camera_exposure_us", 10000)), x=right_btn_x, y=row_y[0], w=120, h=50)
        self.btn_camera_exposure.clicked.connect(self.on_camera_exposure_clicked)
        self.configContainer.add_child(self.btn_camera_exposure)

        self.lb_camera_exposureUnit = MLabel(text="us", x=right_btn_x, y=row_y[0] + 60)
        self.configContainer.add_child(self.lb_camera_exposureUnit)

        # 相机增益 设置 (倍) - 右中
        self.lb_camera_gain = MLabel(text="相机增益:", x=right_label_x, y=row_y[1])
        self.configContainer.add_child(self.lb_camera_gain)

        self.btn_camera_gain = MPushButton(text=str(getattr(cfg, "camera_gain", 1)), x=right_btn_x, y=row_y[1], w=100, h=50)
        self.btn_camera_gain.clicked.connect(self.on_camera_gain_clicked)
        self.configContainer.add_child(self.btn_camera_gain)

        self.lb_camera_gainUnit = MLabel(text="倍", x=right_btn_x, y=row_y[1] + 60)
        self.configContainer.add_child(self.lb_camera_gainUnit)

        self.tabWidget.addTab(self.configContainer, "配置")

    # 槽函数定义
    def on_startRun_clicked(self):
        print("运行模式")
        RunningInfo.instance().run_mode = RunMode.RUN
        self.tabWidget.setCurrentIndex(1)

    def on_exit_clicked(self):
        Modules.instance().config.save(path=Modules.instance().paths.config_path)
        MApplication.instance().exit()
    
    def on_config_clicked(self):
        print("配置修改")
        # 移除 release 面板后，配置页索引改为 2（菜单=0, Debug=1, 配置=2）
        self.tabWidget.setCurrentIndex(2)
        RunningInfo.instance().run_mode = RunMode.STOP

    def on_exit_to_menu(self):
        RunningInfo.instance().run_mode = RunMode.STOP
        Modules.instance().warning.setLow()
        print("退出运行模式")
        self.tabWidget.setCurrentIndex(0)

    def on_baojingshijian_clicked(self):
        numberKeyBoard = NumberKeyBoard(50, 50, 300, 400, max_len=6)
        res = numberKeyBoard.exec()
        if res:
            val = numberKeyBoard.getValue()
            self.btn_baojingshijian.setText(str(val))
            Modules.instance().config.baojingshijian = int(val)

    def on_ng_baojingshu_clicked(self):
        numberKeyBoard = NumberKeyBoard(50, 50, 300, 400, max_len=4)
        res = numberKeyBoard.exec()
        if res:
            val = numberKeyBoard.getValue()
            self.btn_ng_baojingshu.setText(str(val))
            Modules.instance().config.ng_baojingshu = int(val)

    def on_ng_yuzhi_clicked(self):
        numberKeyBoard = NumberKeyBoard(50, 50, 300, 400, max_len=4)
        res = numberKeyBoard.exec()
        if res:
            val = numberKeyBoard.getValue()
            self.btn_ng_yuzhi.setText(str(val))
            Modules.instance().config.ng_yuzhi = int(val)

    def on_camera_exposure_clicked(self):
        numberKeyBoard = NumberKeyBoard(50, 50, 300, 400, max_len=7)
        res = numberKeyBoard.exec()
        if res:
            val = numberKeyBoard.getValue()
            self.btn_camera_exposure.setText(str(val))
            Modules.instance().config.camera_exposure_us = int(val)
            Modules.instance().camera.set_exposure(int(val))

    def on_camera_gain_clicked(self):
        numberKeyBoard = NumberKeyBoard(50, 50, 300, 400, max_len=4)
        res = numberKeyBoard.exec()
        if res:
            val = numberKeyBoard.getValue()
            self.btn_camera_gain.setText(str(val))
            Modules.instance().config.camera_gain = int(val)
            Modules.instance().camera.set_gain(int(val))
