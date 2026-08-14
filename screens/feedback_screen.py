from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from utils.layout_helpers import show_snackbar, center_scroll_content

from database.data_service import submit_feedback
from utils.animations import fade_in, button_press_bounce

KV = """
<FeedbackScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBoxLayout:
        orientation: "vertical"

        MDBoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: dp(12), dp(8)

            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: 0.3, 0.6, 0.35, 1
                on_release: root.go_back()

        ScrollView:
            id: scrollview

            MDBoxLayout:
                id: content_box
                orientation: "vertical"
                padding: dp(24)
                spacing: dp(14)
                size_hint_y: None
                height: self.minimum_height

                MDLabel:
                    text: "Send feedback to the AgriSense team"
                    font_style: "H6"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 0.1, 0.1, 0.1, 1
                    size_hint_y: None
                    height: self.texture_size[1]

                MDLabel:
                    text: "How would you rate the app?"
                    theme_text_color: "Custom"
                    text_color: 0.42, 0.42, 0.42, 1
                    font_style: "Caption"
                    size_hint_y: None
                    height: self.texture_size[1]

                MDBoxLayout:
                    id: star_row
                    size_hint_y: None
                    height: dp(56)
                    spacing: dp(4)
                    pos_hint: {"center_x": 0.5}

                MDLabel:
                    id: rating_label
                    text: ""
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: 0.3, 0.6, 0.35, 1
                    font_style: "Caption"
                    size_hint_y: None
                    height: self.texture_size[1]

                MDTextField:
                    id: message_field
                    hint_text: "Tell us what's working, or what could be better..."
                    multiline: True
                    mode: "rectangle"
                    size_hint_y: None
                    height: dp(160)

                MDRaisedButton:
                    text: "SUBMIT FEEDBACK"
                    size_hint_x: 1
                    md_bg_color: 0.4, 0.73, 0.42, 1
                    on_release: root.send()
"""

Builder.load_string(KV)

STAR_LABELS = {1: "Poor", 2: "Fair", 3: "Good", 4: "Very good", 5: "Excellent"}


class FeedbackScreen(Screen):
    selected_rating = 0

    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        from kivymd.uix.button import MDIconButton
        app = MDApp.get_running_app()
        if not app.current_user:
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            return
        self.selected_rating = 0
        self.ids.rating_label.text = ""
        self.star_buttons = []
        row = self.ids.star_row
        row.clear_widgets()
        for i in range(1, 6):
            star = MDIconButton(
                icon="star-outline",
                theme_text_color="Custom",
                text_color=(0.8, 0.8, 0.8, 1),
                font_size="32sp",
                on_release=lambda btn, n=i: self.set_rating(n),
            )
            self.star_buttons.append(star)
            row.add_widget(star)
        center_scroll_content(self.ids.scrollview, self.ids.content_box)

    def on_enter(self, *args):
        fade_in(self.ids.content_box, duration=0.25)

    def set_rating(self, n):
        self.selected_rating = n
        for i, star in enumerate(self.star_buttons, start=1):
            if i <= n:
                star.icon = "star"
                star.text_color = (0.98, 0.75, 0.14, 1)
            else:
                star.icon = "star-outline"
                star.text_color = (0.8, 0.8, 0.8, 1)
            button_press_bounce(star)
        self.ids.rating_label.text = f"{n} / 5 — {STAR_LABELS[n]}"

    def send(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if not app.current_user:
            show_snackbar("Please log in first.")
            return
        message = self.ids.message_field.text.strip()
        if not message:
            show_snackbar("Please write a message first.")
            return
        submit_feedback(app.current_user["user_id"], message,
                          rating=self.selected_rating or None)
        self.ids.message_field.text = ""
        show_snackbar("Thanks! Your feedback has been sent to the admin.")
        self.go_back()

    def go_back(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        target = "admin_dashboard" if app.current_user and app.current_user.get("user_type") == "admin" else "dashboard"
        self.manager.transition.direction = "right"
        self.manager.current = target

