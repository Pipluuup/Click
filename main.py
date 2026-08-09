# -*- coding: utf-8 -*-
"""
字母随机连发器（GUI 版）

通过界面按钮开始 / 停止。开始后全局监听键盘：按下任意英文字母键时，
吞掉原按键，并模拟键盘输入将英文 26 个大写字母（含被按下的那个）
按随机顺序"打"到当前焦点窗口。全局按 F12 可快速停止。

实现要点：
- 使用 keyboard.hook(on_event, suppress=True) 注册"阻塞型"钩子：
  on_event 既能收到每个按键事件，又能通过返回 False 把该按键吞掉
  （不让它落到其他程序）。block_key 做不到这点——被 block 的按键
  根本不会进入普通 hook 的回调。
- 不用手动防递归：keyboard 库对同进程注入的按键（send/write 内部会
  置 is_replaying=True）不会通知自己的钩子，注入的 26 个字母天然
  不会再次触发 on_event。

运行环境：Windows + Python 3 + tkinter（内置）+ `keyboard` 库。
"""
import queue
import random
import string
import time
import tkinter as tk

import keyboard

ALPHABET = string.ascii_uppercase  # A..Z（要输出的内容）
LETTERS = string.ascii_lowercase   # a..z（keyboard 库中字母键名是小写）
STICKY_WINDOW = 0.6  # 同一键 0.6s 内的重复按下视为系统自动重复，忽略（只触发一次）


class App:
    def __init__(self, root):
        self.root = root
        self.running = False
        self.last_trigger = {}
        self.gui_queue = queue.Queue()  # keyboard 线程 -> GUI 主线程 的通知队列

        root.title("字母随机连发器")
        root.resizable(False, False)

        self.status = tk.Label(root, text="● 已停止", fg="#888888", font=("Microsoft YaHei UI", 11))
        self.status.pack(padx=24, pady=(20, 4))

        self.btn = tk.Button(root, text="开始", width=12, font=("Microsoft YaHei UI", 11),
                             command=self.toggle)
        self.btn.pack(pady=(4, 4))

        tk.Label(root, text="开始后按任意字母 → 随机打出 26 个大写字母\n全局按 F12 快速停止",
                 fg="#999999", font=("Microsoft YaHei UI", 9)).pack(padx=12, pady=(0, 12))

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.poll_gui_queue()

    # ---------- 界面 ----------
    def toggle(self):
        self.stop() if self.running else self.start()

    def update_ui(self):
        if self.running:
            self.status.config(text="● 监听中…", fg="#2f9e44")
            self.btn.config(text="停止")
        else:
            self.status.config(text="● 已停止", fg="#888888")
            self.btn.config(text="开始")

    def poll_gui_queue(self):
        """轮询 keyboard 线程发来的通知（如 F12），在 GUI 主线程里安全处理。"""
        try:
            while True:
                item = self.gui_queue.get_nowait()
                if item == "f12":
                    self.stop()
        except queue.Empty:
            pass
        self.root.after(100, self.poll_gui_queue)

    def on_close(self):
        self.running = False
        keyboard.unhook_all()
        self.root.destroy()

    # ---------- 核心逻辑 ----------
    def start(self):
        self.running = True
        self.last_trigger.clear()
        self.install_hooks()
        self.update_ui()

    def stop(self):
        self.running = False
        keyboard.unhook_all()  # 摘下所有钩子，字母键恢复为正常输入
        self.update_ui()

    def install_hooks(self):
        # suppress=True：本回调能收到每个按键，返回 False 即吞掉该键。
        keyboard.hook(self.on_event, suppress=True)

    def on_event(self, event):
        """在 keyboard 库的后台线程里被调用，不能直接操作 tkinter 控件。

        返回 True  -> 放行；返回 False -> 吞掉该键（不落到其他程序）。
        """
        if not self.running:
            return True  # 已停止：一律放行（兜底，避免钩子残留时误吞键）

        name = event.name
        if name == "f12":
            if event.event_type == "down":
                self.gui_queue.put("f12")  # 交给主线程停止
            return False  # 运行期间吞掉 F12
        if name not in LETTERS:
            return True  # 非字母键：放行，不处理

        if event.event_type == "down":
            now = time.monotonic()
            if now - self.last_trigger.get(name, -1.0) < STICKY_WINDOW:
                return False  # 自动重复 / 极快重按 -> 吞掉但不触发（只触发一次）
            self.last_trigger[name] = now
            self.fire()
        return False  # 吞掉字母键（按下与抬起都吞）

    def fire(self):
        """模拟输入 26 个大写字母（每次新随机顺序）。

        无需手动防递归：keyboard 库对同进程注入的按键不会通知自己的钩子，
        注入的字母不会再次触发 on_event。
        """
        letters = list(ALPHABET)
        random.shuffle(letters)  # 每次按下生成新的随机顺序
        # 大写字母在 keyboard.write 中会自动模拟 Shift
        keyboard.write("".join(letters), delay=0)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
