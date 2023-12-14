import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime

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
                email TEXT,
                gender TEXT,
                age INTEGER
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

        # Отображение заказов на обследование
        orders_label = tk.Label(self.admin_frame, text="Заказы на обследование сегодня:")
        orders_label.pack()

        orders_text = self.get_orders_for_today()
        orders_display = tk.Text(self.admin_frame, height=10, width=40)
        orders_display.insert(tk.END, orders_text)
        orders_display.pack()

        self.admin_frame.pack()

    def get_orders_for_today(self):
        # Получить заказы на обследование за сегодня
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT p.full_name, o.order_date, s.name, s.cost
            FROM orders o
            JOIN patients p ON o.patient_id = p.id
            JOIN services s ON o.service_id = s.id
            WHERE o.order_date = ?
        ''', (today,))
        
        orders = cursor.fetchall()
        
        orders_text = ""
        for order in orders:
            orders_text += f"{order[0]}, {order[1]}, Услуга: {order[2]}, Стоимость: {order[3]}\n"

        return orders_text

    def show_patient_interface(self):
        self.clear_frames()
        tk.Label(self.patient_frame, text="Привет, пациент!").pack()

        # Отображение услуг для записи
        services_label = tk.Label(self.patient_frame, text="Выберите услуги для записи:")
        services_label.pack()

        _services = []
        for service in self.get_services():
            var = tk.IntVar()
            tk.Checkbutton(self.patient_frame, text=service, variable=var).pack()
            _services.append({"name": service, "var": var})

        name_label = tk.Label(self.patient_frame, text="Фамилия Имя Отчество:")
        name_label.pack()
        name_entry = tk.Entry(self.patient_frame)
        name_entry.pack()

        dob_label = tk.Label(self.patient_frame, text="Дата рождения (гггг-мм-дд):")
        dob_label.pack()
        dob_entry = tk.Entry(self.patient_frame)
        dob_entry.pack()

        phone_label = tk.Label(self.patient_frame, text="Номер телефона:")
        phone_label.pack()
        phone_entry = tk.Entry(self.patient_frame)
        phone_entry.pack()

        gender_label = tk.Label(self.patient_frame, text="Пол:")
        gender_label.pack()
        gender_entry = tk.Entry(self.patient_frame)
        gender_entry.pack()

        age_label = tk.Label(self.patient_frame, text="Возраст:")
        age_label.pack()
        age_entry = tk.Entry(self.patient_frame)
        age_entry.pack()

        tk.Button(self.patient_frame, text="Записаться", command=lambda: self.book_appointment(
            name_entry.get(),
            dob_entry.get(),
            phone_entry.get(),
            gender_entry.get(),
            age_entry.get(),
            _services
        )).pack()

        self.patient_frame.pack()

    def get_services(self):
        # Получить список доступных услуг
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM services')
        services = cursor.fetchall()
        return [service[0] for service in services]

    def book_appointment(self, full_name, dob, phone, gender, age, selected_services):
        # Записать на обследование
        cursor = self.conn.cursor()
        
        # Записать пациента
        cursor.execute('''
            INSERT INTO patients (full_name, birth_date, phone, email, gender, age)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (full_name, dob, phone, "", gender, age))
        patient_id = cursor.lastrowid

        # Записать заказы на выбранные услуги
        for service in selected_services:
            if service["var"].get() == 1:
                cursor.execute('INSERT INTO orders (patient_id, service_id, order_date, status) VALUES (?, ?, ?, ?)',
                               (patient_id, self.get_service_id(service["name"]), datetime.now(), 'Pending'))

        self.conn.commit()
        messagebox.showinfo("Успех", "Вы успешно записаны на обследование!")

    def get_service_id(self, service_name):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM services WHERE name = ?', (service_name,))
        service = cursor.fetchone()
        return service[0] if service else None

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
