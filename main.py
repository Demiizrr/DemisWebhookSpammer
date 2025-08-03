import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import requests
import threading
import time

SETTINGS_FILE = "settings.json"
WEBHOOK_PREFIX = "https://discord.com/api/webhooks/"
stop_flag = False

def is_valid_webhook(url):
    return url.startswith(WEBHOOK_PREFIX)

def load_settings():
    defaults = {
        "webhook": "",
        "stored_webhooks": [],
        "message": "",
        "name": "",
        "avatar": "",
        "delay": "20",
        "amount": "10"
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                for key, value in defaults.items():
                    data.setdefault(key, value)
                return data
        except:
            pass
    return defaults

def save_settings():
    settings["webhook"] = webhook_entry.get().strip()
    settings["message"] = message_entry.get().strip()
    settings["name"] = name_entry.get().strip()
    settings["avatar"] = avatar_entry.get().strip()
    settings["delay"] = delay_entry.get().strip()
    settings["amount"] = amount_entry.get().strip()
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def log(text):
    log_output.config(state=tk.NORMAL)
    log_output.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {text}\n")
    log_output.see(tk.END)
    log_output.config(state=tk.DISABLED)

def refresh_webhook_list():
    webhook_listbox.delete(0, tk.END)
    for item in settings["stored_webhooks"]:
        name = item.get("name", item.get("url", ""))
        webhook_listbox.insert(tk.END, name[:50])

def save_current_webhook():
    current = webhook_entry.get().strip()
    if not is_valid_webhook(current):
        messagebox.showerror("Invalid Webhook", "Webhook must start with:\n" + WEBHOOK_PREFIX)
        return

    try:
        response = requests.get(current, timeout=5)
        if response.status_code != 200:
            messagebox.showerror("Invalid Webhook", f"The webhook is inaccessible (status {response.status_code}). Removing.")
            settings["stored_webhooks"] = [item for item in settings["stored_webhooks"] if item["url"] != current]
            save_settings()
            refresh_webhook_list()
            log(f"Invalid webhook removed: {current}")
            return
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to check webhook: {e}")
        return

    name = simpledialog.askstring("Save Webhook", "Enter a name for this webhook:")
    if not name:
        name = current

    if any(item["name"].lower() == name.lower() for item in settings["stored_webhooks"]):
        messagebox.showerror("Name Exists", "This name is already used. Choose another.")
        return

    if any(item["url"] == current for item in settings["stored_webhooks"]):
        messagebox.showinfo("Already Saved", "This webhook is already saved.")
        return

    settings["stored_webhooks"].append({"name": name, "url": current})
    settings["webhook"] = current
    save_settings()
    refresh_webhook_list()
    log(f"Saved webhook: {name} ({current})")

def load_selected_webhook():
    selected = webhook_listbox.curselection()
    if selected:
        url = settings["stored_webhooks"][selected[0]]["url"]
        webhook_entry.delete(0, tk.END)
        webhook_entry.insert(0, url)
        settings["webhook"] = url
        save_settings()
        log(f"Loaded webhook: {url}")

def delete_selected_webhook():
    selected = webhook_listbox.curselection()
    if selected:
        log(f"Deleted webhook: {settings['stored_webhooks'][selected[0]]['url']}")
        del settings["stored_webhooks"][selected[0]]
        save_settings()
        refresh_webhook_list()

def fetch_webhook_info():
    info_output.config(state=tk.NORMAL)
    info_output.delete(1.0, tk.END)
    url = webhook_entry.get().strip()
    if not is_valid_webhook(url):
        info_output.insert(tk.END, "Invalid webhook URL.\n")
        info_output.config(state=tk.DISABLED)
        return
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            pretty = json.dumps(data, indent=4)
            info_output.insert(tk.END, pretty)
        else:
            info_output.insert(tk.END, f"Failed to fetch webhook info.\nStatus: {response.status_code}")
    except Exception as e:
        info_output.insert(tk.END, f"Error: {e}")
    info_output.config(state=tk.DISABLED)

def start_spam():
    global stop_flag
    url = webhook_entry.get().strip()
    message = message_entry.get().strip()
    name = name_entry.get().strip()
    avatar = avatar_entry.get().strip()
    try:
        delay = int(delay_entry.get().strip()) / 1000.0
        count = int(amount_entry.get().strip())
    except:
        messagebox.showerror("Invalid Input", "Delay and message count must be numbers.")
        return

    if not is_valid_webhook(url) or not message or count <= 0:
        messagebox.showerror("Input Error", "Fill out all fields correctly.")
        return

    stop_flag = False
    stop_button.config(state=tk.NORMAL)
    start_button.config(state=tk.DISABLED)
    delete_button.config(state=tk.DISABLED)
    log("Spam started.")
    progress["value"] = 0
    progress["maximum"] = count
    sent_label.config(text=f"0 / {count}")
    rate_limit_label.config(text="")

    save_settings()

    def worker():
        global stop_flag
        sent = 0
        payload = {"content": message}
        if name: payload["username"] = name
        if avatar: payload["avatar_url"] = avatar

        while sent < count and not stop_flag:
            try:
                response = requests.post(url, json=payload, timeout=5)
                if response.status_code == 429:
                    retry = response.json().get("retry_after", 1)
                    rate_limit_label.config(text="Rate Limited")
                    log(f"Rate limited: {retry:.2f}s")
                    time.sleep(retry)
                    continue
                elif response.status_code in [200, 204]:
                    sent += 1
                    progress["value"] = sent
                    sent_label.config(text=f"{sent} / {count}")
                time.sleep(delay)
            except Exception as e:
                log(f"Error sending: {e}")
                time.sleep(0.1)

        if sent == count:
            log("Spam finished.")
        else:
            log("Spam stopped.")
        stop_button.config(state=tk.DISABLED)
        start_button.config(state=tk.NORMAL)
        delete_button.config(state=tk.NORMAL)
        rate_limit_label.config(text="")
        progress["value"] = 0

    threading.Thread(target=worker, daemon=True).start()

def stop_spam():
    global stop_flag
    stop_flag = True
    progress["value"] = 0
    save_settings()

def delete_webhook():
    url = webhook_entry.get().strip()
    if not is_valid_webhook(url):
        messagebox.showerror("Invalid Webhook", "Enter a valid webhook to delete.")
        return
    try:
        requests.delete(url)
        log(f"Terminated webhook: {url}")
    except:
        log(f"Failed to terminate webhook: {url}")

def clear_logs():
    log_output.config(state=tk.NORMAL)
    log_output.delete(1.0, tk.END)
    log_output.config(state=tk.DISABLED)

settings = load_settings()
root = tk.Tk()
root.title("Demi's Discord Webhook Multi-Tool V2")
root.geometry("800x550")
root.configure(bg="#1e1e1e")
font = ("Source Code Pro", 10)

style = ttk.Style()
style.theme_use("default")
style.configure("TNotebook", background="#1e1e1e", borderwidth=0)
style.configure("TNotebook.Tab", background="#2a2a2a", foreground="white", font=font, padding=10)
style.map("TNotebook.Tab", background=[("selected", "#444444")])

notebook = ttk.Notebook(root)
tab_names = ["Webhook", "Info", "Control", "Logs", "Credits"]
tabs = {}
for name in tab_names:
    frame = tk.Frame(notebook, bg="#1e1e1e")
    notebook.add(frame, text=name)
    tabs[name] = frame
notebook.pack(expand=True, fill="both")

# Webhook Tab
webhook_tab = tabs["Webhook"]
tk.Label(webhook_tab, text="Webhook URL:", fg="white", bg="#1e1e1e", font=font).pack(anchor="w", padx=10, pady=(10, 0))
webhook_entry = tk.Entry(webhook_tab, width=60, bg="#2a2a2a", fg="white", insertbackground="white", relief=tk.FLAT, font=font)
webhook_entry.insert(0, settings.get("webhook", ""))
webhook_entry.pack(padx=10, pady=5)
button_frame = tk.Frame(webhook_tab, bg="#1e1e1e")
button_frame.pack(padx=10, pady=5)
tk.Button(button_frame, text="Save", command=save_current_webhook, bg="#4e9ae6", fg="black", font=font).grid(row=0, column=0, padx=5)
tk.Button(button_frame, text="Load", command=load_selected_webhook, bg="#6ee3a8", fg="black", font=font).grid(row=0, column=1, padx=5)
tk.Button(button_frame, text="Delete", command=delete_selected_webhook, bg="#dd3838", fg="black", font=font).grid(row=0, column=2, padx=5)
webhook_listbox = tk.Listbox(webhook_tab, width=50, height=6, bg="#2a2a2a", fg="white", font=font)
webhook_listbox.pack(padx=10, pady=5, fill="x")

# Info Tab
info_tab = tabs["Info"]
info_output = tk.Text(info_tab, bg="#101010", fg="#FFFFFF", font=("Courier New", 9), wrap=tk.NONE)
info_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
tk.Button(info_tab, text="Fetch Webhook Info", command=fetch_webhook_info, bg="#6cd36c", fg="white", font=font).pack(pady=(0, 10))

# Control Tab
control_tab = tabs["Control"]
entries = {}
for i, label in enumerate(["Message", "Webhook Name", "Webhook Avatar", "Delay (ms)", "Messages to Send"]):
    tk.Label(control_tab, text=label+":", fg="white", bg="#1e1e1e", font=font).grid(row=i, column=0, sticky="w", padx=10, pady=3)
    entry = tk.Entry(control_tab, width=50, bg="#2a2a2a", fg="white", insertbackground="white", font=font)
    entry.grid(row=i, column=1, padx=10, pady=3, sticky="ew")
    entries[label] = entry

message_entry = entries["Message"]
name_entry = entries["Webhook Name"]
avatar_entry = entries["Webhook Avatar"]
delay_entry = entries["Delay (ms)"]
amount_entry = entries["Messages to Send"]

message_entry.insert(0, settings.get("message", ""))
name_entry.insert(0, settings.get("name", ""))
avatar_entry.insert(0, settings.get("avatar", ""))
delay_entry.insert(0, settings.get("delay", "1000"))
amount_entry.insert(0, settings.get("amount", "10"))

button_frame = tk.Frame(control_tab, bg="#1e1e1e")
button_frame.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=10)

