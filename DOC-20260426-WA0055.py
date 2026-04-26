import cv2
import os
import sys
import time
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import customtkinter as ctk
from ultralytics import YOLO

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue") 

class SecurityCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Infinity Smart Security - AI Detector")
        self.root.geometry("850x850")
        
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))

        self.base_folder = os.path.join(application_path, "Categories")
        self.categories = ["Persons", "Animals", "Vehicles"]
        self.setup_directories()

        self.model = YOLO('yolov8n.pt')
        self.PERSON_CLASS = [0]
        self.VEHICLE_CLASSES = [1, 2, 3, 5, 7]
        self.ANIMAL_CLASSES = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        
        self.cooldown_time = 5.0
        self.last_capture = {"Persons": 0, "Animals": 0, "Vehicles": 0}
        self.cap = None
        self.is_running = False

        self.build_ui()

    def setup_directories(self):
        for cat in self.categories:
            os.makedirs(os.path.join(self.base_folder, cat), exist_ok=True)

    def build_ui(self):
        # تهيئة الشبكة (Grid) لجعل الواجهة متجاوبة
        self.root.grid_rowconfigure(4, weight=1) # ده بيخلي مساحة فاضية قبل الكارت عشان ميزقوش لتحت
        self.root.grid_columnconfigure(0, weight=1)

        # 1. العنوان
        self.title_label = ctk.CTkLabel(self.root, text="نظام المراقبة الذكي", font=("Arial", 28, "bold"), text_color="#ecf0f1")
        self.title_label.grid(row=0, column=0, pady=(20, 10))

        # 2. إطار شاشة الكاميرا
        self.video_frame = ctk.CTkFrame(self.root, corner_radius=15, fg_color="#1c1c1c", width=640, height=480)
        self.video_frame.grid(row=1, column=0, pady=10, padx=20)
        self.video_frame.grid_propagate(False)
        
        self.video_label = tk.Label(self.video_frame, bg="#000000")
        self.video_label.place(relx=0.5, rely=0.5, anchor="center")

        # 3. إطار أزرار التحكم
        self.btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, pady=10)

        self.start_btn = ctk.CTkButton(
            self.btn_frame, text="تشغيل الكاميرا", font=("Arial", 16, "bold"), 
            fg_color="#27ae60", hover_color="#2ecc71", corner_radius=8, width=160, height=40, 
            command=self.start_camera
        )
        self.start_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = ctk.CTkButton(
            self.btn_frame, text="إيقاف الكاميرا", font=("Arial", 16, "bold"), 
            fg_color="#c0392b", hover_color="#e74c3c", corner_radius=8, width=160, height=40, 
            command=self.stop_camera, state="disabled"
        )
        self.upload_btn = ctk.CTkButton(
            self.btn_frame, text="رفع فيديو", font=("Arial", 16, "bold"), 
            fg_color="#3498db", hover_color="#2980b9", corner_radius=8, width=160, height=40, 
            command=self.upload_video
        )
        self.upload_btn.grid(row=0, column=1, padx=10)

        self.stop_btn.grid(row=0, column=2, padx=10)

        # 4. شريط الحالة
        self.status_label = ctk.CTkLabel(self.root, text="⏳ الحالة: النظام متوقف", font=("Arial", 16), text_color="#95a5a6")
        self.status_label.grid(row=3, column=0, pady=5)

        # 5. كارت فريق Infinity (استخدمنا pady لضمان ظهوره كاملاً)
        self.team_frame = ctk.CTkFrame(self.root, corner_radius=10, fg_color="#2c3e50", border_width=2, border_color="#f39c12")
        self.team_frame.grid(row=5, column=0, pady=(10, 40), padx=40, sticky="ew")

        ctk.CTkLabel(self.team_frame, text="🌟 Proudly Made by Infinity Team 🌟", font=("Arial", 16, "bold"), text_color="#f39c12").pack(pady=(10, 2))
        ctk.CTkLabel(self.team_frame, text="Team Leader: Abdullah", font=("Arial", 14, "bold"), text_color="#ecf0f1").pack()
        ctk.CTkLabel(self.team_frame, text="Members: Judy | Arwa | Rawan | Nouran | Shrouk", font=("Arial", 13), text_color="#bdc3c7").pack(pady=(0, 10))

        # 6. زر الدعم الفني
        self.help_btn = ctk.CTkButton(
            self.root, text="If you have any problem (click here)", font=("Arial", 11, "underline"), 
            fg_color="transparent", text_color="#3498db", hover_color="#2c3e50", width=100, 
            command=self.open_whatsapp
        )
        self.help_btn.place(relx=0.99, rely=0.99, anchor="se")

    def open_whatsapp(self):
        webbrowser.open("https://chat.whatsapp.com/ENFEmq2glfJGc491JwaHnP")

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("خطأ", "لا يمكن الوصول إلى الكاميرا.")
            return
        self.is_running = True
        self.start_btn.configure(state="disabled", fg_color="#7f8c8d")
        if hasattr(self, 'upload_btn'):
            self.upload_btn.configure(state="disabled", fg_color="#7f8c8d")
        self.stop_btn.configure(state="normal", fg_color="#c0392b")
        self.status_label.configure(text="🟢 الحالة: الكاميرا تعمل - جاري التحليل...", text_color="#2ecc71")
        self.update_frame()

    def upload_video(self):
        file_path = filedialog.askopenfilename(
            title="اختر فيديو", 
            filetypes=(("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*"))
        )
        if file_path:
            self.cap = cv2.VideoCapture(file_path)
            if not self.cap.isOpened():
                messagebox.showerror("خطأ", "لا يمكن فتح الفيديو.")
                return
            self.is_running = True
            self.start_btn.configure(state="disabled", fg_color="#7f8c8d")
            self.upload_btn.configure(state="disabled", fg_color="#7f8c8d")
            self.stop_btn.configure(state="normal", fg_color="#c0392b")
            self.status_label.configure(text="🟢 الحالة: جاري تحليل الفيديو...", text_color="#2ecc71")
            self.update_frame()

    def stop_camera(self):
        self.is_running = False
        if self.cap: self.cap.release()
        self.video_label.config(image='')
        self.start_btn.configure(state="normal", fg_color="#27ae60")
        if hasattr(self, 'upload_btn'):
            self.upload_btn.configure(state="normal", fg_color="#3498db")
        self.stop_btn.configure(state="disabled", fg_color="#7f8c8d")
        self.status_label.configure(text="⏳ الحالة: النظام متوقف", text_color="#95a5a6")

    def process_detections(self, frame):
        results = self.model(frame, verbose=False)
        current_time = time.time()
        detected_this_frame = set()
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                if confidence > 0.5:
                    category_name, color = None, (0, 0, 0)
                    if class_id in self.PERSON_CLASS: category_name, color = "Persons", (0, 255, 0)
                    elif class_id in self.VEHICLE_CLASSES: category_name, color = "Vehicles", (0, 0, 255)
                    elif class_id in self.ANIMAL_CLASSES: category_name, color = "Animals", (0, 165, 255)
                    if category_name:
                        detected_this_frame.add(category_name)
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                        cv2.rectangle(frame, (x1, y1 - 30), (x1 + 150, y1), color, -1)
                        cv2.putText(frame, f"{category_name} {confidence:.2f}", (x1 + 5, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        for category in detected_this_frame:
            if current_time - self.last_capture[category] > self.cooldown_time:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filepath = os.path.join(self.base_folder, category, f"snap_{timestamp}.jpg")
                Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).save(filepath)
                self.last_capture[category] = current_time
        return frame

    def update_frame(self):
        if self.is_running:
            ret, frame = self.cap.read()
            if ret:
                processed_frame = self.process_detections(frame)
                img = Image.fromarray(cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)).resize((640, 480))
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                self.root.after(15, self.update_frame)
            else:
                self.stop_camera()
                messagebox.showinfo("انتهى", "انتهى عرض الفيديو.")

    def on_closing(self):
        self.stop_camera()
        self.root.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    app = SecurityCameraApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()