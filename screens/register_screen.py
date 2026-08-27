"""
Register screen – premium redesign.
• Chip-style interactive crop selector (tap to toggle, bounce_scale)
• Icon badges for role selection
• Animated password-strength bar
• Staggered entrance animations
"""
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.menu import MDDropdownMenu
from utils.layout_helpers import show_snackbar
from database.auth_service import register_user, PUBLIC_ROLES, ROLES
from database.data_service import get_all_regions, get_all_crops, last_db_error_occurred
from utils.validators import (
    is_valid_email_format, email_already_registered, check_password_strength,
    is_password_acceptable,
)
from utils.animations import fade_in, stagger_fade_in, bounce_scale

KV = """
<CropChip@MDCard>:
    crop_id: 0
    selected: False
    text: ""
    size_hint_y: None
    height: dp(36)
    size_hint_x: None
    width: self.minimum_width + dp(28)
    radius: [18, 18, 18, 18]
    ripple_behavior: True
    elevation: 0
    md_bg_color: (0.25, 0.62, 0.30, 1) if self.selected else (0.93, 0.97, 0.93, 1)
    padding: dp(12), dp(6), dp(12), dp(6)

    MDLabel:
        text: root.text
        halign: "center"
        bold: root.selected
        font_style: "Caption"
        theme_text_color: "Custom"
        text_color: (1, 1, 1, 1) if root.selected else (0.15, 0.45, 0.20, 1)
        size_hint_x: None
        width: self.texture_size[0]

<RegisterScreen>:
    canvas.before:
        Color:
            rgba: 0.96, 1.0, 0.96, 1
        Rectangle:
            pos: self.pos
            size: self.size

    ScrollView:
        MDBoxLayout:
            id: form_box
            orientation: "vertical"
            padding: dp(24), dp(36), dp(24), dp(28)
            spacing: dp(12)
            size_hint_y: None
            height: self.minimum_height

            # ── back button ────────────────────────────────────────────
            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: 0.25, 0.62, 0.30, 1
                on_release: root.go_back()
                pos_hint: {"x": 0}

            MDLabel:
                text: "Create your account"
                font_style: "H5"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.08, 0.08, 0.08, 1
                size_hint_y: None
                height: self.texture_size[1]

            MDLabel:
                text: "Join AgriSense to track crops and market prices"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.5, 0.5, 0.5, 1
                size_hint_y: None
                height: self.texture_size[1]

            Widget:
                size_hint_y: None
                height: dp(4)

            # ── name row ────────────────────────────────────────────────
            MDBoxLayout:
                spacing: dp(10)
                size_hint_y: None
                height: dp(56)
                MDTextField:
                    id: first_name
                    hint_text: "First name"
                    mode: "rectangle"
                    line_color_focus: 0.25, 0.62, 0.30, 1
                MDTextField:
                    id: last_name
                    hint_text: "Last name"
                    mode: "rectangle"
                    line_color_focus: 0.25, 0.62, 0.30, 1

            # ── email ───────────────────────────────────────────────────
            MDTextField:
                id: email_field
                hint_text: "Email address"
                icon_left: "email-outline"
                mode: "rectangle"
                line_color_focus: 0.25, 0.62, 0.30, 1
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

            # ── password ────────────────────────────────────────────────
            MDTextField:
                id: password_field
                hint_text: "Password"
                icon_left: "lock-outline"
                password: True
                mode: "rectangle"
                line_color_focus: 0.25, 0.62, 0.30, 1
                on_text: root.on_password_change()

            # strength bar track
            MDBoxLayout:
                size_hint_y: None
                height: dp(5)
                radius: [4, 4, 4, 4]
                md_bg_color: 0.90, 0.90, 0.90, 1
                padding: 0
                MDBoxLayout:
                    id: strength_bar
                    size_hint_x: 0
                    radius: [4, 4, 4, 4]
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
                line_color_focus: 0.25, 0.62, 0.30, 1
                on_text: root.check_password_match()

            MDLabel:
                id: match_label
                text: ""
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.42, 0.42, 0.42, 1
                size_hint_y: None
                height: self.texture_size[1] if self.text else 0

            # ── role picker ─────────────────────────────────────────────
            MDLabel:
                text: "Your role"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1
                size_hint_y: None
                height: dp(28)

            MDBoxLayout:
                id: role_chip_row
                orientation: "horizontal"
                spacing: dp(10)
                size_hint_y: None
                height: dp(44)
                padding: dp(2), 0, dp(2), 0

            # ── district picker ─────────────────────────────────────────
            MDRaisedButton:
                id: region_button
                text: "Select your district  ▾"
                md_bg_color: 0.91, 0.96, 0.91, 1
                text_color: 0.1, 0.1, 0.1, 1
                size_hint_x: 1
                _radius: 10
                on_release: root.open_region_menu()

            # ── crop chip selector ──────────────────────────────────────
            MDLabel:
                text: "Crops you're interested in"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1
                size_hint_y: None
                height: dp(28)

            MDLabel:
                text: "Tap to select / deselect"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.55, 0.55, 0.55, 1
                size_hint_y: None
                height: dp(18)

            MDGridLayout:
                id: crop_chip_grid
                cols: 3
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
                adaptive_height: True

            # ── error / submit ──────────────────────────────────────────
            MDLabel:
                id: error_label
                text: ""
                theme_text_color: "Custom"
                text_color: 0.85, 0.18, 0.18, 1
                font_style: "Caption"
                size_hint_y: None
                height: self.texture_size[1]

            MDRaisedButton:
                id: submit_button
                text: "CREATE ACCOUNT"
                pos_hint: {"center_x": 0.5}
                size_hint_x: 1
                md_bg_color: 0.25, 0.62, 0.30, 1
                elevation: 3
                _radius: 10
                on_release: root.do_register()
"""

