from maix import key, time
from collections import defaultdict

UserKey=352

class KeyMonitor:
    """
    封装官方 key.Key 回调，提供查询按下/松开/一次完整按下-释放(消费式) 的接口。
    使用示例：
        km = KeyMonitor.instance()
        # 在主循环中：
        if km.is_down(0): ...
        if km.take_click(0):  # 如果有一次按下-释放（未被消费），返回 True 并清除该记录
            ...
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KeyMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        # 当前按键逻辑状态（True 表示被按下）
        self._pressed = defaultdict(lambda: False)
        # 未消费的按下-释放计数
        self._click_counts = defaultdict(int)
        # 最近一次事件的原始状态和值与时间
        self._last_state = {}
        self._last_time = {}

        # 保持 key 对象引用，避免被回收
        try:
            self._key_obj = key.Key(self._on_key)
        except Exception:
            # 在不支持 key.Key 的环境下，允许失败（测试时可模拟）
            self._key_obj = None

    @classmethod
    def instance(cls):
        return cls()

    def _on_key(self, key_id, state):
        """
        官方回调（可能跑在中断/单线程上下文）。尽量简单快速。
        state 可能是枚举也可能是整数，采用通用判断：
          - 如果 state 有 name 属性：包含 'PRESSED' 则认为按下，包含 'RELEASED' 则认为松开
          - 否则按 bool(state) 判断（非 0 视为按下）
        """
        # 解析布尔按下状态
        is_pressed = False
        try:
            name = getattr(state, "name", None)
            if isinstance(name, str):
                if "PRESSED" in name.upper():
                    is_pressed = True
                elif "RELEASED" in name.upper():
                    is_pressed = False
                else:
                    is_pressed = bool(state)
            else:
                is_pressed = bool(state)
        except Exception:
            is_pressed = bool(state)

        prev = self._pressed.get(key_id, False)
        # 检测到从按下 -> 松开 的转变，记为一次 click（未消费）
        if prev and not is_pressed:
            self._click_counts[key_id] += 1

        # 更新状态与时间
        self._pressed[key_id] = is_pressed
        self._last_state[key_id] = state
        try:
            self._last_time[key_id] = time.ticks_ms()
        except Exception:
            self._last_time[key_id] = None

    # 查询接口 ----
    def is_down(self, key_id):
        """返回当前是否为按下状态（bool）。"""
        return bool(self._pressed.get(key_id, False))

    def is_up(self, key_id):
        """返回当前是否为松开状态（bool）。"""
        return not self.is_down(key_id)

    def peek_click(self, key_id):
        """查看是否存在未消费的按下-释放事件（不消费）。"""
        return self._click_counts.get(key_id, 0) > 0

    def take_click(self, key_id):
        """
        消费一次按下-释放事件：如果存在未消费事件则返回 True 并减少计数；
        否则返回 False。
        """
        cnt = self._click_counts.get(key_id, 0)
        if cnt > 0:
            self._click_counts[key_id] = cnt - 1
            return True
        return False

    def clear_clicks(self, key_id=None):
        """清除指定按键（或全部）的未消费 click 记录。"""
        if key_id is None:
            self._click_counts.clear()
        else:
            self._click_counts[key_id] = 0

    def last_event(self, key_id):
        """返回 (state, timestamp) 最近一次事件原始状态及时间，时间可能为 None。"""
        return (self._last_state.get(key_id, None), self._last_time.get(key_id, None))