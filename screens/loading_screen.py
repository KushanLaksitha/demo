from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import sp

KV = """
<LoadingScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    FloatLayout:
        MDBoxLayout:
            orientation: "vertical"
            spacing: dp(10)
            size_hint: None, None
            size: dp(220), dp(180)
            pos_hint: {"center_x": 0.5, "center_y": 0.55}

            MDIcon:
                id: logo_icon
                icon: "sprout"
                halign: "center"
                font_size: "20sp"
                theme_text_color: "Custom"
                text_color: 0.4, 0.73, 0.42, 1
                pos_hint: {"center_x": 0.5}

            MDLabel:
                id: title_label
                text: "AgriSense"
                halign: "center"
                font_style: "H4"
                bold: True
                opacity: 0
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1
                size_hint_y: None
                height: self.texture_size[1]

            MDLabel:
                id: sub_label
                text: "Growing smarter decisions"
                halign: "center"
                opacity: 0
                theme_text_color: "Custom"
                text_color: 0.42, 0.42, 0.42, 1
                font_style: "Caption"
                size_hint_y: None
                height: self.texture_size[1]

        MDSpinner:
            id: spinner
            pos_hint: {"center_x": 0.5, "center_y": 0.22}
            size_hint: None, None
            size: dp(32), dp(32)
            color: 0.4, 0.73, 0.42, 1
            active: True
"""

Builder.load_string(KV)


class LoadingScreen(Screen):
    def on_enter(self, *args):
        icon = self.ids.logo_icon
        icon.font_size = sp(20)
        grow = Animation(font_size=sp(72), duration=0.6, t="out_back")
        grow.start(icon)

        Animation(opacity=1, duration=0.45).start(self.ids.title_label)
        Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.45).start(self.ids.sub_label), 0.25)

        # gentle infinite breathing pulse once the logo has grown in
        def start_pulse(*_):
            pulse = (Animation(font_size=sp(76), duration=0.9, t="in_out_sine") +
                      Animation(font_size=sp(68), duration=0.9, t="in_out_sine"))
            pulse.repeat = True
            pulse.start(icon)
        Clock.schedule_once(start_pulse, 0.6)

        # Move on to login after the DB health check + a minimum splash time
        Clock.schedule_once(self.finish, 1.8)

    def finish(self, *args):
        self.manager.transition.direction = "left"
        self.manager.current = "login"
