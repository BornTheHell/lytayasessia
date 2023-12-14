import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

class User:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

class Admin(User):
    def __init__(self, conn):
        super().__init__(conn)

    def create_tables(self):
        # Опустим создание таблиц, так как они будут общими для всех пользователей
        pass

class Patient(User):
    def __init__(self, conn):
        super().__init__(conn)

    def book_appointment(self, full_name, dob, phone, gender, age, selected_services):
        # Записать пациента
        self.cursor.execute('''
            INSERT INTO patients (full_name, birth_date, phone, gender, age)
            VALUES (?, ?, ?, ?, ?)
        ''', (full_name, dob, phone, gender, age))

        # Получить ID пациента
        self.cursor.execute('SELECT last_insert_rowid()')
        patient_id = self.cursor.fetchone()[0]

        # Записать выбранные обследования
        for service in selected_services:
            if service["var"].get() == 1:
                self.cursor.execute('''
                    INSERT INTO orders (patient_id, service_id, order_date, status)
                    VALUES (?, ?, ?, ?)
                ''', (patient_id, self.get_service_id(service["name"]), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Pending'))

        self.conn.commit()
        messagebox.showinfo("Успех", "Вы успешно записаны на обследование!")

    def get_service_id(self, service_name):
        self.cursor.execute('SELECT id FROM services WHERE name = ?', (service_name,))
        service = self.cursor.fetchone()
        return service[0] if service else None

class Accountant(User):
    def __init__(self, conn):
        super().__init__(conn)

    # Здесь можно добавить методы для работы с финансами, например, получение отчетов и т. д.

class HospitalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hospital Management System")

        # Инициализация базы данных
        self.conn = sqlite3.connect('hospital.db')

        # Создание объектов для каждой роли
        self.admin = Admin(self.conn)
        self.patient = Patient(self.conn)
        self.accountant = Accountant(self.conn)

        # Создание вкладок
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.patient_tab = tk.Frame(self.notebook)
        self.admin_tab = tk.Frame(self.notebook)
        self.accountant_tab = tk.Frame(self.notebook)

        self.notebook.add(self.patient_tab, text="Пациенты")
        self.notebook.add(self.admin_tab, text="Администратор")
        self.notebook.add(self.accountant_tab, text="Бухгалтер")

        # Вкладка Пациенты
        self.create_patient_tab()

        # Вкладка Администратора
        self.create_admin_tab()

        # Вкладка Бухгалтера
        self.create_accountant_tab()

    def create_tables(self):
        self.admin.create_tables()

    def create_patient_tab(self):
        self.patient_frame = tk.Frame(self.patient_tab)
        self.patient_frame.pack(pady=10)

        tk.Label(self.patient_frame, text="ФИО:").grid(row=0, column=0, padx=10, pady=10)
        self.name_entry = tk.Entry(self.patient_frame)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.patient_frame, text="Дата рождения:").grid(row=1, column=0, padx=10, pady=10)
        self.dob_entry = tk.Entry(self.patient_frame)
        self.dob_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(self.patient_frame, text="Телефон:").grid(row=2, column=0, padx=10, pady=10)
        self.phone_entry = tk.Entry(self.patient_frame)
        self.phone_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(self.patient_frame, text="Пол:").grid(row=3, column=0, padx=10, pady=10)
        self.gender_entry = tk.Entry(self.patient_frame)
        self.gender_entry.grid(row=3, column=1, padx=10, pady=10)

        tk.Label(self.patient_frame, text="Возраст:").grid(row=4, column=0, padx=10, pady=10)
        self.age_entry = tk.Entry(self.patient_frame)
        self.age_entry.grid(row=4, column=1, padx=10, pady=10)

        self.services_frame = tk.Frame(self.patient_tab)
        self.services_frame.pack(pady=10)

        self.selected_services = []

        # Получение списка обследований из базы данных
        self.admin.create_tables()
        services = self.get_services()

        for i, service in enumerate(services):
            var = tk.IntVar()
            tk.Checkbutton(self.services_frame, text=service, variable=var).grid(row=i, column=0, padx=10, pady=5)
            self.selected_services.append({"name": service, "var": var})

        tk.Button(self.patient_tab, text="Записаться", command=self.book_appointment).pack(pady=10)

    def create_admin_tab(self):
        self.admin_frame = tk.Frame(self.admin_tab)
        self.admin_frame.pack(pady=10)

        # Создание формы входа для администратора
        tk.Label(self.admin_frame, text="Логин:").grid(row=0, column=0, padx=10, pady=10)
        self.admin_login_entry = tk.Entry(self.admin_frame)
        self.admin_login_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.admin_frame, text="Пароль:").grid(row=1, column=0, padx=10, pady=10)
        self.admin_password_entry = tk.Entry(self.admin_frame, show="*")
        self.admin_password_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Button(self.admin_frame, text="Войти", command=self.admin_login).grid(row=2, columnspan=2, pady=10)

    def create_accountant_tab(self):
        self.accountant_frame = tk.Frame(self.accountant_tab)
        self.accountant_frame.pack(pady=10)

        # Создание формы входа для бухгалтера
        tk.Label(self.accountant_frame, text="Логин:").grid(row=0, column=0, padx=10, pady=10)
        self.accountant_login_entry = tk.Entry(self.accountant_frame)
        self.accountant_login_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.accountant_frame, text="Пароль:").grid(row=1, column=0, padx=10, pady=10)
        self.accountant_password_entry = tk.Entry(self.accountant_frame, show="*")
        self.accountant_password_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Button(self.accountant_frame, text="Войти", command=self.accountant_login).grid(row=2, columnspan=2, pady=10)

    def book_appointment(self):
        full_name = self.name_entry.get()
        dob = self.dob_entry.get()
        phone = self.phone_entry.get()
        gender = self.gender_entry.get()
        age = self.age_entry.get()

        # Проверка наличия введенных данных
        if not full_name or not dob or not phone or not gender or not age:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля.")
            return

        # Проверка выбора хотя бы одного обследования
        if all(service["var"].get() == 0 for service in self.selected_services):
            messagebox.showerror("Ошибка", "Выберите хотя бы одно обследование.")
            return

        self.patient.book_appointment(full_name, dob, phone, gender, age, self.selected_services)

    def admin_login(self):
        # Здесь можно добавить проверку логина и пароля для администратора
        messagebox.showinfo("Вход", "Вы вошли как администратор.")

    def accountant_login(self):
        # Здесь можно добавить проверку логина и пароля для бухгалтера
        messagebox.showinfo("Вход", "Вы вошли как бухгалтер.")

    def get_services(self):
        self.admin.create_tables()
        self.admin.cursor.execute('SELECT name FROM services')
        services = self.admin.cursor.fetchall()
        return [service[0] for service in services]

if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalApp(root)
    root.mainloop()
