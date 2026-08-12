from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivymd.uix.menu import MDDropdownMenu
from utils.layout_helpers import show_snackbar

from database.auth_service import register_user, ROLES
from database.data_service import get_all_regions, get_all_crops, last_db_error_occurred
from utils.validators import (
    is_valid_email_format, email_already_registered, check_password_strength,
    is_password_acceptable,
)
from utils.animations import fade_in, stagger_fade_in

KV = """
<RegisterScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    ScrollView:
        MDBoxLayout:
            id: form_box
            orientation: "vertical"
            padding: dp(28), dp(36), dp(28), dp(28)
            spacing: dp(10)
            size_hint_y: None
            height: self.minimum_height

            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: 0.3, 0.6, 0.35, 1
                on_release: root.go_back()

            MDLabel:
                text: "Create your account"
                font_style: "H5"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1
                size_hint_y: None
                height: self.texture_size[1]

            MDBoxLayout:
                spacing: dp(10)
                size_hint_y: None
                height: dp(56)
                MDTextField:
                    id: first_name
                    hint_text: "First name"
                    mode: "rectangle"
                MDTextField:
                    id: last_name
                    hint_text: "Last name"
                    mode: "rectangle"

            MDTextField:
                id: email_field
                hint_text: "Email"
                icon_left: "email-outline"
                mode: "rectangle"
                helper_text_mode: "on_error"
                on_focus: if not self.focus: root.validate_email()
                on_text: root.clear_email_error()

            MDLabel:
                id: email_status
                text: ""
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.42, 0.42, 0.42, 1
                size_hint_y: None
                height: self.texture_size[1] if self.text else 0

            MDTextField:
                id: password_field
                hint_text: "Password"
                icon_left: "lock-outline"
                password: True
                mode: "rectangle"
                on_text: root.on_password_change()

            MDBoxLayout:
                size_hint_y: None
                height: dp(6)
                padding: 0
                MDBoxLayout:
                    id: strength_bar
                    size_hint_x: 0
                    md_bg_color: 0.878, 0.878, 0.878, 1

            MDLabel:
                id: strength_label
                text: ""
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.42, 0.42, 0.42, 1
                size_hint_y: None
                height: self.texture_size[1] if self.text else 0

            MDTextField:
                id: confirm_password_field
                hint_text: "Confirm password"
                icon_left: "lock-check-outline"
                password: True
                mode: "rectangle"
                on_text: root.check_password_match()

            MDLabel:
                id: match_label
                text: ""
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.42, 0.42, 0.42, 1
                size_hint_y: None
                height: self.texture_size[1] if self.text else 0

            MDRaisedButton:
                id: role_button
                text: "Select your role  ▾"
                md_bg_color: 0.91, 0.96, 0.91, 1
                text_color: 0.1, 0.1, 0.1, 1
                size_hint_x: 1
                on_release: root.open_role_menu()

            MDRaisedButton:
                id: region_button
                text: "Select your district  ▾"
                md_bg_color: 0.91, 0.96, 0.91, 1
                text_color: 0.1, 0.1, 0.1, 1
                size_hint_x: 1
                on_release: root.open_region_menu()

            MDLabel:
                text: "Which crops interest you?"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1
                size_hint_y: None
                height: self.texture_size[1]
                padding: 0, dp(6)

            MDList:
                id: crop_list
                size_hint_y: None
                height: self.minimum_height

            MDLabel:
                id: error_label
                text: ""
                theme_text_color: "Custom"
                text_color: 0.9, 0.22, 0.21, 1
                font_style: "Caption"
                size_hint_y: None
                height: self.texture_size[1]

            MDRaisedButton:
                id: submit_button
                text: "REGISTER"
                pos_hint: {"center_x": 0.5}
                size_hint_x: 1
                md_bg_color: 0.4, 0.73, 0.42, 1
                on_release: root.do_register()
"""

Builder.load_string(KV)


