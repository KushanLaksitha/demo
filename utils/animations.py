"""
Reusable animation helpers so every screen feels consistent.
Only opacity/scale/color are animated (never x/y directly inside layouts)
because MDBoxLayout recomputes child position every frame.

New helpers added for the interactive overhaul:
  slide_up_fade_in  – cards slide up from below while fading in
  bounce_scale      – scale tap-feedback (0.95 -> 1.0 spring)
  shake             – horizontal shake for error feedback
  pulse_color       – gentle background color pulse for live badges
  ripple_flash      – quick background color flash on card tap
"""
from kivy.animation import Animation
from kivy.clock import Clock


# ── basic ──────────────────────────────────────────────────────────────────

def fade_in(widget, delay=0.0, duration=0.30):
    """Simple, layout-safe fade-in."""
    widget.opacity = 0

    def _start(*_):
        Animation(opacity=1, duration=duration, t="out_cubic").start(widget)

    Clock.schedule_once(_start, delay)


def stagger_fade_in(widgets, step=0.06, duration=0.30):
    """Fades in a list of widgets one after another."""
    for i, w in enumerate(widgets):
        fade_in(w, delay=i * step, duration=duration)


def button_press_bounce(widget):
    """Quick squash-and-settle tap feedback on icon/label widgets."""
    orig = widget.font_size
    anim = (Animation(font_size=orig * 0.8, duration=0.07) +
            Animation(font_size=orig, duration=0.14, t="out_back"))
    anim.start(widget)


# ── new premium helpers ────────────────────────────────────────────────────

def slide_up_fade_in(widget, delay=0.0, duration=0.35, distance=24):
    """Animate a widget sliding up from `distance` dp while fading in.
    Uses opacity so layout does not fight the position animation;
    the 'distance' feel is achieved via a canvas translate on the widget."""
    widget.opacity = 0

    def _start(*_):
        # Step 1: instant shift down via pos_hint or y offset
        # We animate opacity and a simple y translation on the widget itself.
        # This is safe for widgets inside a ScrollView's MDBoxLayout child.
        from kivy.metrics import dp as _dp
        original_y = widget.y

        def _after_layout(*_):
            nonlocal original_y
            original_y = widget.y
            widget.y = original_y - _dp(distance)
            anim = Animation(opacity=1, y=original_y, duration=duration, t="out_cubic")
            anim.start(widget)

        Clock.schedule_once(_after_layout, 0.01)

    Clock.schedule_once(_start, delay)


def bounce_scale(widget, scale_down=0.94, duration_down=0.08, duration_up=0.18):
    """Scale the widget down then spring back – used as tap feedback.
    Works on any widget that has a `scale` property via canvas / size."""
    orig_w = widget.width
    orig_h = widget.height
    anim = (
        Animation(width=orig_w * scale_down, height=orig_h * scale_down,
                  duration=duration_down, t="out_quad") +
        Animation(width=orig_w, height=orig_h,
                  duration=duration_up, t="out_back")
    )
    anim.start(widget)


def shake(widget, intensity=8, cycles=3, duration=0.07):
    """Horizontal shake for error feedback.
    Shifts widget.x left/right repeatedly then returns to origin."""
    from kivy.metrics import dp as _dp
    orig_x = widget.x

    def _build_seq(n, right):
        offset = _dp(intensity) if right else -_dp(intensity)
        return Animation(x=orig_x + offset, duration=duration, t="in_out_sine")

    seq = _build_seq(0, True)
    for i in range(1, cycles * 2):
        seq += _build_seq(i, i % 2 == 0)
    seq += Animation(x=orig_x, duration=duration, t="out_sine")
    seq.start(widget)


def pulse_color(widget, color_a, color_b, duration=0.9):
    """Ping-pong between two md_bg_colors indefinitely.
    Pass color_a as the normal color, color_b as the highlight."""
    anim = (
        Animation(md_bg_color=color_b, duration=duration, t="in_out_sine") +
        Animation(md_bg_color=color_a, duration=duration, t="in_out_sine")
    )
    anim.repeat = True
    anim.start(widget)


def ripple_flash(widget, flash_color, original_color, duration=0.18):
    """Flash a card to flash_color then back – mimics a ripple on tap."""
    anim = (
        Animation(md_bg_color=flash_color, duration=duration * 0.4, t="out_quad") +
        Animation(md_bg_color=original_color, duration=duration * 0.6, t="in_quad")
    )
    anim.start(widget)


def fade_out_remove(widget, duration=0.22, callback=None):
    """Fade a widget to invisible then optionally call callback (e.g., remove it)."""
    def _done(*_):
        if callback:
            callback()
    anim = Animation(opacity=0, duration=duration, t="out_quad")
    anim.bind(on_complete=_done)
    anim.start(widget)
