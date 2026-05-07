"""
Statistics frame — displays usage charts (bar, heatmap, trend, pie).
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from app.presentation.desktop.theme import (
    COLOR_APPLE_BG, COLOR_CARD_WHITE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT_BLUE
)
from charts import chart_drawer


class StatisticsFrame(ctk.CTkFrame):
    """统计界面 — 集成多种图表"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_APPLE_BG, corner_radius=0, **kwargs)
        self.master = master

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=30, pady=(30, 10))
        ctk.CTkLabel(top_bar, text="使用统计", font=("Microsoft YaHei UI", 22, "bold"),
                     text_color=COLOR_TEXT_PRIMARY).pack(side="left")

        self.chart_type = ctk.StringVar(value="柱状图")
        chart_seg = ctk.CTkSegmentedButton(
            top_bar, values=["柱状图", "热力图", "趋势图", "饼图"],
            variable=self.chart_type, command=self.on_chart_change,
            font=("Microsoft YaHei UI", 11)
        )
        chart_seg.pack(side="right")

        self.chart_card = ctk.CTkFrame(self, fg_color=COLOR_CARD_WHITE, corner_radius=15, height=350)
        self.chart_card.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        self.chart_card.grid_propagate(False)

        self.init_chart()

    def init_chart(self):
        self.fig = plt.Figure(figsize=(8, 4), dpi=100, facecolor='white')
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        self.ax.set_facecolor('white')
        for spine in self.ax.spines.values():
            spine.set_visible(False)

    def on_chart_change(self, chart_type):
        self.load_data()

    def load_data(self):
        chart_type = self.chart_type.get()
        stats = self.master.svc.statistics

        if chart_type == "柱状图":
            self.draw_bar_chart()
        elif chart_type == "热力图":
            data = stats.get_hourly_stats()
            chart_drawer.draw_heatmap(self.ax, data, days=30)
        elif chart_type == "趋势图":
            data = stats.get_daily_stats(30)
            chart_drawer.draw_trend(self.ax, data, days=30)
        elif chart_type == "饼图":
            data = stats.get_user_distribution("all")
            chart_drawer.draw_pie(self.ax, data, "all")

        self.canvas.draw()

    def draw_bar_chart(self):
        """绘制原有的柱状图"""
        self.ax.clear()
        for spine in self.ax.spines.values():
            spine.set_visible(False)

        data = self.master.svc.statistics.get_user_stats("all")

        if not data:
            self.ax.text(0.5, 0.5, "暂无数据", ha='center', va='center',
                        fontsize=14, color=COLOR_TEXT_SECONDARY, transform=self.ax.transAxes)
            return

        top_users = data[:5]
        names = [u['user_name'] for u in top_users][::-1]
        values = [u['total_seconds'] / 3600 for u in top_users][::-1]

        user_count = len(names)
        if user_count <= 1:
            bar_height = 0.3
        elif user_count <= 2:
            bar_height = 0.4
        elif user_count <= 3:
            bar_height = 0.5
        else:
            bar_height = 0.6

        y_positions = list(range(len(names)))
        self.ax.barh(y_positions, values, color=COLOR_ACCENT_BLUE, height=bar_height, alpha=0.9)
        self.ax.set_yticks(y_positions)
        self.ax.set_yticklabels(names)
        self.ax.set_ylim(-0.5, max(4.5, len(names) - 0.5))

        max_val = max(values) if values else 1
        self.ax.set_xlim(0, max_val * 1.15)

        self.ax.set_title("Top 5 活跃用户", loc='left',
                         fontdict={'size': 14, 'weight': 'bold', 'color': COLOR_TEXT_PRIMARY}, pad=15)
        self.ax.set_xlabel("总使用时长 (小时)", fontdict={'size': 10, 'color': COLOR_TEXT_SECONDARY})
        self.ax.grid(axis='x', linestyle='-', alpha=0.3, color='#E5E5EA')
