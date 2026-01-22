import tkinter as tk
from tkinter import filedialog

def pick_file():
    # root = tk.Tk()
    # root.withdraw()           # 隐藏主窗口
    # try:
    #     path = filedialog.askopenfilename(title="选择文件")
    # finally:
    #     root.destroy()        # 关闭 Tcl/Tk 资源
    path = filedialog.askopenfilename(title="选择文件")
    return path

if __name__ == "__main__":
    chosen = pick_file()
    print("选中：", chosen)