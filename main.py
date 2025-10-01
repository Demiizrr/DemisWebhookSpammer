import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
import threading
import time

SETTINGS_FILE = "settings.json"
WEBHOOK_PREFIX = "https://discord.com/api/webhooks/"
stop_flag = False

themes = {
    "Dark": {
        "bg": "#1e1e1e",
        "fg": "#ffffff",
        "text1": "#b0b0b0",
        "text2": "#888888",
        "button": "#4e9ae6",
        "button_fg": "#000000",
        "textbox": "#2a2a2a",
        "textbox_fg": "#ffffff"
    },
    "Light": {
        "bg": "#f5f5f5",
        "fg": "#000000",
        "text1": "#333333",
        "text2": "#666666",
        "button": "#4e9ae6",
        "button_fg": "#ffffff",
        "textbox": "#ffffff",
        "textbox_fg": "#000000"
    },
    "Ocean": {
        "bg": "#0a2540",
        "fg": "#e0f2ff",
        "text1": "#7dd3fc",
        "text2": "#38bdf8",
        "button": "#0ea5e9",
        "button_fg": "#ffffff",
        "textbox": "#1e3a5f",
        "textbox_fg": "#e0f2ff"
    },
    "Sunset": {
        "bg": "#2d1b3d",
        "fg": "#fff5e6",
        "text1": "#ffb380",
        "text2": "#ff8c66",
        "button": "#ff6b9d",
        "button_fg": "#ffffff",
        "textbox": "#4a2f5c",
        "textbox_fg": "#fff5e6"
    },
    "Forest": {
        "bg": "#1a2f1a",
        "fg": "#e8f5e8",
        "text1": "#90ee90",
        "text2": "#66cc66",
        "button": "#4caf50",
        "button_fg": "#ffffff",
        "textbox": "#2d4a2d",
        "textbox_fg": "#e8f5e8"
    },
    "Cyberpunk": {
        "bg": "#0d0221",
        "fg": "#00ffff",
        "text1": "#ff006e",
        "text2": "#8338ec",
        "button": "#ff006e",
        "button_fg": "#ffffff",
        "textbox": "#1a0b2e",
        "textbox_fg": "#00ffff"
    },
    "Midnight": {
        "bg": "#0f1419",
        "fg": "#c9d1d9",
        "text1": "#8b949e",
        "text2": "#6e7681",
        "button": "#238636",
        "button_fg": "#ffffff",
        "textbox": "#161b22",
        "textbox_fg": "#c9d1d9"
    }
}

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
        "amount": "10",
        "theme": "Dark"
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
    settings["theme"] = theme_box.get()
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
            messagebox.showerror("Invalid Webhook", f"Webhook inaccessible ({response.status_code})")
            return
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed: {e}")
        return
    
    # Check if webhook already exists
    for webhook in settings["stored_webhooks"]:
        if webhook["url"] == current:
            messagebox.showinfo("Already Saved", "This webhook is already in your list!")
            return
    
    settings["stored_webhooks"].append({"name": current, "url": current})
    settings["webhook"] = current
    save_settings()
    refresh_webhook_list()
    log(f"Saved webhook: {current[:50]}...")

def load_selected_webhook():
    selected = webhook_listbox.curselection()
    if selected:
        url = settings["stored_webhooks"][selected[0]]["url"]
        webhook_entry.delete(0, tk.END)
        webhook_entry.insert(0, url)
        settings["webhook"] = url
        save_settings()
        log(f"Loaded webhook: {url[:50]}...")

def delete_selected_webhook():
    selected = webhook_listbox.curselection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a webhook to delete from the list!")
        return
    
    webhook_url = settings["stored_webhooks"][selected[0]]["url"]
    
    # Remove from list
    log(f"Removed from list: {webhook_url[:50]}...")
    del settings["stored_webhooks"][selected[0]]
    
    save_settings()
    refresh_webhook_list()

