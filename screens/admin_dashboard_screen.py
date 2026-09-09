"""
Admin Dashboard Screen – Clean, Premium Design.
"""
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from utils.layout_helpers import show_snackbar

from database.data_service import (
    get_all_users_for_admin, toggle_user_status_by_admin, update_user_role_by_admin,
    delete_user_by_admin, get_all_regions, get_average_rating
)
from database.auth_service import admin_create_user, ALL_ROLES, validate_admin_session
from utils.validators import is_valid_email_format, is_password_acceptable
from utils.animations import stagger_fade_in, bounce_scale

KV = """
<AdminDashboardScreen>:
    canvas.before:
        Color:
            rgba: 0.95, 0.97, 0.95, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBoxLayout:
        orientation: "vertical"
        spacing: 0

        # ────────────────────────────────────────────────────────────────
        # TOP BAR
        # ────────────────────────────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(14), dp(8), dp(8), dp(8)
            spacing: dp(6)
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

            MDLabel:
                text: "Admin Console"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1

            MDIconButton:
                icon: "logout"
                theme_text_color: "Custom"
                text_color: 0.78, 0.18, 0.18, 1
                on_release: root.logout()

        # ────────────────────────────────────────────────────────────────
        # STATS BANNER  (green gradient style)
        # ────────────────────────────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(70)
            padding: dp(14), dp(10), dp(10), dp(10)
            spacing: dp(10)
            canvas.before:
                Color:
                    rgba: 0.20, 0.55, 0.28, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            # Left: counters
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(3)
                MDLabel:
                    id: user_count_label
                    text: "Loading..."
                    font_style: "Subtitle1"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                MDLabel:
                    id: avg_rating_banner
                    text: ""
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.80, 0.94, 0.82, 1

            # Right: Feedback nav button
            MDCard:
                size_hint: None, None
                size: dp(140), dp(40)
                radius: [8, 8, 8, 8]
                md_bg_color: 1, 1, 1, 0.15
                elevation: 0
                ripple_behavior: True
                on_release: root.go_to_feedback()

                MDBoxLayout:
                    padding: dp(6), dp(4)
                    spacing: dp(4)
                    MDIconButton:
                        icon: "star-outline"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        size_hint: None, None
                        size: dp(28), dp(28)
                        user_font_size: "18sp"
                    MDLabel:
                        text: "Feedback"
                        font_style: "Button"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        halign: "left"
                        valign: "center"

        # ────────────────────────────────────────────────────────────────
        # SEARCH + CREATE ROW
        # ────────────────────────────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(52)
            padding: dp(10), dp(6), dp(10), dp(6)
            spacing: dp(8)
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            MDTextField:
                id: user_search_field
                hint_text: "Search users..."
                icon_left: "magnify"
                mode: "rectangle"
                line_color_focus: 0.20, 0.55, 0.28, 1
                on_text: root.on_search_text_changed(self.text)

            MDRaisedButton:
                id: create_btn
                text: "+ Add"
                md_bg_color: 0.20, 0.55, 0.28, 1
                text_color: 1, 1, 1, 1
                _radius: 8
                size_hint_x: None
                width: dp(62)
                elevation: 0
                on_release: root.toggle_create_form()

        # ────────────────────────────────────────────────────────────────
        # ROLE FILTER CHIPS
        # ────────────────────────────────────────────────────────────────
        ScrollView:
            size_hint_y: None
            height: dp(40)
            do_scroll_y: False
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            MDBoxLayout:
                id: role_filter_box
                orientation: "horizontal"
                spacing: dp(6)
                padding: dp(10), dp(5), dp(10), dp(5)
                size_hint_x: None
                width: self.minimum_width

        # ────────────────────────────────────────────────────────────────
        # MAIN SCROLLABLE AREA  (form + user list)
        # ────────────────────────────────────────────────────────────────
        MDScrollView:
            do_scroll_y: True
            do_scroll_x: False
            bar_width: 2
            bar_color: 0.20, 0.55, 0.28, 0.45

            MDBoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(0)

                # ── Collapsible Create Form ─────────────────────────────
                MDCard:
                    id: create_user_card
                    orientation: "vertical"
                    size_hint_y: None
                    height: 0
                    opacity: 0
                    padding: dp(14), dp(12), dp(14), dp(14)
                    spacing: dp(8)
                    radius: [0, 0, 0, 0]
                    md_bg_color: 1, 1, 1, 1
                    elevation: 2

                    MDLabel:
                        text: "Create New Account"
                        bold: True
                        font_style: "Subtitle1"
                        theme_text_color: "Custom"
                        text_color: 0.20, 0.55, 0.28, 1
                        size_hint_y: None
                        height: dp(26)

                    MDBoxLayout:
                        spacing: dp(8)
                        size_hint_y: None
                        height: dp(48)
                        MDTextField:
                            id: new_first_name
                            hint_text: "First name"
                            mode: "rectangle"
                        MDTextField:
                            id: new_last_name
                            hint_text: "Last name"
                            mode: "rectangle"

                    MDTextField:
                        id: new_email
                        hint_text: "Email address"
                        icon_left: "email-outline"
                        mode: "rectangle"
                        size_hint_y: None
                        height: dp(48)

                    MDTextField:
                        id: new_password
                        hint_text: "Password"
                        icon_left: "lock-outline"
                        password: True
                        mode: "rectangle"
                        size_hint_y: None
                        height: dp(48)

                    MDBoxLayout:
                        spacing: dp(8)
                        size_hint_y: None
                        height: dp(44)
                        MDRaisedButton:
                            id: new_role_btn
                            text: "Role: Policymaker"
                            md_bg_color: 0.93, 0.96, 0.93, 1
                            text_color: 0.15, 0.15, 0.15, 1
                            size_hint_x: 0.5
                            _radius: 8
                            elevation: 0
                            on_release: root.open_create_role_menu()
                        MDRaisedButton:
                            id: new_region_btn
                            text: "Select District"
                            md_bg_color: 0.93, 0.96, 0.93, 1
                            text_color: 0.15, 0.15, 0.15, 1
                            size_hint_x: 0.5
                            _radius: 8
                            elevation: 0
                            on_release: root.open_create_region_menu()

                    MDLabel:
                        id: create_user_error
                        text: ""
                        theme_text_color: "Custom"
                        text_color: 0.82, 0.15, 0.15, 1
                        font_style: "Caption"
                        size_hint_y: None
                        height: self.texture_size[1] if self.text else 0

                    MDBoxLayout:
                        spacing: dp(8)
                        size_hint_y: None
                        height: dp(40)
                        MDRaisedButton:
                            text: "CREATE ACCOUNT"
                            md_bg_color: 0.20, 0.55, 0.28, 1
                            text_color: 1, 1, 1, 1
                            size_hint_x: 0.65
                            _radius: 8
                            elevation: 0
                            on_release: root.submit_new_user()
                        MDFlatButton:
                            text: "Cancel"
                            theme_text_color: "Custom"
                            text_color: 0.5, 0.5, 0.5, 1
                            size_hint_x: 0.35
                            on_release: root.close_create_form()

                    # Divider
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(1)
                        canvas.before:
                            Color:
                                rgba: 0.88, 0.88, 0.88, 1
                            Rectangle:
                                pos: self.pos
                                size: self.size

                # ── Section Label ───────────────────────────────────────
                MDBoxLayout:
                    size_hint_y: None
                    height: dp(36)
                    padding: dp(14), dp(6), dp(14), dp(4)
                    MDLabel:
                        id: user_section_label
                        text: "All Users"
                        font_style: "Overline"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.4, 0.4, 0.4, 1
                        halign: "left"

                # ── User Cards ──────────────────────────────────────────
                MDBoxLayout:
                    id: users_list_box
                    orientation: "vertical"
                    spacing: dp(6)
                    padding: dp(10), 0, dp(10), dp(16)
                    size_hint_y: None
                    height: self.minimum_height
"""

