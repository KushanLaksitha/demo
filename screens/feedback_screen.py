from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from utils.layout_helpers import show_snackbar, center_scroll_content

from database.data_service import submit_feedback
from utils.animations import fade_in, button_press_bounce, bounce_scale, stagger_fade_in

KV = """
<FeedbackScreen>:
    canvas.before:
        Color:
            rgba: 0.96, 0.98, 0.96, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBoxLayout:
        orientation: "vertical"

        # Top Bar Navigation
        MDBoxLayout:
            size_hint_y: None
            height: dp(52)
            padding: dp(12), dp(4)
            spacing: dp(8)

            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: 0.25, 0.62, 0.30, 1
                on_release: root.go_back()

            MDLabel:
                text: "Share Your Feedback"
                font_style: "Subtitle1"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.15, 0.35, 0.18, 1

        ScrollView:
            id: scrollview

            MDBoxLayout:
                id: content_box
                orientation: "vertical"
                padding: dp(16)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height

                # Hero Header Banner Card
                MDCard:
                    size_hint_y: None
                    height: dp(76)
                    radius: [14, 14, 14, 14]
                    padding: dp(12)
                    spacing: dp(10)
                    md_bg_color: 0.25, 0.62, 0.30, 0.12
                    elevation: 0

                    MDIconButton:
                        icon: "comment-heart-outline"
                        theme_text_color: "Custom"
                        text_color: 0.25, 0.62, 0.30, 1
                        user_font_size: "26sp"
                        pos_hint: {"center_y": 0.5}

                    MDBoxLayout:
                        orientation: "vertical"
                        spacing: dp(2)
                        pos_hint: {"center_y": 0.5}
                        MDLabel:
                            text: "We Value Your Voice! 💬"
                            bold: True
                            font_style: "Subtitle2"
                            theme_text_color: "Custom"
                            text_color: 0.15, 0.35, 0.18, 1
                            size_hint_y: None
                            height: self.texture_size[1]
                        MDLabel:
                            text: "Tap ratings & quick pills below. No typing required!"
                            font_style: "Caption"
                            theme_text_color: "Custom"
                            text_color: 0.35, 0.45, 0.35, 1
                            size_hint_y: None
                            height: self.texture_size[1]

                # Step 1: Mood & Rating Card
                MDCard:
                    id: card_step1
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(164)
                    padding: dp(12)
                    spacing: dp(8)
                    radius: [14, 14, 14, 14]
                    md_bg_color: 1, 1, 1, 1
                    elevation: 1

                    MDLabel:
                        text: "1. How was your experience?"
                        bold: True
                        font_style: "Subtitle2"
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.2, 0.2, 1
                        size_hint_y: None
                        height: self.texture_size[1]

                    # 5 Emoji reaction buttons row
                    MDBoxLayout:
                        id: emoji_row
                        size_hint_y: None
                        height: dp(42)
                        spacing: dp(4)
                        pos_hint: {"center_x": 0.5}

                    # Star Rating Row
                    MDBoxLayout:
                        id: star_row
                        size_hint_y: None
                        height: dp(34)
                        spacing: dp(4)
                        pos_hint: {"center_x": 0.5}

                    MDLabel:
                        id: rating_label
                        text: "Tap an emoji or star to rate"
                        halign: "center"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.25, 0.62, 0.30, 1
                        font_style: "Caption"
                        size_hint_y: None
                        height: self.texture_size[1]

                # Step 2: Topic Selection Chips Card
                MDCard:
                    id: card_step2
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(94)
                    padding: dp(12)
                    spacing: dp(8)
                    radius: [14, 14, 14, 14]
                    md_bg_color: 1, 1, 1, 1
                    elevation: 1

                    MDLabel:
                        text: "2. Select Topic (Optional)"
                        bold: True
                        font_style: "Subtitle2"
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.2, 0.2, 1
                        size_hint_y: None
                        height: self.texture_size[1]

                    ScrollView:
                        size_hint_y: None
                        height: dp(36)
                        do_scroll_y: False
                        MDBoxLayout:
                            id: topic_chips_box
                            orientation: "horizontal"
                            spacing: dp(6)
                            size_hint_x: None
                            width: self.minimum_width

                # Step 3: Quick Impression Pills (Pre-filled Preset Messages) Card
                MDCard:
                    id: card_step3
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(12)
                    spacing: dp(8)
                    radius: [14, 14, 14, 14]
                    md_bg_color: 1, 1, 1, 1
                    elevation: 1

                    MDLabel:
                        text: "3. Tap 1-Tap Quick Feedback Pills:"
                        bold: True
                        font_style: "Subtitle2"
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.2, 0.2, 1
                        size_hint_y: None
                        height: self.texture_size[1]

                    MDBoxLayout:
                        id: quick_pills_box
                        orientation: "vertical"
                        spacing: dp(6)
                        size_hint_y: None
                        height: self.minimum_height

                # Step 4: Text Remarks & Action Card
                MDCard:
                    id: card_step4
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(220)
                    padding: dp(12)
                    spacing: dp(8)
                    radius: [14, 14, 14, 14]
                    md_bg_color: 1, 1, 1, 1
                    elevation: 1

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(24)
                        MDLabel:
                            text: "4. Additional Details (Optional)"
                            bold: True
                            font_style: "Subtitle2"
                            theme_text_color: "Custom"
                            text_color: 0.2, 0.2, 0.2, 1
                        MDFlatButton:
                            text: "Clear Form"
                            theme_text_color: "Custom"
                            text_color: 0.7, 0.2, 0.2, 1
                            on_release: root.clear_form()

                    MDTextField:
                        id: message_field
                        hint_text: "Tap quick pills above or type custom notes..."
                        multiline: True
                        mode: "rectangle"
                        size_hint_y: None
                        height: dp(90)
                        line_color_focus: 0.25, 0.62, 0.30, 1

                    MDRaisedButton:
                        id: submit_btn
                        text: "SUBMIT FEEDBACK"
                        size_hint_x: 1
                        height: dp(44)
                        _radius: 10
                        md_bg_color: 0.25, 0.62, 0.30, 1
                        on_release: root.send()
"""

