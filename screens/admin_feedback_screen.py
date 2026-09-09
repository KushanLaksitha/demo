"""
Admin Feedback & Ratings Screen
--------------------------------
A dedicated screen for the admin to review all user feedback and ratings.
Features:
  - Overall average rating summary card
  - Scrollable list of all feedback entries (newest first)
  - Mark-as-reviewed action per entry
  - Back to Admin Dashboard button
  - Logout button
"""
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from utils.layout_helpers import show_snackbar

from database.data_service import (
    get_all_feedback_for_admin, mark_feedback_reviewed, get_average_rating
)
from database.auth_service import validate_admin_session
from utils.animations import stagger_fade_in, fade_in

KV = """
<AdminFeedbackScreen>:
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
            padding: dp(6), dp(4), dp(12), dp(4)
            spacing: dp(4)
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: 0.25, 0.62, 0.30, 1
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
                text_color: 0.85, 0.2, 0.2, 1
                on_release: root.logout()

        # ── Summary Card ────────────────────────────────────────────────
        MDCard:
            id: summary_card
            size_hint_y: None
            height: dp(64)
            padding: dp(16), dp(12)
            spacing: dp(8)
            radius: [0, 0, 0, 0]
            elevation: 1
            md_bg_color: 0.15, 0.45, 0.85, 1

            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(2)

                MDLabel:
                    id: avg_rating_label
                    text: "Loading..."
                    font_style: "Subtitle1"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1

                MDLabel:
                    id: rating_subtext
                    text: ""
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.85, 0.92, 1, 1

        # ── Refresh Button Bar ──────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(36)
            padding: dp(12), dp(4)
            spacing: dp(8)

            MDLabel:
                id: entry_count_label
                text: ""
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.4, 0.4, 0.4, 1

            MDFlatButton:
                text: "Refresh"
                theme_text_color: "Custom"
                text_color: 0.25, 0.62, 0.30, 1
                size_hint_x: None
                width: dp(70)
                on_release: root.load_feedback()

        # ── Scrollable Feedback List ────────────────────────────────────
        MDScrollView:
            do_scroll_y: True
            do_scroll_x: False
            bar_width: 2
            bar_color: 0.25, 0.62, 0.30, 0.6

            MDBoxLayout:
                id: feedback_list_box
                orientation: "vertical"
                spacing: dp(8)
                padding: dp(12), dp(4), dp(12), dp(16)
                size_hint_y: None
                height: self.minimum_height
"""

Builder.load_string(KV)


def _stars(rating):
    """Convert numeric rating to star string."""
    if not rating:
        return "No rating"
    r = int(round(float(rating)))
    r = max(0, min(5, r))
    return "★" * r + "☆" * (5 - r)


def _status_color(status):
    return (0.85, 0.95, 0.85, 1) if status == "reviewed" else (0.93, 0.965, 0.93, 1)


