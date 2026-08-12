from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from utils.layout_helpers import show_snackbar

from database.data_service import get_all_crops, get_user_preferred_crop_ids, set_user_preferred_crop_ids
from utils.animations import stagger_fade_in

KV = """
<CropSelectionScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBoxLayout:
        orientation: "vertical"
        padding: dp(24), dp(50), dp(24), dp(24)
        spacing: dp(14)

        MDLabel:
            text: "Which crops do you want to follow?"
            font_style: "H6"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.1, 0.1, 0.1, 1
            size_hint_y: None
            height: self.texture_size[1]

        MDLabel:
            text: "Pick as many as you like — you can change this anytime from your profile."
            theme_text_color: "Custom"
            text_color: 0.42, 0.42, 0.42, 1
            font_style: "Caption"
            size_hint_y: None
            height: self.texture_size[1]

        ScrollView:
            MDList:
                id: crop_list

        MDRaisedButton:
            text: "CONTINUE"
            pos_hint: {"center_x": 0.5}
            size_hint_x: 1
            md_bg_color: 0.4, 0.73, 0.42, 1
            on_release: root.save_and_continue()
"""

Builder.load_string(KV)


class CropSelectionScreen(Screen):
    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        from kivymd.uix.list import OneLineAvatarIconListItem
        from kivymd.uix.selectioncontrol import MDCheckbox

        app = MDApp.get_running_app()
        self.crops = get_all_crops()  # [(id, name), ...]
        preferred = set(get_user_preferred_crop_ids(app.current_user["user_id"]))
        self.checkboxes = {}

        self.ids.crop_list.clear_widgets()
        items = []
        for crop_id, crop_name in self.crops:
            item = OneLineAvatarIconListItem(text=crop_name)
            cb = MDCheckbox(active=crop_id in preferred, size_hint=(None, None), size=("48dp", "48dp"))
            cb.pos_hint = {"center_y": 0.5}
            item.add_widget(cb)
            self.checkboxes[crop_id] = cb
            self.ids.crop_list.add_widget(item)
            items.append(item)
        stagger_fade_in(items, step=0.06, duration=0.25)

    def save_and_continue(self):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        selected = [cid for cid, cb in self.checkboxes.items() if cb.active]
        if not selected:
            show_snackbar("Please select at least one crop.")
            return
        set_user_preferred_crop_ids(app.current_user["user_id"], selected)
        app.current_user["preferred_crop_ids"] = selected
        self.manager.transition.direction = "left"
        self.manager.current = "dashboard"
