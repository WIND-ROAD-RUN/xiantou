from ImgProModule.Utility import ProcessResultIndexMap
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

    def decide_alarm_action_by_xiantou(self, processResultIndexMap: ProcessResultIndexMap)->bool:
        cfg = Modules.instance().config

        if len(processResultIndexMap) == 0:
            return True
        else:
            try:
                xiantou_count = len(processResultIndexMap.get(ClassId.XianTou, []))
            except Exception:
                try:
                    xiantou_count = len(processResultIndexMap[ClassId.XianTou])
                except Exception:
                    xiantou_count = 0

            if xiantou_count > int(cfg.ng_yuzhi):
                return False
            else:
                return True
            
    def decide_alarm_Frame_must_alarm_without_windowSize(self, processResultIndexMap: ProcessResultIndexMap):
        try:
            duanxian_count = len(processResultIndexMap.get(ClassId.duanxian, []))
            print(processResultIndexMap)
        except Exception:
            try:
                duanxian_count = len(processResultIndexMap[ClassId.duanxian])
            except Exception:
                duanxian_count = 0

            if duanxian_count > 0:
                return True
            else:
                return False
            
    def decide_alarm_Frame_is_skip(self, processResultIndexMap: ProcessResultIndexMap):
        isSkip = False
        if len(processResultIndexMap) == 0:
            isSkip=False
        else:
            try:
                qita = len(processResultIndexMap.get(ClassId.qita, []))
            except Exception:
                try:
                    qita = len(processResultIndexMap[ClassId.qita])
                except Exception:
                    qita = 0
            
            if qita > 0:
                isSkip = True
            
            #print("断线数量:",duanxian_count,"其他异常数量:",qita,"本帧是否跳过报警:",isSkip)


        return isSkip

    def decide_alarm_action(self, processResultIndexMap: ProcessResultIndexMap):
        """
        判断是否需要开启或关闭报警（纯判断，不直接操作硬件）。

        说明：
        - 本函数只负责根据当前帧的检测结果与内部计数器得出动作决策，
          返回 "open" / "close" / None，具体执行由调用方 open_alarm()/close_alarm() 完成。
        - 使用滑动窗口统计最近 N 帧（window_size，来源于 cfg.ng_baojinshu_rongyu）
          中被判定为“本帧告警”的帧数；当窗口内告警帧数 >= cfg.ng_baojingshu 时，
          返回 "open" 请求开启报警。
        - 关闭规则：当连续清洁帧（即非告警帧）达到 clear_needed 次（来源于 cfg.alarm_clear_consecutive）
          时，返回 "close" 请求关闭报警，并重置相关计数器。
        - 本函数会维护以下内部状态：
            self._recent_alarm_window : 最近若干帧的 0/1 列表（1 表示本帧为告警）
            self._clear_counter         : 连续合格（非告警）帧计数
            self._alarm_counter         : （兼容旧逻辑）可用于记录连续未合格次数（此处未增加）
        - 若当前帧被 decide_alarm_Frame_is_skip 判定为跳过（例如断线/其他异常），
          则不会更新窗口或计数器，也不会返回动作（返回 None）。

        参数：
            processResultIndexMap (ProcessResultIndexMap) -- 引擎/算法产生的本帧结果映射

        返回：
            "open"  -- 表示应开启报警（调用方应执行 open_alarm）
            "close" -- 表示应关闭报警（调用方应执行 close_alarm）
            None    -- 表示不做任何动作

        注意：
        - 函数内部对 cfg 字段做了容错处理（int 转换、默认值回退），以避免配置异常导致崩溃。
        - 函数不会直接与硬件或定时器交互，便于单元测试和职责分离。
        """
        cfg = Modules.instance().config

        # 如果之前的跳帧计数器未用尽，直接跳过本帧判定（消耗一次）
        if getattr(self, "_skip_frames_remaining", 0) > 0:
            try:
                self._skip_frames_remaining -= 1
            except Exception:
                self._skip_frames_remaining = 0
            return None

        # 获取连续合格清除阈值（连续多少帧为合格才关闭报警）
        try:
            clear_needed = int(getattr(cfg, "alarm_clear_consecutive", self._clear_required))
        except Exception:
            clear_needed = self._clear_required

        # 如果当前帧因断线/其他异常被判定为跳过报警，则跳过当前帧并标记再跳若干帧（总跳过帧数由 self.skip_frame_total 控制）
        isSkip = self.decide_alarm_Frame_is_skip(processResultIndexMap)
        if isSkip:
            try:
                # 当前帧已被跳过，设置后续需要跳过的帧数（总跳过帧数 = self.skip_frame_total）
                self._skip_frames_remaining = max(0, int(getattr(self, "skip_frame_total", 2)) - 1)
            except Exception:
                self._skip_frames_remaining = max(0, 2 - 1)
            return None
        
        isMustAlarm = self.decide_alarm_Frame_must_alarm_without_windowSize(processResultIndexMap)
        if isMustAlarm:
            print("本帧断线告警，直接开启报警")
            return "open"
        elif isMustAlarm is False:
            return None

        # 判断本帧是否为线头告警（decide_alarm_action_by_xiantou 返回 True 表示“无告警/合格”）
        isXiantouAlarm = self.decide_alarm_action_by_xiantou(processResultIndexMap)
        # 语义：isAlarmInFrame 为 True 表示本帧被视为“告警帧”
        isAlarmInFrame = bool(isXiantouAlarm)

        # 窗口大小（最近 N 帧），优先读取配置 ng_baojinshu_rongyu
        try:
            window_size = int(getattr(cfg, "ng_baojinshu_rongyu", self._window_size))
        except Exception:
            window_size = self._window_size

        # 将本帧告警（0/1）推入滑动窗口并保证长度
        self._recent_alarm_window.append(1 if isAlarmInFrame else 0)
        if len(self._recent_alarm_window) > window_size:
            try:
                self._recent_alarm_window.pop(0)
            except Exception:
                # 出错则截取最近 window_size 个元素以恢复一致性
                self._recent_alarm_window = self._recent_alarm_window[-window_size:]

        # 统计窗口内告警帧数（容错求和）
        try:
            alarm_count_in_window = sum(self._recent_alarm_window)
        except Exception:
            alarm_count_in_window = 0
            for v in self._recent_alarm_window:
                try:
                    alarm_count_in_window += int(bool(v))
                except Exception:
                    pass

        # 读取触发告警所需的帧内告警次数阈值（cfg.ng_baojingshu）
        try:
            ng_threshold = int(cfg.ng_baojingshu)
        except Exception:
            ng_threshold = 1

        # 如果窗口内达到触发条件，则请求开启报警
        if alarm_count_in_window >= ng_threshold:
            # 打印滑动窗口调试信息：窗口内容、窗口内告警数、阈值、窗口大小
            try:
                print("Alarm-window:", self._recent_alarm_window,
                      "count_in_window:", alarm_count_in_window,
                      "ng_threshold:", ng_threshold,
                      "window_size:", window_size)
            except Exception:
                pass
            # 遇到触发情况时，重置连续合格计数（因为出现了告警）
            self._clear_counter = 0
            return "open"

        # 如果本帧被认为是合格（非告警），则增加连续合格计数，满足条件时请求关闭报警
        if not isAlarmInFrame:
            self._clear_counter += 1
            if self._clear_counter >= clear_needed:
                # 达到关闭条件：重置计数与窗口，返回关闭请求
                self._clear_counter = 0
                self._recent_alarm_window = []
                return "close"
            else:
                return None

        # 默认不做任何动作
        return None

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

    def warning_alarm_timeout(self, processResultIndexMap: ProcessResultIndexMap):
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

        action = self.decide_alarm_action(processResultIndexMap)
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
        self.warning_alarm_timeout(processResultIndexMap)

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