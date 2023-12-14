import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
import random

class LabAssistant:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.role = "Lab Assistant"
        self.appointments = []

    def process_biomaterial(self):
        messagebox.showinfo("Processing Biomaterial", "Processing biomaterial...")

    def make_appointment(self, service):
        appointment = {"service": service}
        self.appointments.append(appointment)

class Timer:
    def __init__(self, timeout_minutes):
        self.timeout_minutes = timeout_minutes
        self.start_time = None

    def start_timer(self):
        self.start_time = time.time()

    def check_timeout(self):
        if self.start_time is not None:
            elapsed_time = time.time() - self.start_time
            remaining_time = self.timeout_minutes * 60 - elapsed_time
            if remaining_time <= 0:
                messagebox.showinfo("Session Timeout", "Session timeout! Logging out...")
                return True
            elif remaining_time <= 900:
                messagebox.showinfo("Session Timeout", f"Session will timeout in {int(remaining_time/60)} minutes.")
        return False

class Person:
    def __init__(self, full_name, phone, email, username, password):
        self.full_name = full_name
        self.phone = phone
        self.email = email
        self.username = username
        self.password = password

def verify_captcha(user_captcha, entered_captcha):
    return user_captcha == entered_captcha

def register_person(full_name, phone, email, username, password):
    return Person(full_name, phone, email, username, password)

def generate_captcha():
    captcha_characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    captcha = ''.join(random.choice(captcha_characters) for _ in range(4))
    return captcha

def on_register_button_click():
    full_name = entry_full_name.get()
    phone = entry_phone.get()
    email = entry_email.get()
    username = entry_reg_username.get()
    password = entry_reg_password.get()

    user_captcha = generate_captcha()
    entered_captcha = simpledialog.askstring("Captcha", f"Enter the following captcha:\n{user_captcha}")

    if verify_captcha(user_captcha, entered_captcha):
        person = register_person(full_name, phone, email, username, password)
        messagebox.showinfo("Registration", "Registration successful!")

        entry_full_name.delete(0, tk.END)
        entry_phone.delete(0, tk.END)
        entry_email.delete(0, tk.END)
        entry_reg_username.delete(0, tk.END)
        entry_reg_password.delete(0, tk.END)
    else:
        messagebox.showerror("Captcha Verification Failed", "Captcha verification failed. Please try again.")

def on_appointment_button_click():
    selected_service = combo_service.get()

    if selected_service:
        service = services[selected_service]

        verification_result = verify_captcha("abcd", "abcd")  # Replace with actual verification logic
        if verification_result:
            user.make_appointment(service)
            messagebox.showinfo("Appointment", "Appointment made successfully!")
            update_appointments_table()
        else:
            messagebox.showerror("Verification Failed", "Verification failed. Please try again.")
    else:
        messagebox.showwarning("Incomplete Data", "Please select a service.")

def update_appointments_table():
    tree.delete(*tree.get_children())  # Очищаем таблицу перед обновлением
    for i, appointment in enumerate(user.appointments):
        tree.insert("", i, values=(user.username, appointment["service"]["name"],
                                   appointment["service"]["price"]))

def on_login_button_click():
    entered_username = entry_username.get()
    entered_password = entry_password.get()

    if entered_username == "sample_username" and entered_password == "sample_password":
        global user
        user = LabAssistant(entered_username, entered_password)
        messagebox.showinfo("Welcome", f"Welcome, {user.username}! Role: {user.role}")

        timer = Timer(10)  # 10 minutes session timeout for lab assistants
        timer.start_timer()

        def process_biomaterial():
            user.process_biomaterial()
            if timer.check_timeout():
                root.destroy()

        lab_assistant_window = tk.Toplevel(root)
        lab_assistant_window.title("Lab Assistant Window")

        btn_process_biomaterial = tk.Button(lab_assistant_window, text="Process Biomaterial", command=process_biomaterial)
        btn_process_biomaterial.pack(pady=10)
    else:
        messagebox.showerror("Login Failed", "Login failed. Please try again.")

root = tk.Tk()
root.title("Lab Management System")

# Добавляем Entry для ввода полного имени
entry_full_name = tk.Entry(root)
entry_full_name.pack(pady=10)

# Добавляем Entry для ввода номера телефона
entry_phone = tk.Entry(root)
entry_phone.pack(pady=10)

# Добавляем Entry для ввода электронной почты
entry_email = tk.Entry(root)
entry_email.pack(pady=10)

# Добавляем Entry для ввода логина при регистрации
entry_reg_username = tk.Entry(root)
entry_reg_username.pack(pady=10)

# Добавляем Entry для ввода пароля при регистрации
entry_reg_password = tk.Entry(root, show="*")
entry_reg_password.pack(pady=10)

# Добавляем кнопку "Register"
btn_register = tk.Button(root, text="Register", command=on_register_button_click)
btn_register.pack(pady=10)

# Создаем Combobox для выбора услуги
combo_service = ttk.Combobox(root, state="readonly")
combo_service.pack(pady=10)

# Добавляем услуги
services = {
    "Blood Test": {"name": "Blood Test", "price": 50},
    "Urine Test": {"name": "Urine Test", "price": 30},
    "X-ray": {"name": "X-ray", "price": 80}
}

# Добавляем кнопку "Make Appointment"
btn_appointment = tk.Button(root, text="Make Appointment", command=on_appointment_button_click)
btn_appointment.pack(pady=10)

# Добавляем Treeview для отображения таблицы
tree = ttk.Treeview(root, columns=("Username", "Service", "Price"), show="headings")
tree.heading("Username", text="Username")
tree.heading("Service", text="Service")
tree.heading("Price", text="Price")
tree.pack(pady=10)

# Добавляем кнопку "Login"
btn_login = tk.Button(root, text="Login", command=on_login_button_click)
btn_login.pack(pady=10)

root.mainloop()