Builder.load_string(KV)


ROLE_META = {
    "admin":       {"color": (0.75, 0.15, 0.15, 1),  "label": "Admin"},
    "policymaker": {"color": (0.15, 0.42, 0.82, 1),  "label": "Policy"},
    "trader":      {"color": (0.80, 0.50, 0.08, 1),  "label": "Trader"},
    "farmer":      {"color": (0.20, 0.55, 0.28, 1),  "label": "Farmer"},
}


class AdminDashboardScreen(Screen):
    selected_role_filter = "all"
    search_query = ""
    new_user_role = "policymaker"
    new_user_region_id = None
    create_form_open = False
    dialog = None

    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if not app.current_user or not validate_admin_session(app.current_user.get("user_id")):
            app.current_user = None
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            return
        self._setup_role_filter_chips()
        self.load_users()
        self._update_banner()

    # ── Banner ────────────────────────────────────────────────────────────────
    def _update_banner(self):
        try:
            users = get_all_users_for_admin()
            self.ids.user_count_label.text = f"{len(users)} registered users"
        except Exception:
            self.ids.user_count_label.text = "User accounts"
        try:
            avg, count = get_average_rating()
            if avg and count:
                self.ids.avg_rating_banner.text = f"Avg rating  {avg}/5  from {count} reviews"
            else:
                self.ids.avg_rating_banner.text = "No ratings yet"
        except Exception:
            self.ids.avg_rating_banner.text = ""

    # ── Navigation ────────────────────────────────────────────────────────────
    def go_to_feedback(self):
        if self.manager:
            self.manager.transition.direction = "left"
            self.manager.current = "admin_feedback"

    def logout(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        app.current_user = None
        if self.manager:
            self.manager.transition.direction = "right"
            self.manager.current = "login"
        show_snackbar("Logged out successfully.")

    # ── Filter Chips ──────────────────────────────────────────────────────────
    def _setup_role_filter_chips(self):
        box = self.ids.role_filter_box
        box.clear_widgets()
        roles = ["all", "farmer", "trader", "policymaker", "admin"]
        self._filter_chip_widgets = {}
        for r in roles:
            is_sel = (r == self.selected_role_filter)
            btn = MDRaisedButton(
                text=r.capitalize(),
                size_hint=(None, None),
                height=dp(28),
                _radius=14,
                elevation=0,
                md_bg_color=(0.20, 0.55, 0.28, 1) if is_sel else (0.90, 0.94, 0.90, 1),
                text_color=(1, 1, 1, 1) if is_sel else (0.25, 0.40, 0.25, 1),
                on_release=lambda x, role=r: self.set_role_filter(role)
            )
            box.add_widget(btn)
            self._filter_chip_widgets[r] = btn

    def set_role_filter(self, role):
        self.selected_role_filter = role
        for r, btn in self._filter_chip_widgets.items():
            sel = (r == role)
            btn.md_bg_color = (0.20, 0.55, 0.28, 1) if sel else (0.90, 0.94, 0.90, 1)
            btn.text_color   = (1, 1, 1, 1) if sel else (0.25, 0.40, 0.25, 1)
        self.load_users()

    def on_search_text_changed(self, text):
        self.search_query = text
        self.load_users()

    # ── User List ─────────────────────────────────────────────────────────────
    def load_users(self):
        box = self.ids.users_list_box
        box.clear_widgets()

        users = get_all_users_for_admin(
            role_filter=self.selected_role_filter,
            search_query=self.search_query
        )

        # Update section label
        role_display = "All Users" if self.selected_role_filter == "all" \
            else f"{self.selected_role_filter.capitalize()}s"
        self.ids.user_section_label.text = (
            f"{role_display}  ({len(users)})"
        )

        if not users:
            box.add_widget(MDLabel(
                text="No users match the current filter.",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.55, 0.55, 0.55, 1),
                size_hint_y=None,
                height=dp(70)
            ))
            return

        cards = []
        for u in users:
            card = self._build_user_card(u)
            box.add_widget(card)
            cards.append(card)
        stagger_fade_in(cards, step=0.04, duration=0.22)

    def _build_user_card(self, u):
        role_key   = u["user_type"].lower()
        meta       = ROLE_META.get(role_key, {"color": (0.4, 0.4, 0.4, 1), "label": role_key.capitalize()})
        is_active  = u["is_active"]

        card = MDCard(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(6),
            size_hint_y=None,
            height=dp(128),
            radius=[10, 10, 10, 10],
            md_bg_color=(1, 1, 1, 1),
            elevation=1
        )

        # — Row 1: Name + role pill + status dot ——————————————
        row1 = MDBoxLayout(orientation="horizontal", spacing=dp(8),
                           size_hint_y=None, height=dp(26))

        name_lbl = MDLabel(
            text=u["full_name"],
            bold=True,
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=(0.10, 0.10, 0.10, 1)
        )

        role_pill = MDCard(
            size_hint=(None, None), size=(dp(56), dp(20)),
            radius=[5, 5, 5, 5], elevation=0,
            md_bg_color=meta["color"], padding=[dp(4), dp(2), dp(4), dp(2)]
        )
        role_pill.add_widget(MDLabel(
            text=meta["label"], halign="center",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(1, 1, 1, 1)
        ))

        # Active / Suspended indicator
        status_color = (0.15, 0.60, 0.25, 1) if is_active else (0.78, 0.18, 0.18, 1)
        status_bg    = (0.88, 0.97, 0.89, 1) if is_active else (0.98, 0.88, 0.88, 1)
        status_pill  = MDCard(
            size_hint=(None, None), size=(dp(72), dp(20)),
            radius=[5, 5, 5, 5], elevation=0,
            md_bg_color=status_bg, padding=[dp(4), dp(2), dp(4), dp(2)]
        )
        status_pill.add_widget(MDLabel(
            text="Active" if is_active else "Suspended",
            halign="center", font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=status_color
        ))

        row1.add_widget(name_lbl)
        row1.add_widget(role_pill)
        row1.add_widget(status_pill)

        # — Row 2: Email + district ——————————————————————————
        row2 = MDLabel(
            text=f"{u['email']}  |  {u['district']}",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.50, 0.50, 0.50, 1),
            size_hint_y=None,
            height=dp(18)
        )

        # — Row 3: Action buttons ————————————————————————————
        row3 = MDBoxLayout(orientation="horizontal", spacing=dp(6),
                           size_hint_y=None, height=dp(34))

        toggle_btn = MDRaisedButton(
            text="Suspend" if is_active else "Activate",
            size_hint_x=0.38, _radius=6, elevation=0,
            md_bg_color=(0.97, 0.88, 0.88, 1) if is_active else (0.88, 0.97, 0.89, 1),
            text_color=(0.78, 0.15, 0.15, 1) if is_active else (0.15, 0.55, 0.22, 1),
            on_release=lambda x, uid=u["user_id"]: self.toggle_user_status(uid)
        )
        role_btn = MDRaisedButton(
            text="Change Role",
            size_hint_x=0.36, _radius=6, elevation=0,
            md_bg_color=(0.91, 0.94, 0.98, 1),
            text_color=(0.15, 0.42, 0.82, 1),
            on_release=lambda b, uid=u["user_id"], cr=u["user_type"]: self.open_role_change_menu(b, uid, cr)
        )
        delete_btn = MDRaisedButton(
            text="Delete",
            size_hint_x=0.26, _radius=6, elevation=0,
            md_bg_color=(0.98, 0.91, 0.91, 1),
            text_color=(0.82, 0.18, 0.18, 1),
            on_release=lambda x, uid=u["user_id"], em=u["email"]: self.confirm_delete_user(uid, em)
        )

        row3.add_widget(toggle_btn)
        row3.add_widget(role_btn)
        row3.add_widget(delete_btn)

        card.add_widget(row1)
        card.add_widget(row2)
        card.add_widget(row3)
        return card

    # ── User Actions ──────────────────────────────────────────────────────────
    def toggle_user_status(self, user_id):
        if self._is_me(user_id):
            show_snackbar("You cannot suspend your own admin account.")
            return
        ok, msg = toggle_user_status_by_admin(user_id)
        show_snackbar(msg)
        if ok:
            self.load_users()

    def _is_me(self, user_id):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        return app.current_user and app.current_user.get("user_id") == user_id

    def open_role_change_menu(self, caller, user_id, current_role):
        if self._is_me(user_id):
            show_snackbar("You cannot change your own admin role.")
            return
        items = [
            {
                "text": ("[ Current ]  " if r == current_role else "  ") + r.capitalize(),
                "viewclass": "OneLineListItem",
                "on_release": lambda *_, r=r: self.change_user_role(user_id, r),
            }
            for r in ALL_ROLES
        ]
        self.role_menu = MDDropdownMenu(caller=caller, items=items, width_mult=3.5)
        self.role_menu.open()

    def change_user_role(self, user_id, new_role):
        if hasattr(self, "role_menu") and self.role_menu:
            self.role_menu.dismiss()
        ok, msg = update_user_role_by_admin(user_id, new_role)
        show_snackbar(msg)
        if ok:
            self.load_users()

    def confirm_delete_user(self, user_id, email):
        if self._is_me(user_id):
            show_snackbar("You cannot delete your own admin account.")
            return
        self.dialog = MDDialog(
            title="Delete Account",
            text=f"Permanently delete account '{email}'?\nThis action cannot be undone.",
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=(0.5, 0.5, 0.5, 1),
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="DELETE",
                    md_bg_color=(0.82, 0.15, 0.15, 1),
                    text_color=(1, 1, 1, 1),
                    on_release=lambda x, uid=user_id: self._do_delete(uid)
                ),
            ],
        )
        self.dialog.open()

    def _do_delete(self, user_id):
        if self.dialog:
            self.dialog.dismiss()
        ok, msg = delete_user_by_admin(user_id)
        show_snackbar(msg)
        if ok:
            self.load_users()
            self._update_banner()

    # ── Create Form ───────────────────────────────────────────────────────────
    def toggle_create_form(self):
        if self.create_form_open:
            self.close_create_form()
        else:
            self.open_create_form()

    def open_create_form(self):
        self.create_form_open = True
        self.ids.create_btn.text = "Close"
        card = self.ids.create_user_card
        card.opacity = 1
        card.height  = dp(330)
        bounce_scale(card)
        self.regions = get_all_regions()

    def close_create_form(self):
        self.create_form_open = False
        self.ids.create_btn.text = "+ Add"
        card = self.ids.create_user_card
        card.height  = 0
        card.opacity = 0
        self.ids.create_user_error.text = ""
        self.new_user_role      = "policymaker"
        self.new_user_region_id = None
        self.ids.new_role_btn.text   = "Role: Policymaker"
        self.ids.new_region_btn.text = "Select District"
        for fid in ("new_first_name", "new_last_name", "new_email", "new_password"):
            self.ids[fid].text = ""

    def open_create_role_menu(self):
        items = [
            {"text": r.capitalize(), "viewclass": "OneLineListItem",
             "on_release": lambda *_, r=r: self.pick_create_role(r)}
            for r in ALL_ROLES
        ]
        self.create_role_menu = MDDropdownMenu(
            caller=self.ids.new_role_btn, items=items, width_mult=3)
        self.create_role_menu.open()

    def pick_create_role(self, role):
        self.new_user_role = role
        self.ids.new_role_btn.text = f"Role: {role.capitalize()}"
        if hasattr(self, "create_role_menu"):
            self.create_role_menu.dismiss()

    def open_create_region_menu(self):
        if not hasattr(self, "regions") or not self.regions:
            self.regions = get_all_regions()
        items = [
            {"text": district, "viewclass": "OneLineListItem",
             "on_release": lambda *_, rid=rid, d=district: self.pick_create_region(rid, d)}
            for rid, name, district in self.regions
        ]
        self.create_region_menu = MDDropdownMenu(
            caller=self.ids.new_region_btn, items=items, width_mult=3)
        self.create_region_menu.open()

    def pick_create_region(self, region_id, district):
        self.new_user_region_id  = region_id
        self.ids.new_region_btn.text = f"District: {district}"
        if hasattr(self, "create_region_menu"):
            self.create_region_menu.dismiss()

    def submit_new_user(self):
        self.ids.create_user_error.text = ""
        fn       = self.ids.new_first_name.text.strip()
        ln       = self.ids.new_last_name.text.strip()
        email    = self.ids.new_email.text.strip()
        password = self.ids.new_password.text

        if not all([fn, ln, email, password, self.new_user_region_id]):
            self.ids.create_user_error.text = "Please fill in all fields and select a district."
            return
        if not is_valid_email_format(email):
            self.ids.create_user_error.text = "Enter a valid email address."
            return
        if not is_password_acceptable(password):
            self.ids.create_user_error.text = "Password too weak (min 8 chars, UPPER, number & symbol)."
            return

        ok, msg = admin_create_user(
            email=email, password=password,
            first_name=fn, last_name=ln,
            user_type=self.new_user_role,
            region_id=self.new_user_region_id
        )
        if not ok:
            self.ids.create_user_error.text = msg
            return

        show_snackbar(msg)
        self.close_create_form()
        self.load_users()
        self._update_banner()
