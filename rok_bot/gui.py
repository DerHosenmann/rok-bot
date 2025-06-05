import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk

DEFAULT_CONFIDENCE = 0.8
DEFAULT_SCROLL_DURATION = 2.0
DEFAULT_SCANS_PER_PASS = 5
DEFAULT_PAUSE_NO_GEM = 0.5
DEFAULT_ZOOM_CLICKS_FIRST = 0
DEFAULT_ZOOM_CLICKS_SECOND = 0
DEFAULT_ZOOM_CLICKS_THIRD = 0
DEFAULT_FARMING_DURATION = 300

bot_process = None
log_file_position = 0

def start_bot():
    global bot_process, log_file_position
    if bot_process is None or bot_process.poll() is not None:
        script_path = os.path.join(os.path.dirname(__file__), 'gem_farmer.py')
        try:
            open(log_file_path, 'w').close()
            log_file_position = 0
            bot_process = subprocess.Popen([
                'python',
                script_path,
                '--confidence-gem', str(confidence_var.get()),
                '--scroll-duration', str(scroll_duration_var.get()),
                '--scans-per-pass', str(scans_var.get()),
                '--pause-no-gem', str(pause_var.get()),
                '--zoom-out-clicks-first', str(zoom_first_var.get()),
                '--zoom-out-clicks-second', str(zoom_second_var.get()),
                '--zoom-out-clicks-third', str(zoom_third_var.get()),
                '--farming-duration', str(farming_duration_var.get()),
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
root.geometry('600x500')
root.resizable(True, True)

style = ttk.Style(root)
try:
    style.theme_use('clam')
except tk.TclError:
    pass

frame = ttk.Frame(root, padding=10)
frame.pack(fill='x')

options = ttk.LabelFrame(root, text='Settings', padding=10)
options.pack(fill='x', padx=10, pady=5)

ttk.Label(options, text='Gem detection confidence (0-1):').grid(row=0, column=0, sticky='w')
confidence_var = tk.DoubleVar(value=DEFAULT_CONFIDENCE)
ttk.Entry(options, textvariable=confidence_var, width=6).grid(row=0, column=1, sticky='w')

ttk.Label(options, text='Scroll duration per segment (s):').grid(row=1, column=0, sticky='w')
scroll_duration_var = tk.DoubleVar(value=DEFAULT_SCROLL_DURATION)
ttk.Entry(options, textvariable=scroll_duration_var, width=6).grid(row=1, column=1, sticky='w')

ttk.Label(options, text='Scans per horizontal pass:').grid(row=2, column=0, sticky='w')
scans_var = tk.IntVar(value=DEFAULT_SCANS_PER_PASS)
ttk.Entry(options, textvariable=scans_var, width=6).grid(row=2, column=1, sticky='w')

ttk.Label(options, text='Pause if no gem (s):').grid(row=3, column=0, sticky='w')
pause_var = tk.DoubleVar(value=DEFAULT_PAUSE_NO_GEM)
ttk.Entry(options, textvariable=pause_var, width=6).grid(row=3, column=1, sticky='w')

ttk.Label(options, text='Zoom out clicks after march (step 1):').grid(row=4, column=0, sticky='w')
zoom_first_var = tk.IntVar(value=DEFAULT_ZOOM_CLICKS_FIRST)
ttk.Entry(options, textvariable=zoom_first_var, width=6).grid(row=4, column=1, sticky='w')

ttk.Label(options, text='Zoom out clicks after march (step 2):').grid(row=5, column=0, sticky='w')
zoom_second_var = tk.IntVar(value=DEFAULT_ZOOM_CLICKS_SECOND)
ttk.Entry(options, textvariable=zoom_second_var, width=6).grid(row=5, column=1, sticky='w')
ttk.Label(options, text='Zoom out clicks after march (step 3):').grid(row=6, column=0, sticky='w')
zoom_third_var = tk.IntVar(value=DEFAULT_ZOOM_CLICKS_THIRD)
ttk.Entry(options, textvariable=zoom_third_var, width=6).grid(row=6, column=1, sticky='w')
ttk.Label(options, text='Farming wait after dispatch (s):').grid(row=7, column=0, sticky='w')
farming_duration_var = tk.IntVar(value=DEFAULT_FARMING_DURATION)
ttk.Entry(options, textvariable=farming_duration_var, width=6).grid(row=7, column=1, sticky='w')

start_button = ttk.Button(frame, text='Start Bot', command=start_bot)
start_button.grid(row=0, column=0, padx=5, pady=5)

stop_button = ttk.Button(frame, text='Stop Bot', command=stop_bot)
stop_button.grid(row=0, column=1, padx=5, pady=5)

status_var = tk.StringVar(value='Bot stopped')
status_label = ttk.Label(frame, textvariable=status_var)
status_label.grid(row=1, column=0, columnspan=2)

ttk.Label(root, text='Activity Log:').pack(anchor='w', padx=10)
log_box = ScrolledText(root, width=70, height=20, state='disabled')
log_box.pack(padx=10, pady=10, fill='both', expand=True)

log_file_path = os.path.join(os.path.dirname(__file__), 'bot_status.log')

def update_log_box():
    global log_file_position
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            f.seek(log_file_position)
            new_text = f.read()
            log_file_position = f.tell()
        if new_text:
            log_box.config(state='normal')
            log_box.insert(tk.END, new_text)
            # Limit to last 300 lines
            lines = log_box.get('1.0', tk.END).splitlines()
            if len(lines) > 300:
                start_index = len(lines) - 300 + 1
                log_box.delete('1.0', f'{start_index}.0')
            # Auto-scroll only if at bottom
            _, last = log_box.yview()
            if last == 1.0:
                log_box.see(tk.END)
            log_box.config(state='disabled')
    except FileNotFoundError:
        pass
    root.after(1000, update_log_box)

root.protocol('WM_DELETE_WINDOW', on_close)
update_log_box()
root.mainloop()
