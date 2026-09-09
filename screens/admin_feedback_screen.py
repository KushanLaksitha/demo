"""
Admin Feedback & Ratings Screen – Clean, Modern, Bug-Free Design.
"""
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from utils.layout_helpers import show_snackbar

from database.data_service import (
    get_all_feedback_for_admin, mark_feedback_reviewed, get_average_rating
)
from database.auth_service import validate_admin_session
from utils.animations import stagger_fade_in

KV = """
<AdminFeedbackScreen>:
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
            height: dp(56)
            padding: dp(8), dp(8), dp(8), dp(8)
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
                text_color: 0.1, 0.1, 0.1, 1

            MDIconButton:
                icon: "logout"
                theme_text_color: "Custom"
                text_color: 0.78, 0.18, 0.18, 1
                on_release: root.logout()

        # ── Summary Banner (Green) ──────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(72)
            padding: dp(14), dp(10), dp(14), dp(10)
            spacing: dp(10)
            canvas.before:
                Color:
                    rgba: 0.20, 0.55, 0.28, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(3)
                MDLabel:
                    id: avg_rating_label
                    text: "Average Rating: Loading..."
                    font_style: "Subtitle1"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1

                MDLabel:
                    id: rating_subtext
                    text: "Reviewing feedback submissions"
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.80, 0.94, 0.82, 1

            MDIconButton:
                icon: "refresh"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                on_release: root.load_feedback()

        # ── Counter Subheader ───────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(36)
            padding: dp(14), dp(6), dp(14), dp(6)
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
                Color:
                    rgba: 0.92, 0.92, 0.92, 1
                Line:
                    points: self.x, self.y, self.x + self.width, self.y
                    width: 1

            MDLabel:
                id: entry_count_label
                text: "All Submissions"
                font_style: "Overline"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.45, 0.45, 0.45, 1

        # ── Scrollable List ─────────────────────────────────────────────
        MDScrollView:
            do_scroll_y: True
            do_scroll_x: False
            bar_width: 2
            bar_color: 0.20, 0.55, 0.28, 0.45

            MDBoxLayout:
                id: feedback_list_box
                orientation: "vertical"
                spacing: dp(8)
                padding: dp(10), dp(10), dp(10), dp(20)
                size_hint_y: None
                height: self.minimum_height
"""

Builder.load_string(KV)


class AdminFeedbackScreen(Screen):

    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if not app.current_user or not validate_admin_session(app.current_user.get("user_id")):
            app.current_user = None
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            return
        self.load_feedback()

    def load_feedback(self):
        try:
            avg, count = get_average_rating()
        except Exception:
            avg, count = None, 0

        if avg is None or count == 0:
            self.ids.avg_rating_label.text = "Average: No ratings yet"
            self.ids.rating_subtext.text = "No reviews submitted by users"
        else:
            self.ids.avg_rating_label.text = f"Average: {avg} / 5.0 Stars"
            self.ids.rating_subtext.text = f"Based on {count} user submission{'s' if count != 1 else ''}"

        try:
            items = get_all_feedback_for_admin()
        except Exception as e:
            items = []
            show_snackbar(f"Error loading feedback: {e}")

        box = self.ids.feedback_list_box
        box.clear_widgets()

        total = len(items)
        reviewed_count = sum(1 for f in items if f["status"] == "reviewed")
        new_count = total - reviewed_count

        self.ids.entry_count_label.text = (
            f"SUBMISSIONS ({total})  |  REVIEWED ({reviewed_count})  |  NEW ({new_count})"
        )

        if not items:
            placeholder = MDCard(
                size_hint_y=None,
                height=dp(80),
                radius=[10, 10, 10, 10],
                md_bg_color=(1, 1, 1, 1),
                elevation=0,
                padding=dp(16)
            )
            placeholder.add_widget(MDLabel(
                text="No feedback submitted yet.",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.55, 0.55, 0.55, 1)
            ))
            box.add_widget(placeholder)
            return

        cards = []
        for fb in items:
            card = self._build_feedback_card(fb)
            box.add_widget(card)
            cards.append(card)

        stagger_fade_in(cards, step=0.04, duration=0.22)

    def _build_feedback_card(self, fb):
        reviewed = fb["status"] == "reviewed"
        rating_val = fb.get("rating") or 0

        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(160) if not reviewed else dp(120),
            radius=[10, 10, 10, 10],
            md_bg_color=(1, 1, 1, 1),
            elevation=1,
            padding=dp(12),
            spacing=dp(6)
        )

        # ── Row 1: From + Status Badge ──────────────────────────────
        row1 = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(26),
            spacing=dp(8)
        )

        from_label = MDLabel(
            text=f"From: {fb.get('from', 'User')}",
            bold=True,
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=(0.12, 0.12, 0.12, 1)
        )

        status_badge = MDCard(
            size_hint=(None, None),
            size=(dp(74), dp(22)),
            radius=[5, 5, 5, 5],
            elevation=0,
            md_bg_color=(0.88, 0.97, 0.89, 1) if reviewed else (0.98, 0.92, 0.80, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )
        status_badge.add_widget(MDLabel(
            text="Reviewed" if reviewed else "New",
            halign="center",
            font_style="Caption",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.15, 0.55, 0.22, 1) if reviewed else (0.75, 0.45, 0.05, 1)
        ))

        row1.add_widget(from_label)
        row1.add_widget(status_badge)

        # ── Row 2: Rating Display ───────────────────────────────────
        row2 = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(22),
            spacing=dp(4)
        )
        star_icon = MDIconButton(
            icon="star",
            theme_text_color="Custom",
            text_color=(0.95, 0.70, 0.10, 1),
            size_hint=(None, None),
            size=(dp(22), dp(22)),
            user_font_size="16sp"
        )
        rating_text = MDLabel(
            text=f"Score: {rating_val} / 5",
            font_style="Caption",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.3, 0.3, 0.3, 1)
        )
        row2.add_widget(star_icon)
        row2.add_widget(rating_text)

        # ── Row 3: Message Text ─────────────────────────────────────
        msg_text = (fb.get("message") or "").strip() or "No text feedback provided."
        msg_label = MDLabel(
            text=msg_text,
            font_style="Body2",
            theme_text_color="Custom",
            text_color=(0.20, 0.20, 0.20, 1),
            size_hint_y=None,
            height=dp(36)
        )

        # ── Row 4: Submitted Date ───────────────────────────────────
        submitted = fb.get("submitted_at")
        date_str = submitted.strftime("%d %b %Y, %I:%M %p") if submitted else "Recent"
        meta_label = MDLabel(
            text=date_str,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.55, 0.55, 0.55, 1),
            size_hint_y=None,
            height=dp(18)
        )

        card.add_widget(row1)
        card.add_widget(row2)
        card.add_widget(msg_label)
        card.add_widget(meta_label)

        # ── Row 5: Action Button (for unreviewed) ───────────────────
        if not reviewed:
            action_row = MDBoxLayout(
                size_hint_y=None,
                height=dp(34),
                spacing=dp(6)
            )
            mark_btn = MDRaisedButton(
                text="Mark as Reviewed",
                md_bg_color=(0.20, 0.55, 0.28, 1),
                text_color=(1, 1, 1, 1),
                _radius=6,
                elevation=0,
                size_hint_x=1,
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
            show_snackbar(f"Error: {e}")

    def go_to_admin_dashboard(self):
        if self.manager:
            self.manager.transition.direction = "right"
            self.manager.current = "admin_dashboard"

    def logout(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        app.current_user = None
        if self.manager:
            self.manager.transition.direction = "right"
            self.manager.current = "login"
        show_snackbar("Logged out successfully.")