def delete_webhook_from_discord():
    webhook_url = webhook_entry.get().strip()
    
    if not is_valid_webhook(webhook_url):
        messagebox.showerror("Invalid Webhook", "Please enter a valid webhook URL first!")
        return
    
    # Ask for confirmation
    confirm = messagebox.askyesno(
        "Delete Webhook",
        f"Are you sure you want to DELETE this webhook from Discord?\n\n{webhook_url[:50]}...\n\nThis action CANNOT be undone!"
    )
    
    if not confirm:
        return
    
    # Delete from Discord
    try:
        response = requests.delete(webhook_url, timeout=5)
        if response.status_code == 204:
            log(f"✅ Webhook deleted from Discord successfully!")
            messagebox.showinfo("Success", "Webhook has been permanently deleted from Discord!")
            
            # Remove from saved list if it exists
            for i, webhook in enumerate(settings["stored_webhooks"]):
                if webhook["url"] == webhook_url:
                    del settings["stored_webhooks"][i]
                    save_settings()
                    refresh_webhook_list()
                    break
                    
        elif response.status_code == 404:
            log(f"⚠️ Webhook not found on Discord (already deleted)")
            messagebox.showwarning("Not Found", "Webhook was already deleted or doesn't exist!")
        else:
            log(f"❌ Failed to delete webhook (Status: {response.status_code})")
            messagebox.showerror("Error", f"Failed to delete webhook from Discord (Status: {response.status_code})")
    except Exception as e:
        log(f"❌ Error deleting webhook: {e}")
        messagebox.showerror("Error", f"Failed to delete webhook: {e}")

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
            log(f"Fetched info for {url[:50]}...")
        else:
            info_output.insert(tk.END, f"Failed to fetch webhook info. Status: {response.status_code}")
            log(f"Failed fetching info. Status: {response.status_code}")
    except Exception as e:
        info_output.insert(tk.END, f"Error: {e}")
        log(f"Error fetching webhook info: {e}")
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
        messagebox.showerror("Invalid Input", "Delay and count must be numbers.")
        return
    if not is_valid_webhook(url) or not message:
        messagebox.showerror("Input Error", "Fill out all fields correctly.")
        return
    stop_flag = False
    stop_button.config(state=tk.NORMAL)
    start_button.config(state=tk.DISABLED)
    log(f"Spam started (count={count if count else '∞'})")
    if count == 0:
        progress.config(mode="indeterminate")
        progress.start(50)
    else:
        progress.config(mode="determinate", maximum=count, value=0)
    save_settings()
    def worker():
        global stop_flag
        sent = 0
        payload = {"content": message}
        if name: payload["username"] = name
        if avatar: payload["avatar_url"] = avatar
        while (count == 0 or sent < count) and not stop_flag:
            try:
                response = requests.post(url, json=payload, timeout=5)
                if response.status_code == 429:
                    retry = response.json().get("retry_after", 1)
                    log(f"Rate limited. Retrying in {retry:.2f}s")
                    time.sleep(retry)
                    continue
                elif response.status_code in [200, 204]:
                    sent += 1
                    if count != 0:
                        progress["value"] = sent
                        sent_label.config(text=f"{sent} / {count}")
                    log(f"Message {sent} sent (status {response.status_code})")
                else:
                    log(f"Failed to send (status {response.status_code})")
            except Exception as e:
                log(f"Error sending: {e}")
                time.sleep(0.1)
            time.sleep(delay)
        if sent == count and count != 0:
            log("Spam finished successfully.")
        else:
            log("Spam stopped manually.")
        stop_button.config(state=tk.DISABLED)
        start_button.config(state=tk.NORMAL)
        progress.stop()
        progress.config(value=0)
    threading.Thread(target=worker, daemon=True).start()

def stop_spam():
    global stop_flag
    stop_flag = True
    progress.stop()
    progress.config(value=0)
    save_settings()

