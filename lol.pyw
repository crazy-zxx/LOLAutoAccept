import os
import time
import requests
import re
import base64
import urllib3
import threading
import tkinter as tk
from tkinter import messagebox

urllib3.disable_warnings()


class LOL:
    def __init__(self):
        super().__init__()
        self.__url = None
        self.__headers = None
        self.__token = None
        self.__port = None
        self.__result = None

    def update_game_status(self):
        # 运行 cmd 命令获取输出结果
        result = os.popen('wmic PROCESS WHERE name="LeagueClientUx.exe" GET commandline')
        self.__result = result.read().replace(' ', '').split(' ')

        # 游戏未启动的时候会返回：['\n\n\n\n']
        if len(self.__result[0]) < 5:
            return False
        else:
            # 获取用户 token
            token = re.findall(re.compile(r'"--remoting-auth-token=(.*?)"'), self.__result[0])
            # 获取用户端口
            self.__port = re.findall(re.compile(r'"--app-port=(.*?)"'), self.__result[0])
            # 获取解密之后的 token
            self.__token = base64.b64encode(("riot:" + token[0]).encode("UTF-8")).decode("UTF-8")
            # 制作请求头
            self.__headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": "Basic " + self.__token
            }
            # 构造本机请求地址
            self.__url = 'https://127.0.0.1:' + str(self.__port[0])

            return True

    def get(self, url):
        return requests.get(url=self.__url + url, headers=self.__headers, verify=False).json()

    def post(self, url):
        return requests.post(url=self.__url + url, headers=self.__headers, verify=False).json()

    def auto_accept(self, stop_event):
        # 检测停止线程的事件
        while not stop_event.is_set():
            try:
                # 检查并更新用户的游戏状态信息
                if self.update_game_status():
                    state_url = self.__url + '/lol-lobby/v2/lobby/matchmaking/search-state'
                    accept_url = self.__url + '/lol-matchmaking/v1/ready-check/accept'
                    # 查询对局状态：未开始寻找（Invalid）、寻找中（Searching）、找到（Found）
                    resp = requests.get(state_url, headers=self.__headers, verify=False)
                    game_state = resp.json()['searchState']
                    # 如果找到对局，自动接受
                    if game_state == 'Found':
                        resp = requests.post(accept_url, headers=self.__headers, verify=False)
            except Exception as e:
                # print(e)
                pass
            finally:
                time.sleep(3)


class LOLUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LOL自动接受对局工具")
        # 设置窗口大小
        window_width = 300
        window_height = 150
        # 获取屏幕宽度和高度
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        # 计算窗口左上角的坐标
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        # 设置窗口的位置和大小
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        # 禁止调整窗口大小
        self.root.resizable(False, False)

        self.lol = LOL()
        self.stop_event = threading.Event()
        self.thread = None

        self.start_button = tk.Button(root, text="启动自动接受", command=self.start_auto_accept)
        self.start_button.pack(pady=20)

        self.stop_button = tk.Button(root, text="停止自动接受", command=self.stop_auto_accept, state=tk.DISABLED)
        self.stop_button.pack(pady=20)

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_auto_accept(self):
        if not self.thread or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self.lol.auto_accept, args=(self.stop_event,))
            self.thread.start()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            messagebox.showwarning("警告", "自动接受已经在运行中！")

    def stop_auto_accept(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join()
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def on_close(self):
        self.stop_auto_accept()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = LOLUI(root)
    # 打开软件后默认启动自动接受对局
    app.start_auto_accept()
    # 打开软件后默认最小化窗口
    root.iconify()
    root.mainloop()