Builder.load_string(KV)

ROLE_ICONS = {
    "farmer": "●",
    "trader": "●",
}


class RegisterScreen(Screen):
    selected_role = None
    selected_region_id = None
    email_valid = False
    _crop_chips = {}        # crop_id -> chip widget
    _role_chips = {}        # role -> chip widget

    def on_pre_enter(self, *args):
        regions = get_all_regions()
        self.region_menu = MDDropdownMenu(
            caller=self.ids.region_button,
            items=[
                {
                    "text": district,
                    "viewclass": "OneLineListItem",
                    "on_release": lambda rid=rid, d=district: self.pick_region(rid, d),
                }
                for rid, name, district in regions
            ],
        )

        # ── role chips ────────────────────────────────────────────────
        row = self.ids.role_chip_row
        row.clear_widgets()
        self._role_chips = {}
        for role in PUBLIC_ROLES:
            chip = self._make_role_chip(role)
            row.add_widget(chip)
            self._role_chips[role] = chip

        # ── crop chips ────────────────────────────────────────────────
        self.crops = get_all_crops()
        grid = self.ids.crop_chip_grid
        grid.clear_widgets()
        self._crop_chips = {}
        for crop_id, crop_name in self.crops:
            chip = self._make_crop_chip(crop_id, crop_name)
            grid.add_widget(chip)
            self._crop_chips[crop_id] = chip

        had_error, error_msg = last_db_error_occurred()
        if had_error:
            self.ids.error_label.text = error_msg

    def _make_role_chip(self, role):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel
        from kivymd.uix.boxlayout import MDBoxLayout

        chip = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(44),
            radius=[10, 10, 10, 10],
            elevation=0,
            ripple_behavior=True,
            md_bg_color=(0.93, 0.97, 0.93, 1),
            padding=(dp(8), dp(4), dp(8), dp(4)),
        )
        lbl = MDLabel(
            text=f"{ROLE_ICONS.get(role, '')} {role.capitalize()}",
            halign="center",
            bold=False,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.15, 0.45, 0.20, 1),
        )
        chip.add_widget(lbl)
        chip._lbl = lbl
        chip.bind(on_release=lambda inst, r=role: self.pick_role_chip(r))
        return chip

    def _make_crop_chip(self, crop_id, crop_name):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel

        chip = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(38),
            radius=[12, 12, 12, 12],
            elevation=0,
            ripple_behavior=True,
            md_bg_color=(0.93, 0.97, 0.93, 1),
            padding=(dp(6), dp(4), dp(6), dp(4)),
        )
        lbl = MDLabel(
            text=crop_name,
            halign="center",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.15, 0.45, 0.20, 1),
        )
        chip.add_widget(lbl)
        chip._lbl = lbl
        chip._selected = False
        chip.bind(on_release=lambda inst, cid=crop_id: self.toggle_crop_chip(cid))
        return chip

    def pick_role_chip(self, role):
        self.selected_role = role
        for r, chip in self._role_chips.items():
            selected = r == role
            from kivy.animation import Animation
            Animation(md_bg_color=(0.25, 0.62, 0.30, 1) if selected else (0.93, 0.97, 0.93, 1),
                      duration=0.18).start(chip)
            chip._lbl.text_color = (1, 1, 1, 1) if selected else (0.15, 0.45, 0.20, 1)
            chip._lbl.bold = selected
        bounce_scale(self._role_chips[role])

    def toggle_crop_chip(self, crop_id):
        chip = self._crop_chips[crop_id]
        chip._selected = not chip._selected
        selected = chip._selected
        from kivy.animation import Animation
        Animation(md_bg_color=(0.25, 0.62, 0.30, 1) if selected else (0.93, 0.97, 0.93, 1),
                  duration=0.18).start(chip)
        chip._lbl.text_color = (1, 1, 1, 1) if selected else (0.15, 0.45, 0.20, 1)
        chip._lbl.bold = selected
        bounce_scale(chip)

    def on_enter(self, *args):
        stagger_fade_in(list(self.ids.form_box.children)[::-1], step=0.03, duration=0.25)

    # ── live validation ──────────────────────────────────────────────────
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
            self.ids.email_status.text_color = (0.85, 0.18, 0.18, 1)
            self.email_valid = False
            return
        if email_already_registered(email):
            self.ids.email_status.text = "⚠ An account with this email already exists."
            self.ids.email_status.text_color = (0.85, 0.18, 0.18, 1)
            self.email_valid = False
            return
        self.ids.email_status.text = "✓ Email looks good."
        self.ids.email_status.text_color = (0.26, 0.63, 0.28, 1)
        self.email_valid = True

    def on_password_change(self):
        password = self.ids.password_field.text
        score, label, color_hex, missing = check_password_strength(password)
        from kivy.utils import get_color_from_hex
        from kivy.animation import Animation
        width_fraction = score / 5
        target = max(width_fraction, 0.02) if password else 0
        Animation(size_hint_x=target, duration=0.22, t="out_quad").start(self.ids.strength_bar)
        self.ids.strength_bar.md_bg_color = get_color_from_hex(color_hex)
        if not password:
            self.ids.strength_label.text = ""
        elif missing:
            self.ids.strength_label.text = f"{label} — needs: {missing[0].lower()}"
        else:
            self.ids.strength_label.text = f"{label} password ✓"
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
            self.ids.match_label.text_color = (0.85, 0.18, 0.18, 1)

    # ── dropdowns ─────────────────────────────────────────────────────────
    def open_region_menu(self):
        self.region_menu.open()

    def pick_region(self, region_id, district):
        self.selected_region_id = region_id
        self.ids.region_button.text = f"District: {district}  ▾"
        self.region_menu.dismiss()

    # ── submit ────────────────────────────────────────────────────────────
    def do_register(self):
        from utils.animations import shake as _shake
        self.ids.error_label.text = ""
        first_name = self.ids.first_name.text.strip()
        last_name = self.ids.last_name.text.strip()
        email = self.ids.email_field.text.strip()
        password = self.ids.password_field.text
        confirm_password = self.ids.confirm_password_field.text
        crop_ids = [cid for cid, chip in self._crop_chips.items() if chip._selected]

        def _err(msg, field=None):
            self.ids.error_label.text = msg
            if field:
                _shake(field)

        if not all([first_name, last_name, email, password, confirm_password,
                    self.selected_role, self.selected_region_id]):
            _err("Please fill in every field, pick a role and district.")
            return
        if not is_valid_email_format(email):
            _err("Please enter a valid email address.", self.ids.email_field)
            return
        if email_already_registered(email):
            _err("An account with this email already exists.", self.ids.email_field)
            return
        if password != confirm_password:
            _err("Passwords do not match.", self.ids.confirm_password_field)
            return
        if not is_password_acceptable(password):
            _err("Password too weak — add uppercase, number, and a symbol.", self.ids.password_field)
            return
        if not crop_ids:
            _err("Please select at least one crop you're interested in.")
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
