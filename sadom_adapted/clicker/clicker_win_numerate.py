# pyinstaller -F --upx-exclude "vcruntime140.dll" --onefile clicker_win_numerate.py
import os.path
from tkinter import *
from time import sleep
import sys


def create_window():
    window = Toplevel(root)
    return window


def set_params(obj, params):
    x_coord, y_coord = int(params[1]) + 30, int(params[2]) + 30
    obj.geometry(f'{size}x{size}+{x_coord}+{y_coord}')
    obj.overrideredirect(True)
    obj.attributes("-topmost", True)
    label = Label(obj, text=params[0], font=("Arial", 100, 'bold'))
    label.pack(fill='both', expand=True)
    obj.after(3000, lambda: obj.destroy())


if __name__ == "__main__":
    size = 200
    conf_file = 'clicker_win_numerate_conf.txt'
    while True:
        params = ''
        if not os.path.exists(conf_file):
            open(conf_file, 'w').close()
        with open(conf_file, 'r') as f:
            params = f.readline()
        if params:
            open(conf_file, 'w').close()
            params = [item.split("|") for item in params.split(" ")]
            print(f'Yeah: {params}')
            root = Tk()
            set_params(root, params[0])
            for item in params[1:]:
                win = create_window()
                set_params(win, item)

            root.mainloop()

        sleep(1)
