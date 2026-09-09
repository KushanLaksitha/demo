"""
Admin Create User / Policymaker Screen – Dedicated account creation interface.
Allows Admin to create Policymakers (and other roles) with immediate activation.
"""
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from utils.layout_helpers import show_snackbar

from database.data_service import get_all_regions
from database.auth_service import admin_create_user, ALL_ROLES
from utils.validators import is_valid_email_format, is_password_acceptable

KV = """
<AdminCreateUserScreen>:
    canvas.before:
        Color:
            rgba: 0.95, 0.97, 0.95, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBoxLayout:
        orientation: "vertical"
        spacing: 0

        # ── Top Bar ──────────────────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(54)
            padding: dp(8), dp(6), dp(8), dp(6)
            spacing: dp(4)
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
                Color:
                    rgba: 0.88, 0.88, 0.88, 1
                Line:
                    points: self.x, self.y, self.x + self.width, self.y
                    width: 1

            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: 0.20, 0.55, 0.28, 1
                on_release: root.go_to_admin_dashboard()

            MDLabel:
                text: "Create User Account"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.12, 0.12, 0.12, 1

            MDIconButton:
                icon: "logout"
                theme_text_color: "Custom"
                text_color: 0.78, 0.18, 0.18, 1
                on_release: root.logout()

        # ── Info Banner (Green) ─────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(64)
            padding: dp(16), dp(10), dp(16), dp(10)
            spacing: dp(8)
            canvas.before:
                Color:
                    rgba: 0.20, 0.55, 0.28, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            MDIcon:
                icon: "account-plus"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                size_hint: None, None
                size: dp(28), dp(28)
                pos_hint: {"center_y": 0.5}

            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(2)
                pos_hint: {"center_y": 0.5}

                MDLabel:
                    text: "Instant Account Activation"
                    font_style: "Subtitle2"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1

                MDLabel:
                    text: "Created accounts are activated immediately."
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.82, 0.94, 0.84, 1

        # ── Scrollable Form Area ────────────────────────────────────────
        MDScrollView:
            do_scroll_y: True
            do_scroll_x: False
            bar_width: 2
            bar_color: 0.20, 0.55, 0.28, 0.5

            MDBoxLayout:
                orientation: "vertical"
                padding: dp(16), dp(16), dp(16), dp(32)
                spacing: dp(14)
                size_hint_y: None
                height: self.minimum_height

                # Form Card
                MDCard:
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(16)
                    spacing: dp(12)
                    radius: [12, 12, 12, 12]
                    md_bg_color: 1, 1, 1, 1
                    elevation: 1

                    MDLabel:
                        text: "Account Details"
                        font_style: "Subtitle1"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.20, 0.55, 0.28, 1
                        size_hint_y: None
                        height: dp(26)

                    # First & Last Name
                    MDBoxLayout:
                        spacing: dp(10)
                        size_hint_y: None
                        height: dp(54)
                        MDTextField:
                            id: first_name_field
                            hint_text: "First name"
                            mode: "rectangle"
                            line_color_focus: 0.20, 0.55, 0.28, 1
                        MDTextField:
                            id: last_name_field
                            hint_text: "Last name"
                            mode: "rectangle"
                            line_color_focus: 0.20, 0.55, 0.28, 1

                    # Email
                    MDTextField:
                        id: email_field
                        hint_text: "Email address"
                        icon_left: "email-outline"
                        mode: "rectangle"
                        line_color_focus: 0.20, 0.55, 0.28, 1
                        size_hint_y: None
                        height: dp(54)

                    # Password
                    MDTextField:
                        id: password_field
                        hint_text: "Password"
                        icon_left: "lock-outline"
                        password: True
                        mode: "rectangle"
                        line_color_focus: 0.20, 0.55, 0.28, 1
                        size_hint_y: None
                        height: dp(54)

                    MDLabel:
                        text: "Password must be at least 8 chars, with UPPERCASE, number & symbol."
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.55, 0.55, 0.55, 1
                        size_hint_y: None
                        height: dp(16)

                    # Role & District Selector Row
                    MDBoxLayout:
                        spacing: dp(10)
                        size_hint_y: None
                        height: dp(46)
                        MDRaisedButton:
                            id: role_select_btn
                            text: "Role: Policymaker"
                            md_bg_color: 0.92, 0.95, 0.92, 1
                            text_color: 0.15, 0.15, 0.15, 1
                            size_hint_x: 0.5
                            _radius: 8
                            elevation: 0
                            on_release: root.open_role_menu()

                        MDRaisedButton:
                            id: region_select_btn
                            text: "Select District"
                            md_bg_color: 0.92, 0.95, 0.92, 1
                            text_color: 0.15, 0.15, 0.15, 1
                            size_hint_x: 0.5
                            _radius: 8
                            elevation: 0
                            on_release: root.open_region_menu()

                    # Error Message
                    MDLabel:
                        id: error_label
                        text: ""
                        theme_text_color: "Custom"
                        text_color: 0.82, 0.15, 0.15, 1
                        font_style: "Caption"
                        bold: True
                        size_hint_y: None
                        height: self.texture_size[1] if self.text else 0

                    # Submit Button
                    MDRaisedButton:
                        id: submit_btn
                        text: "CREATE ACCOUNT"
                        md_bg_color: 0.20, 0.55, 0.28, 1
                        text_color: 1, 1, 1, 1
                        size_hint_x: 1
                        size_hint_y: None
                        height: dp(44)
                        _radius: 8
                        elevation: 0
                        on_release: root.submit_form()

                    # Cancel Button
                    MDFlatButton:
                        text: "Cancel & Return to Dashboard"
                        theme_text_color: "Custom"
                        text_color: 0.45, 0.45, 0.45, 1
                        size_hint_x: 1
                        size_hint_y: None
                        height: dp(36)
                        on_release: root.go_to_admin_dashboard()
"""

