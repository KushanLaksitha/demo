"""
Reusable animation helpers so every screen feels consistent.
Only opacity is animated (never x/y) because these widgets live inside
MDBoxLayout/MDGridLayout containers that recompute child position every
frame -- animating position directly gets fought by the layout and
looks glitchy. Opacity fades are layout-safe and still read as a nice
"content settling in" effect.
"""
from kivy.animation import Animation
from kivy.clock import Clock


def fade_in(widget, delay=0.0, duration=0.30):
    """Simple, layout-safe fade-in."""
    widget.opacity = 0

    def _start(*_):
        Animation(opacity=1, duration=duration, t="out_cubic").start(widget)

    Clock.schedule_once(_start, delay)


def stagger_fade_in(widgets, step=0.06, duration=0.30):
    """Fades in a list of widgets one after another -- used for card
    lists (home feed, alerts, recommendations, feedback list)."""
    for i, w in enumerate(widgets):
        fade_in(w, delay=i * step, duration=duration)


def button_press_bounce(widget):
    """Quick squash-and-settle tap feedback, e.g. on star rating taps.
    widget.font_size is always a resolved float here (Kivy properties
    convert "72sp"-style strings to pixels at assignment time), so it's
    safe to do arithmetic directly on it."""
    orig = widget.font_size
    anim = Animation(font_size=orig * 0.8, duration=0.07) + \
           Animation(font_size=orig, duration=0.14, t="out_back")
    anim.start(widget)
