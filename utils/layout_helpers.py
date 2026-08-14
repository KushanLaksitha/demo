"""
Small layout helper(s) so short lists (e.g. "no alerts yet", 2-3 cards)
sit centred in the middle of the screen on a phone instead of sticking
to the top with a big empty gap underneath -- looks much better on
mobile where the viewport is tall and narrow.
"""
from kivy.clock import Clock


def center_scroll_content(scrollview, box):
    """Call once after `box` has been (re)populated. Adds symmetric
    top/bottom padding to `box` so its content is vertically centred
    inside `scrollview` whenever the content is shorter than the
    viewport; once content overflows, padding collapses to 0 and it
    behaves like a normal scrollable list."""
    if not scrollview or not box:
        return
    _updating = [False]

    def _update(*_):
        if _updating[0]:
            return
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
            extra = max(0, (available - content_without_padding) / 2)

            if abs(top - extra) > 1:
                _updating[0] = True
                box.padding = (left, extra, right, extra)
        except Exception as e:
            print(f"[LayoutHelper] center_scroll_content update skipped: {e}")
        finally:
            _updating[0] = False

    try:
        scrollview.bind(height=_update)
        box.bind(minimum_height=_update)
        Clock.schedule_once(_update, 0)
    except Exception as e:
        print(f"[LayoutHelper] center_scroll_content bind skipped: {e}")


def show_snackbar(text: str):
    """Display a KivyMD MDSnackbar safely with an MDLabel child widget."""
    try:
        from kivymd.uix.snackbar import MDSnackbar
        from kivymd.uix.label import MDLabel
        MDSnackbar(MDLabel(text=text)).open()
    except Exception as e:
        print(f"[LayoutHelper] show_snackbar failed: {e}")