def clear_logs():
    log_output.config(state=tk.NORMAL)
    log_output.delete(1.0, tk.END)
    log_output.config(state=tk.DISABLED)

def apply_theme(theme_name):
    theme = themes[theme_name]
    root.configure(bg=theme["bg"])
    
    # Apply to all tabs
    for tab in tabs.values():
        tab.configure(bg=theme["bg"])
        for widget in tab.winfo_children():
            widget_class = widget.winfo_class()
            try:
                if widget_class == "Label":
                    widget.configure(bg=theme["bg"], fg=theme["text1"])
                elif widget_class == "Entry":
                    widget.configure(bg=theme["textbox"], fg=theme["textbox_fg"], 
                                   insertbackground=theme["textbox_fg"])
                elif widget_class == "Button":
                    # Keep special button colors but update based on theme
                    current_bg = widget.cget("bg")
                    if "ff" in current_bg.lower() or "green" in current_bg.lower():
                        pass  # Keep special colors for start/stop/etc
                    else:
                        widget.configure(bg=theme["button"], fg=theme["button_fg"])
                elif widget_class == "Text":
                    widget.configure(bg=theme["textbox"], fg=theme["textbox_fg"])
                elif widget_class == "Listbox":
                    widget.configure(bg=theme["textbox"], fg=theme["textbox_fg"])
                elif widget_class == "Frame":
                    widget.configure(bg=theme["bg"])
            except:
                pass
    
    # Update notebook style
    style.configure("TNotebook", background=theme["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", background=theme["textbox"], 
                   foreground=theme["text1"], font=font, padding=10)
    style.map("TNotebook.Tab", background=[("selected", theme["button"])])
    
    log(f"Theme changed to: {theme_name}")

settings = load_settings()
root = tk.Tk()
root.title("Demi's Discord Webhook Multi-Tool V2.1")
root.geometry("800x600")
root.configure(bg=themes[settings.get("theme", "Dark")]["bg"])

# Try to load icon, but don't crash if it doesn't exist
try:
    root.iconbitmap("icon.ico")
except:
    pass

font = ("Segoe UI", 10)

style = ttk.Style()
style.theme_use("default")
current_theme = themes[settings.get("theme", "Dark")]
style.configure("TNotebook", background=current_theme["bg"], borderwidth=0)
style.configure("TNotebook.Tab", background=current_theme["textbox"], 
               foreground=current_theme["text1"], font=font, padding=10)
style.map("TNotebook.Tab", background=[("selected", current_theme["button"])])

notebook = ttk.Notebook(root)
tabs = {}
for name in ["Webhook", "Info", "Control", "Logs", "Settings", "Credits"]:
    frame = tk.Frame(notebook, bg=current_theme["bg"])
    notebook.add(frame, text=name)
    tabs[name] = frame
notebook.pack(expand=True, fill="both")

# WEBHOOK TAB
webhook_tab = tabs["Webhook"]
tk.Label(webhook_tab, text="Webhook URL:", fg=current_theme["text1"], 
         bg=current_theme["bg"], font=font).pack(anchor="w", padx=10, pady=(10, 0))
webhook_entry = tk.Entry(webhook_tab, width=60, bg=current_theme["textbox"], 
                        fg=current_theme["textbox_fg"], insertbackground=current_theme["textbox_fg"], 
                        relief=tk.FLAT, font=font)
webhook_entry.insert(0, settings.get("webhook", ""))
webhook_entry.pack(padx=10, pady=5)

btn_frame = tk.Frame(webhook_tab, bg=current_theme["bg"])
btn_frame.pack(pady=5)
tk.Button(btn_frame, text="Save Webhook", command=save_current_webhook, 
         bg=current_theme["button"], fg=current_theme["button_fg"], font=font).pack(side=tk.LEFT, padx=5)

tk.Label(webhook_tab, text="Saved Webhooks:", fg=current_theme["text1"], 
         bg=current_theme["bg"], font=font).pack(anchor="w", padx=10, pady=(10, 0))
webhook_listbox = tk.Listbox(webhook_tab, width=50, height=6, bg=current_theme["textbox"], 
                             fg=current_theme["textbox_fg"], font=font)
webhook_listbox.pack(padx=10, pady=5, fill="x")

btn_frame2 = tk.Frame(webhook_tab, bg=current_theme["bg"])
btn_frame2.pack(pady=5)
tk.Button(btn_frame2, text="Load", command=load_selected_webhook, 
         bg="#6ee3a8", fg="black", font=font).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame2, text="Remove from List", command=delete_selected_webhook, 
         bg="#dd3838", fg="white", font=font).pack(side=tk.LEFT, padx=5)

