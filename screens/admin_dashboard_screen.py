"""
Admin Dashboard Screen - User Account & System Management.
Allows Admin to:
1. Manage all user accounts (View, Search, Filter by role, Toggle Active/Suspend, Change Role, Delete User).
2. Create Policy Maker (and other role) accounts with immediate activation.
3. Navigate to the dedicated Ratings & Feedback screen.
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
            rgba: 0.96, 0.98, 0.96, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBoxLayout:
        orientation: "vertical"
        spacing: 0

        # ── Top Navigation Bar ──────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(52)
            padding: dp(12), dp(6), dp(8), dp(6)
            spacing: dp(8)
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            MDLabel:
                text: "Admin Console"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1

            MDIconButton:
                icon: "logout"
                theme_text_color: "Custom"
                text_color: 0.85, 0.2, 0.2, 1
                on_release: root.logout()

        # ── Quick Stats / Nav Banner ────────────────────────────────────
        MDCard:
            size_hint_y: None
            height: dp(56)
            radius: [0, 0, 0, 0]
            elevation: 1
            md_bg_color: 0.15, 0.45, 0.85, 1
            padding: dp(12), dp(8)

            MDBoxLayout:
                spacing: dp(12)
                orientation: "horizontal"

                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(2)
                    MDLabel:
                        id: user_count_label
                        text: "Loading users..."
                        font_style: "Subtitle2"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                    MDLabel:
                        id: avg_rating_banner
                        text: ""
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.85, 0.92, 1, 1

                MDRaisedButton:
                    text: "★ Ratings & Feedback"
                    md_bg_color: 1, 1, 1, 0.18
                    text_color: 1, 1, 1, 1
                    _radius: 8
                    size_hint_x: None
                    width: dp(148)
                    elevation: 0
                    on_release: root.go_to_feedback()

        # ── Action Bar: Create + Search ─────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(44)
            padding: dp(8), dp(4)
            spacing: dp(8)

            MDRaisedButton:
                id: create_btn
                text: "+ Create Account"
                md_bg_color: 0.25, 0.62, 0.30, 1
                text_color: 1, 1, 1, 1
                _radius: 8
                size_hint_x: None
                width: dp(148)
                on_release: root.toggle_create_form()

            MDTextField:
                id: user_search_field
                hint_text: "Search name or email..."
                icon_left: "magnify"
                mode: "rectangle"
                line_color_focus: 0.25, 0.62, 0.30, 1
                on_text: root.on_search_text_changed(self.text)

        # ── Role Filter Chips ───────────────────────────────────────────
        ScrollView:
            size_hint_y: None
            height: dp(36)
            do_scroll_y: False
            MDBoxLayout:
                id: role_filter_box
                orientation: "horizontal"
                spacing: dp(6)
                padding: dp(8), dp(3)
                size_hint_x: None
                width: self.minimum_width

        # ── Scrollable Content Area ─────────────────────────────────────
        MDScrollView:
            do_scroll_y: True
            do_scroll_x: False
            bar_width: 2
            bar_color: 0.25, 0.62, 0.30, 0.6

            MDBoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(0)
                padding: 0

                # Collapsible Create Account Form
                MDCard:
                    id: create_user_card
                    orientation: "vertical"
                    size_hint_y: None
                    height: 0
                    opacity: 0
                    padding: dp(12)
                    spacing: dp(8)
                    radius: [0, 0, 12, 12]
                    md_bg_color: 1, 1, 1, 1
                    elevation: 2

                    MDLabel:
                        id: create_form_title
                        text: "Create New Account"
                        bold: True
                        font_style: "Subtitle1"
                        theme_text_color: "Custom"
                        text_color: 0.25, 0.62, 0.30, 1
                        size_hint_y: None
                        height: dp(24)

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
                        hint_text: "Password (min 8 chars, UPPER, num, symbol)"
                        icon_left: "lock-outline"
                        password: True
                        mode: "rectangle"
                        size_hint_y: None
                        height: dp(48)

                    MDBoxLayout:
                        spacing: dp(8)
                        size_hint_y: None
                        height: dp(42)
                        MDRaisedButton:
                            id: new_role_btn
                            text: "Role: Policymaker ▾"
                            md_bg_color: 0.91, 0.95, 0.91, 1
                            text_color: 0.1, 0.1, 0.1, 1
                            size_hint_x: 0.5
                            _radius: 8
                            on_release: root.open_create_role_menu()
                        MDRaisedButton:
                            id: new_region_btn
                            text: "Select District ▾"
                            md_bg_color: 0.91, 0.95, 0.91, 1
                            text_color: 0.1, 0.1, 0.1, 1
                            size_hint_x: 0.5
                            _radius: 8
                            on_release: root.open_create_region_menu()

                    MDLabel:
                        id: create_user_error
                        text: ""
                        theme_text_color: "Custom"
                        text_color: 0.85, 0.18, 0.18, 1
                        font_style: "Caption"
                        size_hint_y: None
                        height: self.texture_size[1] if self.text else 0

                    MDBoxLayout:
                        spacing: dp(8)
                        size_hint_y: None
                        height: dp(40)
                        MDRaisedButton:
                            text: "CREATE ACCOUNT"
                            md_bg_color: 0.25, 0.62, 0.30, 1
                            size_hint_x: 0.6
                            _radius: 8
                            on_release: root.submit_new_user()
                        MDFlatButton:
                            text: "Cancel"
                            theme_text_color: "Custom"
                            text_color: 0.5, 0.5, 0.5, 1
                            size_hint_x: 0.4
                            on_release: root.close_create_form()

                # User cards list
                MDBoxLayout:
                    id: users_list_box
                    orientation: "vertical"
                    spacing: dp(8)
                    padding: dp(8), dp(8), dp(8), dp(16)
                    size_hint_y: None
                    height: self.minimum_height
"""

