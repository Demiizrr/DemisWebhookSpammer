import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
import threading
import time
import json
import os

SETTINGS_FILE = "settings.json"
WEBHOOK_PREFIX = "https://discord.com/api/webhooks/"

def is_valid_webhook(url):
    return url.startswith(WEBHOOK_PREFIX)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                data.setdefault("webhook", "")
                data.setdefault("message", "")
                data.setdefault("spam", "")
                data.setdefault("stored_webhooks", [])
                return data
        except:
            pass
    return {"webhook": "", "message": "", "spam": "", "stored_webhooks": []}

def save_settings():
    webhook = url_entry.get().strip()
    if not is_valid_webhook(webhook):
        return
    data["webhook"] = webhook
    data["message"] = msg_entry.get().strip()
    data["spam"] = spam_entry.get().strip()
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def send_message():
    webhook_url = url_entry.get().strip()
    message = msg_entry.get().strip()
    if not is_valid_webhook(webhook_url):
        messagebox.showerror("Invalid Webhook", "Webhook must start with:\n" + WEBHOOK_PREFIX)
        return
    try:
        spam_count = int(spam_entry.get().strip())
    except:
        messagebox.showerror("Input Error", "Spam Amount must be an integer.")
        return
    if not message or spam_count <= 0:
        messagebox.showerror("Input Error", "All fields must be filled correctly.")
        return
    send_button.config(state=tk.DISABLED)
    def spam():
        for i in range(spam_count):
            try:
                requests.post(webhook_url, json={"content": message}, headers={"Content-Type": "application/json"}, timeout=3)
            except:
                pass
            send_button.config(text=f"Sending ({i+1}/{spam_count})")
            time.sleep(0.01)
        send_button.config(text="Send", state=tk.NORMAL)
    threading.Thread(target=spam, daemon=True).start()

def font_try(font_name):
    try:
        return (font_name, 10)
    except:
        return ("Courier New", 10)

def create_label(text, row):
    label = tk.Label(frame, text=text, bg="#1e1e1e", fg="white", font=font)
    label.grid(row=row, column=0, sticky=tk.W, pady=(10 if row > 0 else 0), padx=5)

def create_entry(row):
    entry = tk.Entry(frame, width=40, bg="#2a2a2a", fg="white", insertbackground="white", relief=tk.FLAT, font=font)
    entry.grid(row=row, column=0, pady=5, padx=5)
    return entry

def refresh_webhook_list():
    webhook_listbox.delete(0, tk.END)
    cleaned_list = []

    for item in data.get("stored_webhooks", []):
        if isinstance(item, dict):
            cleaned_list.append(item)
            webhook_listbox.insert(tk.END, item.get("name", item.get("url", ""))[:50])
        elif isinstance(item, str) and is_valid_webhook(item):
            new_item = {"name": item, "url": item}
            cleaned_list.append(new_item)
            webhook_listbox.insert(tk.END, item[:50])

    if cleaned_list != data["stored_webhooks"]:
        data["stored_webhooks"] = cleaned_list
        save_settings()

def save_current_webhook():
    current = url_entry.get().strip()
    if not is_valid_webhook(current):
        messagebox.showerror("Invalid Webhook", "Webhook must start with:\n" + WEBHOOK_PREFIX)
        return

    name = simpledialog.askstring("Save Webhook (not required)", "Enter a name for this webhook:")
    if not name:
        name = current

    for entry in data["stored_webhooks"]:
        if entry["url"] == current:
            messagebox.showinfo("Exists", "This webhook already exists.")
            return

    data["stored_webhooks"].append({"name": name, "url": current})
    refresh_webhook_list()
    save_settings()

def load_selected_webhook():
    try:
        selection = webhook_listbox.curselection()
        if selection:
            selected = data["stored_webhooks"][selection[0]]
            url_entry.delete(0, tk.END)
            url_entry.insert(0, selected["url"])
    except:
        pass

def delete_selected_webhook():
    selection = webhook_listbox.curselection()
    if selection:
        del data["stored_webhooks"][selection[0]]
        refresh_webhook_list()
        save_settings()

def on_close():
    save_settings()
    root.destroy()

root = tk.Tk()
root.title("Demi's Discord Webhook Spammer")
root.geometry("400x460")
root.configure(bg="#1e1e1e")
root.eval('tk::PlaceWindow . center')
root.iconbitmap("icon.ico")

font = font_try("Source Code Pro")

frame = tk.Frame(root, bg="#1e1e1e")
frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

create_label("Webhook URL:", 0)
url_entry = create_entry(1)

create_label("Message:", 2)
msg_entry = create_entry(3)

create_label("Spam Amount:", 4)
spam_entry = create_entry(5)

data = load_settings()
url_entry.insert(0, data.get("webhook", ""))
msg_entry.insert(0, data.get("message", ""))
spam_entry.insert(0, data.get("spam", ""))

send_button = tk.Button(
    frame, text="Send", command=send_message,
    bg="#333333", fg="white", activebackground="#444444", activeforeground="white",
    relief=tk.FLAT, font=font, width=20
)
send_button.grid(row=6, column=0, pady=20)

store_frame = tk.Frame(frame, bg="#1e1e1e")
store_frame.grid(row=7, column=0, pady=10)

webhook_listbox = tk.Listbox(
    store_frame, width=30, height=4, bg="#2a2a2a", fg="white",
    relief=tk.FLAT, font=font, highlightbackground="#444444", selectbackground="#444444"
)
webhook_listbox.grid(row=0, column=0, rowspan=3, padx=(0, 5))

tk.Button(store_frame, text="Save", command=save_current_webhook,
          bg="#333333", fg="white", font=font, relief=tk.FLAT, width=8).grid(row=0, column=1, pady=2)

tk.Button(store_frame, text="Load", command=load_selected_webhook,
          bg="#333333", fg="white", font=font, relief=tk.FLAT, width=8).grid(row=1, column=1, pady=2)

tk.Button(store_frame, text="Delete", command=delete_selected_webhook,
          bg="#333333", fg="white", font=font, relief=tk.FLAT, width=8).grid(row=2, column=1, pady=2)

refresh_webhook_list()
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