# INFO TAB
info_tab = tabs["Info"]
info_output = tk.Text(info_tab, bg=current_theme["textbox"], fg=current_theme["textbox_fg"], 
                     font=("Courier New", 9), wrap=tk.NONE)
info_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
tk.Button(info_tab, text="Fetch Webhook Info", command=fetch_webhook_info, 
         bg="#6cd36c", fg="white", font=font).pack(pady=(0, 10))

# CONTROL TAB
control_tab = tabs["Control"]
tk.Label(control_tab, text="Message:", fg=current_theme["text1"], 
         bg=current_theme["bg"], font=font).grid(row=0, column=0, sticky="w", padx=10, pady=3)
message_entry = tk.Entry(control_tab, width=50, bg=current_theme["textbox"], 
                        fg=current_theme["textbox_fg"], insertbackground=current_theme["textbox_fg"], font=font)
message_entry.grid(row=0, column=1, padx=10, pady=3)
message_entry.insert(0, settings.get("message", ""))

tk.Label(control_tab, text="Webhook Name:", fg=current_theme["text1"], 
         bg=current_theme["bg"], font=font).grid(row=1, column=0, sticky="w", padx=10, pady=3)
name_entry = tk.Entry(control_tab, width=50, bg=current_theme["textbox"], 
                     fg=current_theme["textbox_fg"], insertbackground=current_theme["textbox_fg"], font=font)
name_entry.grid(row=1, column=1, padx=10, pady=3)
name_entry.insert(0, settings.get("name", ""))

tk.Label(control_tab, text="(URL) Webhook Avatar:", fg=current_theme["text1"], 
         bg=current_theme["bg"], font=font).grid(row=2, column=0, sticky="w", padx=10, pady=3)
avatar_entry = tk.Entry(control_tab, width=50, bg=current_theme["textbox"], 
                       fg=current_theme["textbox_fg"], insertbackground=current_theme["textbox_fg"], font=font)
avatar_entry.grid(row=2, column=1, padx=10, pady=3)
avatar_entry.insert(0, settings.get("avatar", ""))

tk.Label(control_tab, text="Delay (ms):", fg=current_theme["text1"], 
         bg=current_theme["bg"], font=font).grid(row=3, column=0, sticky="w", padx=10, pady=3)
delay_entry = tk.Entry(control_tab, width=50, bg=current_theme["textbox"], 
                      fg=current_theme["textbox_fg"], insertbackground=current_theme["textbox_fg"], font=font)
delay_entry.grid(row=3, column=1, padx=10, pady=3)
delay_entry.insert(0, settings.get("delay", "20"))

tk.Label(control_tab, text="Messages to Send (0 = infinite):", fg=current_theme["text1"], 
         bg=current_theme["bg"], font=font).grid(row=4, column=0, sticky="w", padx=10, pady=3)
amount_entry = tk.Entry(control_tab, width=50, bg=current_theme["textbox"], 
                       fg=current_theme["textbox_fg"], insertbackground=current_theme["textbox_fg"], font=font)
amount_entry.grid(row=4, column=1, padx=10, pady=3)
amount_entry.insert(0, settings.get("amount", "10"))

