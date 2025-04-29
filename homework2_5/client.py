import tkinter as tk
from tkinter import messagebox
import socket

class ATMClient:
    def __init__(self, master):
        self.master = master
        self.master.title("ATM Client")
        self.master.geometry("300x200")

        # 直接设置目标服务器的IP地址（需手动修改为实际IP）
        self.host = "192.168.157.219"  # 替换为你的服务器IP
        self.port = 2525
        self.sock = None
        self.current_user = None
        self.authenticated = False

        # 删除原 show_connection_frame() 逻辑，直接尝试连接
        self.create_connection()
        self.show_login_frame()  # 直接显示登录界面

    def create_connection(self):
        try:
            self.sock = socket.socket()
            self.sock.connect((self.host, self.port))  # 使用预设的IP
        except Exception as e:
            messagebox.showerror("错误", f"连接失败: {e}")
            self.master.destroy()  # 连接失败直接退出

    def show_login_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.master)
        frame.pack(pady=20)

        tk.Label(frame, text="用户ID:").grid(row=0, column=0)
        self.user_entry = tk.Entry(frame)
        self.user_entry.grid(row=0, column=1)

        tk.Button(frame, text="登录", command=self.send_helo).grid(row=1, columnspan=2, pady=10)

    def send_helo(self):
        userid = self.user_entry.get().strip()
        if not userid:
            messagebox.showerror("错误", "请输入用户ID")
            return

        try:
            self.sock.send(f"HELO {userid}".encode())
            response = self.sock.recv(1024).decode()
            if response == "500 AUTH REQUIRE":
                self.current_user = userid
                self.show_password_frame()
            else:
                messagebox.showerror("错误", "无效的用户ID")
        except Exception as e:
            messagebox.showerror("错误", f"通信错误: {e}")

    def show_password_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.master)
        frame.pack(pady=20)

        tk.Label(frame, text="密码:").grid(row=0, column=0)
        self.pass_entry = tk.Entry(frame, show="*")
        self.pass_entry.grid(row=0, column=1)

        tk.Button(frame, text="提交", command=self.send_pass).grid(row=1, columnspan=2, pady=10)

    def send_pass(self):
        password = self.pass_entry.get().strip()
        if not password:
            messagebox.showerror("错误", "请输入密码")
            return

        try:
            self.sock.send(f"PASS {password}".encode())
            response = self.sock.recv(1024).decode()
            if response == "525 OK!":
                self.authenticated = True
                self.show_main_menu()
            else:
                messagebox.showerror("错误", "密码错误")
                self.show_login_frame()
        except Exception as e:
            messagebox.showerror("错误", f"通信错误: {e}")

    def show_main_menu(self):
        self.clear_frame()
        frame = tk.Frame(self.master)
        frame.pack(pady=20)

        tk.Button(frame, text="查询余额", width=15, command=self.check_balance).pack(pady=5)
        tk.Button(frame, text="取款", width=15, command=self.show_withdraw).pack(pady=5)
        tk.Button(frame, text="退出", width=15, command=self.logout).pack(pady=5)

    def check_balance(self):
        try:
            self.sock.send("BALA".encode())
            response = self.sock.recv(1024).decode()
            if response.startswith("AMNT:"):
                balance = response.split(":")[1]
                messagebox.showinfo("余额", f"当前余额: ${balance}")
            else:
                messagebox.showerror("错误", "获取余额失败")
        except Exception as e:
            messagebox.showerror("错误", f"通信错误: {e}")

    def show_withdraw(self):
        withdraw_win = tk.Toplevel(self.master)
        withdraw_win.title("取款")

        tk.Label(withdraw_win, text="金额:").pack(pady=5)
        self.amount_entry = tk.Entry(withdraw_win)
        self.amount_entry.pack(pady=5)

        tk.Button(withdraw_win, text="提交", command=lambda: self.withdraw(self.amount_entry.get())).pack(pady=10)

    def withdraw(self, amount):
        try:
            amount = float(amount)
            if amount <= 0:
                messagebox.showerror("错误", "无效金额")
                return

            self.sock.send(f"WDRA {amount:.2f}".encode())
            response = self.sock.recv(1024).decode()
            if response == "525 OK!":
                messagebox.showinfo("成功", "取款成功")
            else:
                messagebox.showerror("错误", "取款失败")
        except ValueError:
            messagebox.showerror("错误", "无效金额")
        except Exception as e:
            messagebox.showerror("错误", f"通信错误: {e}")

    def logout(self):
        try:
            self.sock.send("BYE".encode())
            response = self.sock.recv(1024).decode()
            if response == "BYE":
                self.authenticated = False
                self.current_user = None
                self.sock.close()
                self.create_connection()
                self.show_login_frame()
        except Exception as e:
            messagebox.showerror("错误", f"退出错误: {e}")

    def clear_frame(self):
        for widget in self.master.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ATMClient(root)
    root.mainloop()