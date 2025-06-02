#!/usr/bin/env python3
"""
Безопасный скрипт для рассылки писем через Gmail
Пароль вводится во время выполнения, не хранится в коде
"""

import smtplib
import getpass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import sys

def send_email_batch(sender_email, sender_password, recipients, subject, body, attachment_path=None):
    """Отправка письма нескольким получателям"""
    
    # Gmail SMTP настройки
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    try:
        # Подключение к серверу
        print("🔌 Подключение к Gmail SMTP...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Включаем шифрование
        
        # Авторизация
        print("🔐 Авторизация...")
        server.login(sender_email, sender_password)
        print("✅ Успешная авторизация!")
        
        # Отправляем каждому получателю
        successful_sends = 0
        failed_sends = 0
        
        for recipient in recipients:
            try:
                # Создаем сообщение
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient.strip()
                msg['Subject'] = subject
                
                # Добавляем текст
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # Добавляем вложение, если есть
                if attachment_path and os.path.exists(attachment_path):
                    with open(attachment_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
                
                # Отправляем
                text = msg.as_string()
                server.sendmail(sender_email, recipient.strip(), text)
                print(f"✅ Отправлено: {recipient.strip()}")
                successful_sends += 1
                
            except Exception as e:
                print(f"❌ Ошибка отправки {recipient}: {e}")
                failed_sends += 1
        
        # Закрываем соединение
        server.quit()
        
        print(f"\n📊 ИТОГИ:")
        print(f"✅ Успешно отправлено: {successful_sends}")
        print(f"❌ Ошибок: {failed_sends}")
        
        return successful_sends, failed_sends
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return 0, len(recipients)

def get_recipients():
    """Получение списка получателей"""
    print("\n📧 ПОЛУЧАТЕЛИ:")
    print("Введите email адреса получателей (по одному на строку)")
    print("Для завершения введите пустую строку")
    
    recipients = []
    while True:
        email = input(f"Получатель {len(recipients) + 1}: ").strip()
        if not email:
            break
        
        # Простая валидация email
        if '@' in email and '.' in email:
            recipients.append(email)
            print(f"✅ Добавлен: {email}")
        else:
            print("❌ Некорректный email, попробуйте снова")
    
    return recipients

def get_email_content():
    """Получение содержимого письма"""
    print("\n✍️ СОДЕРЖИМОЕ ПИСЬМА:")
    
    subject = input("Тема письма: ").strip()
    
    print("\nТекст письма (для завершения введите '###' на отдельной строке):")
    body_lines = []
    while True:
        line = input()
        if line.strip() == '###':
            break
        body_lines.append(line)
    
    body = '\n'.join(body_lines)
    
    return subject, body

def get_attachment():
    """Получение пути к вложению"""
    attachment = input("\nПуть к файлу-вложению (или Enter для пропуска): ").strip()
    
    if attachment and os.path.exists(attachment):
        print(f"✅ Вложение найдено: {attachment}")
        return attachment
    elif attachment:
        print("❌ Файл не найден")
        return None
    else:
        return None

def main():
    """Основная функция"""
    print("="*50)
    print("📧 Gmail массовая рассылка")
    print("="*50)
    
    # Получаем email отправителя
    sender_email = input("\n👤 Ваш Gmail: ").strip()
    
    # Безопасно получаем пароль
    print("\n🔐 Введите пароль (или App Password для Gmail):")
    print("ℹ️  Символы не отображаются для безопасности")
    sender_password = getpass.getpass("Пароль: ")
    
    # Получаем получателей
    recipients = get_recipients()
    
    if not recipients:
        print("❌ Нет получателей. Выход.")
        return
    
    print(f"\n📋 Получатели ({len(recipients)}):")
    for i, recipient in enumerate(recipients, 1):
        print(f"  {i}. {recipient}")
    
    # Получаем содержимое
    subject, body = get_email_content()
    
    # Получаем вложение
    attachment_path = get_attachment()
    
    # Подтверждение
    print(f"\n📋 СВОДКА:")
    print(f"От: {sender_email}")
    print(f"Кому: {len(recipients)} получателей")
    print(f"Тема: {subject}")
    print(f"Вложение: {'Да' if attachment_path else 'Нет'}")
    
    confirm = input("\n❓ Отправить письма? (y/n): ").lower()
    
    if confirm in ['y', 'yes', 'да', 'д']:
        print("\n🚀 Начинаем отправку...")
        successful, failed = send_email_batch(
            sender_email, sender_password, recipients, 
            subject, body, attachment_path
        )
        
        if successful > 0:
            print(f"\n🎉 Рассылка завершена!")
        
    else:
        print("❌ Отправка отменена")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")