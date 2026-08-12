"""
AgriSense visual theme: white background, light-green accents.
Import COLORS wherever a screen needs a colour, so the whole app stays consistent.
"""
from kivymd.utils.get_hex_from_color import get_color_from_hex as hx

COLORS = {
    "primary": hx("#66BB6A"),        # light green - buttons, headers
    "primary_dark": hx("#4C9950"),   # pressed / accents
    "primary_light": hx("#E8F5E9"),  # card backgrounds
    "background": hx("#FFFFFF"),     # app background
    "surface": hx("#FFFFFF"),        # cards
    "text_primary": hx("#1B1B1B"),
    "text_secondary": hx("#6B6B6B"),
    "success": hx("#43A047"),
    "warning": hx("#FB8C00"),
    "danger": hx("#E53935"),
    "divider": hx("#E0E0E0"),
}

PALETTE_MD = "Green"          # KivyMD theme palette name
PALETTE_MD_HUE = "500"
FONT_TITLE = "20sp"
FONT_BODY = "14sp"
FONT_SMALL = "12sp"

# Icons used for the bottom "tiktok style" navigation across all 3 roles
NAV_ICONS = {
    "home": "view-dashboard",
    "recommendations": "lightbulb-on",
    "alerts": "bell-ring",
    "history": "chart-line",
    "profile": "account-circle",
}