start_button = tk.Button(button_frame, text="Start", command=start_spam, bg="#45ff7d", fg="black", font=font, width=10)
stop_button = tk.Button(button_frame, text="Stop", command=stop_spam, bg="#ff5959", fg="black", font=font, state=tk.DISABLED, width=10)
delete_button = tk.Button(button_frame, text="Delete Webhook", command=delete_webhook, bg="#820000", fg="white", font=font, width=16)

start_button.pack(side="left", padx=(0, 5))
stop_button.pack(side="left", padx=(0, 5))
delete_button.pack(side="left")

control_tab.grid_columnconfigure(0, weight=0)
control_tab.grid_columnconfigure(1, weight=0)

progress = ttk.Progressbar(control_tab, orient="horizontal", length=400, mode="determinate")
progress.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
sent_label = tk.Label(control_tab, text="0 / 0", fg="white", bg="#1e1e1e", font=font)
sent_label.grid(row=7, column=1, sticky="e", padx=10)
rate_limit_label = tk.Label(control_tab, text="", fg="red", bg="#1e1e1e", font=(font[0], 9))
rate_limit_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

# Logs Tab
logs_tab = tabs["Logs"]
log_output = tk.Text(logs_tab, bg="#101010", fg="white", font=("Courier New", 9), relief=tk.FLAT, state=tk.DISABLED)
log_output.pack(expand=True, fill="both", padx=10, pady=10)
tk.Button(logs_tab, text="Clear Logs", command=clear_logs, bg="#b85939", fg="white", font=font).pack(pady=5)

# Credits Tab
credits_tab = tabs["Credits"]
tk.Label(credits_tab, text="Credits", fg="white", bg="#1e1e1e", font=(font[0], 14, "bold")).pack(pady=(30, 10))
tk.Label(credits_tab, text="Made by Demiizrr", fg="#9900ff", bg="#1e1e1e", font=(font[0], 12)).pack(pady=10)
tk.Label(credits_tab, text="@zacdemiizrr", fg="white", bg="#1e1e1e", font=(font[0], 12)).pack(pady=2)
tk.Label(credits_tab, text="DM me on Discord for questions or what ever", fg="white", bg="#1e1e1e", font=font).pack(pady=2)
tk.Label(credits_tab, text="This tool was made for educational/testing purposes.\nDo not abuse it.", fg="#888", bg="#1e1e1e", font=(font[0], 9)).pack(pady=(10, 0))

refresh_webhook_list()
root.mainloop()