Builder.load_string(KV)

EMOJI_RATINGS = [
    (1, "😡", "Disappointed"),
    (2, "🙁", "Needs Work"),
    (3, "😐", "Okay"),
    (4, "🙂", "Good"),
    (5, "😍", "Loved it!"),
]

STAR_LABELS = {1: "Poor", 2: "Fair", 3: "Good", 4: "Very good", 5: "Loved it!"}

TOPIC_OPTIONS = [
    "📈 Price Predictions",
    "🌾 Crop Guidance",
    "🌦️ Weather Info",
    "⚡ Speed & UI",
    "🐞 Bug / Issue",
    "💡 Feature Idea",
]

PRESET_PILLS = [
    "🎯 Price forecasts are super accurate & helpful!",
    "⚡ App is fast, smooth & very easy to navigate",
    "🌾 Helps me plan crop sales & harvest timing",
    "📊 Market demand trends & charts are clear",
    "🔔 Alert notifications keep me updated in time",
    "➕ Requesting support for more crop varieties",
    "🐞 Found a small display or loading issue",
]


class FeedbackScreen(Screen):
    selected_rating = 0
    selected_topic = ""
    active_pills = set()

    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if not app.current_user:
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            return

        self.reset_state()
        self._build_emoji_row()
        self._build_star_row()
        self._build_topic_chips()
        self._build_quick_pills()
        center_scroll_content(self.ids.scrollview, self.ids.content_box)

    def on_enter(self, *args):
        fade_in(self.ids.content_box, duration=0.25)

    def reset_state(self):
        self.selected_rating = 0
        self.selected_topic = ""
        self.active_pills = set()
        self.ids.rating_label.text = "Tap an emoji or star to rate"
        self.ids.message_field.text = ""
        self.ids.submit_btn.text = "SUBMIT FEEDBACK"

    def _build_emoji_row(self):
        row = self.ids.emoji_row
        row.clear_widgets()
        self.emoji_btn_map = {}
        for rating_val, emoji, desc in EMOJI_RATINGS:
            btn = MDRaisedButton(
                text=emoji,
                size_hint=(None, None),
                size=(dp(54), dp(40)),
                _radius=10,
                elevation=0,
                font_size="20sp",
                md_bg_color=(0.93, 0.95, 0.93, 1),
                text_color=(0.2, 0.2, 0.2, 1),
                on_release=lambda x, val=rating_val: self.set_rating(val),
            )
            self.emoji_btn_map[rating_val] = btn
            row.add_widget(btn)

    def _build_star_row(self):
        row = self.ids.star_row
        row.clear_widgets()
        self.star_buttons = []
        for i in range(1, 6):
            star = MDIconButton(
                icon="star-outline",
                theme_text_color="Custom",
                text_color=(0.8, 0.8, 0.8, 1),
                font_size="28sp",
                on_release=lambda btn, n=i: self.set_rating(n),
            )
            self.star_buttons.append(star)
            row.add_widget(star)

    def _build_topic_chips(self):
        box = self.ids.topic_chips_box
        box.clear_widgets()
        self.topic_chip_map = {}
        for topic in TOPIC_OPTIONS:
            btn = MDRaisedButton(
                text=topic,
                size_hint=(None, None),
                height=dp(32),
                _radius=16,
                elevation=0,
                md_bg_color=(0.92, 0.95, 0.92, 1),
                text_color=(0.2, 0.45, 0.2, 1),
                on_release=lambda x, t=topic: self.toggle_topic(t),
            )
            box.add_widget(btn)
            self.topic_chip_map[topic] = btn

    def _build_quick_pills(self):
        box = self.ids.quick_pills_box
        box.clear_widgets()
        self.pill_widget_map = {}
        for pill in PRESET_PILLS:
            btn = MDRaisedButton(
                text=pill,
                size_hint_x=1,
                size_hint_y=None,
                height=dp(36),
                _radius=8,
                elevation=0,
                md_bg_color=(0.95, 0.97, 0.95, 1),
                text_color=(0.15, 0.35, 0.18, 1),
                on_release=lambda x, p=pill: self.toggle_pill(p),
            )
            box.add_widget(btn)
            self.pill_widget_map[pill] = btn

    def set_rating(self, n):
        self.selected_rating = n
        # Update emoji highlights
        for val, btn in self.emoji_btn_map.items():
            if val == n:
                btn.md_bg_color = (0.25, 0.62, 0.30, 1)
                btn.text_color = (1, 1, 1, 1)
                bounce_scale(btn)
            else:
                btn.md_bg_color = (0.93, 0.95, 0.93, 1)
                btn.text_color = (0.2, 0.2, 0.2, 1)

        # Update stars
        for i, star in enumerate(self.star_buttons, start=1):
            if i <= n:
                star.icon = "star"
                star.text_color = (0.98, 0.75, 0.14, 1)
            else:
                star.icon = "star-outline"
                star.text_color = (0.8, 0.8, 0.8, 1)
            button_press_bounce(star)

        emoji_symbol = dict(EMOJI_RATINGS)[n][0]
        label_desc = STAR_LABELS[n]
        self.ids.rating_label.text = f"{emoji_symbol} {n} / 5 — {label_desc}"
        self.ids.submit_btn.text = f"SUBMIT FEEDBACK ({n} ★)"

    def toggle_topic(self, topic):
        if self.selected_topic == topic:
            self.selected_topic = ""
        else:
            self.selected_topic = topic

        for t, btn in self.topic_chip_map.items():
            if t == self.selected_topic:
                btn.md_bg_color = (0.25, 0.62, 0.30, 1)
                btn.text_color = (1, 1, 1, 1)
                bounce_scale(btn)
            else:
                btn.md_bg_color = (0.92, 0.95, 0.92, 1)
                btn.text_color = (0.2, 0.45, 0.2, 1)

        self._sync_message_from_selections()

    def toggle_pill(self, pill):
        btn = self.pill_widget_map.get(pill)
        if pill in self.active_pills:
            self.active_pills.remove(pill)
            if btn:
                btn.md_bg_color = (0.95, 0.97, 0.95, 1)
                btn.text_color = (0.15, 0.35, 0.18, 1)
        else:
            self.active_pills.add(pill)
            if btn:
                btn.md_bg_color = (0.35, 0.72, 0.38, 1)
                btn.text_color = (1, 1, 1, 1)
                bounce_scale(btn)

        self._sync_message_from_selections()

    def _sync_message_from_selections(self):
        parts = []
        if self.selected_topic:
            parts.append(f"[{self.selected_topic}]")
        if self.active_pills:
            parts.extend(list(self.active_pills))

        concatenated = " ".join(parts)
        curr_custom = self._extract_custom_user_notes()

        if curr_custom:
            new_text = f"{concatenated}\nNote: {curr_custom}" if concatenated else curr_custom
        else:
            new_text = concatenated

        self.ids.message_field.text = new_text

    def _extract_custom_user_notes(self):
        text = self.ids.message_field.text.strip()
        if "Note: " in text:
            return text.split("Note: ", 1)[1].strip()
        # If user typed something completely manual
        parts = []
        if self.selected_topic:
            parts.append(f"[{self.selected_topic}]")
        parts.extend(list(self.active_pills))
        prefix = " ".join(parts)
        if text.startswith(prefix):
            return text[len(prefix):].strip()
        return text

    def clear_form(self):
        self.reset_state()
        self._build_topic_chips()
        self._build_quick_pills()
        show_snackbar("Feedback form cleared.")

    def send(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if not app.current_user:
            show_snackbar("Please log in first.")
            return

        message = self.ids.message_field.text.strip()

        # If user didn't select or type text, but picked a rating, generate a default message
        if not message:
            if self.selected_rating:
                desc = STAR_LABELS.get(self.selected_rating, "")
                message = f"User rated app {self.selected_rating}/5 stars ({desc})."
            else:
                show_snackbar("Please select a rating or tap a quick feedback pill!")
                return

        submit_feedback(
            app.current_user["user_id"],
            message,
            rating=self.selected_rating or None
        )

        show_snackbar("🎉 Thank you! Your feedback has been sent to the team.")
        self.clear_form()
        self.go_back()

    def go_back(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        target = "admin_dashboard" if app.current_user and app.current_user.get("user_type") == "admin" else "dashboard"
        self.manager.transition.direction = "right"
        self.manager.current = target


