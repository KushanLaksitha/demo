"""
Admin Feedback & Ratings Screen – Clean, Spacious, Professional Card Design.
"""
from datetime import datetime
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from utils.layout_helpers import show_snackbar

from database.data_service import (
    get_all_feedback_for_admin, mark_feedback_reviewed, get_average_rating
)
from utils.animations import stagger_fade_in

KV = """
<AdminFeedbackScreen>:
    canvas.before:
        Color:
            rgba: 0.94, 0.96, 0.94, 1
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
                text: "Ratings & Feedback"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.12, 0.12, 0.12, 1

            MDIconButton:
                icon: "logout"
                theme_text_color: "Custom"
                text_color: 0.78, 0.18, 0.18, 1
                on_release: root.logout()

        # ── Rating Scorecard Banner ─────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(76)
            padding: dp(16), dp(10), dp(12), dp(10)
            spacing: dp(12)
            canvas.before:
                Color:
                    rgba: 0.20, 0.55, 0.28, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            # Left: Big Rating Number & Stars
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(2)
                size_hint_x: 0.62

                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: dp(6)
                    size_hint_y: None
                    height: dp(32)

                    MDLabel:
                        id: avg_score_text
                        text: "3.5"
                        font_style: "H5"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        size_hint_x: None
                        width: dp(46)

                    MDBoxLayout:
                        id: banner_stars_box
                        orientation: "horizontal"
                        spacing: dp(2)
                        size_hint_y: None
                        height: dp(24)
                        pos_hint: {"center_y": 0.5}

                MDLabel:
                    id: rating_subtext
                    text: "Average rating from user reviews"
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.82, 0.94, 0.84, 1
                    size_hint_y: None
                    height: dp(18)

            # Right: Pending & Refresh
            MDBoxLayout:
                orientation: "horizontal"
                spacing: dp(4)
                size_hint_x: 0.38
                pos_hint: {"center_y": 0.5}

                MDLabel:
                    id: pending_count_label
                    text: "2 Pending"
                    font_style: "Caption"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 0.92, 0.65, 1
                    halign: "right"
                    valign: "center"

                MDIconButton:
                    icon: "refresh"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    on_release: root.load_feedback()

        # ── Interactive Filter Chips ────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(42)
            padding: dp(12), dp(5), dp(12), dp(5)
            spacing: dp(8)
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
                Color:
                    rgba: 0.90, 0.90, 0.90, 1
                Line:
                    points: self.x, self.y, self.x + self.width, self.y
                    width: 1

            MDRaisedButton:
                id: filter_all_btn
                text: "All (4)"
                size_hint: None, None
                height: dp(30)
                _radius: 15
                elevation: 0
                md_bg_color: 0.20, 0.55, 0.28, 1
                text_color: 1, 1, 1, 1
                on_release: root.set_filter("all")

            MDRaisedButton:
                id: filter_new_btn
                text: "New (2)"
                size_hint: None, None
                height: dp(30)
                _radius: 15
                elevation: 0
                md_bg_color: 0.92, 0.95, 0.92, 1
                text_color: 0.25, 0.40, 0.25, 1
                on_release: root.set_filter("new")

            MDRaisedButton:
                id: filter_reviewed_btn
                text: "Reviewed (2)"
                size_hint: None, None
                height: dp(30)
                _radius: 15
                elevation: 0
                md_bg_color: 0.92, 0.95, 0.92, 1
                text_color: 0.25, 0.40, 0.25, 1
                on_release: root.set_filter("reviewed")

        # ── Scrollable Feedback Cards List ──────────────────────────────
        MDScrollView:
            do_scroll_y: True
            do_scroll_x: False
            bar_width: 3
            bar_color: 0.20, 0.55, 0.28, 0.5

            MDBoxLayout:
                id: feedback_list_box
                orientation: "vertical"
                spacing: dp(14)
                padding: dp(12), dp(12), dp(12), dp(30)
                size_hint_y: None
                height: self.minimum_height
"""

Builder.load_string(KV)


