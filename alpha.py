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
                phone TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending'
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

        def get_pending_orders(self):
            self.cursor.execute('''
                SELECT orders.id, patients.full_name, patients.phone, services.name, orders.cost, orders.order_date
                FROM orders
                JOIN patients ON orders.patient_id = patients.id
                JOIN services ON orders.service_id = services.id
                WHERE orders.status = ?
            ''', ('Pending',))

            return self.cursor.fetchall()

    
class LabAssistant(User):
    def __init__(self, conn, root=None):
        super().__init__(conn)
        self.root = root

    # Другие методы класса

    def complete_service(self, order_id):
        try:
            with self.conn:
                self.cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('Completed', order_id))
            print(f"Заказ с ID {order_id} успешно завершен лаборантом.")
            
            # Получим информацию о заказе
            order_info = self.get_order_info(order_id)
            
            # Проверим, завершено ли обследование
            if order_info and order_info['status'] == 'Completed':
                # Вызовем метод лаборанта для создания отчета
                self.generate_report(order_info)
        except Exception as e:
            print(f"Произошла ошибка при завершении заказа: {e}")

    def generate_report(self, order_info):
        try:
            # Ваша логика по созданию отчета
            report_data = f"Отчет для заказа {order_info['id']}. Пациент: {order_info['patient_id']}."
            self.save_report_to_database(report_data)
            print("Отчет успешно создан и сохранен.")
        except Exception as e:
            print(f"Произошла ошибка при генерации отчета: {e}")

    def save_report_to_database(self, report_data):
        try:
            with self.conn:
                self.cursor.execute('INSERT INTO reports (content, creation_date) VALUES (?, ?)',
                                    (report_data, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        except Exception as e:
            print(f"Произошла ошибка при сохранении отчета в базу данных: {e}")

    def get_order_info(self, order_id):
        try:
            with self.conn:
                self.cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
                return self.cursor.fetchone()
        except Exception as e:
            print(f"Произошла ошибка при получении информации о заказе: {e}")

    


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
        self.lab_tab = tk.Frame(self.notebook)
        self.notebook.add(self.lab_tab, text="Лаборант")
        self.create_lab_tab()

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
        self.lab_session_timer_id = self.after(1000, self.check_lab_session_timeout)

    def check_lab_session_timeout(self):
        current_time = datetime.now()
        elapsed_time = current_time - self.lab_start_time
        remaining_time = self.lab_session_timeout - elapsed_time

        if elapsed_time >= self.lab_session_timeout:
            messagebox.showinfo("Таймаут", "Сессия лаборанта завершена из-за бездействия.")
            self.logout()
        elif remaining_time <= timedelta(minutes=5):
            messagebox.showinfo("Предупреждение", f"До конца сессии лаборанта осталось {int(remaining_time.total_seconds() // 60)} минут.")

        self.lab_session_timer_id = self.after(1000, self.check_lab_session_timeout)

    def admin_session(self):
        self.admin.session_timeout = datetime.now() + timedelta(minutes=10)
        self.lab_start_time = datetime.now()
        self.lab_session_timeout = timedelta(minutes=15)
        self.show_patients_and_services()

    def create_lab_tab(self):
        self.lab_frame = tk.Frame(self.lab_tab)
        self.lab_frame.pack(pady=10)

        tk.Label(self.lab_frame, text="Список заказов", font=("Helvetica", 16)).pack(pady=10)

        # Создаем таблицу для отображения заказов
        self.order_tree = ttk.Treeview(self.lab_frame, columns=("ID", "Full Name", "Phone", "Service", "Cost", "Order Date"))
        self.order_tree.heading("#0", text="ID")
        self.order_tree.heading("ID", text="ID")
        self.order_tree.heading("Full Name", text="Full Name")
        self.order_tree.heading("Phone", text="Phone")
        self.order_tree.heading("Service", text="Service")
        self.order_tree.heading("Cost", text="Cost")
        self.order_tree.heading("Order Date", text="Order Date")
        self.order_tree.pack(expand=True, fill=tk.BOTH)

        # Добавляем кнопку для просмотра заказов
        tk.Button(self.lab_frame, text="Просмотреть заказы", command=self.show_orders).pack(pady=10)

    def show_orders(self):
        # Заполняем таблицу заказов данными
        self.load_orders(self.admin)

    def load_orders(self, admin):
        data = admin.get_pending_orders()
        self.order_tree.delete(*self.order_tree.get_children())  # Очищаем таблицу перед заполнением новыми данными
        for row in data:
            self.order_tree.insert("", "end", values=row)

    def logout(self):
        self.destroy()

    def accept_patient(self, patient_id):
        try:
            self.cursor.execute('UPDATE patients SET status = ? WHERE id = ?', ('Accepted', patient_id))
            self.conn.commit()
            print(f"Пациент с ID {patient_id} успешно принят лаборантом.")
        except Exception as e:
            print(f"Произошла ошибка при принятии пациента: {e}")

class Laborant(User):
    def __init__(self, conn):
        super().__init__(conn)

    def accept_order(self, patient_id, service_id, order_date):
        try:
            self.cursor.execute('''
                UPDATE orders 
                SET status = ?, order_date = ?
                WHERE patient_id = ? AND service_id = ? AND status = ?
            ''', ('Accepted', order_date, patient_id, service_id, 'Pending'))

            self.conn.commit()
            print(f"Заказ для пациента с ID {patient_id} принят лаборантом.")
        except Exception as e:
            print(f"Произошла ошибка при принятии заказа: {e}")


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


class LabResearcher(User):
    def __init__(self, conn, root=None):
        super().__init__(conn)
        self.root = root

    def view_patients_reports(self):
        try:
            with self.conn:
                self.cursor.execute('SELECT * FROM reports')
                reports = self.cursor.fetchall()
                for report in reports:
                    order_info = self.get_order_info(report['order_id'])
                    patient_info = self.get_patient_info(order_info['patient_id'])
                    print(f"Отчет для пациента {patient_info['full_name']} ({patient_info['dob']}): {report['content']}")
        except Exception as e:
            print(f"Произошла ошибка при просмотре отчетов: {e}")

    def get_patient_info(self, patient_id):
        self.cursor.execute('SELECT * FROM patients WHERE id = ?', (patient_id,))
        return self.cursor.fetchone()

    def check_labsis_credentials(self, entered_login, entered_password):
        return entered_login == "labsis" and entered_password == "labsis_password"


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
            "accountant": "12345",
            "laborant": "12345",
            "labsis": "12345",
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
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.lab_assistant_tab = tk.Frame(self.notebook)
        self.notebook.add(self.lab_assistant_tab, text="Лаборант")
        self.lab_assistant = LabAssistant(self.conn)
        

        self.create_lab_assistant_tab()

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


    def create_lab_assistant_tab(self):
        self.lab_assistant_tab = tk.Frame(self.notebook)
        self.notebook.add(self.lab_assistant_tab, text="Лаборант")
        self.create_lab_assistant_widgets()

    # Создаем объект лаборанта
        self.lab_assistant = LabAssistant(self.conn)

    def check_labsis_credentials(self, entered_login, entered_password):
        return entered_login == "labsis" and entered_password == "12345"
    
    def check_credentials(self, entered_login, entered_password):
        print(f"Entered Login: {entered_login}, Entered Password: {entered_password}")
        return entered_login in self.credentials and self.credentials[entered_login] == entered_password

    def create_lab_assistant_widgets(self):
        self.lab_assistant_frame = tk.Frame(self.lab_assistant_tab)
        self.lab_assistant_frame.pack(pady=10)
    
        tk.Label(self.lab_assistant_frame, text="ID заказа:").grid(row=0, column=0, padx=10, pady=10)
        self.order_id_entry = tk.Entry(self.lab_assistant_frame)
        self.order_id_entry.grid(row=0, column=1, padx=10, pady=10)
    
        tk.Button(self.lab_assistant_frame, text="Принять заказ", command=self.accept_order).grid(row=1, columnspan=2, pady=10)
        tk.Button(self.lab_assistant_frame, text="Выполнить услугу", command=self.complete_service).grid(row=2, columnspan=2, pady=10)
        tk.Button(self.lab_assistant_frame, text="Создать отчет", command=self.generate_report).grid(row=3, columnspan=2, pady=10)

    def show_lab_assistant_widgets(self):
        self.notebook.select(self.lab_assistant_tab)


    def accept_order(self):
        order_id = self.order_id_entry.get()
        if order_id.isdigit():
            self.lab_assistant.accept_patient(int(order_id))
            messagebox.showinfo("Успех", f"Заказ с ID {order_id} принят лаборантом.")
        else:
            messagebox.showerror("Ошибка", "Введите корректный ID заказа.")


    def complete_service(self):
        order_id = self.order_id_entry.get()
        if order_id:
            self.lab_assistant.complete_service(int(order_id))
        else:
            messagebox.showerror("Ошибка", "Введите ID заказа.")

    def generate_report(self):
        self.lab_assistant.generate_report()
        messagebox.showinfo("Успех", "Отчет успешно создан и сохранен.")


    def check_laborant_credentials(self, entered_login, entered_password):
        # Здесь вы можете добавить логику проверки логина и пароля для лаборанта
        return entered_login == "laborant" and entered_password == "12345"

    def get_patients(self):
        self.patient.cursor.execute('SELECT * FROM patients')
        return self.patient.cursor.fetchall()

    def laborant_session(self):
        self.create_lab_assistant_tab()
        self.show_lab_assistant_widgets()

        # Здесь вы можете добавить логику для сессии лаборанта, например, просмотр заказов и их выполнение

        self.create_logout_button()  # добавляем кнопку выхода

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

    def labsis_session(self):
        # Добавьте логику для сессии лаборанта-исследователя, если необходимо
        self.create_lab_assistant_tab()
        self.show_lab_assistant_widgets()
        self.create_logout_button()

    def login(self):
        entered_login = self.login_entry.get()
        entered_password = self.password_entry.get()

        if self.check_credentials(entered_login, entered_password):
            self.login_attempts = 0

            if entered_login == "admin":
                self.admin_session()
            elif entered_login == "accountant":
                self.accountant_session()
            elif entered_login == "laborant":
                self.laborant_session()
            elif entered_login == "labsis":
                self.labsis_session()
            else:
                messagebox.showerror("Ошибка", "Неверный логин или пароль.")
        else:
            self.login_attempts += 1

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
