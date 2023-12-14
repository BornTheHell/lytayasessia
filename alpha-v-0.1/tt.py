import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from tkcalendar import DateEntry

class User:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

class Admin(User):
    def __init__(self, conn, root=None):
        super().__init__(conn)
        self.root = root
        
    def create_tables(self):
        self.cursor.execute("PRAGMA table_info(services)")
        columns = [column[1] for column in self.cursor.fetchall()]

        if 'cost' not in columns:
            self.cursor.execute('ALTER TABLE services ADD COLUMN cost REAL NOT NULL DEFAULT 0')

        # Создание таблицы services, если ее нет
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                cost REAL NOT NULL DEFAULT 0
            )
        ''')

        # Добавление обследований с проверкой на уникальность имени
        services_to_add = [
            ('Рентген', 5000.0),
            ('Анализ крови', 1000.0),
            ('МРТ', 8000.0),
            ('УЗИ', 3000.0)
        ]

        for service_name, cost in services_to_add:
            self.cursor.execute('''
                INSERT OR IGNORE INTO services (name, cost)
                VALUES (?, ?)
            ''', (service_name, cost))

        self.conn.commit()

        # Удаление таблиц patients и orders (если они есть)
        self.cursor.execute('DROP TABLE IF EXISTS patients')
        self.cursor.execute('DROP TABLE IF EXISTS orders')

        # Создание таблиц patients
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        ''')

        # Создание таблиц orders
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                status TEXT NOT NULL,
                cost REAL NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (service_id) REFERENCES services (id)
            )
        ''')

        self.conn.commit()

    

class AdminApp(tk.Tk):
    def __init__(self, admin):
        super().__init__()
        self.title("Admin Dashboard")
        self.admin = admin
        self.login_attempts = 0
        self.captcha_attempts = 0
        self.captcha_code = self.admin.generate_captcha_code()
        self.session_timeout = timedelta(minutes=10)
        self.session_start_time = datetime.now()

        # Создаем таблицу для отображения данных
        self.tree = ttk.Treeview(self, columns=("ID", "Full Name", "Birth Date", "Phone", "Service", "Cost", "Order Date", "Status"))
        self.tree.heading("#0", text="ID")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Full Name", text="Full Name")
        self.tree.heading("Birth Date", text="Birth Date")
        self.tree.heading("Phone", text="Phone")
        self.tree.heading("Service", text="Service")
        self.tree.heading("Cost", text="Cost")
        self.tree.heading("Order Date", text="Order Date")
        self.tree.heading("Status", text="Status")
        self.tree.pack(expand=True, fill=tk.BOTH)

        # Заполняем таблицу данными
        self.load_data(admin)

        # Добавляем кнопку выхода
        tk.Button(self, text="Выход", command=self.logout).pack(pady=10)

        # Запускаем таймер сессии
        self.start_session_timer()

    def load_data(self, admin):
        data = admin.get_patients_and_services()
        for row in data:
            self.tree.insert("", "end", values=row)

    def start_session_timer(self):
        self.session_timer_id = self.after(1000, self.check_session_timeout)

    def check_session_timeout(self):
        current_time = datetime.now()
        elapsed_time = current_time - self.session_start_time
        remaining_time = self.session_timeout - elapsed_time

        if elapsed_time >= self.session_timeout:
            messagebox.showinfo("Таймаут", "Сессия завершена из-за бездействия.")
            self.logout()
        elif remaining_time <= timedelta(minutes=5):
            messagebox.showinfo("Предупреждение", f"До конца текущей сессии осталось {int(remaining_time.total_seconds() // 60)} минут.")

        self.session_timer_id = self.after(1000, self.check_session_timeout)

    def logout(self):
        self.destroy()


class Patient(User):
    def __init__(self, conn):
        super().__init__(conn)

    def book_appointment(self, full_name, dob, phone, selected_services, order_date):
        self.cursor.execute('''
            INSERT INTO patients (full_name, birth_date, phone)
            VALUES (?, ?, ?)
        ''', (full_name, dob, phone))

        self.cursor.execute('SELECT last_insert_rowid()')
        patient_id = self.cursor.fetchone()[0]

        for service in selected_services:
            if service["var"].get() == 1:
                service_info = self.get_service_info(service["name"])
                self.cursor.execute('''
                    INSERT INTO orders (patient_id, service_id, order_date, status, cost)
                    VALUES (?, ?, ?, ?, ?)
                ''', (patient_id, service_info[0], order_date, 'Pending', service_info[1]))

        self.conn.commit()
        messagebox.showinfo("Успех", "Вы успешно записаны на обследование!")

    def get_service_info(self, service_name):
        self.cursor.execute('SELECT id, cost FROM services WHERE name = ?', (service_name,))
        service_info = self.cursor.fetchone()
        return service_info if service_info else (None, 0.0)




class Accountant:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()

    def calculate_expenses(self):
        # Ваш код для расчета расходов на обследования
        # Например, можно использовать SQL-запрос для получения общей стоимости обследований
        self.cursor.execute('SELECT SUM(cost) FROM services')
        total_expenses = self.cursor.fetchone()[0]
        return total_expenses if total_expenses else 0
    
    def generate_reports(self):
        # Add logic to generate reports from the data stored in the database
        pass

class HospitalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hospital Management System")
        self.credentials = {
            "admin": "12345",
            "accountant": "12345"
        }

        self.conn = sqlite3.connect('hospital.db')
        self.admin = Admin(self.conn)
        self.patient = Patient(self.conn)
        self.accountant = Accountant(self.conn)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.patient_tab = tk.Frame(self.notebook)
        self.login_tab = tk.Frame(self.notebook)

        self.notebook.add(self.patient_tab, text="Пациенты")
        self.notebook.add(self.login_tab, text="Войти")
        self.login_attempts = 0

        self.create_patient_tab()
        self.create_login_tab()
        self.create_tables()

    def create_tables(self):
        self.admin.create_tables()

    def create_patient_tab(self):
        self.patient_frame = tk.Frame(self.patient_tab)
        self.patient_frame.pack(pady=10)

        tk.Label(self.patient_frame, text="ФИО:").grid(row=0, column=0, padx=10, pady=10)
        self.name_entry = tk.Entry(self.patient_frame)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.patient_frame, text="Дата рождения:").grid(row=1, column=0, padx=10, pady=10)
        self.dob_entry = DateEntry(
            self.patient_frame, 
            width=12, 
            background='darkblue',
            foreground='white', 
            borderwidth=2, 
            date_pattern='dd.MM.yyyy',
            font='Arial 10',
            locale='ru_RU'
        )
        self.dob_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(self.patient_frame, text="Телефон:").grid(row=2, column=0, padx=10, pady=10)
        self.phone_entry = tk.Entry(self.patient_frame)
        self.phone_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(self.patient_frame, text="Выберите обследования:").grid(row=3, column=0, padx=10, pady=10)

        self.services_frame = tk.Frame(self.patient_tab)
        self.services_frame.pack(pady=10)

        self.selected_services = []

        # Получение списка обследований из базы данных
        services = self.get_services()

        for i, service in enumerate(services):
            var = tk.IntVar()
            tk.Checkbutton(self.services_frame, text=service[1], variable=var).grid(row=i, column=0, padx=10, pady=5)
            self.selected_services.append({"name": service[1], "var": var, "cost": service[2]})

        tk.Label(self.patient_frame, text="Дата записи:").grid(row=4, column=0, padx=10, pady=10)
        self.order_date_entry = DateEntry(
            self.patient_frame, 
            width=12, 
            background='darkblue',
            foreground='white', 
            borderwidth=2, 
            date_pattern='dd.MM.yyyy',
            font='Arial 10',
            locale='ru_RU',
            state='readonly',  # Запрет выбора другой даты
            validate='focusout'  # Проверка на изменение даты при потере фокуса
        )

        self.order_date_entry.grid(row=4, column=1, padx=10, pady=10)

        tk.Button(self.patient_tab, text="Записаться", command=self.book_appointment).pack(pady=10)

    def get_patients(self):
        self.patient.cursor.execute('SELECT * FROM patients')
        return self.patient.cursor.fetchall()
    
    def check_credentials(self, entered_login, entered_password):
        print(f"Entered Login: {entered_login}, Entered Password: {entered_password}")
        return entered_login == "admin" and entered_password == "12345"


    def create_login_tab(self):
        self.login_frame = tk.Frame(self.login_tab)
        self.login_frame.pack(pady=10)

        tk.Label(self.login_frame, text="Логин:").grid(row=0, column=0, padx=10, pady=10)
        self.login_entry = tk.Entry(self.login_frame)
        self.login_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.login_frame, text="Пароль:").grid(row=1, column=0, padx=10, pady=10)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Button(self.login_frame, text="Войти", command=self.login).grid(row=2, columnspan=2, pady=10)

    def login(self):
        entered_login = self.login_entry.get()
        entered_password = self.password_entry.get()

        # Проверка учетных данных
        if self.check_credentials(entered_login, entered_password):
            # Сброс счетчика неверных попыток логина и пароля
            self.login_attempts = 0

            # Проверка роли пользователя и запуск соответствующей сессии
            if entered_login == "admin":
                self.admin_session()
            elif entered_login == "accountant":
                self.accountant_session()

            messagebox.showinfo("Вход", f"Вы вошли как {entered_login}.")
        else:
            # Увеличение счетчика неверных попыток логина и пароля
            self.login_attempts += 1

            # Если достигнуто максимальное количество попыток, отображаем капчу (в этом случае оставляем вашу логику)
            if self.login_attempts >= 3:
                # self.show_captcha_window()  # Капча убрана
                pass
            else:
                messagebox.showerror("Ошибка", "Неверный логин или пароль.")

    def admin_session(self):
        self.admin.session_timeout = datetime.now() + timedelta(minutes=10)
        self.show_patients_and_services()

    def accountant_session(self):
        self.accountant.session_timeout = datetime.now() + timedelta(minutes=10)
        self.show_expenses()

    def show_patients_and_services(self):
        for widget in self.patient_tab.winfo_children():
            widget.destroy()

        tk.Label(self.patient_tab, text="Список пациентов и обследований", font=("Helvetica", 16)).pack(pady=10)

        # Получаем список пациентов и обследований
        patients = self.get_patients()
        services = self.get_services()

        # Выводим информацию о пациентах
        tk.Label(self.patient_tab, text="Пациенты:").pack()
        if patients:
            for patient in patients:
                tk.Label(self.patient_tab, text=f"ID: {patient[0]}, Имя: {patient[1]}, Дата рождения: {patient[2]}, Телефон: {patient[3]}").pack()
        else:
            tk.Label(self.patient_tab, text="Нет зарегистрированных пациентов").pack()

        # Выводим информацию об обследованиях
        tk.Label(self.patient_tab, text="Обследования:").pack()
        if services:
            for service in services:
                tk.Label(self.patient_tab, text=f"ID: {service[0]}, Название: {service[1]}, Стоимость: {service[2]}").pack()
        else:
            tk.Label(self.patient_tab, text="Нет доступных обследований").pack()

        self.create_logout_button()

    def book_appointment(self):
        full_name = self.name_entry.get()
        dob = self.dob_entry.get()
        phone = self.phone_entry.get()
        order_date = self.order_date_entry.get()

        if not full_name or not dob or not phone:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля.")
            return

        if all(service["var"].get() == 0 for service in self.selected_services):
            messagebox.showerror("Ошибка", "Выберите хотя бы одно обследование.")
            return

        self.patient.book_appointment(full_name, dob, phone, self.selected_services, order_date)

    def show_expenses(self):
        for widget in self.patient_tab.winfo_children():
            widget.destroy()

        tk.Label(self.patient_tab, text="Расходы на обследования", font=("Helvetica", 16)).pack(pady=10)

        total_expenses = self.accountant.calculate_expenses()
        tk.Label(self.patient_tab, text=f"Общие расходы на обследования: {total_expenses}").pack()

        self.create_logout_button()

    def create_logout_button(self):
        tk.Button(self.patient_tab, text="Выйти", command=self.logout).pack(pady=10)

    def logout(self):
        self.notebook.select(self.login_tab)

    def get_services(self):
        self.admin.cursor.execute('SELECT * FROM services')
        return self.admin.cursor.fetchall()




if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalApp(root)
    root.mainloop()
