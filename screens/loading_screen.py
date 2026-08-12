"""
Premium loading / splash screen.
Gradient background (light-green → white), growing logo with breathing pulse,
staggered text, and 3-dot progress indicator at the bottom.
"""
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import sp, dp

KV = """
<LoadingScreen>:
    canvas.before:
        # Gradient-like background using two overlapping rectangles
        Color:
            rgba: 0.94, 0.99, 0.94, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.75, 0.93, 0.76, 0.45
        Ellipse:
            pos: -self.width * 0.3, self.height * 0.45
            size: self.width * 1.6, self.height * 0.7

    FloatLayout:
        # ── centre content ──────────────────────────────────────────────
        MDBoxLayout:
            orientation: "vertical"
            spacing: dp(8)
            size_hint: None, None
            size: dp(260), dp(200)
            pos_hint: {"center_x": 0.5, "center_y": 0.56}

            MDIcon:
                id: logo_icon
                icon: "sprout"
                halign: "center"
                font_size: "10sp"
                theme_text_color: "Custom"
                text_color: 0.25, 0.62, 0.30, 1
                pos_hint: {"center_x": 0.5}

            MDLabel:
                id: title_label
                text: "AgriSense"
                halign: "center"
                font_style: "H4"
                bold: True
                opacity: 0
                theme_text_color: "Custom"
                text_color: 0.08, 0.08, 0.08, 1
                size_hint_y: None
                height: self.texture_size[1]

            MDLabel:
                id: sub_label
                text: "Growing smarter decisions"
                halign: "center"
                opacity: 0
                theme_text_color: "Custom"
                text_color: 0.38, 0.38, 0.38, 1
                font_style: "Caption"
                size_hint_y: None
                height: self.texture_size[1]

        # ── three-dot progress indicator ────────────────────────────────
        MDBoxLayout:
            id: dots_row
            orientation: "horizontal"
            spacing: dp(10)
            size_hint: None, None
            size: dp(72), dp(16)
            pos_hint: {"center_x": 0.5, "center_y": 0.16}

            MDIcon:
                id: dot1
                icon: "circle"
                font_size: "10sp"
                theme_text_color: "Custom"
                text_color: 0.4, 0.73, 0.42, 1
                opacity: 0.3

            MDIcon:
                id: dot2
                icon: "circle"
                font_size: "10sp"
                theme_text_color: "Custom"
                text_color: 0.4, 0.73, 0.42, 1
                opacity: 0.3

            MDIcon:
                id: dot3
                icon: "circle"
                font_size: "10sp"
                theme_text_color: "Custom"
                text_color: 0.4, 0.73, 0.42, 1
                opacity: 0.3
"""

Builder.load_string(KV)


class LoadingScreen(Screen):
    _dot_event = None

    def on_enter(self, *args):
        icon = self.ids.logo_icon
        icon.font_size = sp(10)

        # Grow logo in with spring easing
        grow = Animation(font_size=sp(76), duration=0.65, t="out_back")
        grow.start(icon)

        # Stagger title + subtitle
        Animation(opacity=1, duration=0.45).start(self.ids.title_label)
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.45).start(self.ids.sub_label), 0.30
        )

        # Breathing pulse after logo grows in
        def start_pulse(*_):
            pulse = (
                Animation(font_size=sp(80), duration=0.95, t="in_out_sine") +
                Animation(font_size=sp(72), duration=0.95, t="in_out_sine")
            )
            pulse.repeat = True
            pulse.start(icon)

        Clock.schedule_once(start_pulse, 0.65)

        # Animated 3-dot progress indicator
        Clock.schedule_once(self._start_dots, 0.5)

        # Move on after splash
        Clock.schedule_once(self.finish, 2.0)

    def _start_dots(self, *_):
        dots = [self.ids.dot1, self.ids.dot2, self.ids.dot3]
        self._dot_index = 0

        def _cycle(*_):
            for i, d in enumerate(dots):
                target_op = 1.0 if i == self._dot_index else 0.3
                Animation(opacity=target_op, duration=0.25, t="out_quad").start(d)
            self._dot_index = (self._dot_index + 1) % 3

        self._dot_event = Clock.schedule_interval(_cycle, 0.38)

    def finish(self, *args):
        if self._dot_event:
            self._dot_event.cancel()
        self.manager.transition.direction = "left"
        self.manager.current = "login"