Builder.load_string(KV)


ROLE_COLORS = {
    "admin": (0.75, 0.15, 0.15, 1),
    "policymaker": (0.15, 0.45, 0.85, 1),
    "trader": (0.85, 0.55, 0.1, 1),
    "farmer": (0.25, 0.62, 0.30, 1),
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

    def _update_banner(self):
        """Update the top stats banner."""
        try:
            users = get_all_users_for_admin()
            self.ids.user_count_label.text = f"{len(users)} registered users"
        except Exception:
            self.ids.user_count_label.text = "User accounts"

        try:
            avg, count = get_average_rating()
            if avg and count:
                self.ids.avg_rating_banner.text = f"★ {avg}/5 avg rating from {count} submissions"
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

    # ── ROLE FILTER CHIPS ─────────────────────────────────────────────────────
    def _setup_role_filter_chips(self):
        box = self.ids.role_filter_box
        box.clear_widgets()
        roles = ["all", "farmer", "trader", "policymaker", "admin"]
        self._filter_chip_widgets = {}
        for r in roles:
            btn = MDRaisedButton(
                text=r.capitalize(),
                size_hint=(None, None),
                height=dp(30),
                _radius=15,
                elevation=0,
                md_bg_color=(0.25, 0.62, 0.30, 1) if r == self.selected_role_filter else (0.91, 0.95, 0.91, 1),
                text_color=(1, 1, 1, 1) if r == self.selected_role_filter else (0.2, 0.4, 0.2, 1),
                on_release=lambda x, role=r: self.set_role_filter(role)
            )
            box.add_widget(btn)
            self._filter_chip_widgets[r] = btn

    def set_role_filter(self, role):
        self.selected_role_filter = role
        for r, btn in self._filter_chip_widgets.items():
            sel = (r == role)
            btn.md_bg_color = (0.25, 0.62, 0.30, 1) if sel else (0.91, 0.95, 0.91, 1)
            btn.text_color = (1, 1, 1, 1) if sel else (0.2, 0.4, 0.2, 1)
        self.load_users()

    def on_search_text_changed(self, text):
        self.search_query = text
        self.load_users()

    # ── LOAD USER LIST ────────────────────────────────────────────────────────
    def load_users(self):
        box = self.ids.users_list_box
        box.clear_widgets()

        users = get_all_users_for_admin(
            role_filter=self.selected_role_filter,
            search_query=self.search_query
        )

        if not users:
            box.add_widget(MDLabel(
                text="No user accounts match the selected criteria.",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.45, 0.45, 0.45, 1),
                size_hint_y=None,
                height=dp(60)
            ))
            return

        cards = []
        for u in users:
            card = self._create_user_card(u)
            box.add_widget(card)
            cards.append(card)

        stagger_fade_in(cards, step=0.04, duration=0.22)

    def _create_user_card(self, u):
        role_color = ROLE_COLORS.get(u["user_type"].lower(), (0.2, 0.5, 0.2, 1))
        is_active = u["is_active"]
        status_text = "Active" if is_active else "Suspended"
        status_bg = (0.85, 0.95, 0.85, 1) if is_active else (0.98, 0.88, 0.88, 1)
        status_fg = (0.15, 0.55, 0.20, 1) if is_active else (0.85, 0.2, 0.2, 1)

        card = MDCard(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(6),
            size_hint_y=None,
            height=dp(140),
            radius=[10, 10, 10, 10],
            md_bg_color=(1, 1, 1, 1),
            elevation=1
        )

        # Row 1: Name + Role badge + Status badge
        top_row = MDBoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(28))
        name_label = MDLabel(
            text=u['full_name'],
            bold=True,
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=(0.1, 0.1, 0.1, 1)
        )
        role_badge = MDCard(
            size_hint=(None, None), size=(dp(88), dp(22)),
            radius=[5, 5, 5, 5], elevation=0, md_bg_color=role_color, padding=dp(2)
        )
        role_badge.add_widget(MDLabel(
            text=u['user_type'].capitalize(), halign="center",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(1, 1, 1, 1)
        ))
        status_badge = MDCard(
            size_hint=(None, None), size=(dp(70), dp(22)),
            radius=[5, 5, 5, 5], elevation=0, md_bg_color=status_bg, padding=dp(2)
        )
        status_badge.add_widget(MDLabel(
            text=status_text, halign="center",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=status_fg
        ))
        top_row.add_widget(name_label)
        top_row.add_widget(role_badge)
        top_row.add_widget(status_badge)

        # Row 2: Email + District
        details_label = MDLabel(
            text=f"{u['email']}   •   {u['district']}",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.4, 0.4, 0.4, 1),
            size_hint_y=None,
            height=dp(20)
        )

        # Row 3: Action buttons
        action_row = MDBoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(36))
        toggle_btn = MDRaisedButton(
            text="Suspend" if is_active else "Activate",
            size_hint_x=0.36, _radius=6, elevation=0,
            md_bg_color=(0.95, 0.85, 0.85, 1) if is_active else (0.85, 0.95, 0.85, 1),
            text_color=(0.8, 0.15, 0.15, 1) if is_active else (0.15, 0.55, 0.2, 1),
            on_release=lambda x, uid=u["user_id"]: self.toggle_user_status(uid)
        )
        role_btn = MDRaisedButton(
            text="Role ▾", size_hint_x=0.32, _radius=6, elevation=0,
            md_bg_color=(0.92, 0.95, 0.98, 1), text_color=(0.15, 0.45, 0.8, 1),
            on_release=lambda btn_inst, uid=u["user_id"], cr=u["user_type"]: self.open_role_change_menu(btn_inst, uid, cr)
        )
        delete_btn = MDRaisedButton(
            text="Delete", size_hint_x=0.32, _radius=6, elevation=0,
            md_bg_color=(0.98, 0.9, 0.9, 1), text_color=(0.85, 0.2, 0.2, 1),
            on_release=lambda x, uid=u["user_id"], em=u["email"]: self.confirm_delete_user(uid, em)
        )
        action_row.add_widget(toggle_btn)
        action_row.add_widget(role_btn)
        action_row.add_widget(delete_btn)

        card.add_widget(top_row)
        card.add_widget(details_label)
        card.add_widget(action_row)
        return card

    # ── USER MANAGEMENT ACTIONS ───────────────────────────────────────────────
    def toggle_user_status(self, user_id):
        if self._is_current_user(user_id):
            show_snackbar("You cannot suspend your own admin account.")
            return
        success, msg = toggle_user_status_by_admin(user_id)
        show_snackbar(msg)
        if success:
            self.load_users()

    def _is_current_user(self, user_id):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        return app.current_user and app.current_user.get("user_id") == user_id

    def open_role_change_menu(self, caller, user_id, current_role):
        if self._is_current_user(user_id):
            show_snackbar("You cannot change your own admin role.")
            return
        items = [
            {
                "text": f"{'✓ ' if r == current_role else ''}{r.capitalize()}",
                "viewclass": "OneLineListItem",
                "on_release": lambda *_, r=r: self.change_user_role(user_id, r),
            }
            for r in ALL_ROLES
        ]
        self.role_menu = MDDropdownMenu(caller=caller, items=items, width_mult=3)
        self.role_menu.open()

    def change_user_role(self, user_id, new_role):
        if hasattr(self, 'role_menu') and self.role_menu:
            self.role_menu.dismiss()
        success, msg = update_user_role_by_admin(user_id, new_role)
        show_snackbar(msg)
        if success:
            self.load_users()

    def confirm_delete_user(self, user_id, email):
        if self._is_current_user(user_id):
            show_snackbar("You cannot delete your own admin account.")
            return
        self.dialog = MDDialog(
            title="Delete User Account",
            text=f"Permanently delete '{email}'? This cannot be undone.",
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=(0.5, 0.5, 0.5, 1),
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="DELETE",
                    md_bg_color=(0.85, 0.2, 0.2, 1),
                    text_color=(1, 1, 1, 1),
                    on_release=lambda x, uid=user_id: self.execute_delete_user(uid)
                ),
            ],
        )
        self.dialog.open()

    def execute_delete_user(self, user_id):
        if self.dialog:
            self.dialog.dismiss()
        success, msg = delete_user_by_admin(user_id)
        show_snackbar(msg)
        if success:
            self.load_users()

    # ── CREATE ACCOUNT FORM ───────────────────────────────────────────────────
    def toggle_create_form(self):
        if self.create_form_open:
            self.close_create_form()
        else:
            self.open_create_form()

    def open_create_form(self):
        self.create_form_open = True
        self.ids.create_btn.text = "✕ Cancel"
        card = self.ids.create_user_card
        card.opacity = 1
        card.height = dp(320)
        bounce_scale(card)
        self.regions = get_all_regions()

    def close_create_form(self):
        self.create_form_open = False
        self.ids.create_btn.text = "+ Create Account"
        card = self.ids.create_user_card
        card.height = 0
        card.opacity = 0
        self.ids.create_user_error.text = ""
        self.new_user_role = "policymaker"
        self.new_user_region_id = None
        self.ids.new_role_btn.text = "Role: Policymaker ▾"
        self.ids.new_region_btn.text = "Select District ▾"
        self.ids.new_first_name.text = ""
        self.ids.new_last_name.text = ""
        self.ids.new_email.text = ""
        self.ids.new_password.text = ""

    def open_create_role_menu(self):
        items = [
            {
                "text": r.capitalize(),
                "viewclass": "OneLineListItem",
                "on_release": lambda *_, r=r: self.pick_create_role(r),
            }
            for r in ALL_ROLES
        ]
        self.create_role_menu = MDDropdownMenu(caller=self.ids.new_role_btn, items=items, width_mult=3)
        self.create_role_menu.open()

    def pick_create_role(self, role):
        self.new_user_role = role
        self.ids.new_role_btn.text = f"Role: {role.capitalize()} ▾"
        if hasattr(self, 'create_role_menu') and self.create_role_menu:
            self.create_role_menu.dismiss()

    def open_create_region_menu(self):
        if not hasattr(self, 'regions') or not self.regions:
            self.regions = get_all_regions()
        items = [
            {
                "text": district,
                "viewclass": "OneLineListItem",
                "on_release": lambda *_, rid=rid, d=district: self.pick_create_region(rid, d),
            }
            for rid, name, district in self.regions
        ]
        self.create_region_menu = MDDropdownMenu(caller=self.ids.new_region_btn, items=items, width_mult=3)
        self.create_region_menu.open()

    def pick_create_region(self, region_id, district):
        self.new_user_region_id = region_id
        self.ids.new_region_btn.text = f"District: {district} ▾"
        if hasattr(self, 'create_region_menu') and self.create_region_menu:
            self.create_region_menu.dismiss()

    def submit_new_user(self):
        self.ids.create_user_error.text = ""
        fn = self.ids.new_first_name.text.strip()
        ln = self.ids.new_last_name.text.strip()
        email = self.ids.new_email.text.strip()
        password = self.ids.new_password.text

        if not all([fn, ln, email, password, self.new_user_region_id]):
            self.ids.create_user_error.text = "Please fill in all fields and select a district."
            return
        if not is_valid_email_format(email):
            self.ids.create_user_error.text = "Please enter a valid email address."
            return
        if not is_password_acceptable(password):
            self.ids.create_user_error.text = "Password too weak (min 8 chars, UPPER, number & symbol)."
            return

        success, msg = admin_create_user(
            email=email, password=password,
            first_name=fn, last_name=ln,
            user_type=self.new_user_role,
            region_id=self.new_user_region_id
        )
        if not success:
            self.ids.create_user_error.text = msg
            return

        show_snackbar(msg)
        self.close_create_form()
        self.load_users()
        self._update_banner()
