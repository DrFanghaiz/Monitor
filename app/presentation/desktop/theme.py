"""
Unified theme constants — colors, fonts, dimensions.
Single source of truth for all desktop UI styling.
"""
import customtkinter as ctk

# ===== Mist dashboard palette =====
# Main backgrounds
COLOR_APPLE_BG = "#E8EEF5"
COLOR_CARD_WHITE = "#F9FBFD"
COLOR_GLASS_BG = "#F1F5F9"
COLOR_PANEL_SOFT = "#EDF3F8"
COLOR_CARD_ALT = "#F3F7FB"

# Text colors
COLOR_TEXT_PRIMARY = "#17212B"
COLOR_TEXT_SECONDARY = "#617182"
COLOR_TEXT_MUTED = "#8B9AAF"

# Accent colors
COLOR_ACCENT_BLUE = "#2D6CDF"
COLOR_ACCENT_PURPLE = "#7266F0"
COLOR_ACCENT_CYAN = "#4BB7D8"
COLOR_ACCENT_RED = "#E66867"
COLOR_ACCENT_GREEN = "#2FB686"
COLOR_ACCENT_ORANGE = "#F0A44B"

# UI elements
COLOR_SEPARATOR = "#D9E2EC"
COLOR_BORDER_SOFT = "#CFD9E4"
COLOR_TRANSPARENT_KEY = "#000001"
COLOR_RUNNING_BG = "#0E1726"
COLOR_RUNNING_CARD = "#172335"

# Sidebar
COLOR_SIDEBAR_BG = "#101A29"
COLOR_SIDEBAR_CARD = "#162234"
COLOR_SIDEBAR_NAV_TEXT = "#8EA0B4"
COLOR_SIDEBAR_NAV_HOVER = "#1A2940"
COLOR_SIDEBAR_NAV_ACTIVE = "#20314A"

# Buttons / states
COLOR_BUTTON_NEUTRAL = "#E7EDF4"
COLOR_BUTTON_NEUTRAL_HOVER = "#DCE6F0"
COLOR_SUCCESS_BG = "#E7F7F1"
COLOR_DANGER_BG = "#FCEBEA"
COLOR_WARNING_BG = "#FFF3E4"

# ===== Fonts =====
FONT_TITLE = ("SF Pro Display", 30, "bold")
FONT_BOLD = ("SF Pro Text", 16, "bold")
FONT_NORMAL = ("SF Pro Text", 14)
FONT_TIMER = ("SF Mono", 96, "bold")
FONT_TIMER_LABEL = ("SF Pro Text", 14)
FONT_NANO_TIMER = ("SF Mono", 18)
FONT_NANO_USER = ("SF Pro Text", 12, "bold")

# Fallback fonts
try:
    import tkinter.font as tkfont
    if "SF Pro Display" not in tkfont.families():
        FONT_TITLE = ("Segoe UI", 30, "bold")
        FONT_BOLD = ("Segoe UI", 16, "bold")
        FONT_NORMAL = ("Segoe UI", 14)
        FONT_TIMER = ("Consolas", 96, "bold")
        FONT_TIMER_LABEL = ("Segoe UI", 14)
        FONT_NANO_TIMER = ("Consolas", 18)
        FONT_NANO_USER = ("Segoe UI", 12, "bold")
except Exception:
    FONT_TITLE = ("Segoe UI", 30, "bold")
    FONT_BOLD = ("Segoe UI", 16, "bold")
    FONT_NORMAL = ("Segoe UI", 14)
    FONT_TIMER = ("Consolas", 96, "bold")
    FONT_TIMER_LABEL = ("Segoe UI", 14)
    FONT_NANO_TIMER = ("Consolas", 18)
    FONT_NANO_USER = ("Segoe UI", 12, "bold")

# Chinese fallback fonts
FONT_CN_TITLE = ("Microsoft YaHei UI", 22, "bold")
FONT_CN_HEADING = ("Microsoft YaHei UI", 14, "bold")
FONT_CN_BODY = ("Microsoft YaHei UI", 12)
FONT_CN_SMALL = ("Microsoft YaHei UI", 11)
