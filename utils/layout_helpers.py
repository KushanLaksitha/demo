"""
Small layout helper(s) so short lists (e.g. "no alerts yet", 2-3 cards)
sit centred in the middle of the screen on a phone instead of sticking
to the top with a big empty gap underneath -- looks much better on
mobile where the viewport is tall and narrow.
"""
from kivy.clock import Clock


def center_scroll_content(scrollview, box):
    """Call once after `box` has been (re)populated. Vertically centers
    content if shorter than viewport without creating recursive layout bindings."""
    if not scrollview or not box:
        return

    def _update(*_):
        try:
            available = scrollview.height
            if available <= 0:
                return

            pad = box.padding
            if isinstance(pad, (list, tuple)):
                if len(pad) == 4:
                    left, top, right, bottom = pad
                elif len(pad) == 2:
                    left, top = pad
                    right, bottom = pad, pad
                else:
                    left = top = right = bottom = pad[0] if pad else 0
            else:
                left = top = right = bottom = pad

            content_without_padding = max(0, box.minimum_height - top - bottom)
            if content_without_padding <= 0:
                return
            extra = max(0, (available - content_without_padding) / 2)

            if abs(top - extra) > 2:
                box.padding = (left, extra, right, extra)
        except Exception:
            pass

    Clock.schedule_once(_update, 0.05)


def show_snackbar(text: str):
    """Display a KivyMD MDSnackbar safely with an MDLabel child widget."""
    try:
        from kivymd.uix.snackbar import MDSnackbar
        from kivymd.uix.label import MDLabel
        MDSnackbar(MDLabel(text=text)).open()
    except Exception as e:
        print(f"[LayoutHelper] show_snackbar failed: {e}")

