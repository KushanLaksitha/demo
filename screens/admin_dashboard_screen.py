from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from utils.layout_helpers import show_snackbar

from database.data_service import get_all_feedback_for_admin, mark_feedback_reviewed, get_average_rating
from utils.animations import stagger_fade_in, fade_in

KV = """
<AdminDashboardScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBoxLayout:
        orientation: "vertical"
        padding: dp(20), dp(46), dp(20), dp(20)
        spacing: dp(12)

        MDBoxLayout:
            size_hint_y: None
            height: dp(40)
            MDLabel:
                text: "Admin — User Feedback"
                font_style: "H6"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1
            MDIconButton:
                icon: "logout"
                theme_text_color: "Custom"
                text_color: 0.9, 0.22, 0.21, 1
                on_release: root.logout()

        MDCard:
            id: summary_card
            orientation: "horizontal"
            padding: dp(14)
            size_hint_y: None
            height: dp(64)
            radius: [14, 14, 14, 14]
            md_bg_color: 0.933, 0.965, 0.933, 1
            elevation: 0

            MDLabel:
                id: avg_rating_label
                text: "No ratings yet"
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1
                bold: True

        ScrollView:
            MDBoxLayout:
                id: feedback_box
                orientation: "vertical"
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
"""

Builder.load_string(KV)


def _stars_text(rating):
    if not rating:
        return "No rating given"
    r = int(round(rating))
    return "★" * r + "☆" * (5 - r)


class AdminDashboardScreen(Screen):
    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if not app.current_user or app.current_user.get("user_type") != "admin":
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            return
        self.load_feedback()

    def on_enter(self, *args):
        fade_in(self.ids.summary_card, duration=0.3)

    def load_feedback(self):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel
        from kivymd.uix.button import MDFlatButton

        avg, count = get_average_rating()
        if avg is None:
            self.ids.avg_rating_label.text = "No ratings yet"
        else:
            self.ids.avg_rating_label.text = f"⭐ {avg} / 5 average  ·  from {count} rating(s)"

        box = self.ids.feedback_box
        box.clear_widgets()
        items = get_all_feedback_for_admin()
        if not items:
            box.add_widget(MDLabel(text="No feedback submitted yet.",
                                     theme_text_color="Custom", text_color=(0.42, 0.42, 0.42, 1)))
            return
        cards = []
        for f in items:
            reviewed = f["status"] == "reviewed"
            card = MDCard(orientation="vertical", padding=dp(12), spacing=dp(4),
                            size_hint_y=None, height=dp(140), radius=[14, 14, 14, 14],
                            md_bg_color=(1, 1, 1, 1) if reviewed else (0.933, 0.965, 0.933, 1),
                            elevation=0 if reviewed else 1)
            card.add_widget(MDLabel(text=_stars_text(f["rating"]),
                                      theme_text_color="Custom", text_color=(0.98, 0.75, 0.14, 1),
                                      size_hint_y=None, height=dp(24)))
            card.add_widget(MDLabel(text=f["message"], theme_text_color="Custom",
                                      text_color=(0.1, 0.1, 0.1, 1)))
            meta = MDLabel(text=f"From {f['from']} · {f['submitted_at'].strftime('%d %b %Y')} · "
                                  f"{'Reviewed' if reviewed else 'New'}",
                             font_style="Caption", theme_text_color="Custom",
                             text_color=(0.42, 0.42, 0.42, 1))
            card.add_widget(meta)
            if not reviewed:
                btn = MDFlatButton(text="Mark reviewed", theme_text_color="Custom",
                                     text_color=(0.3, 0.6, 0.35, 1),
                                     on_release=lambda x, fid=f["id"]: self.mark_reviewed(fid))
                card.add_widget(btn)
            box.add_widget(card)
            cards.append(card)
        stagger_fade_in(cards, step=0.05, duration=0.28)

    def mark_reviewed(self, feedback_id):
        mark_feedback_reviewed(feedback_id)
        self.load_feedback()

    def logout(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        app.current_user = None
        self.manager.transition.direction = "right"
        self.manager.current = "login"
        show_snackbar("Logged out successfully.")
