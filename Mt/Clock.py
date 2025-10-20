import time
from collections import deque

try:
    ticks_ms = time.ticks_ms
    ticks_diff = time.ticks_diff
except Exception:
    # 兼容性回退
    import time as _time
    def ticks_ms():
        return int(_time.time() * 1000)
    def ticks_diff(a, b):
        return a - b

class RealTimeClock:
    """包装系统真实时间（可扩展为 RTC / NTP 同步）。
    单例：使用 RealTimeClock.instance() 获取唯一实例。
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RealTimeClock, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 无需重复初始化字段，目前为空实现
        pass

    @classmethod
    def instance(cls):
        return cls()

    def now(self):
        # 返回秒级 UNIX 时间或本地时间结构，根据需要扩展
        try:
            return time.time()
        except Exception:
            return ticks_ms() / 1000.0

class Timer:
    """内部使用的定时器对象"""
    def __init__(self, delay_ms, callback, repeat=False, interval_ms=None):
        self.delay_ms = delay_ms
        self.callback = callback
        self.repeat = repeat
        self.interval_ms = interval_ms if interval_ms is not None else delay_ms
        self._acc = 0
        self.active = True

class GameClock:
    """
    引擎时钟（单例）：每帧调用 update(dt_ms)
    支持 time_scale、暂停、fixed timestep 回调、一次/周期定时器调度。
    获取实例用 GameClock.instance(fixed_dt_ms=...)
    注意：首次创建时可传 fixed_dt_ms，后续调用忽略该参数并返回同一实例。
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GameClock, cls).__new__(cls)
        return cls._instance

    def __init__(self, fixed_dt_ms=None):
        # 仅首次初始化时设置属性
        if getattr(self, "_inited", False):
            return
        self._inited = True

        self.total_ms = 0            # 引擎累计时间（毫秒，受 time_scale 影响）
        self.unscaled_total_ms = 0   # 真实累计毫秒（不受 time_scale）
        self.delta_ms = 0
        self.unscaled_delta_ms = 0
        self.time_scale = 1.0
        self.paused = False
        self._last_tick = ticks_ms()
        self._timers = []            # list of Timer
        self._fixed_dt_ms = fixed_dt_ms  # 若指定，支持固定步长模拟
        self._fixed_acc = 0
        self._fixed_callbacks = []   # callbacks called on fixed steps: func(fixed_dt_ms)
        # FPS 统计
        self._fps_acc_ms = 0
        self._frame_count = 0
        self.fps = 0
        # 防止固定步数过多（spiral），可配置
        self.max_fixed_steps_per_update = 5

    @classmethod
    def instance(cls, fixed_dt_ms=None):
        # 方便统一获取单例：首次可传 fixed_dt_ms
        inst = cls(fixed_dt_ms=fixed_dt_ms)
        return inst

    def now_ms(self):
        return ticks_ms()

    def update(self, dt_ms):
        """用外部计算出来的 dt（ms）驱动；也可以内部自动计算差值
        处理：确保 dt_ms 非负；若传入为负或异常则尝试用 ticks_ms/ticks_diff 重算。
        """
        # 规范化 dt_ms 为整数，防止传入异常值
        try:
            dt_ms = int(dt_ms)
        except Exception:
            dt_ms = 0

        # 若传入 dt_ms 为负或 0，尝试用底层 ticks 重新计算（兼容回绕）
        if dt_ms <= 0:
            try:
                now_ticks = ticks_ms()
                last = getattr(self, "_last_tick", None)
                if last is None:
                    dt_calc = 0
                else:
                    try:
                        dt_calc = int(ticks_diff(now_ticks, last))
                    except Exception:
                        dt_calc = int(now_ticks - last)
                    # 处理回绕或异常，保证非负
                    if dt_calc < 0:
                        dt_calc = 0
                dt_ms = dt_calc
                # 更新内部 last tick
                self._last_tick = now_ticks
            except Exception:
                # 最后兜底置 0（避免负数影响统计）
                dt_ms = 0
        else:
            # 若传入正常，仍记录 last tick 为当前 ticks（保持同步）
            try:
                self._last_tick = ticks_ms()
            except Exception:
                pass
        
        # unscaled 时间
        self.unscaled_delta_ms = dt_ms
        self.unscaled_total_ms += dt_ms

        # scaled 时间（受暂停与 time_scale）
        if self.paused:
            self.delta_ms = 0
        else:
            self.delta_ms = int(dt_ms * self.time_scale)
            self.total_ms += self.delta_ms

        # FPS 统计（改为每 1s 更新并平滑）
        self._frame_count += 1
        self._fps_acc_ms += dt_ms
        if self._fps_acc_ms >= 1000:  # 1 秒窗口
            avg = (self._frame_count * 1000.0) / max(1, self._fps_acc_ms)
            self.fps = int(avg)
            self._frame_count = 0
            self._fps_acc_ms = 0

        # 定时器更新（以 unscaled 时间为基准）
        if self._timers:
            for t in list(self._timers):
                if not t.active:
                    continue
                t._acc += dt_ms
                if t._acc >= t.delay_ms:
                    try:
                        t.callback()
                    except Exception:
                        pass
                    if t.repeat:
                        t._acc -= t.interval_ms
                    else:
                        t.active = False
                        try:
                            self._timers.remove(t)
                        except ValueError:
                            pass

        # fixed timestep 回调（使用 scaled delta_ms 做步进，遵循 time_scale/paused）
        if self._fixed_dt_ms:
            self._fixed_acc += self.delta_ms
            steps = 0
            while self._fixed_acc >= self._fixed_dt_ms and steps < self.max_fixed_steps_per_update:
                for cb in list(self._fixed_callbacks):
                    try:
                        cb(self._fixed_dt_ms)
                    except Exception:
                        pass
                self._fixed_acc -= self._fixed_dt_ms
                steps += 1
            # 若累积过大，避免无限循环，保留剩余部分或重设为固定上限
            if self._fixed_acc >= self._fixed_dt_ms:
                # clamp remaining acc to at most one fixed step
                self._fixed_acc = min(self._fixed_acc, self._fixed_dt_ms)

    # timer api
    def schedule_once(self, delay_ms, callback):
        t = Timer(delay_ms, callback, repeat=False)
        self._timers.append(t)
        return t

    def schedule_interval(self, interval_ms, callback):
        t = Timer(interval_ms, callback, repeat=True, interval_ms=interval_ms)
        self._timers.append(t)
        return t

    def cancel_timer(self, timer):
        timer.active = False
        try:
            self._timers.remove(timer)
        except ValueError:
            pass

    # fixed update api
    def add_fixed_callback(self, callback):
        if callback not in self._fixed_callbacks:
            self._fixed_callbacks.append(callback)

    def remove_fixed_callback(self, callback):
        if callback in self._fixed_callbacks:
            self._fixed_callbacks.remove(callback)

    # helpers
    def set_time_scale(self, scale):
        self.time_scale = float(scale)

    def reset(self):
        self.total_ms = 0
        self.unscaled_total_ms = 0
        self.delta_ms = 0
        self.unscaled_delta_ms = 0
        self._timers.clear()
        self._fixed_callbacks.clear()
        self._fixed_acc = 0
        self.fps = 0

# module-level convenience singletons (惰性创建也可直接使用 .instance())
_realtime_clock = None
_game_clock = None

def realtime_clock():
    global _realtime_clock
    if _realtime_clock is None:
        _realtime_clock = RealTimeClock.instance()
    return _realtime_clock

def game_clock(fixed_dt_ms=None):
    global _game_clock
    if _game_clock is None:
        _game_clock = GameClock.instance(fixed_dt_ms=fixed_dt_ms)
    return _game_clock