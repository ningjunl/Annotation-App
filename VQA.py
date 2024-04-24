import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import cv2
from PIL import Image, ImageTk
from setting import save_settings, load_settings

class AnnotationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RoadSide-VQA+VG 标注软件")
        self.geometry("800x300")
        # 初始化变量
        self.rope3d_path = None
        self.image_folder = None
        self.annotation_window = None
        self.image_files = []  # 图片文件列表

        self.setup_ui()  # 确保先调用 setup_ui 来创建所有 UI 组件
        self.load_user_settings()  # 然后加载用户设置

    def setup_ui(self):
        self.rope3d_path_label = tk.Label(self, text="Rope3D数据集路径:")
        self.rope3d_path_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.rope3d_path_entry = tk.Entry(self, width=50)
        self.rope3d_path_entry.grid(row=0, column=1, padx=10, pady=10)

        self.rope3d_browse_button = tk.Button(self, text="浏览", command=lambda: self.browse_directory(self.rope3d_path_entry))
        self.rope3d_browse_button.grid(row=0, column=2, padx=10, pady=10)
        
        self.image_folder_label = tk.Label(self, text="图像文件夹路径:")
        self.image_folder_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.image_folder_entry = tk.Entry(self, width=50)
        self.image_folder_entry.grid(row=1, column=1, padx=10, pady=10)

        self.image_folder_browse_button = tk.Button(self, text="浏览", command=lambda: self.browse_directory(self.image_folder_entry))
        self.image_folder_browse_button.grid(row=1, column=2, padx=10, pady=10)

        #在启动标注之前保存设置
        self.confirm_button = tk.Button(self, text="确定", command=self.start_and_save_settings)
        self.confirm_button.grid(row=2, column=1, pady=20)

    def save_user_settings(self):
        current_settings = load_settings()
        if current_settings.get("last_file_name") != "":
            """保存用户的设置"""
            settings = {
                'rope3d_path': self.rope3d_path_entry.get(),
                'image_folder': self.image_folder_entry.get(),
                'last_file_name': current_settings.get("last_file_name")
            }
        else:
            settings = {
                'rope3d_path': self.rope3d_path_entry.get(),
                'image_folder': self.image_folder_entry.get(),
                'last_file_name': self.annotation_window.file_name if self.annotation_window else "None"
            }
        print(settings)
        save_settings(settings)

    def load_user_settings(self):
        """加载用户的设置"""
        settings = load_settings()
        # 清空输入框，并插入最新的设置值
        self.rope3d_path_entry.delete(0, tk.END)
        self.rope3d_path_entry.insert(0, settings.get('rope3d_path', ''))

        self.image_folder_entry.delete(0, tk.END)
        self.image_folder_entry.insert(0, settings.get('image_folder', ''))
        return settings
    
    def start_and_save_settings(self):
        self.rope3d_path = self.rope3d_path_entry.get()
        self.image_folder = self.image_folder_entry.get()

        # 确保路径有效
        if not all([self.rope3d_path, self.image_folder]):
            messagebox.showerror("错误", "路径不能为空")
            return

        if not os.path.exists(self.rope3d_path) or not os.path.exists(self.image_folder):
            messagebox.showerror("错误", "提供的路径无效")
            return
        
         # 加载图像文件夹中的所有图像文件
        self.load_image_files(self.image_folder)

        # 打开注释窗口
        if self.image_files:
            # 保存用户设置
            self.save_user_settings()
            # 创建必要的文件夹
            self.create_folders(self.rope3d_path)
            self.open_annotation_window()
            
        else:
            messagebox.showerror("错误", "没有找到图像文件")
            return False
        
    def browse_directory(self, entry):
        directory = filedialog.askdirectory()
        if directory:
            entry.delete(0, tk.END)
            entry.insert(0, directory)
    

    def load_image_files(self, directory):
        """加载图像文件夹中的所有图像文件到列表"""
        all_files = [os.path.join(directory, f) for f in os.listdir(directory)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        self.image_files = sorted(all_files)  # 这里添加sorted来确保排序

    def create_folders(self, rope3d_path):
        # 获取Rope3D路径的父目录
        parent_directory = os.path.dirname(rope3d_path)
        
        # 在父目录下创建必要的文件夹
        for folder_name in ["Questions", "Answers", "Labels"]:
            folder_path = os.path.join(parent_directory, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

    def open_annotation_window(self):
        if self.annotation_window is None or not self.annotation_window.winfo_exists():
            self.annotation_window = AnnotationWindow(self, self.image_folder, self.rope3d_path, self.image_files)

class AnnotationWindow(tk.Toplevel):
    def __init__(self, parent, image_folder, rope3d_path, image_files):
        super().__init__(parent)
        self.title("标注窗口")
        self.geometry("1920x1080")
        self.parent = parent
        self.image_folder = image_folder  # 存储传递的 image_folder
        self.rope3d_path = rope3d_path  # 存储传递的 rope3d_folder
        self.image_files = image_files  # 存储传递的图像文件列表
        print(f"初始化 AnnotationWindow: {len(image_files)} 张图片加载")

        self.current_index = 0  # 当前图像的索引
        
        self.image = None
        self.bboxes = []
        self.selected_bboxes = []
        self.file_name = None

        self.setup_ui()

    def setup_ui(self):
        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", pady=10)

        self.file_name_label = tk.Label(top_frame, text="输入文件名(不带后缀):")
        self.file_name_label.pack(side="left", padx=(10, 2))

        self.file_name_entry = tk.Entry(top_frame, width=70)
        self.file_name_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        self.load_button = tk.Button(top_frame, text="加载图像", command=self.load_image)
        self.load_button.pack(side="right", padx=(0, 10))
        self.browse_button = tk.Button(top_frame, text="浏览", command=self.browse_image)
        self.browse_button.pack(side="right", padx=(0, 10))

        # 如果主界面有保存的文件名，则加载它
        if self.parent:
            settings = self.parent.load_user_settings()
            last_file_name = settings.get('last_file_name', '')
            if last_file_name:  # 确保文件名不是 None 或空字符串
                self.file_name_entry.insert(0, last_file_name)
            
        # 输入问题的容器
        question_frame = tk.Frame(self)
        question_frame.pack(fill="x", pady=(5, 0))
        self.question_label = tk.Label(question_frame, text="输入问题:")
        self.question_label.pack(side="left", padx=(10, 2))
        self.question_entry = tk.Text(question_frame, height=2, width=87)
        self.question_entry.pack(side="left", fill="x", expand=True)

        # 输入答案的容器
        answer_frame = tk.Frame(self)
        answer_frame.pack(fill="x", pady=(5, 0))
        self.answer_label = tk.Label(answer_frame, text="输入答案:")
        self.answer_label.pack(side="left", padx=(10, 2))
        self.answer_entry = tk.Text(answer_frame, height=2, width=87)
        self.answer_entry.pack(side="left", fill="x", expand=True)

        self.save_button = tk.Button(self, text="保存标注", command=self.save_annotation)
        self.save_button.pack(pady=(10, 20))

        # 创建一个Frame来放置按钮
        button_frame = tk.Frame(self)
        button_frame.pack(side="top", fill="x", padx=10, pady=10)

        self.prev_button = tk.Button(button_frame, text="上一个", command=self.prev_image)
        self.prev_button.pack(side="left", padx=10)

        self.next_button = tk.Button(button_frame, text="下一个", command=self.next_image)
        self.next_button.pack(side="right", padx=10)

        self.image_canvas = tk.Canvas(self, width=1920, height=1080)
        self.image_canvas.pack(pady=(0, 20))
        self.image_canvas.bind("<Button-1>", self.select_bbox)

        # 状态标签
        self.status_label = tk.Label(self, text="", fg="green", font=("Helvetica", "15", "bold"))
        self.status_label.pack(side="bottom", fill="x")

    def browse_image(self):
        file_path = filedialog.askopenfilename(initialdir=self.image_folder,
                                            title="选择图像",
                                            filetypes=(("JPEG files", "*.jpg;*.jpeg"), ("PNG files", "*.png"), ("All files", "*.*")))
        if file_path:
            self.file_name_entry.delete(0, tk.END)
            self.file_name_entry.insert(0, os.path.splitext(os.path.basename(file_path))[0])
            self.focus_force()  # 重新获取焦点
            self.load_image()  # 如果你想加载图像，可以直接调用 load_image 方法


    #显示图片和标注的主要处理方法
    def load_image(self):
        self.selected_bboxes = []
        self.file_name = self.file_name_entry.get().strip()  # 直接从输入框获取文件名
        if not self.file_name:
            messagebox.showerror("错误", "文件名不能为空")
            return

        # 构建图像的完整路径
        image_path = os.path.join(self.image_folder, f"{self.file_name}.jpg")
        if not os.path.exists(image_path):  # 检查文件是否存在
            messagebox.showerror("错误", f"图像文件不存在: {image_path}")
            return

        # 更新当前索引
        try:
            self.current_index = self.image_files.index(image_path)
        except ValueError:
            messagebox.showerror("错误", "所选文件不在文件列表中")
            return

        # 清除画布上的所有内容
        self.image_canvas.delete("all")

        # 清除问题和答案输入框的内容
        self.question_entry.delete("1.0", tk.END)
        self.answer_entry.delete("1.0", tk.END)

        # 加载图像
        self.image = cv2.imread(image_path)
        if self.image is not None:
            self.display_image()
        else:
            messagebox.showerror("错误", "无法加载图像")
        
        # 更新设置
        self.save_current_settings()

    def save_current_settings(self):
        # 更新设置并保存到文件
        settings = {
            'rope3d_path': self.parent.rope3d_path_entry.get(),
            'image_folder': self.parent.image_folder_entry.get(),
            'last_file_name': self.file_name
        }
        save_settings(settings)

    def display_image(self):
        if self.image is not None:
            # 确保画布尺寸已更新
            self.update_idletasks()
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()

            # 转换图像色彩空间
            image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(image)

            # 保持宽高比调整图像大小
            original_width, original_height = image_pil.size
            self.scale_x = canvas_width / original_width
            self.scale_y = canvas_height / original_height

            new_width = int(original_width * self.scale_x)
            new_height = int(original_height * self.scale_y)
            image_pil = image_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 创建PhotoImage并居中显示
            self.photo_image = ImageTk.PhotoImage(image_pil)
            self.image_canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.photo_image, anchor=tk.CENTER)

            # 加载边界框
            self.load_bboxes()
            self.draw_bboxes()  # 在调整图像大小后绘制边界框
     
    def load_bboxes(self):
        bboxes = []
        self.bbox_counts = {}  # 字典用于计数每个类型的框
        label_file = os.path.join(self.parent.rope3d_path, f"{self.file_name}.txt")
        print("Attempting to load bboxes from:", label_file)
        if os.path.exists(label_file):
            with open(label_file, 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if len(parts) >= 15:  # 确保有足够的数据来构成一个完整的边界框
                        bbox_type = parts[0]
                        if bbox_type in self.bbox_counts:
                            self.bbox_counts[bbox_type] += 1
                        else:
                            self.bbox_counts[bbox_type] = 1

                        bbox_data = {
                            "type": parts[0],
                            "count": self.bbox_counts[bbox_type],  # 为每个框添加计数
                            "truncated": int(parts[1]),
                            "occluded": int(parts[2]),
                            "angle": float(parts[3]),
                            "bbox2d": [float(parts[4]), float(parts[5]), float(parts[6]), float(parts[7])],
                            "dimensions": [float(parts[8]), float(parts[9]), float(parts[10])],
                            "position": [float(parts[11]), float(parts[12]), float(parts[13])],
                            "rotation_y": float(parts[14])
                        }
                        bboxes.append(bbox_data)
                    print("已添加框", bbox_type + str(self.bbox_counts[bbox_type]))
        else:
            print("Label file does not exist:", label_file)
            messagebox.showerror("错误", "Labels文件夹中没有对应label，请检查路径设置")

        if bboxes:
            print("Loaded bboxes:")
        else:
            print("No bboxes loaded.")
        self.bboxes = bboxes  # 确保始终设置self.bboxes，即使为空列表

    def draw_bboxes(self):
        print("Attempting to draw bounding boxes...")
        if not self.bboxes:
            print("No bounding boxes to draw.")
            return

        self.image_canvas.delete("bbox")

        for bbox in self.bboxes:
            x1, y1, x2, y2 = [bbox['bbox2d'][i] * (self.scale_x if i % 2 == 0 else self.scale_y) for i in range(4)]
            bbox_text = f"{bbox['type']} {bbox['count']}"  # 修改显示文本以包含编号
            text_x = x1 + 10
            text_y = y1 + 10

            self.image_canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2, tags="bbox")
            self.image_canvas.create_text(text_x, text_y, text=bbox_text, fill="yellow", font=("Helvetica", "10", "bold"), tags="bbox")

        self.image_canvas.update()

    def select_bbox(self, event):
        x, y = event.x, event.y
        found = False
        for bbox in self.bboxes:
            x1, y1, x2, y2 = [int(bbox['bbox2d'][i] * (self.scale_x if i % 2 == 0 else self.scale_y)) for i in range(4)]
            if x1 <= x <= x2 and y1 <= y <= y2:
                if bbox in self.selected_bboxes:
                    self.selected_bboxes.remove(bbox)  # 如果已选中，则取消选择
                else:
                    self.selected_bboxes.append(bbox)  # 否则添加到选择列表中
                found = True
                break
        if found:
            self.redraw_bboxes()

    def redraw_bboxes(self):
        # 重绘边界框，并根据是否被选中改变边框颜色
        self.image_canvas.delete("bbox")
        for bbox in self.bboxes:
            x1, y1, x2, y2 = [int(bbox['bbox2d'][i] * (self.scale_x if i % 2 == 0 else self.scale_y)) for i in range(4)]
            box_color = "yellow" if bbox in self.selected_bboxes else "red"
            bbox_text = f"{bbox['type']} {bbox['count']}"
            text_x = x1 + 10
            text_y = y1 + 10
            self.image_canvas.create_rectangle(x1, y1, x2, y2, outline=box_color, width=2, tags="bbox")
            self.image_canvas.create_text(text_x, text_y, text=bbox_text, fill="yellow", font=("Helvetica", "10", "bold"), tags="bbox")

        # 显式更新画布以反映变更
        self.image_canvas.update()

    def save_annotation(self):
        if not self.file_name:
            messagebox.showerror("错误", "文件名不能为空。")
            return
        if not self.selected_bboxes:
            messagebox.showerror("错误", "没有选中任何边界框。")
            return

        question = self.question_entry.get("1.0", tk.END).strip()
        answer = self.answer_entry.get("1.0", tk.END).strip()

        if not question:
            messagebox.showerror("错误", "问题不能为空。")
            return
        if not answer:
            messagebox.showerror("错误", "答案不能为空。")
            return

        parent_directory = os.path.dirname(self.parent.rope3d_path)
        question_path = os.path.join(parent_directory, "Questions", f"{self.file_name}.txt")
        answer_path = os.path.join(parent_directory, "Answers", f"{self.file_name}.txt")

        # 确保目录存在
        os.makedirs((os.path.dirname(question_path)), exist_ok=True)
        os.makedirs((os.path.dirname(answer_path)), exist_ok=True)

        # 写入问题和答案，每次保存都覆盖旧数据
        with open(question_path, "w") as q_file:
            q_file.write(question + "\n")
        with open(answer_path, "w") as a_file:
            a_file.write(answer + "\n")

        error_occurred = False
        for bbox in self.selected_bboxes:
            try:
                self.save_single_bbox_annotation(bbox, parent_directory)
            except Exception as e:
                messagebox.showerror("保存错误", f"无法保存文件：{e}")
                error_occurred = True
                break

        if not error_occurred:
            self.status_label.config(text="标注已成功保存！")
            self.status_label.place(relx=0.5, rely=0.5, anchor="center")
            self.after(3000, self.clear_status_message)

    def clear_status_message(self):
        """清除状态消息"""
        self.status_label.config(text="")
        self.status_label.place_forget()  # 可以使用 place_forget 来隐藏标签

    def save_single_bbox_annotation(self, bbox, parent_directory):
        label_path = os.path.join(parent_directory, "Labels", f"{self.file_name}.txt")
        os.makedirs((os.path.dirname(label_path)), exist_ok=True)
        with open(label_path, "a") as l_file:  # 使用 "a" 模式追加数据
            bbox_data = [
                bbox["type"],
                bbox["truncated"],
                bbox["occluded"],
                bbox["angle"],
                *bbox["bbox2d"],
                *bbox["dimensions"],
                *bbox["position"],
                bbox["rotation_y"]
            ]
            l_file.write(" ".join(map(str, bbox_data)) + "\n")


    def prev_image(self):
        if len(self.image_files) > 0:
            self.current_index = (self.current_index - 1) % len(self.image_files)
            self.update_image_entry()
            self.load_image()
        else:
            print("错误：没有图片可切换到上一张。")

    def next_image(self):
        if len(self.image_files) > 0:
            self.current_index = (self.current_index + 1) % len(self.image_files)
            self.update_image_entry()
            self.load_image()
        else:
            print("错误：没有图片可切换到下一张。")

    def update_image_entry(self):
        """更新输入框以反映当前索引的图像文件名"""
        current_file = os.path.basename(self.image_files[self.current_index])
        current_file_name = os.path.splitext(current_file)[0]  # 去掉扩展名
        self.file_name_entry.delete(0, tk.END)
        self.file_name_entry.insert(0, current_file_name)

if __name__ == "__main__":
    app = AnnotationApp()
    app.mainloop()
