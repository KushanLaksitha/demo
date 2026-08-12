from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from utils.layout_helpers import show_snackbar
from database.auth_service import login_user, resend_confirmation
from utils.animations import fade_in

KV = """
<LoginScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    ScrollView:
        MDBoxLayout:
            id: content_box
            orientation: "vertical"
            padding: dp(28), dp(60), dp(28), dp(28)
            spacing: dp(14)
            size_hint_y: None
            height: self.minimum_height

            Widget:
                size_hint_y: None
                height: dp(20)

            MDIcon:
                icon: "sprout"
                halign: "center"
                font_size: "64sp"
                theme_text_color: "Custom"
                text_color: 0.4, 0.73, 0.42, 1
                pos_hint: {"center_x": 0.5}

            MDLabel:
                text: "AgriSense"
                halign: "center"
                font_style: "H4"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1
                size_hint_y: None
                height: self.texture_size[1]

            MDLabel:
                text: "Smart price & production insights for Matale and Kandy"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.42, 0.42, 0.42, 1
                font_style: "Caption"
                size_hint_y: None
                height: self.texture_size[1]

            Widget:
                size_hint_y: None
                height: dp(16)

            MDTextField:
                id: email_field
                hint_text: "Email"
                icon_left: "email-outline"
                mode: "rectangle"
                line_color_focus: 0.4, 0.73, 0.42, 1

            MDTextField:
                id: password_field
                hint_text: "Password"
                icon_left: "lock-outline"
                password: True
                mode: "rectangle"
                line_color_focus: 0.4, 0.73, 0.42, 1

            MDLabel:
                id: error_label
                text: ""
                theme_text_color: "Custom"
                text_color: 0.9, 0.22, 0.21, 1
                font_style: "Caption"
                size_hint_y: None
                height: self.texture_size[1]

            MDRaisedButton:
                text: "LOG IN"
                pos_hint: {"center_x": 0.5}
                size_hint_x: 1
                md_bg_color: 0.4, 0.73, 0.42, 1
                on_release: root.do_login()

            MDTextButton:
                text: "Didn't get a confirmation email? Resend"
                pos_hint: {"center_x": 0.5}
                theme_text_color: "Custom"
                text_color: 0.3, 0.6, 0.35, 1
                on_release: root.do_resend()

            MDBoxLayout:
                orientation: "horizontal"
                spacing: dp(4)
                size_hint_y: None
                height: dp(40)
                pos_hint: {"center_x": 0.5}

                MDLabel:
                    text: "New to AgriSense?"
                    halign: "right"
                    theme_text_color: "Custom"
                    text_color: 0.42, 0.42, 0.42, 1

                MDTextButton:
                    text: "Create an account"
                    theme_text_color: "Custom"
                    text_color: 0.3, 0.6, 0.35, 1
                    on_release: root.go_register()
"""

Builder.load_string(KV)


class LoginScreen(Screen):
    def on_enter(self, *args):
        fade_in(self.ids.content_box, duration=0.3)

    def do_login(self):
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text
        self.ids.error_label.text = ""

        if not email or not password:
            self.ids.error_label.text = "Please enter both email and password."
            return

        success, result = login_user(email, password)
        if not success:
            self.ids.error_label.text = result
            return

        app = self.manager.app if hasattr(self.manager, "app") else self.manager.parent
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        app.current_user = result
        app.route_to_dashboard()

    def do_resend(self):
        email = self.ids.email_field.text.strip()
        if not email:
            self.ids.error_label.text = "Enter your email above first."
            return
        success, msg = resend_confirmation(email)
        show_snackbar(msg)

    def go_register(self):
        self.manager.transition.direction = "left"
        self.manager.current = "register"
