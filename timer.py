import customtkinter as ctk
import time
from datetime import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm
import platform

# --- 1. 配置 ---
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# Apple 风格色板
COLOR_APPLE_BG = "#F5F5F7"
COLOR_CARD_WHITE = "#FFFFFF"
COLOR_TEXT_PRIMARY = "#1D1D1F"
COLOR_TEXT_SECONDARY = "#86868B"
COLOR_ACCENT_BLUE = "#007AFF"
COLOR_ACCENT_RED = "#FF3B30"
COLOR_ACCENT_GOLD = "#FF9500"
COLOR_SEPARATOR = "#E5E5EA"
COLOR_TRANSPARENT_KEY = "#000001"


# 字体
FONT_TITLE = ("Microsoft YaHei UI", 24, "bold")
FONT_BOLD = ("Microsoft YaHei UI", 16, "bold")
FONT_NORMAL = ("Microsoft YaHei UI", 14)
FONT_TIMER = ("Roboto Medium", 80)
FONT_NANO_TIMER = ("Roboto Medium", 18)
FONT_NANO_USER = ("Microsoft YaHei UI", 12, "bold")


# 自动配置中文字体
def configure_matplotlib_font():
    system = platform.system()
    font_candidates = ['Microsoft YaHei', 'SimHei', 'PingFang HK', 'Heiti TC']
    for font_name in font_candidates:
        try:
            if len(fm.findfont(font_name)) > 0:
                plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
                break
        except:
            continue
    plt.rcParams['axes.unicode_minus'] = False


configure_matplotlib_font()

ADMIN_PASSWORD = "123456"
FILE_PATH = "usage_history.txt"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("公用机管理系统 Pro")
        self.geometry("960x680")
        self.minsize(800, 550)

        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.98)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar_frame = SidebarFrame(self)
        self.timer_frame = TimerFrame(self)
        self.history_frame = HistoryFrame(self)
        self.stats_frame = StatisticsFrame(self)
        self.compact_frame = CompactFrame(self)

        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.show_timer_frame()

        self._drag_data = {"x": 0, "y": 0}

    def show_timer_frame(self):
        self.hide_all_frames()
        self.timer_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.sidebar_frame.highlight("timer")

    def show_history_frame(self):
        self.hide_all_frames()
        self.history_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.history_frame.load_data()
        self.sidebar_frame.highlight("history")

    def show_stats_frame(self):
        self.hide_all_frames()
        self.stats_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.stats_frame.filter_mode.set("全部")
        self.stats_frame.animate_load("全部")
        self.sidebar_frame.highlight("stats")

    def hide_all_frames(self):
        self.timer_frame.grid_forget()
        self.history_frame.grid_forget()
        self.stats_frame.grid_forget()

    def switch_to_compact_mode(self):
        self.sidebar_frame.grid_forget()
        self.hide_all_frames()
        self.minsize(0, 0)  # 解锁尺寸
        self.overrideredirect(True)
        self.config(bg=COLOR_TRANSPARENT_KEY)
        self.wm_attributes('-transparentcolor', COLOR_TRANSPARENT_KEY)
        self.attributes('-alpha', 1.0)

        screen_width = self.winfo_screenwidth()
        self.geometry(f"200x36+{screen_width - 220}+50")

        self.compact_frame.pack(fill="both", expand=True)
        self.compact_frame.sync_state()

        for w in [self.compact_frame, self.compact_frame.lbl_mini_timer, self.compact_frame.btn_mini_stop,
                  self.compact_frame.lbl_mini_user]:
            if not isinstance(w, ctk.CTkButton):
                w.bind("<ButtonPress-1>", self.start_drag)
                w.bind("<B1-Motion>", self.do_drag)

    def switch_to_normal_mode(self):
        self.compact_frame.pack_forget()
        self.overrideredirect(False)
        self.wm_attributes('-transparentcolor', "")
        self.config(bg="#F0F0F0")
        self.geometry("960x680")
        self.minsize(800, 550)  # 恢复尺寸锁
        self.attributes('-alpha', 0.98)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.show_timer_frame()
        self.timer_frame.stop_timer()

    def start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_data["x"]
        y = self.winfo_y() + event.y - self._drag_data["y"]
        self.geometry(f"+{x}+{y}")