start_button = tk.Button(control_tab, text="Start", command=start_spam, 
                        bg="#45ff7d", fg="black", font=font, width=10)
stop_button = tk.Button(control_tab, text="Stop", command=stop_spam, 
                       bg="#ff5959", fg="black", font=font, state=tk.DISABLED, width=10)
delete_webhook_button = tk.Button(control_tab, text="Delete", command=delete_webhook_from_discord,
                                 bg="#ff3333", fg="white", font=font, width=10)
start_button.grid(row=5, column=0, padx=10, pady=10, sticky="w")
stop_button.grid(row=5, column=0, padx=10, pady=10, sticky="e")
delete_webhook_button.grid(row=5, column=1, padx=10, pady=10, sticky="e")

progress = ttk.Progressbar(control_tab, orient="horizontal", length=400, mode="determinate")
progress.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
sent_label = tk.Label(control_tab, text="0 / 0", fg=current_theme["text1"], 
                     bg=current_theme["bg"], font=font)
sent_label.grid(row=7, column=1, sticky="e", padx=10)

# LOGS TAB
logs_tab = tabs["Logs"]
log_output = tk.Text(logs_tab, bg=current_theme["textbox"], fg=current_theme["textbox_fg"], 
                    font=("Courier New", 9), relief=tk.FLAT, state=tk.DISABLED)
log_output.pack(expand=True, fill="both", padx=10, pady=10)
tk.Button(logs_tab, text="Clear Logs", command=clear_logs, 
         bg="#b85939", fg="white", font=font).pack(pady=5)

# SETTINGS TAB
settings_tab = tabs["Settings"]
tk.Label(settings_tab, text="Theme:", fg=current_theme["text1"], 
         bg=current_theme["bg"], font=(font[0], 12, "bold")).pack(pady=(20, 10))

theme_frame = tk.Frame(settings_tab, bg=current_theme["bg"])
theme_frame.pack(pady=10)

theme_box = ttk.Combobox(theme_frame, values=list(themes.keys()), 
                        state="readonly", font=font, width=20)
theme_box.set(settings.get("theme", "Dark"))
theme_box.pack(side=tk.LEFT, padx=5)

def change_theme(e):
    apply_theme(theme_box.get())
    save_settings()

theme_box.bind("<<ComboboxSelected>>", change_theme)

tk.Label(settings_tab, text="Available Themes:", fg=current_theme["text2"], 
         bg=current_theme["bg"], font=font).pack(pady=(20, 5))
theme_desc = "Dark • Light • Ocean • Sunset\nForest • Cyberpunk • Midnight"
tk.Label(settings_tab, text=theme_desc, fg=current_theme["text1"], 
         bg=current_theme["bg"], font=(font[0], 9)).pack(pady=5)

# CREDITS TAB
credits_tab = tabs["Credits"]
tk.Label(credits_tab, text="Credits", fg=current_theme["text1"], 
         bg=current_theme["bg"], font=(font[0], 14, "bold")).pack(pady=(30, 10))
tk.Label(credits_tab, text="Made by Demiizrr", fg="#9900ff", 
         bg=current_theme["bg"], font=(font[0], 12)).pack(pady=10)
tk.Label(credits_tab, text="@zacdemiizrr", fg=current_theme["text1"], 
         bg=current_theme["bg"], font=(font[0], 12)).pack(pady=2)
tk.Label(credits_tab, text="DM me on Discord for questions or whatever", 
         fg=current_theme["text1"], bg=current_theme["bg"], font=font).pack(pady=2)
tk.Label(credits_tab, text="This tool was made for educational/testing purposes.\nDo not abuse it.", 
         fg=current_theme["text2"], bg=current_theme["bg"], font=(font[0], 9)).pack(pady=(10, 0))

refresh_webhook_list()
apply_theme(settings.get("theme", "Dark"))
log("Webhook Multi-Tool loaded successfully!")
root.mainloop()
