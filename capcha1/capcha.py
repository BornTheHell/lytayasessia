import tkinter as tk
from tkinter import Entry, Label, StringVar
from PIL import Image, ImageTk
from captcha.image import ImageCaptcha
import random
import string

class CaptchaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Captcha App")

        # Инициализация переменных
        self.correct_answer = None

        # Генерируем и показываем капчу
        self.generate_captcha()

        # Создаем виджет для ввода ответа
        self.answer_var = StringVar()
        self.answer_entry = Entry(root, textvariable=self.answer_var)
        self.answer_entry.pack(pady=10)

        # Кнопка для проверки ответа
        check_button = tk.Button(root, text="Check", command=self.check_answer)
        check_button.pack(pady=5)

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
            self.show_main_app()
        else:
            # Если ответ неверный, генерируем новую капчу
            self.generate_captcha()

    def show_main_app(self):
        # Здесь вы можете добавить код для основной части вашего приложения
        main_label = Label(self.root, text="Добро пожаловать в основную часть приложения!")
        main_label.pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = CaptchaApp(root)
    root.mainloop()