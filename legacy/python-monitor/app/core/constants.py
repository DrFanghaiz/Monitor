"""
Core constants: colors, fonts, theme settings.
Extracted from timer.py to avoid duplication across modules.
"""
import customtkinter as ctk

# --- Theme ---
APP_THEME_MODE = "Light"
APP_COLOR_THEME = "blue"

# ===== Apple Liquid Glass color palette =====
# Main backgrounds
COLOR_APPLE_BG = "#F0F2F5"
COLOR_CARD_WHITE = "#FFFFFF"
COLOR_GLASS_BG = "#F8FAFC"
COLOR_GLASS_BORDER = "rgba(255,255,255,0.3)"

# Text colors
COLOR_TEXT_PRIMARY = "#1A1D21"
COLOR_TEXT_SECONDARY = "#6B7280"
COLOR_TEXT_MUTED = "#9CA3AF"

# Accent colors
COLOR_ACCENT_BLUE = "#2563EB"
COLOR_ACCENT_PURPLE = "#7C3AED"
COLOR_ACCENT_CYAN = "#38BDF8"
COLOR_ACCENT_RED = "#EF4444"
COLOR_ACCENT_GREEN = "#22C55E"
COLOR_ACCENT_ORANGE = "#F59E0B"

# UI elements
COLOR_SEPARATOR = "#E5E7EB"
COLOR_TRANSPARENT_KEY = "#000001"
COLOR_RUNNING_BG = "#0F172A"
COLOR_RUNNING_CARD = "#1E293B"

# --- Fonts ---
FONT_TITLE = ("SF Pro Display", 28, "bold")
FONT_BOLD = ("SF Pro Text", 16, "bold")
FONT_NORMAL = ("SF Pro Text", 14)
FONT_TIMER = ("SF Mono", 96, "bold")
FONT_TIMER_LABEL = ("SF Pro Text", 14)
FONT_NANO_TIMER = ("SF Mono", 18)
FONT_NANO_USER = ("SF Pro Text", 12, "bold")

# Fallback fonts (when SF Pro is unavailable)
try:
    import tkinter.font as tkfont
    if "SF Pro Display" not in tkfont.families():
        FONT_TITLE = ("Segoe UI", 28, "bold")
        FONT_BOLD = ("Segoe UI", 16, "bold")
        FONT_NORMAL = ("Segoe UI", 14)
        FONT_TIMER = ("Consolas", 96, "bold")
        FONT_TIMER_LABEL = ("Segoe UI", 14)
        FONT_NANO_TIMER = ("Consolas", 18)
        FONT_NANO_USER = ("Segoe UI", 12, "bold")
except Exception:
    FONT_TITLE = ("Segoe UI", 28, "bold")
    FONT_BOLD = ("Segoe UI", 16, "bold")
    FONT_NORMAL = ("Segoe UI", 14)
    FONT_TIMER = ("Consolas", 96, "bold")
    FONT_TIMER_LABEL = ("Segoe UI", 14)
    FONT_NANO_TIMER = ("Consolas", 18)
    FONT_NANO_USER = ("Segoe UI", 12, "bold")
