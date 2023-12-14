import tkinter as tk
from tkinter import messagebox
import sqlite3

class HospitalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hospital Management System")

        # Инициализация базы данных
        self.conn = sqlite3.connect('hospital.db')
        self.create_tables()

        # Добавим заглушки для логинов и паролей
        self.admin_username = "admin"
        self.admin_password = "admin_password"

        self.patient_username = "patient"
        self.patient_password = "patient_password"

        self.accountant_username = "accountant"
        self.accountant_password = "accountant_password"

        # Инициализация переменных
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        # Создаем разделы для разных типов пользователей
        self.login_frame = tk.Frame(root)
        self.admin_frame = tk.Frame(root)
        self.patient_frame = tk.Frame(root)
        self.accountant_frame = tk.Frame(root)

        # Первоначально показываем форму входа
        self.show_login()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                birth_date TEXT,
                phone TEXT,
                email TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                cost REAL,
                code TEXT,
                completion_time INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                service_id INTEGER,
                order_date TEXT,
                status TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (service_id) REFERENCES services (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accountants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                last_login DATETIME
            )
        ''')

        self.conn.commit()

    def show_login(self):
        # Очистка предыдущего интерфейса
        self.clear_frames()

        # Создаем элементы для формы входа
        tk.Label(self.login_frame, text="Логин:").pack()
        tk.Entry(self.login_frame, textvariable=self.username_var).pack()
        tk.Label(self.login_frame, text="Пароль:").pack()
        tk.Entry(self.login_frame, textvariable=self.password_var, show='*').pack()
        tk.Button(self.login_frame, text="Войти", command=self.login).pack()

        self.login_frame.pack()

    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()

        if username == self.admin_username and password == self.admin_password:
            self.show_admin_interface()
        elif username == self.patient_username and password == self.patient_password:
            self.show_patient_interface()
        elif username == self.accountant_username and password == self.accountant_password:
            self.show_accountant_interface()
        else:
            messagebox.showerror("Ошибка", "Неверные логин или пароль")

    def show_admin_interface(self):
        self.clear_frames()
        tk.Label(self.admin_frame, text="Привет, администратор!").pack()
        self.admin_frame.pack()

    def show_patient_interface(self):
        self.clear_frames()
        tk.Label(self.patient_frame, text="Привет, пациент!").pack()
        self.patient_frame.pack()

    def show_accountant_interface(self):
        self.clear_frames()
        tk.Label(self.accountant_frame, text="Привет, бухгалтер!").pack()
        self.accountant_frame.pack()

    def clear_frames(self):
        for frame in [self.login_frame, self.admin_frame, self.patient_frame, self.accountant_frame]:
            frame.pack_forget()

if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalApp(root)
    root.mainloop()