# --- 常规组件 ---

class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, width=180, corner_radius=0, fg_color=COLOR_APPLE_BG)
        self.master = master
        self.grid_rowconfigure(5, weight=1)
        self.logo = ctk.CTkLabel(self, text=" 使用管理", font=("Microsoft YaHei UI", 20, "bold"),
                                 text_color=COLOR_TEXT_PRIMARY)
        self.logo.grid(row=0, column=0, padx=20, pady=(40, 30))
        self.btn_timer = self.create_btn("⏱  计时打卡", master.show_timer_frame, 1)
        self.btn_history = self.create_btn("📅  历史记录", master.show_history_frame, 2)
        self.btn_stats = self.create_btn("📊  数据统计", master.show_stats_frame, 3)

    def create_btn(self, text, cmd, row):
        btn = ctk.CTkButton(self, text=text, command=cmd, font=FONT_NORMAL, anchor="w", height=45,
                            fg_color="transparent", text_color=COLOR_TEXT_SECONDARY, hover_color="#E5E5EA",
                            corner_radius=8)
        btn.grid(row=row, column=0, padx=15, pady=5, sticky="ew")
        return btn

    def highlight(self, mode):
        for btn in [self.btn_timer, self.btn_history, self.btn_stats]:
            btn.configure(fg_color="transparent", text_color=COLOR_TEXT_SECONDARY)
        bg_active = "#E3F2FD"
        if mode == "timer":
            self.btn_timer.configure(fg_color=bg_active, text_color=COLOR_ACCENT_BLUE)
        elif mode == "history":
            self.btn_history.configure(fg_color=bg_active, text_color=COLOR_ACCENT_BLUE)
        elif mode == "stats":
            self.btn_stats.configure(fg_color=bg_active, text_color=COLOR_ACCENT_BLUE)


class TimerFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_APPLE_BG, corner_radius=0, **kwargs)
        self.master = master
        self.start_timestamp = None
        self.is_running = False
        self.current_user_name = ""

        self.card = ctk.CTkFrame(self, fg_color=COLOR_CARD_WHITE, corner_radius=20, width=500, height=400)
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.grid_propagate(False)

        self.view_login = ctk.CTkFrame(self.card, fg_color="transparent")
        self.view_running = ctk.CTkFrame(self.card, fg_color="transparent")

        self.setup_login_ui()
        self.setup_running_ui()
        self.view_login.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

    def setup_login_ui(self):
        box = ctk.CTkFrame(self.view_login, fg_color="transparent")
        box.place(relx=0.5, rely=0.5, anchor="center")

        self.toast = ctk.CTkFrame(box, fg_color="#E8F5E9", corner_radius=20, height=40)
        self.lbl_toast = ctk.CTkLabel(self.toast, text="", font=("Microsoft YaHei UI", 14, "bold"),
                                      text_color="#2E7D32")
        self.lbl_toast.pack(padx=20, pady=5)

        ctk.CTkLabel(box, text="👋 欢迎使用", font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(pady=(10, 20))
        self.entry_user = ctk.CTkEntry(box, placeholder_text="在此输入姓名...", width=280, height=50,
                                       font=FONT_BOLD, fg_color=COLOR_APPLE_BG, border_width=0, text_color="black")
        self.entry_user.pack(pady=10)
        self.btn_start = ctk.CTkButton(box, text="开始使用", width=200, height=45, font=FONT_BOLD,
                                       fg_color=COLOR_ACCENT_BLUE, hover_color="#0062B8", command=self.start_sequence)
        self.btn_start.pack(pady=20)
        self.progress = ctk.CTkProgressBar(box, width=280, height=6, progress_color=COLOR_ACCENT_BLUE)

    def setup_running_ui(self):
        box = ctk.CTkFrame(self.view_running, fg_color="transparent")
        box.place(relx=0.5, rely=0.5, anchor="center")
        self.lbl_user = ctk.CTkLabel(box, text="User", font=FONT_BOLD, text_color=COLOR_ACCENT_BLUE)
        self.lbl_user.pack(pady=(0, 5))
        self.lbl_timer = ctk.CTkLabel(box, text="00:00:00", font=FONT_TIMER, text_color=COLOR_TEXT_PRIMARY)
        self.lbl_timer.pack(pady=20)
        btn_box = ctk.CTkFrame(box, fg_color="transparent")
        btn_box.pack(pady=15)
        ctk.CTkButton(btn_box, text="■ 结束", width=120, height=45, fg_color=COLOR_ACCENT_RED, hover_color="#D12F26",
                      font=FONT_BOLD, command=self.stop_timer).pack(side="left", padx=10)
        ctk.CTkButton(btn_box, text="胶囊模式", width=120, height=45, fg_color="#F2F2F7", hover_color="#E5E5EA",
                      text_color=COLOR_ACCENT_BLUE,
                      font=FONT_BOLD, command=self.master.switch_to_compact_mode).pack(side="left", padx=10)

    def start_sequence(self):
        user = self.entry_user.get().strip()
        if not user:
            self.show_toast("⚠️ 请先输入姓名", "#FFEBEE", "#C62828")
            return
        self.current_user_name = user
        self.entry_user.configure(state="disabled")
        self.btn_start.configure(state="disabled", text="正在启动...")
        self.progress.pack(pady=10)
        self.loading_val = 0
        self.animate()

    def animate(self):
        if self.loading_val < 1.05:
            self.loading_val += 0.05
            self.progress.set(self.loading_val)
            self.after(20, self.animate)
        else:
            self.view_login.place_forget()
            self.lbl_user.configure(text=f"👤 {self.current_user_name}")
            self.is_running = True
            self.start_timestamp = datetime.now()
            self.start_counter = time.time()
            self.update_timer()
            self.view_running.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

    def update_timer(self):
        if self.is_running:
            now = time.time()
            elapsed = int(now - self.start_counter)
            h, r = divmod(elapsed, 3600)
            m, s = divmod(r, 60)
            time_str = f"{h:02}:{m:02}:{s:02}"
            self.lbl_timer.configure(text=time_str)
            if hasattr(self.master, 'compact_frame'):
                self.master.compact_frame.lbl_mini_timer.configure(text=time_str)
            self.after(1000, self.update_timer)

    def stop_timer(self):
        if self.is_running:
            self.is_running = False
            self.save_log()
            self.view_running.place_forget()
            self.reset_login()
            self.view_login.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
            self.show_toast("✅ 记录已保存", "#E8F5E9", "#2E7D32")

    def save_log(self):
        end_dt = datetime.now()
        sec = int((end_dt - self.start_timestamp).total_seconds())
        h, r = divmod(sec, 3600)
        m, s = divmod(r, 60)
        dur = f"{h:02}小时{m:02}分{s:02}秒"
        line = f"{self.current_user_name}|{self.start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}|{end_dt.strftime('%Y-%m-%d %H:%M:%S')}|{dur}\n"
        with open(FILE_PATH, "a", encoding="utf-8") as f: f.write(line)

    def reset_login(self):
        self.entry_user.configure(state="normal")
        self.entry_user.delete(0, "end")
        self.btn_start.configure(state="normal", text="开始使用")
        self.progress.pack_forget()
        self.progress.set(0)

    def show_toast(self, msg, bg, fg):
        self.lbl_toast.configure(text=msg, text_color=fg)
        self.toast.configure(fg_color=bg)
        self.toast.pack(side="top", pady=(10, 0), before=self.entry_user)
        self.after(3000, lambda: self.toast.pack_forget())


class CompactFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_CARD_WHITE, bg_color=COLOR_TRANSPARENT_KEY, corner_radius=18, **kwargs)
        self.master = master
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.lbl_mini_user = ctk.CTkLabel(self, text="User", font=FONT_NANO_USER, text_color=COLOR_ACCENT_BLUE)
        self.lbl_mini_user.grid(row=0, column=0, padx=(15, 5), sticky="w")

        self.lbl_mini_timer = ctk.CTkLabel(self, text="00:00:00", font=FONT_NANO_TIMER, text_color=COLOR_TEXT_PRIMARY)
        self.lbl_mini_timer.grid(row=0, column=1, padx=5, sticky="w")

        self.btn_mini_stop = ctk.CTkButton(self, text="■", width=22, height=22, corner_radius=11,
                                           fg_color=COLOR_ACCENT_RED, hover_color="#D12F26", font=("Arial", 8),
                                           command=self.master.switch_to_normal_mode)
        self.btn_mini_stop.grid(row=0, column=2, padx=(5, 8), sticky="e")

    def sync_state(self):
        user = self.master.timer_frame.current_user_name
        disp = user if len(user) < 5 else user[:4] + ".."
        self.lbl_mini_user.configure(text=disp)


class StatisticsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_APPLE_BG, corner_radius=0, **kwargs)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=30, pady=(30, 10))
        ctk.CTkLabel(top_bar, text="使用统计", font=("Microsoft YaHei UI", 22, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(side="left")

        self.filter_mode = ctk.StringVar(value="全部")
        self.seg_button = ctk.CTkSegmentedButton(top_bar, values=["今日", "本月", "全部"],
                                                 command=lambda m: self.animate_load(m),
                                                 variable=self.filter_mode,
                                                 font=("Microsoft YaHei UI", 12, "bold"),
                                                 selected_color=COLOR_CARD_WHITE, text_color=COLOR_TEXT_PRIMARY)
        self.seg_button.pack(side="right")

        self.chart_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_WHITE, corner_radius=15, height=280)
        self.chart_card.grid(row=1, column=0, sticky="ew", padx=30, pady=10)
        self.chart_card.grid_propagate(False)
        self.init_chart()

        self.table_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_WHITE, corner_radius=15)
        self.table_card.grid(row=2, column=0, sticky="nsew", padx=30, pady=(10, 30))

        header_frame = ctk.CTkFrame(self.table_card, fg_color="transparent", height=40)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))

        self.col_weights = [10, 30, 20, 30]
        for i, w in enumerate(self.col_weights): header_frame.grid_columnconfigure(i, weight=w, uniform="cols")
        header_frame.grid_columnconfigure(4, weight=0, minsize=15)

        self.create_header(header_frame, "排名", 0)
        self.create_header(header_frame, "用户姓名", 1)
        self.create_header(header_frame, "统计时长", 2)
        self.create_header(header_frame, "最后使用时间", 3)

        ctk.CTkFrame(self.table_card, fg_color=COLOR_SEPARATOR, height=1).pack(fill="x", padx=20, pady=5)

        self.scroll = ctk.CTkScrollableFrame(self.table_card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def create_header(self, parent, text, col_idx):
        lbl = ctk.CTkLabel(parent, text=text, font=("Microsoft YaHei UI", 12, "bold"), text_color=COLOR_TEXT_SECONDARY)
        lbl.grid(row=0, column=col_idx, sticky="ew")

    def init_chart(self):
        self.fig = plt.Figure(figsize=(6, 3), dpi=100, facecolor='white')
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        self.ax.set_facecolor('white')
        for spine in self.ax.spines.values(): spine.set_visible(False)
        self.ax.tick_params(left=False, bottom=False)
        self.fig.subplots_adjust(left=0.15, bottom=0.2, right=0.95, top=0.85)

    def animate_load(self, mode):
        sorted_users = self.get_data(mode)
        for w in self.scroll.winfo_children(): w.destroy()
        if not sorted_users:
            self.ax.clear()
            self.canvas.draw()
            return

        max_val = 0
        if sorted_users: max_val = sorted_users[0][1]['seconds'] / 3600

        for rank, (name, data) in enumerate(sorted_users, 1):
            self.create_table_row(rank, name, data['seconds'], data['last_seen'])

        names = [u[0] for u in sorted_users[:5]][::-1]
        self.final_values = [u[1]['seconds'] / 3600 for u in sorted_users[:5]][::-1]

        self.animation_frame = 0
        self.total_frames = 20
        self.current_names = names
        self.mode_title = mode
        self.chart_max_xlim = max_val * 1.15 if max_val > 0 else 1

        self.update_chart_animation()

    def update_chart_animation(self):
        if self.animation_frame > self.total_frames: return
        progress = self.animation_frame / self.total_frames
        ease_progress = 1 - (1 - progress) * (1 - progress)
        current_values = [v * ease_progress for v in self.final_values]

        self.ax.clear()
        for spine in self.ax.spines.values(): spine.set_visible(False)
        self.ax.grid(axis='x', linestyle='-', alpha=0.3, color='#E5E5EA')
        self.ax.set_axisbelow(True)
        self.ax.tick_params(axis='y', length=0, labelsize=11, labelcolor=COLOR_TEXT_PRIMARY)
        self.ax.tick_params(axis='x', colors=COLOR_TEXT_SECONDARY, labelsize=9)
        self.ax.set_title(f"Top 5 活跃用户 ({self.mode_title})", loc='left',
                          fontdict={'size': 14, 'weight': 'bold', 'color': COLOR_TEXT_PRIMARY}, pad=15)
        self.ax.set_xlabel("总使用时长 (小时)", fontdict={'size': 10, 'color': COLOR_TEXT_SECONDARY})
        self.ax.set_xlim(0, self.chart_max_xlim)

        self.ax.barh(self.current_names, current_values, color=COLOR_ACCENT_BLUE, height=0.6, alpha=0.9)
        self.canvas.draw()
        self.animation_frame += 1
        self.after(20, self.update_chart_animation)

    def get_data(self, mode):
        if not os.path.exists(FILE_PATH): return []
        user_stats = {}
        now = datetime.now()
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                if "|" not in line: continue
                parts = line.strip().split("|")
                if len(parts) < 4: continue
                name, start_str, end_str, dur_str = parts
                try:
                    record_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                except:
                    continue
                match = False
                if mode == "今日":
                    if record_dt.date() == now.date(): match = True
                elif mode == "本月":
                    if record_dt.month == now.month and record_dt.year == now.year: match = True
                else:
                    match = True
                if not match: continue
                h, m, s = 0, 0, 0
                temp = dur_str
                if "小时" in temp: h, temp = int(temp.split("小时")[0]), temp.split("小时")[1]
                if "分" in temp: m, temp = int(temp.split("分")[0]), temp.split("分")[1]
                if "秒" in temp: s = int(temp.split("秒")[0])
                total_sec = h * 3600 + m * 60 + s
                if name not in user_stats: user_stats[name] = {'seconds': 0, 'last_seen': ""}
                user_stats[name]['seconds'] += total_sec
                user_stats[name]['last_seen'] = end_str
        except Exception as e:
            print(e)
        return sorted(user_stats.items(), key=lambda item: item[1]['seconds'], reverse=True)

    def create_table_row(self, rank, name, seconds, last_seen):
        row = ctk.CTkFrame(self.scroll, fg_color="transparent", height=35)
        row.pack(fill="x", pady=2)
        for i, w in enumerate(self.col_weights):
            row.grid_columnconfigure(i, weight=w, uniform="cols")
        h, r = divmod(seconds, 3600)
        m, s = divmod(r, 60)
        dur_text = f"{h}h {m}m"
        rank_color = COLOR_TEXT_PRIMARY
        rank_font = ("Arial", 12)
        if rank == 1:
            rank_color, rank_font = COLOR_ACCENT_GOLD, ("Arial", 13, "bold")
        elif rank == 2:
            rank_color = "#999999"
        elif rank == 3:
            rank_color = "#CD7F32"

        display_name = name if len(name) < 10 else name[:9] + "..."
        ctk.CTkLabel(row, text=str(rank), text_color=rank_color, font=rank_font).grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(row, text=display_name, text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(row, text=dur_text, text_color=COLOR_ACCENT_BLUE, font=("Arial", 12, "bold")).grid(row=0, column=2,
                                                                                                        sticky="ew")
        date_display = last_seen[5:-3] if len(last_seen) > 10 else last_seen
        ctk.CTkLabel(row, text=date_display, text_color=COLOR_TEXT_SECONDARY, font=("Arial", 11)).grid(row=0, column=3,
                                                                                                       sticky="ew")


# --- 🌟 核心升级：增强版历史记录 ---
class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_APPLE_BG, corner_radius=0, **kwargs)
        self.is_edit_mode = False
        self.check_vars = []  # 存储所有checkbox变量
        self.row_references = []  # 存储 (original_index, checkbox_var) 元组

        self.card = ctk.CTkFrame(self, fg_color=COLOR_CARD_WHITE, corner_radius=15)
        self.card.pack(fill="both", expand=True, padx=30, pady=30)

        # 顶部栏容器
        self.top_bar = ctk.CTkFrame(self.card, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=20, pady=20)

        # 1. 正常模式顶部
        self.normal_top = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        self.normal_top.pack(fill="x")
        ctk.CTkLabel(self.normal_top, text="历史记录", font=("Microsoft YaHei UI", 18, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(self.normal_top, text="✏️ 编辑", width=80, command=self.request_edit_mode,
                      fg_color=COLOR_APPLE_BG, text_color=COLOR_TEXT_PRIMARY, hover_color="#E5E5EA").pack(side="right",
                                                                                                          padx=(10, 0))
        ctk.CTkButton(self.normal_top, text="刷新", width=80, command=self.load_data,
                      fg_color=COLOR_APPLE_BG, text_color=COLOR_TEXT_PRIMARY, hover_color="#E5E5EA").pack(side="right")

        # 2. 编辑模式顶部 (初始隐藏)
        self.edit_top = ctk.CTkFrame(self.top_bar, fg_color="transparent")

        # 筛选框
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.filter_data)  # 实时搜索
        self.entry_search = ctk.CTkEntry(self.edit_top, placeholder_text="🔍 筛选姓名...", textvariable=self.search_var,
                                         width=200)
        self.entry_search.pack(side="left")

        ctk.CTkButton(self.edit_top, text="完成", width=80, command=self.exit_edit_mode,
                      fg_color=COLOR_ACCENT_BLUE, hover_color="#0062B8").pack(side="right")
        ctk.CTkButton(self.edit_top, text="全选", width=80, command=self.toggle_select_all,
                      fg_color=COLOR_APPLE_BG, text_color=COLOR_TEXT_PRIMARY, hover_color="#E5E5EA").pack(side="right",
                                                                                                          padx=10)

        # 列表区域
        self.scroll = ctk.CTkScrollableFrame(self.card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        # 底部批量操作栏 (仅编辑模式显示)
        self.bottom_bar = ctk.CTkFrame(self.card, fg_color="transparent")
        self.btn_delete_bulk = ctk.CTkButton(self.bottom_bar, text="删除选中记录", fg_color=COLOR_ACCENT_RED,
                                             hover_color="#D12F26", command=self.delete_bulk)
        self.btn_delete_bulk.pack(pady=10)

    def request_edit_mode(self):
        dialog = ctk.CTkInputDialog(text="请输入管理员密码:", title="权限验证")
        pwd = dialog.get_input()
        if pwd == ADMIN_PASSWORD:
            self.enter_edit_mode()
        elif pwd is not None:
            self.master.timer_frame.show_toast("🚫 密码错误", "#FFEBEE", "#C62828")

    def enter_edit_mode(self):
        self.is_edit_mode = True
        self.normal_top.pack_forget()
        self.edit_top.pack(fill="x")
        self.bottom_bar.pack(fill="x", side="bottom")
        self.search_var.set("")  # 清空搜索
        self.load_data()

    def exit_edit_mode(self):
        self.is_edit_mode = False
        self.edit_top.pack_forget()
        self.bottom_bar.pack_forget()
        self.normal_top.pack(fill="x")
        self.load_data()

    def filter_data(self, *args):
        self.load_data(filter_text=self.search_var.get())

    def toggle_select_all(self):
        # 检查当前是否全部选中
        all_checked = all(var.get() == 1 for _, var in self.row_references)
        new_state = 0 if all_checked else 1
        for _, var in self.row_references:
            var.set(new_state)

    def delete_bulk(self):
        # 获取要删除的原始行索引
        indices_to_delete = [idx for idx, var in self.row_references if var.get() == 1]

        if not indices_to_delete:
            self.master.timer_frame.show_toast("⚠️ 未选中任何记录", "#FFF3E0", "#E65100")
            return

        # 执行删除 (先读取所有，再剔除)
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 使用 set 提高查找效率
            delete_set = set(indices_to_delete)
            new_lines = [line for i, line in enumerate(lines) if i not in delete_set]

            with open(FILE_PATH, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            self.master.timer_frame.show_toast(f"✅ 已删除 {len(indices_to_delete)} 条记录", "#E8F5E9", "#2E7D32")
            self.load_data(filter_text=self.search_var.get())  # 保持当前筛选状态刷新

        except Exception as e:
            print(f"Delete error: {e}")

    def load_data(self, filter_text=""):
        # 清空 UI 和 引用缓存
        for w in self.scroll.winfo_children(): w.destroy()
        self.row_references.clear()

        if not os.path.exists(FILE_PATH):
            ctk.CTkLabel(self.scroll, text="暂无记录", text_color="gray").pack(pady=50)
            return

        with open(FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 倒序遍历显示，但保留原始 index 用于删除
        # enumerate 返回 (0, line0), (1, line1)...
        all_records = list(enumerate(lines))

        for original_index, line in reversed(all_records):
            if "|" not in line: continue
            parts = line.strip().split("|")
            if len(parts) >= 4:
                user_name = parts[0]
                # 筛选逻辑：如果不匹配，跳过
                if filter_text and filter_text.lower() not in user_name.lower():
                    continue

                self.create_row(user_name, parts[1], parts[2], parts[3], original_index)

    def create_row(self, user, start, end, dur, index):
        card = ctk.CTkFrame(self.scroll, fg_color=COLOR_APPLE_BG, corner_radius=10)
        card.pack(fill="x", pady=4, padx=5)

        # 左侧容器
        left_box = ctk.CTkFrame(card, fg_color="transparent")
        left_box.pack(side="left", padx=10, pady=8)

        # 编辑模式：显示复选框
        if self.is_edit_mode:
            check_var = ctk.IntVar()
            checkbox = ctk.CTkCheckBox(left_box, text="", variable=check_var, width=24, checkbox_width=20,
                                       checkbox_height=20)
            checkbox.pack(side="left", padx=(0, 10))
            # 存入引用列表
            self.row_references.append((index, check_var))

        # 信息显示
        info_box = ctk.CTkFrame(left_box, fg_color="transparent")
        info_box.pack(side="left")
        ctk.CTkLabel(info_box, text=f"{user}", font=("Microsoft YaHei UI", 14, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(info_box, text=f"{start[5:-3]} ➜ {end[5:-3]}", font=("Arial", 12),
                     text_color=COLOR_TEXT_SECONDARY).pack(anchor="w")

        # 右侧容器
        right_box = ctk.CTkFrame(card, fg_color="transparent")
        right_box.pack(side="right", padx=10)
        ctk.CTkLabel(right_box, text=f"⏱ {dur}", font=("Arial", 12, "bold"), text_color=COLOR_ACCENT_BLUE).pack(
            side="right", padx=(0, 10))

        # 正常模式：显示单条删除按钮
        if not self.is_edit_mode:
            ctk.CTkButton(right_box, text="×", width=30, height=30, fg_color="#FFE5E5", text_color="#FF3B30",
                          hover_color="#FFD1D1",
                          command=lambda: self.ask_delete_single(index)).pack(side="right")

    def ask_delete_single(self, index):
        dialog = ctk.CTkInputDialog(text="管理员密码:", title="验证")
        pwd = dialog.get_input()
        if pwd == ADMIN_PASSWORD:
            # 单条删除复用批量删除逻辑，只是列表里只有一个
            try:
                with open(FILE_PATH, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                del lines[index]
                with open(FILE_PATH, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                self.load_data()
            except:
                pass


if __name__ == "__main__":
    app = App()
    app.mainloop()