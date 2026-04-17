import ast
import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class PyPackagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 打包工具")
        self.root.geometry("650x580")  # 稍微加大窗口以适应新控件

        # 变量定义
        default_spec = os.path.join(os.getcwd(), "server.spec")
        self.spec_path = tk.StringVar(value=default_spec if os.path.exists(default_spec) else "")
        self.script_path = tk.StringVar()
        self.icon_path = tk.StringVar()
        self.output_dir = tk.StringVar(value="dist")
        self.app_name = tk.StringVar()
        self.onefile = tk.BooleanVar(value=True)
        self.noconsole = tk.BooleanVar(value=True)  # 新增：控制是否显示控制台窗口，默认不显示
        self.hidden_imports = tk.StringVar()
        self.exclude_modules = tk.StringVar()
        self.additional_data = tk.StringVar()
        self.semi_include = tk.BooleanVar(value=True)
        self.architecture = tk.StringVar(value="64bit")  # 默认64位

        self.create_widgets()

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 脚本选择
        ttk.Label(main_frame, text="Python脚本:").grid(row=0, column=0, sticky=tk.W, pady=2)
        script_frame = ttk.Frame(main_frame)
        script_frame.grid(row=0, column=1, sticky=tk.EW, pady=2)
        ttk.Entry(script_frame, textvariable=self.script_path, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(script_frame, text="浏览...", command=self.browse_script).pack(side=tk.LEFT, padx=5)

        # spec文件选择与读取
        ttk.Label(main_frame, text="Spec文件:").grid(row=1, column=0, sticky=tk.W, pady=2)
        spec_frame = ttk.Frame(main_frame)
        spec_frame.grid(row=1, column=1, sticky=tk.EW, pady=2)
        ttk.Entry(spec_frame, textvariable=self.spec_path, width=32).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(spec_frame, text="浏览...", command=self.browse_spec).pack(side=tk.LEFT, padx=3)
        ttk.Button(spec_frame, text="读取配置", command=self.load_spec_file).pack(side=tk.LEFT, padx=3)

        # 图标选择
        ttk.Label(main_frame, text="图标文件(.ico):").grid(row=2, column=0, sticky=tk.W, pady=2)
        icon_frame = ttk.Frame(main_frame)
        icon_frame.grid(row=2, column=1, sticky=tk.EW, pady=2)
        ttk.Entry(icon_frame, textvariable=self.icon_path, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(icon_frame, text="浏览...", command=self.browse_icon).pack(side=tk.LEFT, padx=5)

        # 输出目录
        ttk.Label(main_frame, text="输出目录:").grid(row=3, column=0, sticky=tk.W, pady=2)
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=3, column=1, sticky=tk.EW, pady=2)
        ttk.Entry(output_frame, textvariable=self.output_dir, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="浏览...", command=self.browse_output).pack(side=tk.LEFT, padx=5)

        # 应用名称
        ttk.Label(main_frame, text="应用名称:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.app_name).grid(row=4, column=1, sticky=tk.EW, pady=2)

        # 打包方式
        ttk.Label(main_frame, text="打包方式:").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Radiobutton(main_frame, text="单个可执行文件", variable=self.onefile, value=True).grid(row=5, column=1,
                                                                                                   sticky=tk.W)
        ttk.Radiobutton(main_frame, text="目录形式", variable=self.onefile, value=False).grid(row=6, column=1,
                                                                                              sticky=tk.W)

        # 新增：控制台窗口选项
        ttk.Label(main_frame, text="窗口选项:").grid(row=7, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(main_frame, text="无控制台 (窗口化应用)", variable=self.noconsole).grid(row=7, column=1,
                                                                                                sticky=tk.W)

        # 架构选择
        ttk.Label(main_frame, text="程序架构:").grid(row=8, column=0, sticky=tk.W, pady=2)
        arch_frame = ttk.Frame(main_frame)
        arch_frame.grid(row=8, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(arch_frame, text="64位", variable=self.architecture, value="64bit").pack(side=tk.LEFT)
        ttk.Radiobutton(arch_frame, text="32位", variable=self.architecture, value="32bit").pack(side=tk.LEFT, padx=10)

        # 包含模式
        ttk.Label(main_frame, text="包含模式:").grid(row=9, column=0, sticky=tk.W, pady=2)
        ttk.Radiobutton(main_frame, text="半包含(排除大型库)", variable=self.semi_include, value=True).grid(row=9,
                                                                                                            column=1,
                                                                                                            sticky=tk.W)
        ttk.Radiobutton(main_frame, text="完全包含所有依赖", variable=self.semi_include, value=False).grid(row=10,
                                                                                                           column=1,
                                                                                                           sticky=tk.W)

        # 高级选项
        advanced_frame = ttk.LabelFrame(main_frame, text="高级选项", padding=(10, 5))
        advanced_frame.grid(row=11, column=0, columnspan=2, sticky=tk.EW, pady=10)

        ttk.Label(advanced_frame, text="隐藏导入:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(advanced_frame, textvariable=self.hidden_imports, width=40).grid(row=0, column=1, sticky=tk.EW,
                                                                                   pady=2)

        ttk.Label(advanced_frame, text="排除模块:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(advanced_frame, textvariable=self.exclude_modules, width=40).grid(row=1, column=1, sticky=tk.EW,
                                                                                    pady=2)

        ttk.Label(advanced_frame, text="额外数据文件:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(advanced_frame, textvariable=self.additional_data, width=40).grid(row=2, column=1, sticky=tk.EW,
                                                                                    pady=2)
        ttk.Label(advanced_frame, text="格式: 源路径:目标路径;多个用分号分隔", foreground="gray").grid(row=3, column=1,
                                                                                                       sticky=tk.W)

        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=12, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="开始打包", command=self.package).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT, padx=5)

        # 日志输出
        ttk.Label(main_frame, text="日志输出:").grid(row=13, column=0, sticky=tk.W, pady=2)
        self.log_text = tk.Text(main_frame, height=8, state=tk.DISABLED)
        self.log_text.grid(row=14, column=0, columnspan=2, sticky=tk.EW)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=14, column=2, sticky=tk.NS)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(14, weight=1)

    def browse_script(self):
        path = filedialog.askopenfilename(
            title="选择Python脚本",
            filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")]
        )
        if path:
            self.script_path.set(path)
            if not self.app_name.get():
                self.app_name.set(os.path.splitext(os.path.basename(path))[0])

    def browse_icon(self):
        path = filedialog.askopenfilename(
            title="选择图标文件",
            filetypes=[("图标文件", "*.ico"), ("所有文件", "*.*")]
        )
        if path:
            self.icon_path.set(path)

    def browse_output(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir.set(path)

    def browse_spec(self):
        path = filedialog.askopenfilename(
            title="选择spec文件",
            filetypes=[("PyInstaller spec", "*.spec"), ("所有文件", "*.*")]
        )
        if path:
            self.spec_path.set(path)

    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.root.update()

    def load_spec_file(self):
        path = self.spec_path.get()
        if not path:
            messagebox.showerror("错误", "请先选择spec文件!")
            return

        if not os.path.isfile(path):
            messagebox.showerror("错误", "指定的spec文件不存在!")
            return

        try:
            spec_info = self.parse_spec_file(path)
        except Exception as e:
            self.log(f"读取spec失败: {e}")
            messagebox.showerror("错误", f"读取spec失败: {e}")
            return

        if spec_info.get("script"):
            self.script_path.set(spec_info["script"])
            if not self.app_name.get():
                self.app_name.set(os.path.splitext(os.path.basename(spec_info["script"]))[0])

        if spec_info.get("icon"):
            self.icon_path.set(spec_info["icon"])

        if spec_info.get("name"):
            self.app_name.set(spec_info["name"])

        hiddenimports = spec_info.get("hiddenimports")
        if hiddenimports is not None:
            self.hidden_imports.set(",".join(hiddenimports))

        excludes = spec_info.get("excludes")
        if excludes is not None:
            self.exclude_modules.set(",".join(excludes))
            default_excludes = {"numpy", "pandas", "matplotlib", "scipy", "sklearn", "tensorflow", "torch"}
            if default_excludes.issubset(set(excludes)):
                self.semi_include.set(True)
            else:
                self.semi_include.set(False)

        datas = spec_info.get("datas")
        if datas is not None:
            formatted_datas = ";".join(f"{src}:{dest}" for src, dest in datas)
            self.additional_data.set(formatted_datas)

        if spec_info.get("console") is not None:
            self.noconsole.set(not spec_info["console"])

        if spec_info.get("onefile") is not None:
            self.onefile.set(spec_info["onefile"])

        if spec_info.get("target_arch"):
            if spec_info["target_arch"] in ("32bit", "64bit"):
                self.architecture.set(spec_info["target_arch"])

        self.log(f"已读取spec文件并填充: {os.path.basename(path)}")

    def package(self):
        if not self.script_path.get():
            messagebox.showerror("错误", "请先选择要打包的Python脚本!")
            return

        try:
            # 检查PyInstaller是否安装
            try:
                import pyinstaller
            except ImportError:
                self.log("PyInstaller未安装，正在自动安装...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
                self.log("PyInstaller安装完成")

            # 准备打包命令
            cmd = ["pyinstaller"]

            if self.onefile.get():
                cmd.append("--onefile")
            else:
                cmd.append("--onedir")

            # 新增：根据复选框状态添加 --noconsole 参数
            if self.noconsole.get():
                cmd.append("--noconsole")

            if self.icon_path.get():
                cmd.extend(["--icon", self.icon_path.get()])

            if self.app_name.get():
                cmd.extend(["--name", self.app_name.get()])

            # 添加架构选择
            if self.architecture.get() == "32bit":
                if sys.platform == "win32":
                    # Windows系统下指定32位Python路径
                    python_32bit = self.find_32bit_python()
                    if python_32bit:
                        cmd.insert(0, python_32bit)
                        self.log(f"使用32位Python: {python_32bit}")
                    else:
                        messagebox.showwarning("警告", "未找到32位Python，将使用当前Python环境")
                else:
                    messagebox.showwarning("警告", "非Windows系统下32位打包可能无效")

            if self.hidden_imports.get():
                for imp in self.hidden_imports.get().split(','):
                    if imp.strip():
                        cmd.extend(["--hidden-import", imp.strip()])

            if self.exclude_modules.get():
                for mod in self.exclude_modules.get().split(','):
                    if mod.strip():
                        cmd.extend(["--exclude-module", mod.strip()])

            if self.additional_data.get():
                for item in self.additional_data.get().split(';'):
                    if item.strip():
                        src_dest = item.split(':', 1)
                        if len(src_dest) == 2:
                            cmd.extend(["--add-data", f"{src_dest[0].strip()}{os.pathsep}{src_dest[1].strip()}"])

            if self.semi_include.get():
                # 半包含模式 - 不打包某些大型库
                cmd.extend(["--exclude-module", "numpy"])
                cmd.extend(["--exclude-module", "pandas"])
                cmd.extend(["--exclude-module", "matplotlib"])
                cmd.extend(["--exclude-module", "scipy"])
                cmd.extend(["--exclude-module", "sklearn"])
                cmd.extend(["--exclude-module", "tensorflow"])
                cmd.extend(["--exclude-module", "torch"])

            cmd.append("--clean")
            cmd.append(self.script_path.get())

            self.log("开始打包...")
            self.log(f"目标架构: {self.architecture.get()}")
            self.log("执行命令: " + " ".join(cmd))

            # 执行打包
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                encoding='utf-8'  # 增加编码防止乱码
            )

            # 实时输出日志
            for line in process.stdout:
                self.log(line.strip())

            process.wait()

            if process.returncode == 0:
                self.log("打包成功完成!")
                messagebox.showinfo("完成", "打包成功完成!")
            else:
                self.log("打包失败!")
                messagebox.showerror("错误", "打包过程中出现错误!")

        except Exception as e:
            self.log(f"发生错误: {str(e)}")
            messagebox.showerror("错误", f"打包失败: {str(e)}")

    def find_32bit_python(self):
        """尝试查找32位Python解释器"""
        # 检查当前Python是否是32位
        if sys.maxsize <= 2 ** 32:
            self.log("当前Python已经是32位")
            return None

        possible_paths = [
            r"F:\python\python27\python.exe",  # Python 3.6
            r"F:\python\python37\python.exe",  # Python 3.7
            r"F:\python\python311\python.exe",  # Python 3.11
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Python38-32", "python.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python38-32", "python.exe")
        ]

        for path in possible_paths:
            if os.path.exists(path):
                # 验证是否是32位Python
                try:
                    output = subprocess.check_output([path, "-c", "import sys; print(sys.maxsize <= 2**32)"])
                    if output.decode().strip() == "True":
                        return path
                except:
                    continue

        return None

    def parse_spec_file(self, path):
        """读取spec文件并提取常用配置，避免重复输入"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=path)

        spec_info = {
            "script": None,
            "icon": None,
            "datas": [],
            "hiddenimports": [],
            "excludes": [],
            "name": None,
            "console": None,
            "target_arch": None,
            "onefile": None
        }

        collect_seen = False
        exclude_binaries_flag = None

        def literal_or_none(node):
            try:
                return ast.literal_eval(node)
            except Exception:
                return None

        def call_name(call_node):
            if isinstance(call_node, ast.Call):
                func = call_node.func
                if isinstance(func, ast.Name):
                    return func.id
                if isinstance(func, ast.Attribute):
                    return func.attr
            return ""

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                func_name = call_name(node.value)

                if func_name == "Analysis":
                    if node.value.args:
                        scripts_value = literal_or_none(node.value.args[0])
                        if isinstance(scripts_value, list) and scripts_value:
                            spec_info["script"] = scripts_value[0]
                        elif isinstance(scripts_value, str):
                            spec_info["script"] = scripts_value

                    for kw in node.value.keywords:
                        value = literal_or_none(kw.value)
                        if kw.arg == "datas" and isinstance(value, (list, tuple)):
                            parsed_datas = []
                            for item in value:
                                if isinstance(item, (list, tuple)) and len(item) >= 2:
                                    parsed_datas.append((item[0], item[1]))
                            spec_info["datas"] = parsed_datas
                        elif kw.arg == "hiddenimports" and isinstance(value, (list, tuple)):
                            spec_info["hiddenimports"] = list(value)
                        elif kw.arg == "excludes" and isinstance(value, (list, tuple)):
                            spec_info["excludes"] = list(value)

                elif func_name == "EXE":
                    for kw in node.value.keywords:
                        value = literal_or_none(kw.value)
                        if kw.arg == "name" and isinstance(value, str):
                            spec_info["name"] = value
                        elif kw.arg == "console":
                            spec_info["console"] = bool(value)
                        elif kw.arg == "icon":
                            if isinstance(value, (list, tuple)):
                                spec_info["icon"] = value[0] if value else None
                            elif isinstance(value, str):
                                spec_info["icon"] = value
                        elif kw.arg == "target_arch" and isinstance(value, str):
                            spec_info["target_arch"] = value
                        elif kw.arg == "exclude_binaries":
                            exclude_binaries_flag = bool(value)

                elif func_name == "COLLECT":
                    collect_seen = True

        if exclude_binaries_flag is True:
            spec_info["onefile"] = True
        elif exclude_binaries_flag is False and collect_seen:
            spec_info["onefile"] = False

        return spec_info


def main():
    root = tk.Tk()
    app = PyPackagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
