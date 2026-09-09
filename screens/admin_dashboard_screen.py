"""
Admin Dashboard Screen – Clean, Robust User Management Interface.
Allows Admin to:
1. View, search, and filter all registered accounts by role.
2. Toggle active/suspended status, change roles, or delete users.
3. Quick navigate to dedicated "Create User Account" and "Ratings & Feedback" screens.
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
    delete_user_by_admin, get_average_rating
)
from database.auth_service import ALL_ROLES
from utils.animations import stagger_fade_in

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

        # ── TOP APP BAR ──────────────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(54)
            padding: dp(14), dp(6), dp(8), dp(6)
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

            MDLabel:
                text: "Admin Console"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.12, 0.12, 0.12, 1

            MDIconButton:
                icon: "account-plus"
                theme_text_color: "Custom"
                text_color: 0.20, 0.55, 0.28, 1
                tooltip_text: "Create User"
                on_release: root.go_to_create_user()

            MDIconButton:
                icon: "comment-text-outline"
                theme_text_color: "Custom"
                text_color: 0.20, 0.55, 0.28, 1
                tooltip_text: "Feedback & Reviews"
                on_release: root.go_to_feedback()

            MDIconButton:
                icon: "logout"
                theme_text_color: "Custom"
                text_color: 0.78, 0.18, 0.18, 1
                tooltip_text: "Logout"
                on_release: root.logout()

        # ── STATS & ACTIONS BANNER ──────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(72)
            padding: dp(14), dp(8), dp(14), dp(8)
            spacing: dp(8)
            canvas.before:
                Color:
                    rgba: 0.20, 0.55, 0.28, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            # Left: counters
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(2)
                size_hint_x: 0.48
                pos_hint: {"center_y": 0.5}

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
                    text_color: 0.82, 0.94, 0.84, 1

            # Right: Action Buttons
            MDBoxLayout:
                orientation: "horizontal"
                spacing: dp(6)
                size_hint_x: 0.52
                pos_hint: {"center_y": 0.5}

                MDRaisedButton:
                    id: create_user_nav_btn
                    text: "+ New User"
                    size_hint: None, None
                    size: dp(94), dp(36)
                    _radius: 8
                    elevation: 0
                    md_bg_color: 1, 1, 1, 0.25
                    text_color: 1, 1, 1, 1
                    on_release: root.go_to_create_user()

                MDRaisedButton:
                    id: feedback_nav_btn
                    text: "Feedback"
                    size_hint: None, None
                    size: dp(86), dp(36)
                    _radius: 8
                    elevation: 0
                    md_bg_color: 1, 1, 1, 0.20
                    text_color: 1, 1, 1, 1
                    on_release: root.go_to_feedback()

        # ── SEARCH + ACTION ROW ─────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(54)
            padding: dp(12), dp(6), dp(12), dp(6)
            spacing: dp(8)
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            MDTextField:
                id: user_search_field
                hint_text: "Search by name or email"
                icon_left: "magnify"
                mode: "rectangle"
                line_color_focus: 0.20, 0.55, 0.28, 1
                on_text: root.on_search_text_changed(self.text)

            MDRaisedButton:
                text: "+ Create"
                md_bg_color: 0.20, 0.55, 0.28, 1
                text_color: 1, 1, 1, 1
                _radius: 8
                size_hint_x: None
                width: dp(82)
                elevation: 0
                on_release: root.go_to_create_user()

        # ── ROLE FILTER CHIPS ───────────────────────────────────────────
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

        # ── SCROLLABLE LIST AREA ────────────────────────────────────────
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

                # Section header
                MDBoxLayout:
                    size_hint_y: None
                    height: dp(34)
                    padding: dp(14), dp(6), dp(14), dp(4)
                    MDLabel:
                        id: user_section_label
                        text: "All Users"
                        font_style: "Overline"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.45, 0.45, 0.45, 1
                        halign: "left"

                # Users list
                MDBoxLayout:
                    id: users_list_box
                    orientation: "vertical"
                    spacing: dp(8)
                    padding: dp(10), 0, dp(10), dp(24)
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
    dialog = None

    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if not app.current_user or app.current_user.get("user_type") != "admin":
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            return
        self._setup_role_filter_chips()
        self.load_users()
        self._update_banner()

    def _update_banner(self):
        try:
            users = get_all_users_for_admin()
            self.ids.user_count_label.text = f"{len(users)} Users"
        except Exception:
            self.ids.user_count_label.text = "User Accounts"
        try:
            avg, count = get_average_rating()
            if avg and count:
                self.ids.avg_rating_banner.text = f"Avg {avg}/5 ({count} rev)"
            else:
                self.ids.avg_rating_banner.text = "No ratings yet"
        except Exception:
            self.ids.avg_rating_banner.text = ""

    def go_to_create_user(self):
        try:
            if self.manager:
                self.manager.transition.direction = "left"
                self.manager.current = "admin_create_user"
        except Exception as e:
            print(f"[Admin] go_to_create_user error: {e}")
            show_snackbar(f"Navigation error: {e}")

    def go_to_feedback(self):
        try:
            if self.manager:
                self.manager.transition.direction = "left"
                self.manager.current = "admin_feedback"
        except Exception as e:
            print(f"[Admin] go_to_feedback error: {e}")
            show_snackbar(f"Navigation error: {e}")

    def logout(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        app.current_user = None
        if self.manager:
            self.manager.transition.direction = "right"
            self.manager.current = "login"
        show_snackbar("Logged out successfully.")

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

    def load_users(self):
        box = self.ids.users_list_box
        box.clear_widgets()

        try:
            users = get_all_users_for_admin(
                role_filter=self.selected_role_filter,
                search_query=self.search_query
            )
        except Exception as e:
            print(f"[Admin] load_users error: {e}")
            users = []

        role_display = "All Users" if self.selected_role_filter == "all" \
            else f"{self.selected_role_filter.capitalize()}s"
        self.ids.user_section_label.text = f"{role_display}  ({len(users)})"

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
        stagger_fade_in(cards, step=0.03, duration=0.20)

    def _build_user_card(self, u):
        role_key   = u.get("user_type", "").lower()
        meta       = ROLE_META.get(role_key, {"color": (0.4, 0.4, 0.4, 1), "label": role_key.capitalize()})
        is_active  = u.get("is_active", True)

        card = MDCard(
            orientation="vertical",
            padding=[dp(14), dp(12), dp(14), dp(12)],
            spacing=dp(8),
            size_hint_y=None,
            height=dp(132),
            radius=[10, 10, 10, 10],
            md_bg_color=(1, 1, 1, 1),
            elevation=1
        )

        # Row 1: Name + Role + Status
        row1 = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(26))
        name_lbl = MDLabel(
            text=u.get("full_name", "User"),
            bold=True,
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=(0.10, 0.10, 0.10, 1),
            pos_hint={"center_y": 0.5}
        )
        role_pill = MDCard(
            size_hint=(None, None), size=(dp(58), dp(22)),
            radius=[5, 5, 5, 5], elevation=0,
            md_bg_color=meta["color"], padding=[dp(4), dp(2), dp(4), dp(2)],
            pos_hint={"center_y": 0.5}
        )
        role_pill.add_widget(MDLabel(
            text=meta["label"], halign="center", valign="center",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(1, 1, 1, 1)
        ))

        status_color = (0.15, 0.60, 0.25, 1) if is_active else (0.78, 0.18, 0.18, 1)
        status_bg    = (0.88, 0.97, 0.89, 1) if is_active else (0.98, 0.88, 0.88, 1)
        status_pill  = MDCard(
            size_hint=(None, None), size=(dp(72), dp(22)),
            radius=[5, 5, 5, 5], elevation=0,
            md_bg_color=status_bg, padding=[dp(4), dp(2), dp(4), dp(2)],
            pos_hint={"center_y": 0.5}
        )
        status_pill.add_widget(MDLabel(
            text="Active" if is_active else "Suspended",
            halign="center", valign="center", font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=status_color
        ))

        row1.add_widget(name_lbl)
        row1.add_widget(role_pill)
        row1.add_widget(status_pill)

        # Row 2: Email + District
        row2 = MDLabel(
            text=f"{u.get('email', '')}  |  {u.get('district', '')}",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.50, 0.50, 0.50, 1),
            size_hint_y=None,
            height=dp(18)
        )

        # Row 3: Action buttons
        row3 = MDBoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(34))
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
            text=f"Permanently delete account '{email}'?\\nThis action cannot be undone.",
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
