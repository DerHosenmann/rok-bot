import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

DEFAULT_CONFIDENCE = 0.8
DEFAULT_SCROLL_DURATION = 2.0
DEFAULT_SCANS_PER_PASS = 5
DEFAULT_PAUSE_NO_GEM = 0.5

bot_process = None

def start_bot():
    global bot_process
    if bot_process is None or bot_process.poll() is not None:
        script_path = os.path.join(os.path.dirname(__file__), 'gem_farmer.py')
        try:
            open(log_file_path, 'w').close()
            bot_process = subprocess.Popen([
                'python',
                script_path,
                '--confidence-gem', str(confidence_var.get()),
                '--scroll-duration', str(scroll_duration_var.get()),
                '--scans-per-pass', str(scans_var.get()),
                '--pause-no-gem', str(pause_var.get()),
            ])
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
        update_log_box()
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

options = tk.LabelFrame(root, text='Settings', padx=10, pady=10)
options.pack(fill='x', padx=10, pady=5)

tk.Label(options, text='Gem detection confidence (0-1):').grid(row=0, column=0, sticky='w')
confidence_var = tk.DoubleVar(value=DEFAULT_CONFIDENCE)
tk.Entry(options, textvariable=confidence_var, width=6).grid(row=0, column=1, sticky='w')

tk.Label(options, text='Scroll duration per segment (s):').grid(row=1, column=0, sticky='w')
scroll_duration_var = tk.DoubleVar(value=DEFAULT_SCROLL_DURATION)
tk.Entry(options, textvariable=scroll_duration_var, width=6).grid(row=1, column=1, sticky='w')

tk.Label(options, text='Scans per horizontal pass:').grid(row=2, column=0, sticky='w')
scans_var = tk.IntVar(value=DEFAULT_SCANS_PER_PASS)
tk.Entry(options, textvariable=scans_var, width=6).grid(row=2, column=1, sticky='w')

tk.Label(options, text='Pause if no gem (s):').grid(row=3, column=0, sticky='w')
pause_var = tk.DoubleVar(value=DEFAULT_PAUSE_NO_GEM)
tk.Entry(options, textvariable=pause_var, width=6).grid(row=3, column=1, sticky='w')

start_button = tk.Button(frame, text='Start Bot', command=start_bot)
start_button.grid(row=0, column=0, padx=5, pady=5)

stop_button = tk.Button(frame, text='Stop Bot', command=stop_bot)
stop_button.grid(row=0, column=1, padx=5, pady=5)

status_var = tk.StringVar(value='Bot stopped')
status_label = tk.Label(frame, textvariable=status_var)
status_label.grid(row=1, column=0, columnspan=2)

log_box = ScrolledText(root, width=60, height=20, state='disabled')
log_box.pack(padx=10, pady=10)

log_file_path = os.path.join(os.path.dirname(__file__), 'bot_status.log')

def update_log_box():
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        log_box.config(state='normal')
        log_box.delete('1.0', tk.END)
        log_box.insert(tk.END, ''.join(lines[-200:]))
        log_box.see(tk.END)
        log_box.config(state='disabled')
    except FileNotFoundError:
        pass
    root.after(1000, update_log_box)

root.protocol('WM_DELETE_WINDOW', on_close)
update_log_box()
root.mainloop()
