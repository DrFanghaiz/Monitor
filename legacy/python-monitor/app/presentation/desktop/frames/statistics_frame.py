"""
Statistics frame — usage charts (bar, heatmap, trend, pie).
Matplotlib imported lazily.
"""
import customtkinter as ctk
from app.presentation.desktop.theme import (
    COLOR_BG, COLOR_CARD, COLOR_TEXT, COLOR_TEXT_SECONDARY,
    COLOR_BLUE, COLOR_BORDER,
    FONT_HEADING, FONT_SMALL
)


class StatisticsFrame(ctk.CTkFrame):
    """统计界面 — 按需加载 matplotlib"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_BG, corner_radius=0, **kwargs)
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self._plt = plt
        self._FigureCanvasTkAgg = FigureCanvasTkAgg
        from charts import chart_drawer
        self._cd = chart_drawer

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(30, 12))
        ctk.CTkLabel(header, text="使用统计", font=FONT_HEADING,
                     text_color=COLOR_TEXT).pack(side="left")

        self.chart_type = ctk.StringVar(value="柱状图")
        seg = ctk.CTkSegmentedButton(
            header, values=["柱状图", "热力图", "趋势图", "饼图"],
            variable=self.chart_type, command=self._on_change,
            font=FONT_SMALL
        )
        seg.pack(side="right")

        # Chart area
        self.chart_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=12,
                                       border_width=1, border_color=COLOR_BORDER)
        self.chart_card.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.chart_card.grid_rowconfigure(0, weight=1)
        self.chart_card.grid_columnconfigure(0, weight=1)

        self._init_chart()

    def _init_chart(self):
        self.fig = self._plt.Figure(figsize=(8, 4), dpi=100, facecolor='white')
        self.ax = self.fig.add_subplot(111)
        self.canvas = self._FigureCanvasTkAgg(self.fig, master=self.chart_card)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        self.ax.set_facecolor('white')
        for spine in self.ax.spines.values():
            spine.set_visible(False)

    def _on_change(self, _):
        self.load_data()

    def load_data(self):
        ct = self.chart_type.get()
        stats = self.master.svc.statistics

        if ct == "柱状图":
            self._draw_bar()
        elif ct == "热力图":
            self._cd.draw_heatmap(self.ax, stats.get_hourly_stats(), days=30)
        elif ct == "趋势图":
            self._cd.draw_trend(self.ax, stats.get_daily_stats(30), days=30)
        elif ct == "饼图":
            self._cd.draw_pie(self.ax, stats.get_user_distribution("all"), "all")

        self.canvas.draw()

    def _draw_bar(self):
        self.ax.clear()
        for spine in self.ax.spines.values():
            spine.set_visible(False)

        data = self.master.svc.statistics.get_user_stats("all")
        if not data:
            self.ax.text(0.5, 0.5, "暂无数据", ha='center', va='center',
                        fontsize=14, color=COLOR_TEXT_SECONDARY,
                        transform=self.ax.transAxes)
            return

        top = data[:5]
        names = [u['user_name'] for u in top][::-1]
        values = [u['total_seconds'] / 3600 for u in top][::-1]

        n = len(names)
        bar_h = {1: 0.3, 2: 0.4, 3: 0.5}.get(n, 0.6)
        y = list(range(n))
        self.ax.barh(y, values, color=COLOR_BLUE, height=bar_h, alpha=0.9)
        self.ax.set_yticks(y)
        self.ax.set_yticklabels(names)
        self.ax.set_ylim(-0.5, max(4.5, n - 0.5))
        mx = max(values) if values else 1
        self.ax.set_xlim(0, mx * 1.15)
        self.ax.set_title("Top 5 活跃用户", loc='left',
                         fontdict={'size': 14, 'weight': 'bold', 'color': COLOR_TEXT}, pad=15)
        self.ax.set_xlabel("总使用时长 (小时)",
                          fontdict={'size': 10, 'color': COLOR_TEXT_SECONDARY})
        self.ax.grid(axis='x', linestyle='-', alpha=0.3, color='#E5E5EA')