class AdminFeedbackScreen(Screen):
    current_filter = "all"
    cached_items = []

    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if not app.current_user:
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            return
        self.load_feedback()

    def set_filter(self, filter_name):
        self.current_filter = filter_name
        # Update chip styles
        chips = {
            "all": self.ids.filter_all_btn,
            "new": self.ids.filter_new_btn,
            "reviewed": self.ids.filter_reviewed_btn,
        }
        for name, btn in chips.items():
            if name == filter_name:
                btn.md_bg_color = (0.20, 0.55, 0.28, 1)
                btn.text_color = (1, 1, 1, 1)
            else:
                btn.md_bg_color = (0.92, 0.95, 0.92, 1)
                btn.text_color = (0.25, 0.40, 0.25, 1)
        self.render_cards()

    def load_feedback(self):
        # 1. Update rating scorecard
        try:
            avg, count = get_average_rating()
        except Exception as e:
            print(f"[AdminFeedback] get_average_rating error: {e}")
            avg, count = None, 0

        score_val = float(avg) if avg else 0.0
        self.ids.avg_score_text.text = f"{score_val:.1f}" if count > 0 else "--"
        self.ids.rating_subtext.text = (
            f"Based on {count} user review{'s' if count != 1 else ''}"
        ) if count > 0 else "No user reviews yet"

        # Update banner stars
        stars_box = self.ids.banner_stars_box
        stars_box.clear_widgets()
        full_stars = int(round(score_val))
        for i in range(1, 6):
            icon_name = "star" if i <= full_stars else "star-outline"
            icon_color = (1, 0.85, 0.25, 1) if i <= full_stars else (0.80, 0.92, 0.82, 0.7)
            stars_box.add_widget(MDIcon(
                icon=icon_name,
                theme_text_color="Custom",
                text_color=icon_color,
                size_hint=(None, None),
                size=(dp(20), dp(20)),
            ))

        # 2. Fetch feedback items
        try:
            self.cached_items = get_all_feedback_for_admin()
        except Exception as e:
            print(f"[AdminFeedback] get_all_feedback error: {e}")
            self.cached_items = []
            show_snackbar(f"Error loading feedback: {e}")

        # 3. Update filter chip counters
        total = len(self.cached_items)
        reviewed_cnt = sum(1 for f in self.cached_items if f.get("status") == "reviewed")
        new_cnt = total - reviewed_cnt

        self.ids.filter_all_btn.text = f"All ({total})"
        self.ids.filter_new_btn.text = f"New ({new_cnt})"
        self.ids.filter_reviewed_btn.text = f"Reviewed ({reviewed_cnt})"
        self.ids.pending_count_label.text = f"{new_cnt} Pending" if new_cnt > 0 else "All Reviewed"

        self.render_cards()

    def render_cards(self):
        box = self.ids.feedback_list_box
        box.clear_widgets()

        # Filter items
        if self.current_filter == "new":
            items = [f for f in self.cached_items if f.get("status") != "reviewed"]
        elif self.current_filter == "reviewed":
            items = [f for f in self.cached_items if f.get("status") == "reviewed"]
        else:
            items = self.cached_items

        if not items:
            placeholder = MDCard(
                size_hint_y=None,
                height=dp(100),
                radius=[12, 12, 12, 12],
                md_bg_color=(1, 1, 1, 1),
                elevation=1,
                padding=dp(20)
            )
            placeholder.add_widget(MDLabel(
                text="No feedback found in this category.",
                halign="center",
                font_style="Subtitle2",
                theme_text_color="Custom",
                text_color=(0.50, 0.50, 0.50, 1)
            ))
            box.add_widget(placeholder)
            return

        cards = []
        for fb in items:
            try:
                card = self._build_feedback_card(fb)
                box.add_widget(card)
                cards.append(card)
            except Exception as e:
                print(f"[AdminFeedback] Error building card: {e}")

        if cards:
            stagger_fade_in(cards, step=0.03, duration=0.20)

    def _build_feedback_card(self, fb):
        reviewed = fb.get("status") == "reviewed"
        rating_val = int(fb.get("rating") or 0)
        msg_text = (fb.get("message") or "").strip() or "No message provided."

        # Estimate text height accurately
        lines = msg_text.count('\n') + max(1, len(msg_text) // 34)
        msg_height = max(dp(28), dp(lines * 20))

        # Calculate exact total card height:
        # padding (14 top + 14 bottom = 28)
        # row1 header: dp(30)
        # row2 stars: dp(24)
        # row3 message card: msg_height + dp(18) padding
        # row4 timestamp: dp(20)
        # row5 button (if not reviewed): dp(38) + dp(8)
        # inner spacings: 4 * dp(8) = dp(32)
        base_h = dp(28) + dp(30) + dp(24) + (msg_height + dp(18)) + dp(20) + dp(32)
        if not reviewed:
            base_h += dp(46)

        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=base_h,
            radius=[12, 12, 12, 12],
            md_bg_color=(1, 1, 1, 1),
            elevation=1,
            padding=[dp(16), dp(14), dp(16), dp(14)],
            spacing=dp(8)
        )

        # ── Row 1: User Name + Status Badge ─────────────────────────
        row1 = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(30),
            spacing=dp(8)
        )

        user_icon = MDIcon(
            icon="account-circle",
            theme_text_color="Custom",
            text_color=(0.20, 0.55, 0.28, 1),
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={"center_y": 0.5}
        )

        from_label = MDLabel(
            text=fb.get("from", "User"),
            bold=True,
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=(0.10, 0.10, 0.10, 1),
            pos_hint={"center_y": 0.5}
        )

        status_bg = (0.88, 0.97, 0.89, 1) if reviewed else (0.98, 0.92, 0.80, 1)
        status_fg = (0.15, 0.55, 0.22, 1) if reviewed else (0.75, 0.45, 0.05, 1)
        status_badge = MDCard(
            size_hint=(None, None),
            size=(dp(78), dp(24)),
            radius=[6, 6, 6, 6],
            elevation=0,
            md_bg_color=status_bg,
            padding=[dp(6), dp(2), dp(6), dp(2)],
            pos_hint={"center_y": 0.5}
        )
        status_badge.add_widget(MDLabel(
            text="Reviewed" if reviewed else "New",
            halign="center",
            valign="center",
            font_style="Caption",
            bold=True,
            theme_text_color="Custom",
            text_color=status_fg
        ))

        row1.add_widget(user_icon)
        row1.add_widget(from_label)
        row1.add_widget(status_badge)

        # ── Row 2: 5 Stars + Score Text ─────────────────────────────
        row2 = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(24),
            spacing=dp(3)
        )
        for i in range(1, 6):
            star_type = "star" if i <= rating_val else "star-outline"
            star_col = (0.95, 0.70, 0.10, 1) if i <= rating_val else (0.80, 0.80, 0.80, 1)
            row2.add_widget(MDIcon(
                icon=star_type,
                theme_text_color="Custom",
                text_color=star_col,
                size_hint=(None, None),
                size=(dp(18), dp(18)),
                pos_hint={"center_y": 0.5}
            ))

        rating_num = MDLabel(
            text=f"  {rating_val} / 5",
            font_style="Caption",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.40, 0.40, 0.40, 1),
            pos_hint={"center_y": 0.5}
        )
        row2.add_widget(rating_num)

        # ── Row 3: Message Card (Soft green tint) ───────────────────
        msg_card = MDCard(
            size_hint_y=None,
            height=msg_height + dp(18),
            radius=[8, 8, 8, 8],
            elevation=0,
            md_bg_color=(0.96, 0.98, 0.96, 1),
            padding=[dp(12), dp(8), dp(12), dp(8)]
        )
        msg_label = MDLabel(
            text=msg_text,
            font_style="Body2",
            theme_text_color="Custom",
            text_color=(0.18, 0.18, 0.18, 1)
        )
        msg_card.add_widget(msg_label)

        # ── Row 4: Timestamp with Clock Icon ────────────────────────
        row4 = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(20),
            spacing=dp(5)
        )
        clock_icon = MDIcon(
            icon="clock-outline",
            theme_text_color="Custom",
            text_color=(0.55, 0.55, 0.55, 1),
            size_hint=(None, None),
            size=(dp(16), dp(16)),
            pos_hint={"center_y": 0.5}
        )
        submitted = fb.get("submitted_at")
        if hasattr(submitted, "strftime"):
            date_str = submitted.strftime("%d %b %Y, %I:%M %p")
        elif submitted:
            date_str = str(submitted)
        else:
            date_str = "Recent"

        date_label = MDLabel(
            text=date_str,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.55, 0.55, 0.55, 1),
            pos_hint={"center_y": 0.5}
        )
        row4.add_widget(clock_icon)
        row4.add_widget(date_label)

        card.add_widget(row1)
        card.add_widget(row2)
        card.add_widget(msg_card)
        card.add_widget(row4)

        # ── Row 5: Action Button (only if not reviewed) ─────────────
        if not reviewed:
            action_row = MDBoxLayout(
                size_hint_y=None,
                height=dp(38),
                spacing=dp(6)
            )
            mark_btn = MDRaisedButton(
                text="MARK AS REVIEWED",
                md_bg_color=(0.20, 0.55, 0.28, 1),
                text_color=(1, 1, 1, 1),
                _radius=8,
                elevation=0,
                size_hint_x=1,
                size_hint_y=None,
                height=dp(36),
                on_release=lambda x, fid=fb["id"]: self._mark_reviewed(fid)
            )
            action_row.add_widget(mark_btn)
            card.add_widget(action_row)

        return card

    def _mark_reviewed(self, feedback_id):
        try:
            mark_feedback_reviewed(feedback_id)
            show_snackbar("Feedback marked as reviewed.")
            self.load_feedback()
        except Exception as e:
            print(f"[AdminFeedback] mark_feedback error: {e}")
            show_snackbar(f"Error: {e}")

    def go_to_admin_dashboard(self):
        try:
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "admin_dashboard"
        except Exception as e:
            print(f"[AdminFeedback] go_to_admin_dashboard error: {e}")

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
            print(f"[AdminFeedback] logout error: {e}")