def _status_text_color(status):
    return (0.15, 0.55, 0.20, 1) if status == "reviewed" else (0.25, 0.62, 0.30, 1)


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
        """Load and render all feedback entries."""
        # Update summary
        try:
            avg, count = get_average_rating()
        except Exception:
            avg, count = None, 0

        if avg is None or count == 0:
            self.ids.avg_rating_label.text = "No ratings yet"
            self.ids.rating_subtext.text = "No feedback submitted by users"
        else:
            stars = _stars(avg)
            self.ids.avg_rating_label.text = f"{stars}   {avg} / 5.0"
            self.ids.rating_subtext.text = f"Average across {count} submission{'s' if count != 1 else ''}"

        # Load entries
        try:
            items = get_all_feedback_for_admin()
        except Exception as e:
            items = []
            show_snackbar(f"Error loading feedback: {e}")

        box = self.ids.feedback_list_box
        box.clear_widgets()

        # Entry count label
        total = len(items)
        reviewed_count = sum(1 for f in items if f["status"] == "reviewed")
        self.ids.entry_count_label.text = (
            f"{total} total  •  {reviewed_count} reviewed  •  {total - reviewed_count} new"
        ) if total > 0 else "No feedback entries yet"

        if not items:
            placeholder = MDCard(
                size_hint_y=None,
                height=dp(80),
                radius=[12, 12, 12, 12],
                md_bg_color=(1, 1, 1, 1),
                elevation=0,
                padding=dp(16)
            )
            placeholder.add_widget(MDLabel(
                text="No feedback submitted yet.",
                halign="center",
                theme_text_color="Custom",
                text_color=(0.5, 0.5, 0.5, 1)
            ))
            box.add_widget(placeholder)
            return

        cards = []
        for fb in items:
            card = self._build_feedback_card(fb)
            box.add_widget(card)
            cards.append(card)

        stagger_fade_in(cards, step=0.05, duration=0.25)

    def _build_feedback_card(self, fb):
        """Build a single feedback card widget with fixed heights to avoid binding bugs."""
        reviewed = fb["status"] == "reviewed"
        bg = (1, 1, 1, 1) if reviewed else (0.933, 0.965, 0.933, 1)
        elev = 0 if reviewed else 1

        # -- Wrap everything in a fixed outer card --
        # We estimate height: header(28) + stars(24) + message(variable) + meta(18) + button(32 if not reviewed) + padding(24)
        msg_text = str(fb.get("message") or "")
        # Rough line estimate: ~40 chars per line at Caption size on 336px wide card
        est_lines = max(1, (len(msg_text) // 38) + 1)
        msg_height = est_lines * dp(18)
        btn_height = dp(36) if not reviewed else 0
        total_height = dp(28 + 24 + 18 + 20 + 16) + msg_height + btn_height  # header+stars+meta+sep+padding + msg + btn

        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=total_height,
            radius=[12, 12, 12, 12],
            md_bg_color=bg,
            elevation=elev,
            padding=[dp(12), dp(10), dp(12), dp(10)],
            spacing=dp(6)
        )

        # Row 1: From name + status badge
        header_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(26),
            spacing=dp(8)
        )

        from_label = MDLabel(
            text=f"From: {fb.get('from', 'Unknown')}",
            bold=True,
            font_style="Subtitle2",
            theme_text_color="Custom",
            text_color=(0.1, 0.1, 0.1, 1)
        )

        status_badge = MDCard(
            size_hint=(None, None),
            size=(dp(72), dp(20)),
            radius=[5, 5, 5, 5],
            elevation=0,
            md_bg_color=_status_color(fb["status"]),
            padding=dp(2)
        )
        status_badge.add_widget(MDLabel(
            text="Reviewed" if reviewed else "New",
            halign="center",
            font_style="Caption",
            bold=True,
            theme_text_color="Custom",
            text_color=_status_text_color(fb["status"])
        ))

        header_row.add_widget(from_label)
        header_row.add_widget(status_badge)

        # Row 2: Stars
        stars_label = MDLabel(
            text=_stars(fb.get("rating")),
            font_style="Body1",
            theme_text_color="Custom",
            text_color=(0.98, 0.75, 0.14, 1),
            size_hint_y=None,
            height=dp(24)
        )

        # Row 3: Message text (fixed height estimate)
        msg_label = MDLabel(
            text=msg_text or "(No message)",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=(0.15, 0.15, 0.15, 1),
            size_hint_y=None,
            height=msg_height,
            text_size=(None, None)  # will be set after layout
        )

        # Row 4: Timestamp meta
        submitted = fb.get("submitted_at")
        date_str = submitted.strftime("%d %b %Y  %H:%M") if submitted else "Unknown date"
        meta_label = MDLabel(
            text=date_str,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=dp(18)
        )

        card.add_widget(header_row)
        card.add_widget(stars_label)
        card.add_widget(msg_label)
        card.add_widget(meta_label)

        # Row 5: Mark reviewed button (only for new items)
        if not reviewed:
            btn_row = MDBoxLayout(
                size_hint_y=None,
                height=dp(34),
                spacing=dp(6)
            )
            mark_btn = MDRaisedButton(
                text="✓ Mark as Reviewed",
                md_bg_color=(0.25, 0.62, 0.30, 1),
                text_color=(1, 1, 1, 1),
                _radius=6,
                elevation=0,
                size_hint_x=1,
                on_release=lambda x, fid=fb["id"]: self._mark_reviewed(fid)
            )
            btn_row.add_widget(mark_btn)
            card.add_widget(btn_row)

        # Fix msg_label text_size after card is laid out
        def _fix_text_size(dt, lbl=msg_label):
            try:
                lbl.text_size = (lbl.width, None)
                # Recalc height from texture
                lbl.texture_update()
                if lbl.texture_size[1] > 0:
                    lbl.height = lbl.texture_size[1]
                    # Adjust parent card height
                    card.height = sum(
                        child.height for child in card.children
                    ) + dp(20) + len(card.children) * dp(6)
            except Exception:
                pass

        Clock.schedule_once(_fix_text_size, 0.1)

        return card

    def _mark_reviewed(self, feedback_id):
        """Mark a single feedback entry as reviewed and reload."""
        try:
            mark_feedback_reviewed(feedback_id)
            show_snackbar("Marked as reviewed.")
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
