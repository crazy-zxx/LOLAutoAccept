import json
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

# ================================= uin 和 skey 获取 ================================
# 先启动 pengu loader，在英雄联盟界面按 F12 进入开发者模式，查看联盟的HTML源码，找到下面的这个 iframe 元素中的 src 链接：
# <iframe id="rpcs-login-helper2" src="https://ssl.ptlogin2.qq.com/jump?***" style="display: none;"></iframe>
# 打开浏览器，在新建标签页中按 F12 进入开发者模式，访问上面的 src 链接，在第一个请求的响应头的 set-cookie 中可以找到 uin 和 skey 值
uin = 'o1934109821'
skey = '@tnkY9V57o'

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
        print(self.__result)

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

    def auto_accept(self, stop_event):
        # 检测停止线程的事件
        while not stop_event.is_set():
            try:
                # 检查并更新用户的游戏状态信息
                if self.update_game_status():

                    # 查询对局寻找状态
                    state_url = self.__url + '/lol-lobby/v2/lobby/matchmaking/search-state'
                    # 查询对局状态：未开始寻找（Invalid）、寻找中（Searching）、找到（Found）
                    state_resp = requests.get(state_url, headers=self.__headers, verify=False)
                    game_state = state_resp.json()['searchState']
                    # 如果找到对局
                    if game_state == 'Found':
                        # 补充骰子
                        dice_url = "https://comm.ams.game.qq.com/ide/"
                        headers = {
                            "content-type": "application/x-www-form-urlencoded",
                            "cookie": f"uin={uin}; skey={skey};"
                        }
                        # 大乱斗
                        data = {
                            "iChartId": "378916",
                            "iSubChartId": "378916",
                            "sIdeToken": "Rb22Nt",
                            "sArea": "6",
                        }
                        # 无限火力
                        infinite_data = {
                            'iChartId': '393050',
                            'iSubChartId': '393050',
                            'sIdeToken': '6f9Yvi',
                            "sArea": "6",
                        }
                        result = requests.post(url=dice_url, headers=headers, data=data, verify=False)
                        print(json.loads(result.content.decode('utf-8'))['sMsg'])
                        result = requests.post(url=dice_url, headers=headers, data=infinite_data, verify=False)
                        print(json.loads(result.content.decode('utf-8'))['sMsg'])

                        # 自动接受对局
                        accept_url = self.__url + '/lol-matchmaking/v1/ready-check/accept'
                        accept_resp = requests.post(accept_url, headers=self.__headers, verify=False)
                        print(accept_resp.content.decode('utf-8'))

            except Exception as e:
                print(e)
                raise
            finally:
                time.sleep(3)


class LOLUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LOL自动接受对局工具")
        # 设置窗口大小
        window_width = 500
        window_height = 300
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

        info = """
        先启动 pengu loader，在英雄联盟界面按 F12 进入开发者模式，
        查看联盟的HTML源码，找到下面的这个 iframe 元素中的 src 链接：
        <iframe id="rpcs-login-helper2" src="https://ssl.ptlogin2.qq.com/jump?***" 
        打开浏览器，在新建标签页中按 F12 进入开发者模式，访问上面的 src 链接，
        在第一个请求的响应头的 set-cookie 中可以找到 uin 和 skey 值
        """
        self.info = tk.Label(self.root, text=info)
        self.info.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=10)
        self.uin_label = tk.Label(self.root, text="uin：")
        self.uin_label.grid(row=1, column=0, sticky="nsew", padx=5, pady=10)
        self.uin_entry = tk.Entry(self.root, width=25)
        self.uin_entry.insert(0, uin)
        self.uin_entry.grid(row=1, column=1, sticky="nsew", padx=5, pady=10)

        self.skey_label = tk.Label(self.root, text="skey：")
        self.skey_label.grid(row=2, column=0, sticky="nsew", padx=5, pady=10)
        self.skey_entry = tk.Entry(self.root, width=25)
        self.skey_entry.insert(0, skey)
        self.skey_entry.grid(row=2, column=1, sticky="nsew", padx=5, pady=10)

        self.start_button = tk.Button(root, text="启动自动接受", command=self.start_auto_accept)
        self.start_button.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)

        self.stop_button = tk.Button(root, text="停止自动接受", command=self.stop_auto_accept, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, padx=10, pady=10, sticky=tk.E)

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_auto_accept(self):
        if not self.thread or not self.thread.is_alive():
            global uin, skey
            uin = self.uin_entry.get()
            skey = self.skey_entry.get()
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
    # # 打开软件后默认启动自动接受对局
    # app.start_auto_accept()
    # # 打开软件后默认最小化窗口
    # root.iconify()
    root.mainloop()
