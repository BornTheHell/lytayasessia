import tkinter as tk
from tkinter import Entry, Label, StringVar
from PIL import Image, ImageTk
from captcha.image import ImageCaptcha
import random
import string
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
        self.login_frame = tk.Frame(self.root)  # Recreate login_frame
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

        # Пересоздаем admin_frame
        if hasattr(self, 'admin_frame'):
            self.admin_frame.destroy()

        self.admin_frame = tk.Frame(self.root)

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


class CaptchaApp:
    def __init__(self, root, hospital_app):
        self.root = root
        self.hospital_app = hospital_app
        self.root.title("Captcha App")

        # Инициализация переменных
        self.correct_answer = None

        # Создаем виджет для ввода ответа
        self.answer_var = StringVar()
        self.answer_entry = Entry(root, textvariable=self.answer_var)
        self.answer_entry.pack(pady=10)

        # Кнопка для проверки ответа
        check_button = tk.Button(root, text="Check", command=self.check_answer)
        check_button.pack(pady=5)

        # Генерируем и показываем капчу
        self.generate_captcha()

    def generate_captcha(self):
        # Создаем объект captcha с размерами изображения
        captcha = ImageCaptcha(width=200, height=100)

        # Генерируем случайный текст для капчи
        captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

        # Создаем изображение капчи
        image = captcha.generate(captcha_text)

        # Сохраняем изображение или отображаем его
        captcha.write(captcha_text, 'captcha.png')

        # Отображаем изображение капчи на форме
        photo = ImageTk.PhotoImage(Image.open('captcha.png'))
        label = Label(self.root, image=photo)
        label.photo = photo  # чтобы избежать сборщика мусора
        label.pack(pady=10)

        # Сохраняем правильный ответ
        self.correct_answer = captcha_text

    def check_answer(self):
        # Получаем введенный пользователем ответ
        user_answer = self.answer_var.get()

        # Проверяем ответ
        if user_answer == self.correct_answer:
            # Очищаем экран и переходим к основной части программы
            for widget in self.root.winfo_children():
                widget.destroy()
            self.hospital_app.show_login()
        else:
            # Если ответ неверный, генерируем новую капчу
            self.generate_captcha()


if __name__ == "__main__":
    root = tk.Tk()
    
    # Создаем объект HospitalApp и передаем его в CaptchaApp
    hospital_app = HospitalApp(root)
    captcha_app = CaptchaApp(root, hospital_app)
    
    root.mainloop()
