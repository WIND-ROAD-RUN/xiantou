from ImgProModule.Utility import ProcessResultIndexMap ,ProcessResult
from MaixCam.RunningInfo import RunningInfo, RunMode
from MaixCam.Modules import Modules
from Mt.MApplication import MApplication
from Mt.KeyMonitor import UserKey
from MaixCam.Utilty import ClassId
from maix import time
import os

class FrameCallBefore:
    def __init__(self):
        app = MApplication.instance()
        # 只使用引擎时钟（必须保证 app.game_clock 已创建）
        self._game_clock = app.game_clock
        # 以引擎时钟初始化 last 时间，避免首次比较出错
        now = self._now_ms()
        self._last_debug_ms = now
        self._last_run_ms = now
        self.disp = app.disp

        # 节流间隔（毫秒），按需调整
        # 频率 f(Hz) = 1000 / interval_ms
        self.debug_interval_ms = 10   # debug 模式下算法处理频率 (20Hz)
        self.run_interval_ms = 10    # 运行模式下算法处理频率 (20Hz)

        # 报警定时器句柄（GameClock Timer 对象），用于在 N ms 后自动关闭报警
        self._alarm_timer = None

        # 用于“连续多帧达到合格检测才关闭报警”的计数和阈值（可从 config 中读取）
        self._clear_counter = 0
        try:
            cfg = Modules.instance().config
            # config 中若存在 alarm_clear_consecutive 则使用，否则默认 3 帧
            self._clear_required = int(getattr(cfg, "alarm_clear_consecutive", 3))
        except Exception:
            self._clear_required = 2

        # 新增：用于滑动窗口统计在最近 N 帧中 isAlarmInFrame 为 True 的次数（由 ng_baojinshu_rongyu 控制）
        try:
            cfg = Modules.instance().config
            self._window_size = int(getattr(cfg, "ng_baojinshu_rongyu", 5))
        except Exception:
            self._window_size = 5
        self._recent_alarm_window = []  # 存 0/1 值，长度保持 <= _window_size

        # 用于跳帧控制：当检测到断线/其他异常需要跳过报警时，跳过当前帧及随后的 skip_frames_remaining 帧
        # 将跳过的“总帧数（包含本帧）”作为可配置成员变量，允许硬编码修改
        self.skip_frame_total = 2  # <-- 硬编码修改此值，例如 3 表示跳过当前帧及后两帧（共3帧）
        self._skip_frames_remaining = 0

        # 长按检测：用于实现“按住2秒切换 enable_alarm”
        self._alarm_press_start_ms = None
        self._alarm_long_pressed_triggered = False
        self.lastIsSkipTakePicture=False

    def __call__(self):
        self.run()

    def _now_ms(self):
        # 仅使用 engine clock 的 unscaled 时间（毫秒）
        try:
            return int(self._game_clock.unscaled_total_ms)
        except Exception:
            # 兜底为 time.ticks_ms，理论上不会走到这里
            try:
                return int(time.ticks_ms())
            except Exception:
                return int(time.time() * 1000)

    def _elapsed_ms(self, now, last):
        # 直接相减并保证非负（引擎时钟应单调递增）
        diff = int(now - last)
        if diff < 0:
            diff = -diff
        return diff 

    def run(self):
        mode = RunningInfo.instance().run_mode
        km = Modules.instance().keyMonotor

        # 长按2秒切换 enable_alarm 的逻辑
        now = self._now_ms()
        try:
            key_down = km.is_down(key_id=UserKey)
        except Exception:
            key_down = False

        if key_down:
            if self._alarm_press_start_ms is None:
                # 按下开始计时
                self._alarm_press_start_ms = now
                self._alarm_long_pressed_triggered = False
            else:
                # 已按下，检查是否达到2秒且未触发过
                if (not self._alarm_long_pressed_triggered) and (now - self._alarm_press_start_ms >= 1200):
                    self._alarm_long_pressed_triggered = True
                    Modules.instance().isEnableAlarm = not Modules.instance().isEnableAlarm
                    if Modules.instance().isEnableAlarmLabel:
                        if Modules.instance().isEnableAlarm:
                            Modules.instance().isEnableAlarmLabel.setText("启用")
                        else:
                            Modules.instance().isEnableAlarmLabel.setText("禁用")
                    # 清除点击记录以防其他逻辑误触
                    try:
                        km.clear_clicks()
                    except Exception:
                        pass
        else:
            # 按键释放，重置长按检测状态
            self._alarm_press_start_ms = None
            self._alarm_long_pressed_triggered = False

        if mode == RunMode.RUN:
            if self.lastIsSkipTakePicture:
                self.run_run()
                self.lastIsSkipTakePicture=False
            else:
                self.lastIsSkipTakePicture=True
    
        elif mode == RunMode.STOP:
            self.run_stop()
            

    def decide_alarm_action(self, processResultIndexMap: ProcessResultIndexMap,processResult:ProcessResult,width:int=0):
        # 处理流程：
        # 1. 仅在识别到且只识别到一个主体时才进入主体内线头判断，否则返回 None 让上层保持现状。
        body=processResultIndexMap.get(ClassId.body, [])
        if len(body) != 1:
            return None
        
        bodyIndex = body[0]

        # 2. 若主体存在但完全没有线头检测结果，则视为线头缺失，立即请求开启报警。
        xiantou = processResultIndexMap.get(ClassId.xiantou, [])
        bodyRect = processResult[bodyIndex]

        if bodyRect.centralX < width/4 or bodyRect.centralX > width*3/4:
            return None

        if len(xiantou) ==0 :
            return "open"
        
        hasXiantouInBody = False

        # 3. 遍历每个线头，确认其中心点是否落在主体矩形内部，只要找到一个即视为主体内存在线头。
        for xiantouIndex in xiantou:
            xiantouRect = processResult[xiantouIndex]

            if (xiantouRect.centralX >= bodyRect.leftTop.x and
                xiantouRect.centralX <= bodyRect.rightTop.x and
                xiantouRect.centralY >= bodyRect.leftTop.y and
                xiantouRect.centralY <= bodyRect.leftBottom.y):
                hasXiantouInBody = True
                break

        # 4. 主体内找不到线头则继续报警，否则返回 "false" 交由上层保持或关闭报警。
        if not hasXiantouInBody:
            return "open"

        return "false"

    def open_alarm(self):
        """
        执行开启报警：置高电平并（重）设置定时器在 cfg.baojingshijian 毫秒后自动关闭。
        """
        warningCom = Modules.instance().warning
        cfg = Modules.instance().config

        try:
            warningCom.setHight()
        except Exception:
            pass

        # 取消已有定时器
        try:
            if getattr(self, "_alarm_timer", None):
                self._game_clock.cancel_timer(self._alarm_timer)
        except Exception:
            pass

        def _alarm_timeout():
            try:
                warningCom.setLow()
            except Exception:
                pass
            try:
                self._alarm_timer = None
                self._clear_counter = 0
            except Exception:
                pass

        try:
            self._alarm_timer = self._game_clock.schedule_once(int(cfg.baojingshijian), _alarm_timeout)
        except Exception:
            # 若无法调度定时器则兜底关闭
            try:
                warningCom.setLow()
            except Exception:
                pass
            self._alarm_timer = None

    def close_alarm(self):
        """
        立即关闭报警：取消定时器、置低电平并重置计数器。
        """
        warningCom = Modules.instance().warning
        try:
            if getattr(self, "_alarm_timer", None):
                self._game_clock.cancel_timer(self._alarm_timer)
                self._alarm_timer = None
        except Exception:
            pass

        try:
            warningCom.setLow()
        except Exception:
            pass

        self._clear_counter = 0

    def warning_alarm_timeout(self, processResultIndexMap: ProcessResultIndexMap,processResult:ProcessResult,width:int=0):
        """
        入口：先检查全局开关，再通过 decide_alarm_action 得到动作並调用 open_alarm/close_alarm。
        """
        warningCom = Modules.instance().warning
        if not Modules.instance().isEnableAlarm:
            try:
                if getattr(self, "_alarm_timer", None):
                    self._game_clock.cancel_timer(self._alarm_timer)
                    self._alarm_timer = None
            except Exception:
                pass
            try:
                warningCom.setLow()
            except Exception:
                pass
            return

        action = self.decide_alarm_action(processResultIndexMap,processResult,width)
        if action == "open":
            self.open_alarm()
        elif action == "close":
            self.close_alarm()

    def isTrigger(self):
        # 按下按键保存图片
        km = Modules.instance().keyMonotor
        if  km.take_click(key_id=UserKey):
            km.clear_clicks()
            return True
        return False

    def run_run(self):
        now = self._now_ms()
        elapsed = self._elapsed_ms(now, self._last_debug_ms)
        # 只有超过间隔才执行昂贵处理
        if elapsed < self.debug_interval_ms:
            return
        self._last_debug_ms = now

        camera = Modules.instance().camera
        imgProCom = Modules.instance().imgProCom

        # 读取并处理 —— 这是昂贵操作，已被节流
        img = camera.read()
        imgProCom.run(img)

        processResultIndexMap = imgProCom.context.processResultIndexMap
        processResult = imgProCom.context.processResult
        self.warning_alarm_timeout(processResultIndexMap,processResult,img.size()[0])

        if self.isTrigger():
            dirPath = Modules.instance().paths.img_path
            # 生成时间戳文件名：YYYYMMDD_HHMMSS_mmm.jpg
            try:
                t = time.time()
                lt = time.localtime(t)
                ms = int((t - int(t)) * 1000)
                fname = "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}_{:03d}.jpg".format(
                    lt[0], lt[1], lt[2], lt[3], lt[4], lt[5], ms)
            except Exception:
                # 兜底：使用引擎时钟或时间戳
                gc = getattr(MApplication.instance(), "game_clock", None)
                if gc:
                    fname = "img_{:d}.jpg".format(int(gc.unscaled_total_ms))
                else:
                    fname = "img_{:d}.jpg".format(int(time.time() * 1000))
            # 确保目录存在并保存
            try:
                if dirPath and not os.path.exists(dirPath):
                    os.makedirs(dirPath)
            except Exception:
                pass
            img.save(os.path.join(dirPath, fname))

        maskImg = imgProCom.getMaskImg(img)

        mods = Modules.instance()
        if getattr(mods, "disDebug", None):
            mods.disDebug.setImage(maskImg)
            mods.countLabel.setText(str(len(imgProCom.context.processResult)))

    def run_stop(self):
        # 停止模式下可做低频维护任务，或直接 return
        return
    
    def isTriggerTakePictures(self):
        return Modules.instance().keyMonotor.peek_click(key_id=UserKey)