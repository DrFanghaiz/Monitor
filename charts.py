"""
图表绘制模块
包含热力图、趋势图、饼图
Phase 3: no longer imports db — receives data from statistics_service via caller.
"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from datetime import datetime, timedelta


# 配置中文字体
def configure_font():
    font_candidates = ['Microsoft YaHei', 'SimHei', 'PingFang HK', 'Heiti TC']
    for font_name in font_candidates:
        try:
            found_path = fm.findfont(font_name, fallback_to_default=False)
            if found_path:
                plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
                break
        except Exception:
            continue
    plt.rcParams['axes.unicode_minus'] = False


configure_font()

# ===== 液态玻璃风格配色 =====
COLOR_PRIMARY = "#2563EB"
COLOR_SECONDARY = "#6B7280"
COLOR_ACCENT = "#F59E0B"
COLOR_CYAN = "#38BDF8"
COLOR_PURPLE = "#7C3AED"
COLOR_GREEN = "#22C55E"

PIE_COLORS = [
    "#2563EB", "#7C3AED", "#F59E0B", "#22C55E",
    "#38BDF8", "#EF4444", "#EC4899", "#14B8A6",
    "#8B5CF6", "#F97316", "#06B6D4", "#84CC16",
]


class ChartDrawer:
    """图表绘制器 — 只负责绘图，数据由调用方传入。"""

    @staticmethod
    def draw_heatmap(ax, hourly_data: list, days: int = 30):
        """
        绘制使用热力图（按小时/日期）
        Args:
            ax: matplotlib axes
            hourly_data: list of dicts with keys date, hour, hours
            days: number of days to display
        """
        ax.clear()

        if not hourly_data:
            ax.text(0.5, 0.5, "暂无数据", ha='center', va='center',
                   fontsize=14, color=COLOR_SECONDARY, transform=ax.transAxes)
            ax.set_axis_off()
            return

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)

        date_range = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                      for i in range(days)]

        matrix = np.zeros((24, days))
        date_to_idx = {d: i for i, d in enumerate(date_range)}
        for row in hourly_data:
            if row['date'] in date_to_idx:
                col = date_to_idx[row['date']]
                hour = row['hour']
                matrix[hour, col] = row['hours']

        im = ax.imshow(matrix, aspect='auto', cmap='YlOrRd',
                       interpolation='nearest', vmin=0)

        ax.set_yticks([0, 6, 12, 18, 23])
        ax.set_yticklabels(['0:00', '6:00', '12:00', '18:00', '23:00'])

        step = max(1, days // 7)
        ax.set_xticks(range(0, days, step))
        ax.set_xticklabels([date_range[i][5:] for i in range(0, days, step)], rotation=45)

        ax.set_title("使用时间热力图", fontsize=14, fontweight='bold', pad=10)
        ax.set_ylabel("时间", fontsize=10)
        ax.set_xlabel("日期", fontsize=10)

        for spine in ax.spines.values():
            spine.set_visible(False)

    @staticmethod
    def draw_trend(ax, daily_data: list, days: int = 30):
        """
        绘制使用趋势图
        Args:
            ax: matplotlib axes
            daily_data: list of dicts with keys date, hours, users
            days: number of days (for display reference)
        """
        ax.clear()

        if not daily_data:
            ax.text(0.5, 0.5, "暂无数据", ha='center', va='center',
                   fontsize=14, color=COLOR_SECONDARY, transform=ax.transAxes)
            ax.set_axis_off()
            return

        dates = [row['date'] for row in daily_data]
        hours = [row['hours'] for row in daily_data]
        users = [row['users'] for row in daily_data]

        line1 = ax.plot(dates, hours, color=COLOR_PRIMARY, linewidth=2.5,
                       marker='o', markersize=5, markerfacecolor='white',
                       markeredgewidth=2, markeredgecolor=COLOR_PRIMARY,
                       label='使用时长(小时)')
        ax.fill_between(range(len(dates)), hours, alpha=0.12, color=COLOR_PRIMARY)

        ax.set_ylabel("使用时长 (小时)", color=COLOR_PRIMARY, fontsize=10, fontweight='bold')
        ax.tick_params(axis='y', labelcolor=COLOR_PRIMARY)

        ax2 = ax.twinx()
        line2 = ax2.plot(dates, users, color=COLOR_ACCENT, linewidth=2.5,
                        linestyle='--', marker='s', markersize=5,
                        markerfacecolor='white', markeredgewidth=2,
                        markeredgecolor=COLOR_ACCENT, label='用户数')
        ax2.set_ylabel("用户数", color=COLOR_ACCENT, fontsize=10, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor=COLOR_ACCENT)

        step = max(1, len(dates) // 7)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels([dates[i][5:] for i in range(0, len(dates), step)], rotation=45)

        ax.set_title("使用趋势", fontsize=14, fontweight='bold', pad=10)

        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper left', fontsize=9)

        for spine in ax.spines.values():
            spine.set_visible(False)
        for spine in ax2.spines.values():
            spine.set_visible(False)

        ax.grid(axis='y', linestyle='--', alpha=0.3)

    @staticmethod
    def draw_pie(ax, distribution_data: list, filter_mode: str = "all"):
        """
        绘制用户使用占比饼图
        Args:
            ax: matplotlib axes
            distribution_data: list of dicts with keys user_name, total_seconds
            filter_mode: display label for title ('今日', '本月', 'all')
        """
        ax.clear()

        if not distribution_data:
            ax.text(0.5, 0.5, "暂无数据", ha='center', va='center',
                   fontsize=14, color=COLOR_SECONDARY, transform=ax.transAxes)
            ax.set_axis_off()
            return

        top_users = distribution_data[:8]
        other_seconds = sum(row['total_seconds'] for row in distribution_data[8:])

        labels = [row['user_name'] for row in top_users]
        sizes = [row['total_seconds'] / 3600 for row in top_users]

        if other_seconds > 0:
            labels.append("其他")
            sizes.append(other_seconds / 3600)

        colors = PIE_COLORS[:len(labels)] if len(labels) <= len(PIE_COLORS) else \
                 PIE_COLORS * (len(labels) // len(PIE_COLORS) + 1)
        colors = colors[:len(labels)]

        explode = [0.08 if i == 0 else 0.03 for i in range(len(labels))]

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            colors=colors, explode=explode, startangle=90,
            pctdistance=0.72, labeldistance=1.08,
            wedgeprops={'linewidth': 2, 'edgecolor': 'white'}
        )

        for text in texts:
            text.set_fontsize(10)
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        mode_text = {"今日": "今日", "本月": "本月", "all": "全部"}
        ax.set_title(f"用户使用占比 ({mode_text.get(filter_mode, '全部')})",
                    fontsize=14, fontweight='bold', pad=10)

        ax.axis('equal')


# 全局图表绘制器
chart_drawer = ChartDrawer()
