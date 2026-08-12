"""
Login screen – premium redesign.
• Animated top logo/banner with green gradient feel
• shake() animation on fields when login fails
• Login button shows a spinner while authenticating
• Keyboard-friendly scrollable layout
"""
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from utils.layout_helpers import show_snackbar
from database.auth_service import login_user, resend_confirmation
from utils.animations import fade_in, shake

KV = """
<LoginScreen>:
    canvas.before:
        Color:
            rgba: 0.96, 1.0, 0.96, 1
        Rectangle:
            pos: self.pos
            size: self.size
        # top accent ellipse
        Color:
            rgba: 0.4, 0.73, 0.42, 0.12
        Ellipse:
            pos: -self.width * 0.2, self.height * 0.68
            size: self.width * 1.4, self.height * 0.5

    ScrollView:
        MDBoxLayout:
            id: content_box
            orientation: "vertical"
            padding: dp(28), dp(52), dp(28), dp(32)
            spacing: dp(14)
            size_hint_y: None
            height: self.minimum_height

            # ── branding ─────────────────────────────────────────────
            MDBoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: dp(160)
                spacing: dp(6)

                MDIcon:
                    id: logo_icon
                    icon: "sprout"
                    halign: "center"
                    font_size: "62sp"
                    theme_text_color: "Custom"
                    text_color: 0.25, 0.62, 0.30, 1
                    pos_hint: {"center_x": 0.5}

                MDLabel:
                    text: "AgriSense"
                    halign: "center"
                    font_style: "H4"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 0.08, 0.08, 0.08, 1
                    size_hint_y: None
                    height: self.texture_size[1]

                MDLabel:
                    text: "Smart price & production insights"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.42, 0.42, 0.42, 1
                    font_style: "Caption"
                    size_hint_y: None
                    height: self.texture_size[1]

            Widget:
                size_hint_y: None
                height: dp(10)

            # ── form card ─────────────────────────────────────────────
            MDCard:
                orientation: "vertical"
                padding: dp(20)
                spacing: dp(14)
                radius: [18, 18, 18, 18]
                size_hint_y: None
                height: self.minimum_height
                md_bg_color: 1, 1, 1, 1
                elevation: 2

                MDLabel:
                    text: "Sign in to your account"
                    font_style: "Subtitle1"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 0.1, 0.1, 0.1, 1
                    size_hint_y: None
                    height: self.texture_size[1]

                MDTextField:
                    id: email_field
                    hint_text: "Email address"
                    icon_left: "email-outline"
                    mode: "rectangle"
                    line_color_focus: 0.25, 0.62, 0.30, 1
                    radius: [8, 8, 8, 8]

                MDTextField:
                    id: password_field
                    hint_text: "Password"
                    icon_left: "lock-outline"
                    password: True
                    mode: "rectangle"
                    line_color_focus: 0.25, 0.62, 0.30, 1
                    radius: [8, 8, 8, 8]

                MDLabel:
                    id: error_label
                    text: ""
                    theme_text_color: "Custom"
                    text_color: 0.85, 0.18, 0.18, 1
                    font_style: "Caption"
                    size_hint_y: None
                    height: self.texture_size[1]

                MDRaisedButton:
                    id: login_btn
                    text: "LOG IN"
                    pos_hint: {"center_x": 0.5}
                    size_hint_x: 1
                    md_bg_color: 0.25, 0.62, 0.30, 1
                    elevation: 3
                    _radius: 10
                    on_release: root.do_login()

            # ── links ─────────────────────────────────────────────────
            MDTextButton:
                text: "Didn't get a confirmation email?  Resend"
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
                    text_color: 0.25, 0.62, 0.30, 1
                    on_release: root.go_register()
"""

Builder.load_string(KV)


class LoginScreen(Screen):
    def on_enter(self, *args):
        box = self.ids.content_box
        box.opacity = 0
        fade_in(box, duration=0.38)

    def do_login(self):
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text
        self.ids.error_label.text = ""

        if not email or not password:
            self.ids.error_label.text = "Please enter both email and password."
            shake(self.ids.email_field)
            shake(self.ids.password_field)
            return

        # Show in-button feedback
        btn = self.ids.login_btn
        btn.text = "Checking…"
        btn.disabled = True

        from kivy.clock import Clock

        def _attempt(*_):
            success, result = login_user(email, password)
            if not success:
                btn.text = "LOG IN"
                btn.disabled = False
                self.ids.error_label.text = result
                shake(self.ids.email_field)
                shake(self.ids.password_field)
                return

            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            app.current_user = result
            btn.text = "LOG IN"
            btn.disabled = False
            app.route_to_dashboard()

        Clock.schedule_once(_attempt, 0.12)

    def do_resend(self):
        email = self.ids.email_field.text.strip()
        if not email:
            self.ids.error_label.text = "Enter your email above first."
            shake(self.ids.email_field)
            return
        success, msg = resend_confirmation(email)
        show_snackbar(msg)

    def go_register(self):
        self.manager.transition.direction = "left"
        self.manager.current = "register"