class RegisterScreen(Screen):
    selected_role = None
    selected_region_id = None
    email_valid = False

    def on_pre_enter(self, *args):
        self.role_menu = MDDropdownMenu(
            caller=self.ids.role_button,
            items=[{"text": r.capitalize(), "viewclass": "OneLineListItem",
                     "on_release": lambda x=r: self.pick_role(x)} for r in ROLES],
        )
        regions = get_all_regions()
        self.region_menu = MDDropdownMenu(
            caller=self.ids.region_button,
            items=[{"text": f"{district}", "viewclass": "OneLineListItem",
                     "on_release": lambda rid=rid, district=district: self.pick_region(rid, district)}
                    for rid, name, district in regions],
        )
        self.crops = get_all_crops()
        self.crop_checkboxes = {}
        self.ids.crop_list.clear_widgets()
        from kivymd.uix.list import OneLineAvatarIconListItem
        from kivymd.uix.selectioncontrol import MDCheckbox
        for crop_id, crop_name in self.crops:
            item = OneLineAvatarIconListItem(text=crop_name)
            cb = MDCheckbox(size_hint=(None, None), size=("48dp", "48dp"), pos_hint={"center_y": 0.5})
            item.add_widget(cb)
            self.crop_checkboxes[crop_id] = cb
            self.ids.crop_list.add_widget(item)

        had_error, error_msg = last_db_error_occurred()
        if had_error:
            self.ids.error_label.text = error_msg

    def on_enter(self, *args):
        # gentle staggered entrance for the whole form
        stagger_fade_in(list(self.ids.form_box.children)[::-1], step=0.03, duration=0.25)

    # ---------------- live validation ----------------
    def clear_email_error(self):
        self.ids.email_status.text = ""
        self.email_valid = False

    def validate_email(self):
        email = self.ids.email_field.text.strip()
        if not email:
            self.ids.email_status.text = ""
            return
        if not is_valid_email_format(email):
            self.ids.email_status.text = "⚠ That doesn't look like a valid email."
            self.ids.email_status.text_color = (0.9, 0.22, 0.21, 1)
            self.email_valid = False
            return
        if email_already_registered(email):
            self.ids.email_status.text = "⚠ An account with this email already exists."
            self.ids.email_status.text_color = (0.9, 0.22, 0.21, 1)
            self.email_valid = False
            return
        self.ids.email_status.text = "✓ Email looks good."
        self.ids.email_status.text_color = (0.26, 0.63, 0.28, 1)
        self.email_valid = True

    def on_password_change(self):
        password = self.ids.password_field.text
        score, label, color_hex, missing = check_password_strength(password)
        from kivy.utils import get_color_from_hex
        width_fraction = score / 5
        self.ids.strength_bar.size_hint_x = max(width_fraction, 0.02) if password else 0
        self.ids.strength_bar.md_bg_color = get_color_from_hex(color_hex)
        if not password:
            self.ids.strength_label.text = ""
        elif missing:
            self.ids.strength_label.text = f"{label} — still needs: {missing[0].lower()}"
        else:
            self.ids.strength_label.text = f"{label} password"
        self.check_password_match()

    def check_password_match(self):
        pw = self.ids.password_field.text
        confirm = self.ids.confirm_password_field.text
        if not confirm:
            self.ids.match_label.text = ""
            return
        if pw == confirm:
            self.ids.match_label.text = "✓ Passwords match."
            self.ids.match_label.text_color = (0.26, 0.63, 0.28, 1)
        else:
            self.ids.match_label.text = "⚠ Passwords do not match."
            self.ids.match_label.text_color = (0.9, 0.22, 0.21, 1)

    # ---------------- dropdowns ----------------
    def open_role_menu(self):
        self.role_menu.open()

    def open_region_menu(self):
        self.region_menu.open()

    def pick_role(self, role):
        self.selected_role = role
        self.ids.role_button.text = f"Role: {role.capitalize()}  ▾"
        self.role_menu.dismiss()

    def pick_region(self, region_id, district):
        self.selected_region_id = region_id
        self.ids.region_button.text = f"District: {district}  ▾"
        self.region_menu.dismiss()

    # ---------------- submit ----------------
    def do_register(self):
        self.ids.error_label.text = ""
        first_name = self.ids.first_name.text.strip()
        last_name = self.ids.last_name.text.strip()
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text
        confirm_password = self.ids.confirm_password_field.text
        crop_ids = [cid for cid, cb in self.crop_checkboxes.items() if cb.active]

        if not all([first_name, last_name, email, password, confirm_password,
                     self.selected_role, self.selected_region_id]):
            self.ids.error_label.text = "Please fill in every field, and pick a role and district."
            return
        if not is_valid_email_format(email):
            self.ids.error_label.text = "Please enter a valid email address."
            return
        if email_already_registered(email):
            self.ids.error_label.text = "An account with this email already exists."
            return
        if password != confirm_password:
            self.ids.error_label.text = "Passwords do not match."
            return
        if not is_password_acceptable(password):
            self.ids.error_label.text = "Password is too weak — add uppercase, lowercase, a number and a symbol."
            return
        if not crop_ids:
            self.ids.error_label.text = "Please select at least one crop you're interested in."
            return

        success, message = register_user(
            email, password, first_name, last_name, self.selected_role,
            self.selected_region_id, crop_ids=crop_ids,
        )
        if not success:
            self.ids.error_label.text = message
            return

        show_snackbar(message)
        self.manager.transition.direction = "right"
        self.manager.current = "login"

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "login"
