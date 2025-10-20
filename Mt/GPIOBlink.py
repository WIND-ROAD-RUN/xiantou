# ...existing code...
from maix import gpio, pinmap, time, err
try:
    import _thread
except Exception:
    _thread = None

class GPIOBlink:
    """
    简单 GPIO 输出/闪烁组件
    参数:
      pin_name (str): 引脚名，如 "A29"
      gpio_name (str): gpio 名，如 "GPIOA29"
      initial (int): 初始电平 0/1
    方法:
      set() / clear() / toggle()
      start_blink(period_ms) / stop_blink()
      deinit() 释放资源
    """
    def __init__(self, pin_name="A29", gpio_name="GPIOA29", initial=0):
        err.check_raise(pinmap.set_pin_function(pin_name, gpio_name), "set pin failed")
        self._pin = gpio.GPIO(gpio_name, gpio.Mode.OUT)
        self._pin.value(initial)
        self._blink_running = False
        self._blink_thread_launched = False
        self._lock = None
        if _thread:
            try:
                self._lock = _thread.allocate_lock()
            except Exception:
                self._lock = None

    def setHight(self):
        self._pin.high()

    def setLow(self):
        self._pin.low()

    def set(self):
        self._pin.value(1)

    def clear(self):
        self._pin.value(0)

    def toggle(self):
        # 兼容性：优先使用 toggle 方法，否则用 value 读写
        try:
            self._pin.toggle()
        except Exception:
            try:
                v = self._pin.value()
                self._pin.value(0 if v else 1)
            except Exception:
                # 最后兜底置 1
                self._pin.value(1)

    def _blink_worker(self, period_ms):
        # 后台线程循环
        while self._blink_running:
            try:
                self.toggle()
            except Exception:
                pass
            time.sleep_ms(period_ms)

    def start_blink(self, period_ms=500):
        """启动后台闪烁（非阻塞）。如果设备不支持 _thread，会在当前线程阻塞运行。"""
        if self._blink_running:
            return
        self._blink_running = True
        if _thread:
            try:
                _thread.start_new_thread(self._blink_worker, (period_ms,))
                self._blink_thread_launched = True
                return
            except Exception:
                # 线程启动失败，退化到阻塞模式（调用者需注意）
                pass
        # 无线程支持或线程启动失败，阻塞模式（调用者应在独立协程/线程中调用）
        try:
            self._blink_worker(period_ms)
        except Exception:
            self._blink_running = False
            raise

    def stop_blink(self):
        self._blink_running = False
        # 如果线程未启动且在阻塞模式，则无需额外操作

    def deinit(self):
        self.stop_blink()
        try:
            self.clear()
        except Exception:
            pass
# ...existing code...