Builder.load_string(KV)


class AdminCreateUserScreen(Screen):
    selected_role = "policymaker"
    selected_region_id = None
    regions = []

    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if not app.current_user:
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            return
        self.reset_form()

    def reset_form(self):
        self.selected_role = "policymaker"
        self.selected_region_id = None
        self.regions = get_all_regions()

        self.ids.first_name_field.text = ""
        self.ids.last_name_field.text = ""
        self.ids.email_field.text = ""
        self.ids.password_field.text = ""
        self.ids.error_label.text = ""

        self.ids.role_select_btn.text = "Role: Policymaker"
        self.ids.region_select_btn.text = "Select District"

    def open_role_menu(self):
        items = [
            {
                "text": r.capitalize(),
                "viewclass": "OneLineListItem",
                "on_release": lambda *_, role=r: self.pick_role(role)
            }
            for r in ALL_ROLES
        ]
        self.role_menu = MDDropdownMenu(
            caller=self.ids.role_select_btn,
            items=items,
            width_mult=3
        )
        self.role_menu.open()

    def pick_role(self, role):
        self.selected_role = role
        self.ids.role_select_btn.text = f"Role: {role.capitalize()}"
        if hasattr(self, "role_menu"):
            self.role_menu.dismiss()

    def open_region_menu(self):
        if not self.regions:
            self.regions = get_all_regions()
        items = [
            {
                "text": district,
                "viewclass": "OneLineListItem",
                "on_release": lambda *_, rid=rid, d=district: self.pick_region(rid, d)
            }
            for rid, name, district in self.regions
        ]
        self.region_menu = MDDropdownMenu(
            caller=self.ids.region_select_btn,
            items=items,
            width_mult=3
        )
        self.region_menu.open()

    def pick_region(self, region_id, district):
        self.selected_region_id = region_id
        self.ids.region_select_btn.text = f"District: {district}"
        if hasattr(self, "region_menu"):
            self.region_menu.dismiss()

    def submit_form(self):
        self.ids.error_label.text = ""
        fn = self.ids.first_name_field.text.strip()
        ln = self.ids.last_name_field.text.strip()
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text

        if not fn or not ln:
            self.ids.error_label.text = "Please enter both first and last name."
            return
        if not email:
            self.ids.error_label.text = "Please enter an email address."
            return
        if not is_valid_email_format(email):
            self.ids.error_label.text = "Please enter a valid email format (e.g. name@domain.com)."
            return
        if not password:
            self.ids.error_label.text = "Please enter a password."
            return
        if not is_password_acceptable(password):
            self.ids.error_label.text = "Password too weak: minimum 8 chars, uppercase, number & symbol."
            return
        if not self.selected_region_id:
            self.ids.error_label.text = "Please select a district."
            return

        ok, msg = admin_create_user(
            email=email,
            password=password,
            first_name=fn,
            last_name=ln,
            user_type=self.selected_role,
            region_id=self.selected_region_id
        )

        if not ok:
            self.ids.error_label.text = msg
            return

        show_snackbar(f"Account created successfully for {email}!")
        self.go_to_admin_dashboard()

    def go_to_admin_dashboard(self):
        try:
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "admin_dashboard"
        except Exception as e:
            print(f"[AdminCreateUser] go_to_admin_dashboard error: {e}")

    def logout(self):
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            app.current_user = None
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            show_snackbar("Logged out successfully.")
        except Exception as e:
            print(f"[AdminCreateUser] logout error: {e}")
