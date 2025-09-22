#!/usr/bin/env python3
"""
Mail Gönderici - Modern GUI + Hover + Rounded
"""
import os
import re
import json
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from tkinter import Tk, Frame, Label, Entry, Text, Button, END, BOTH, LEFT, RIGHT, Y, X, filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.mail_gui_config.json')
EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

class MailGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('📧 Mail Gönderici — Modern GUI')
        self.root.geometry('1280x720')
        self.root.configure(bg='#1e1e2e')

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#1e1e2e')
        style.configure('TLabel', background='#1e1e2e', foreground='white', font=('Segoe UI', 11))
        style.configure('Rounded.TButton', font=('Segoe UI', 10, 'bold'), padding=8, relief='flat', background='#3a3a4e', foreground='white')
        style.map('Rounded.TButton', background=[('active', '#5a5aff')])

        self.config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': '',
            'password': ''
        }
        self.load_config()
        self.create_widgets()

    def create_widgets(self):
        smtp_frame = ttk.Frame(self.root, padding=12, style='TFrame')
        smtp_frame.pack(fill=X, pady=8)

        def add_entry(row, col, text, var, width=None, password=False):
            ttk.Label(smtp_frame, text=text).grid(row=row, column=col, sticky='w', padx=5, pady=5)
            entry = Entry(smtp_frame, font=('Consolas', 11), bg='#2e2e3e', fg='white', insertbackground='white', show='*' if password else '')
            if var:
                entry.insert(0, var)
            if width:
                entry.config(width=width)
            entry.grid(row=row, column=col+1, sticky='ew', padx=5)
            return entry

        self.smtp_entry = add_entry(0, 0, 'SMTP Server:', self.config.get('smtp_server', ''))
        self.port_entry = add_entry(0, 2, 'Port:', str(self.config.get('smtp_port', 587)), width=8)
        self.user_entry = add_entry(1, 0, 'E-posta:', self.config.get('username', ''))
        self.pass_entry = add_entry(1, 2, 'Şifre:', self.config.get('password', ''), password=True)

        save_btn = ttk.Button(smtp_frame, text='💾 Kaydet', style='Rounded.TButton', command=self.save_config)
        save_btn.grid(row=0, column=4, rowspan=2, padx=10, pady=5)

        smtp_frame.grid_columnconfigure(1, weight=1)

        middle = ttk.Frame(self.root, padding=12, style='TFrame')
        middle.pack(fill=BOTH, expand=True)

        left_col = ttk.Frame(middle, style='TFrame')
        left_col.pack(side=LEFT, fill=BOTH, expand=True)

        ttk.Label(left_col, text='📬 Alıcılar:').pack(anchor='w')
        self.recipients_text = Text(left_col, height=10, bg='#2e2e3e', fg='white', insertbackground='white', font=('Consolas', 11), relief='flat')
        self.recipients_text.pack(fill=BOTH, expand=True, pady=4)

        ttk.Label(left_col, text='📌 Başlık:').pack(anchor='w', pady=(8,0))
        self.subject_entry = Entry(left_col, font=('Segoe UI', 11), bg='#2e2e3e', fg='white', insertbackground='white', relief='flat')
        self.subject_entry.pack(fill=X, pady=2)

        ttk.Label(left_col, text='📝 Mesaj:').pack(anchor='w', pady=(8,0))
        self.body_text = Text(left_col, height=8, bg='#2e2e3e', fg='white', insertbackground='white', font=('Segoe UI', 11), relief='flat')
        self.body_text.pack(fill=BOTH, expand=True, pady=4)

        right_col = ttk.Frame(middle, width=420, style='TFrame')
        right_col.pack(side=RIGHT, fill=Y, padx=10)

        ttk.Label(right_col, text='🖼️ Resim Ayarları').pack(anchor='w')
        ttk.Button(right_col, text='📁 Klasör Seç', style='Rounded.TButton', command=self.select_image_folder).pack(fill=X, pady=4)
        ttk.Button(right_col, text='🖼️ Tek Resim Seç', style='Rounded.TButton', command=self.select_single_image).pack(fill=X, pady=4)
        ttk.Button(right_col, text='❌ Temizle', style='Rounded.TButton', command=self.clear_image_selection).pack(fill=X, pady=4)

        self.image_info_label = ttk.Label(right_col, text='Seçili: yok', wraplength=380)
        self.image_info_label.pack(anchor='w', pady=(6,0))

        if PIL_AVAILABLE:
            self.preview_label = Label(right_col, bg='#1e1e2e')
            self.preview_label.pack(pady=8)
        else:
            ttk.Label(right_col, text='⚠️ PIL bulunamadı — önizleme yok').pack(pady=8)

        bottom = ttk.Frame(self.root, padding=10, style='TFrame')
        bottom.pack(fill=BOTH)

        ttk.Button(bottom, text='🚀 Gönder', style='Rounded.TButton', command=self.on_send).pack(side=LEFT, padx=5)
        ttk.Button(bottom, text='🧹 Log Temizle', style='Rounded.TButton', command=self.clear_log).pack(side=LEFT, padx=5)

        self.log_text = Text(bottom, height=6, bg='#101018', fg='lime', insertbackground='lime', font=('Consolas', 10), relief='flat')
        self.log_text.pack(fill=BOTH, expand=True, side=RIGHT)

        self.image_folder = None
        self.single_image = None

    def log(self, *args):
        text = ' '.join(str(a) for a in args)
        self.log_text.insert(END, text + '\n')
        self.log_text.see('end')
        print(text)

    def save_config(self):
        self.config['smtp_server'] = self.smtp_entry.get().strip()
        try:
            self.config['smtp_port'] = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showerror('Hata', 'Port rakam olmalı')
            return
        self.config['username'] = self.user_entry.get().strip()
        self.config['password'] = self.pass_entry.get().strip()
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self.config, f)
            messagebox.showinfo('Bilgi', f'Ayarlar kaydedildi: {CONFIG_PATH}')
        except Exception as e:
            messagebox.showerror('Hata', f'Ayarlar kaydedilemedi: {e}')

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    data = json.load(f)
                self.config.update(data)
            except Exception:
                pass

    def select_image_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.image_folder = folder
        self.single_image = None
        self.image_info_label.config(text=f'Seçili klasör: {folder}')
        self._update_preview_from_folder()

    def select_single_image(self):
        file = filedialog.askopenfilename(filetypes=[('PNG Files', '*.png'), ('All files','*.*')])
        if not file:
            return
        self.single_image = file
        self.image_folder = None
        self.image_info_label.config(text=f'Seçili tek resim: {file}')
        self._update_preview_single()

    def clear_image_selection(self):
        self.image_folder = None
        self.single_image = None
        self.image_info_label.config(text='Seçili: yok')
        if PIL_AVAILABLE:
            self.preview_label.config(image='')

    def _update_preview_single(self):
        if not PIL_AVAILABLE or not self.single_image:
            return
        try:
            img = Image.open(self.single_image)
            img.thumbnail((360,240))
            tkimg = ImageTk.PhotoImage(img)
            self.preview_label.image = tkimg
            self.preview_label.config(image=tkimg)
        except Exception as e:
            self.log('Önizleme hatası:', e)

    def _update_preview_from_folder(self):
        if not PIL_AVAILABLE or not self.image_folder:
            return
        p = os.path.join(self.image_folder, '1.png')
        if os.path.exists(p):
            try:
                img = Image.open(p)
                img.thumbnail((360,240))
                tkimg = ImageTk.PhotoImage(img)
                self.preview_label.image = tkimg
                self.preview_label.config(image=tkimg)
            except Exception as e:
                self.log('Önizleme hatası:', e)

    def validate_email(self, email):
        return EMAIL_REGEX.match(email)

    def build_image_list_for_recipients(self, recipients):
        n = len(recipients)
        if self.single_image:
            return [self.single_image] * n
        if self.image_folder:
            images = []
            for i in range(1, n+1):
                p = os.path.join(self.image_folder, f"{i}.png")
                if not os.path.exists(p):
                    return None
                images.append(p)
            return images
        return None

    def on_send(self):
        raw = self.recipients_text.get('1.0', END).strip()
        if not raw:
            messagebox.showerror('Hata', 'Alıcı listesi boş')
            return
        lines = [l.strip() for l in raw.replace(',', '\n').splitlines() if l.strip()]
        recipients = lines
        invalid = [r for r in recipients if not self.validate_email(r)]
        if invalid:
            messagebox.showerror('Hata', f'Geçersiz e-posta adresleri:\n{invalid[:10]}')
            return

        subject = self.subject_entry.get().strip() or '(no subject)'
        body = self.body_text.get('1.0', END).strip()

        image_list = self.build_image_list_for_recipients(recipients)
        if image_list is None:
            messagebox.showerror('Hata', 'Resimlerden bir veya daha fazlası eksik.')
            return

        if not messagebox.askyesno('Onay', f'{len(recipients)} kişiye mail gönderilecek. Göndermek istiyor musunuz?'):
            return

        smtp_server = self.smtp_entry.get().strip() or self.config.get('smtp_server')
        try:
            smtp_port = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showerror('Hata', 'Port sayısı hatalı')
            return
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()

        self.log('SMTP:', smtp_server, smtp_port, 'Kullanıcı:', username)

        try:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
            server.login(username, password)
        except Exception as e:
            messagebox.showerror('Hata', f'SMTP bağlantı/oturum açma hatası:\n{e}')
            return

        failed = []
        for idx, (email, img_path) in enumerate(zip(recipients, image_list), start=1):
            try:
                msg = MIMEMultipart()
                msg['From'] = username
                msg['To'] = email
                msg['Subject'] = subject

                msg.attach(MIMEText(body, 'plain'))
                with open(img_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(img_path))
                    msg.attach(img)

                server.send_message(msg)
                self.log(f'[{idx}/{len(recipients)}] Gönderildi ->', email, f'({os.path.basename(img_path)})')
                time.sleep(0.6)
            except Exception as e:
                self.log(f'[{idx}/{len(recipients)}] Hata ->', email, e)
                failed.append((email, str(e)))

        server.quit()

        if failed:
            messagebox.showwarning('Bitti - Hatalar Var', f"Gönderim tamamlandı fakat {len(failed)} hata oldu. Log'u kontrol et.")
        else:
            messagebox.showinfo('Bitti', 'Tüm mailler gönderildi!')

    def clear_log(self):
        self.log_text.delete('1.0', END)

if __name__ == '__main__':
    root = Tk()
    app = MailGUI(root)
    root.mainloop()
