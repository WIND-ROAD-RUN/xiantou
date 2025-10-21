from ImgProModule.Utility import ProcessResultIndexMap
from MaixCam.RunningInfo import RunningInfo, RunMode
from MaixCam.Modules import Modules
from Mt.MApplication import MApplication
from Mt.KeyMonitor import UserKey
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

        # 新增：连续空检测计数与阈值（连续多少帧/周期未检测到物体才触发报警）
        self._alarm_counter = 0
        self.enable_alarm = True

        # 长按检测：用于实现“按住2秒切换 enable_alarm”
        self._alarm_press_start_ms = None
        self._alarm_long_pressed_triggered = False

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
                if (not self._alarm_long_pressed_triggered) and (now - self._alarm_press_start_ms >= 2000):
                    self._alarm_long_pressed_triggered = True
                    self.enable_alarm = not self.enable_alarm
                    print("alarm long-press toggled:", self.enable_alarm)
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
            self.run_run()
        elif mode == RunMode.STOP:
            self.run_stop()

    def warning_alarm_timeout(self,processResult:ProcessResultIndexMap):
        warningCom = Modules.instance().warning
        if not self.enable_alarm:
            if getattr(self, "_alarm_timer", None):
                        self._game_clock.cancel_timer(self._alarm_timer)
                        self._alarm_timer = None
            warningCom.setLow()       
            return

        
        cfg=Modules.instance().config

        # 无检测结果：计数 +1；有检测结果：清零并立即关闭报警
        if len(processResult) == 0:
            self._alarm_counter += 1
        else:
            if len(processResult[0]) < int(cfg.ng_yuzhi):
                self._alarm_counter += 1
            else:
                # 有检测到物体：重置计数，取消定时器并确保报警关闭
                self._alarm_counter = 0
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

        # 只有达到连续未检测阈值才真正触发报警
        if self._alarm_counter < int(cfg.ng_baojingshu):
            # 阈值未达，不报警（可选：确保报警为低电平）
            try:
                warningCom.setLow()
            except Exception:
                pass
            return

        # 达到阈值：开启报警，并把关闭报警的定时器重置为 cfg.baojingshijian ms（每次触发都会重置计时）
        try:
            warningCom.setHight()
        except Exception:
            pass

        # 取消已有定时器（如果存在），重新安排 cfg.baojingshijian ms 后关闭报警
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
            # 清除句柄
            try:
                self._alarm_timer = None
                # 超时后也将计数清零，避免立即再次触发（如果希望保留计数可去掉）
                self._alarm_counter = 0
            except Exception:
                pass

        try:
            self._alarm_timer = self._game_clock.schedule_once(int(cfg.baojingshijian), _alarm_timeout)
        except Exception:
            # 若时钟不可用或调度失败，兜底直接关闭（避免永久报警）
            try:
                warningCom.setLow()
            except Exception:
                pass
            self._alarm_timer = None

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

        processResult = imgProCom.context.processResultIndexMap
        self.warning_alarm_timeout(processResult)

        # 按下按键保存图片
        km = Modules.instance().keyMonotor
        if not km.take_click(key_id=UserKey):
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
            km.clear_clicks()

        #maskImg = imgProCom.getMaskImg(img)

        mods = Modules.instance()
        if getattr(mods, "disDebug", None):
            mods.disDebug.setImage(img)
            mods.countLabel.setText(str(len(imgProCom.context.processResult)))

    def run_stop(self):
        # 停止模式下可做低频维护任务，或直接 return
        return
    
    def isTriggerTakePictures(self):
        return Modules.instance().keyMonotor.peek_click(key_id=UserKey)