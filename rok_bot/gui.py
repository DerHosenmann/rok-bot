import os
import subprocess
import tkinter as tk
from tkinter import messagebox

bot_process = None

def start_bot():
    global bot_process
    if bot_process is None or bot_process.poll() is not None:
        script_path = os.path.join(os.path.dirname(__file__), 'gem_farmer.py')
        try:
            bot_process = subprocess.Popen(['python', script_path])
            status_var.set('Bot running')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to start bot: {e}')
    else:
        messagebox.showinfo('Info', 'Bot is already running')

def stop_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        bot_process.terminate()
        bot_process.wait(timeout=5)
        status_var.set('Bot stopped')
    else:
        messagebox.showinfo('Info', 'Bot is not running')

def on_close():
    if bot_process and bot_process.poll() is None:
        if messagebox.askyesno('Quit', 'Bot is running. Stop it and exit?'):
            stop_bot()
        else:
            return
    root.destroy()

root = tk.Tk()
root.title('RoK Bot GUI')

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

start_button = tk.Button(frame, text='Start Bot', command=start_bot)
start_button.grid(row=0, column=0, padx=5, pady=5)

stop_button = tk.Button(frame, text='Stop Bot', command=stop_bot)
stop_button.grid(row=0, column=1, padx=5, pady=5)

status_var = tk.StringVar(value='Bot stopped')
status_label = tk.Label(frame, textvariable=status_var)
status_label.grid(row=1, column=0, columnspan=2)

root.protocol('WM_DELETE_WINDOW', on_close)
root.mainloop()
