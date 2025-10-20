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
        Modules.instance().disRelease=self.labelDisImgRel
        Modules.instance().countLabel=self.countButton

    def buildUI(self):
        self.tabWidget = MTabWidget(self.margin, self.margin, self.width - self.margin*2, self.height -  self.margin*2)
        self.tabWidget.setTabBarVisible(False)

        self.build_Menu()
        self.build_Debug()
        self.build_Release()
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
        btn_count = 3
        btn_width = int(self.menuContainer.w * 0.5)
        btn_height = int(self.menuContainer.h * 0.12)
        btn_gap = int((self.menuContainer.h - self.titleLabel.y - self.titleLabel.h - btn_count * btn_height) / (btn_count + 1))
        btn_x = (self.menuContainer.w - btn_width) // 2
        btn_y_start = self.titleLabel.y + self.titleLabel.h + btn_gap

        # 分别创建并命名按钮（竖直排列）
        self.btn_debug = MPushButton(text="Debug模式", x=btn_x, y=btn_y_start, w=btn_width, h=btn_height)
        self.btn_release = MPushButton(text="Release模式", x=btn_x, y=btn_y_start + btn_height + btn_gap, w=btn_width, h=btn_height)
        self.btn_config = MPushButton(text="配置修改", x=btn_x, y=btn_y_start + (btn_height + btn_gap) * 2, w=btn_width, h=btn_height)

        btn_w = 150
        btn_h = 50
        btn_margin = 10
        btn_x = self.menuContainer.w - btn_w - btn_margin 
        btn_y = btn_margin
        self.btn_exit= MPushButton(text="退出程序",x=btn_x, y=btn_y, w=btn_w, h=btn_h)

        # 连接槽函数
        self.btn_debug.clicked.connect(self.on_debug_clicked)
        self.btn_release.clicked.connect(self.on_release_clicked)
        self.btn_config.clicked.connect(self.on_config_clicked)
        self.btn_exit.clicked.connect(self.on_exit_clicked)

        self.menuContainer.add_child(self.titleLabel)
        self.menuContainer.add_child(self.btn_debug)
        self.menuContainer.add_child(self.btn_release)
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

    def build_Release(self):
        self.releaseContainer = MTabPage(0, 0, self.tabWidget.w, self.tabWidget.h)

        self.labelDisImgRel= MLabel(text="Release模式下运行中...", x=self.margin, y=self.margin,w=self.width-self.margin*2,h=self.height*2)
        self.releaseContainer.add_child(self.labelDisImgRel)

        btn_w = 100
        btn_h = 50
        btn_margin = 10
        btn_x = self.releaseContainer.w - btn_w - btn_margin  # 右上角
        btn_y = btn_margin
        self.exit_release_btn = MPushButton(text="退出", x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        self.exit_release_btn.clicked.connect(self.on_exit_to_menu)
        self.releaseContainer.add_child(self.exit_release_btn)


        self.tabWidget.addTab(self.releaseContainer, "Release")

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

        cfg=Modules.instance().config

        # 间隔设置
        self.lb_jiange= MLabel(text="间隔:", x=50, y=100)
        self.configContainer.add_child(self.lb_jiange)

        self.btn_jiange = MPushButton(text=str(cfg.jiange), x=200, y=100, w=100, h=50)
        self.btn_jiange.clicked.connect(self.on_jiange_clicked)
        self.configContainer.add_child(self.btn_jiange)

        self.lb_jiangeUnit = MLabel(text="个", x=200, y=160)
        self.configContainer.add_child(self.lb_jiangeUnit)

        # 延时触发时间设置
        self.lb_yanshichufashijian= MLabel(text="延时触发时间:", x=300, y=100)
        self.configContainer.add_child(self.lb_yanshichufashijian)

        self.btn_yanshichufashijian = MPushButton(text=str(cfg.yanshichufashijian), x=520, y=100, w=100, h=50)
        self.btn_yanshichufashijian.clicked.connect(self.on_yanshichufashijian_clicked)
        self.configContainer.add_child(self.btn_yanshichufashijian)

        self.lb_yanshichufashijianUnit = MLabel(text="ms", x=520, y=160)
        self.configContainer.add_child(self.lb_yanshichufashijianUnit)

        # 触发时间设置
        self.lb_chufashijian= MLabel(text="触发时间:", x=50, y=220)
        self.configContainer.add_child(self.lb_chufashijian)

        self.btn_chufashijian = MPushButton(text=str(cfg.chufashijian), x=200, y=220, w=100, h=50)
        self.btn_chufashijian.clicked.connect(self.on_chufashijian_clicked)
        self.configContainer.add_child(self.btn_chufashijian)

        self.lb_chufashijianUnit = MLabel(text="ms", x=200, y=280)
        self.configContainer.add_child(self.lb_chufashijianUnit)

        # 小斗一次设置
        self.lb_xiaodouyici= MLabel(text="小斗一次:", x=300, y=220)
        self.configContainer.add_child(self.lb_xiaodouyici)

        self.btn_xiaodouyici = MPushButton(text=str(cfg.xiaodouyici), x=520, y=220, w=100, h=50)
        self.btn_xiaodouyici.clicked.connect(self.on_xiaodouyici_clicked)
        self.configContainer.add_child(self.btn_xiaodouyici)

        self.tabWidget.addTab(self.configContainer, "配置")

        self.lb_xiaodouyiciUnit = MLabel(text="个", x=520, y=280)
        self.configContainer.add_child(self.lb_xiaodouyiciUnit)

        # 大斗一次设置
        self.lb_dadouyici= MLabel(text="大斗一次:", x=50, y=340)
        self.configContainer.add_child(self.lb_dadouyici)

        self.btn_dadouyici = MPushButton(text=str(cfg.dadouyici), x=200, y=340, w=100, h=50)
        self.btn_dadouyici.clicked.connect(self.on_dadouyici_clicked)
        self.configContainer.add_child(self.btn_dadouyici)

        self.lb_dadouyiciUnit = MLabel(text="个", x=200, y=400)
        self.configContainer.add_child(self.lb_dadouyiciUnit)

        # 总数设置
        self.lb_zongshu= MLabel(text="总数:", x=300, y=340)
        self.configContainer.add_child(self.lb_zongshu)

        self.btn_zongshu = MPushButton(text=str(cfg.zongshu), x=520, y=340, w=100, h=50)
        self.btn_zongshu.clicked.connect(self.on_zongshu_clicked)
        self.configContainer.add_child(self.btn_zongshu)

        self.lb_zongshuUnit = MLabel(text="个", x=520, y=400)
        self.configContainer.add_child(self.lb_zongshuUnit)

        self.tabWidget.addTab(self.configContainer, "配置")

    # 槽函数定义
    def on_debug_clicked(self):
        print("Debug模式")
        RunningInfo.instance().run_mode = RunMode.DEBUG
        self.tabWidget.setCurrentIndex(1)

    def on_exit_clicked(self):
        Modules.instance().config.save(path=Modules.instance().paths.config_path)
        MApplication.instance().exit()
    
    def on_release_clicked(self):
        print("Release模式")
        self.tabWidget.setCurrentIndex(2)
        RunningInfo.instance().run_mode = RunMode.RUN

    def on_config_clicked(self):
        print("配置修改")
        self.tabWidget.setCurrentIndex(3)
        RunningInfo.instance().run_mode = RunMode.STOP

    def on_exit_to_menu(self):
        RunningInfo.instance().run_mode = RunMode.STOP
        Modules.instance().warning.setLow()
        print("退出Debug")
        self.tabWidget.setCurrentIndex(0)

    def on_jiange_clicked(self):
        numberKeyBoard=NumberKeyBoard(50, 50, 300, 400, max_len=4)
        res=numberKeyBoard.exec()
        if res:
           self.btn_jiange.setText(str(numberKeyBoard.getValue()))
           Modules.instance().config.jiange = numberKeyBoard.getValue()

    def on_yanshichufashijian_clicked(self):
        numberKeyBoard=NumberKeyBoard(50, 50, 300, 400, max_len=4)
        res=numberKeyBoard.exec()
        if res:
           self.btn_yanshichufashijian.setText(str(numberKeyBoard.getValue()))
           Modules.instance().config.yanshichufashijian = numberKeyBoard.getValue()

    def on_chufashijian_clicked(self):
        numberKeyBoard=NumberKeyBoard(50, 50, 300, 400, max_len=4)
        res=numberKeyBoard.exec()
        if res:
           self.btn_chufashijian.setText(str(numberKeyBoard.getValue()))
           Modules.instance().config.chufashijian = numberKeyBoard.getValue()

    def on_xiaodouyici_clicked(self):
        numberKeyBoard=NumberKeyBoard(50, 50, 300, 400, max_len=4)
        res=numberKeyBoard.exec()
        if res:
            self.btn_xiaodouyici.setText(str(numberKeyBoard.getValue()))
            Modules.instance().config.xiaodouyici = numberKeyBoard.getValue()

    def on_dadouyici_clicked(self):
        numberKeyBoard=NumberKeyBoard(50, 50, 300, 400, max_len=4)
        res=numberKeyBoard.exec()
        if res:
           self.btn_dadouyici.setText(str(numberKeyBoard.getValue()))
           Modules.instance().config.dadouyici = numberKeyBoard.getValue()

    def on_zongshu_clicked(self):
        numberKeyBoard=NumberKeyBoard(50, 50, 300, 400, max_len=4)
        res=numberKeyBoard.exec()
        if res:
           self.btn_zongshu.setText(str(numberKeyBoard.getValue()))
           Modules.instance().config.zongshu = numberKeyBoard.getValue()
