import tkinter as tk
from tkinter import messagebox
import requests
import threading
import time
import json
import os

SETTINGS_FILE = "settings.json"

# Load previous settings if available
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load settings: {e}")
    return {}

# Save current input values to file
def save_settings():
    data = {
        "webhook": url_entry.get().strip(),
        "message": msg_entry.get().strip(),
        "spam": spam_entry.get().strip()
    }
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Failed to save settings: {e}")

# Function to send messages
def send_message():
    webhook_url = url_entry.get().strip()
    message = msg_entry.get().strip()

    try:
        spam_count = int(spam_entry.get().strip())
    except ValueError:
        messagebox.showerror("Input Error", "Spam Amount must be an integer.")
        return

    if not webhook_url or not message or spam_count <= 0:
        messagebox.showerror("Input Error", "All fields must be filled correctly.")
        return

    # Disable the button while sending
    send_button.config(state=tk.DISABLED)

    def spam():
        success_count = 0
        for i in range(spam_count):
            try:
                response = requests.post(
                    webhook_url,
                    json={"content": message},
                    headers={"Content-Type": "application/json"},
                    timeout=3
                )
                if response.status_code == 204:
                    success_count += 1
                else:
                    print(f"Error {i+1}: {response.status_code}")
            except Exception as e:
                print(f"Exception {i+1}: {e}")

            # Update button label with progress
            send_button.config(text=f"Sending ({i+1}/{spam_count})")
            time.sleep(0.2)  # slight delay to reduce risk of rate limiting

        # Reset button
        send_button.config(text="Send", state=tk.NORMAL)

    threading.Thread(target=spam, daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("Discord Webhook Spammer")
root.geometry("400x360")
root.configure(bg="#1e1e1e")
root.eval('tk::PlaceWindow . center')

# Font fallback
def font_try(font_name):
    try:
        return (font_name, 10)
    except:
        return ("Courier New", 10)

font = font_try("Source Code Pro")  # Roboto Mono if preferred

# Labels and input fields
def create_label(text, row):
    label = tk.Label(frame, text=text, bg="#1e1e1e", fg="white", font=font)
    label.grid(row=row, column=0, sticky=tk.W, pady=(10 if row > 0 else 0), padx=5)

def create_entry(row):
    entry = tk.Entry(frame, width=40, bg="#2a2a2a", fg="white", insertbackground="white", relief=tk.FLAT, font=font)
    entry.grid(row=row, column=0, pady=5, padx=5)
    return entry

frame = tk.Frame(root, bg="#1e1e1e")
frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

create_label("Webhook URL:", 0)
url_entry = create_entry(1)

create_label("Message:", 2)
msg_entry = create_entry(3)

create_label("Spam Amount:", 4)
spam_entry = create_entry(5)

# Load saved data if any
data = load_settings()
url_entry.insert(0, data.get("webhook", ""))
msg_entry.insert(0, data.get("message", ""))
spam_entry.insert(0, data.get("spam", ""))

# Send Button
send_button = tk.Button(
    frame, text="Send", command=send_message,
    bg="#333333", fg="white", activebackground="#444444", activeforeground="white",
    relief=tk.FLAT, font=font, width=20
)
send_button.grid(row=6, column=0, pady=20)

# Save on close
def on_close():
    save_settings()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
