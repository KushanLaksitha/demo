from datetime import datetime
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from database.data_service import (
    get_market_summary, get_recommendations_for_user, get_alerts_for_user,
    mark_alert_read, get_all_crops, get_price_history, get_production_history,
    get_user_preferred_crop_ids,
)
from utils.animations import fade_in, stagger_fade_in
from utils.layout_helpers import center_scroll_content, show_snackbar

ROLE_TAGLINE = {
    "farmer": "Plan your harvest with confidence",
    "trader": "Track market prices before you buy or sell",
    "policymaker": "Regional supply & price overview",
}
ROLE_ICON = {"farmer": "sprout", "trader": "cart-outline", "policymaker": "chart-areaspline"}

KV = """
<DashboardScreen>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBottomNavigation:
        id: bottom_nav
        panel_color: 1, 1, 1, 1
        selected_color_background: 0.91, 0.96, 0.91, 1
        text_color_active: 0.3, 0.6, 0.35, 1
        text_color_normal: 0.6, 0.6, 0.6, 1

        MDBottomNavigationItem:
            name: "home"
            text: "Home"
            icon: "view-dashboard"
            on_tab_press: root.load_home()

            ScrollView:
                MDBoxLayout:
                    id: home_box
                    orientation: "vertical"
                    padding: dp(16), dp(16), dp(16), dp(16)
                    spacing: dp(12)
                    size_hint_y: None
                    height: self.minimum_height

        MDBottomNavigationItem:
            name: "recommendations"
            text: "For You"
            icon: "lightbulb-on"
            on_tab_press: root.load_recommendations()

            ScrollView:
                MDBoxLayout:
                    id: rec_box
                    orientation: "vertical"
                    padding: dp(16)
                    spacing: dp(10)
                    size_hint_y: None
                    height: self.minimum_height

        MDBottomNavigationItem:
            name: "alerts"
            text: "Alerts"
            icon: "bell-ring"
            on_tab_press: root.load_alerts()

            ScrollView:
                MDBoxLayout:
                    id: alert_box
                    orientation: "vertical"
                    padding: dp(16)
                    spacing: dp(10)
                    size_hint_y: None
                    height: self.minimum_height

        MDBottomNavigationItem:
            name: "history"
            text: "History"
            icon: "chart-line"
            on_tab_press: root.load_history()

            MDBoxLayout:
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(8)

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(48)
                    spacing: dp(8)
                    adaptive_width: True
                    pos_hint: {"center_x": 0.5}
                    MDRaisedButton:
                        id: crop_button
                        text: "Crop  ▾"
                        md_bg_color: 0.91, 0.96, 0.91, 1
                        text_color: 0.1, 0.1, 0.1, 1
                        on_release: root.open_crop_menu()
                    MDRaisedButton:
                        id: metric_button
                        text: "Price"
                        md_bg_color: 0.4, 0.73, 0.42, 1
                        on_release: root.toggle_metric()

                ScrollView:
                    MDBoxLayout:
                        id: history_box
                        orientation: "vertical"
                        spacing: dp(12)
                        padding: dp(4)
                        size_hint_y: None
                        height: self.minimum_height

        MDBottomNavigationItem:
            name: "profile"
            text: "Profile"
            icon: "account-circle"
            on_tab_press: root.load_profile()

            ScrollView:
                MDBoxLayout:
                    id: profile_box
                    orientation: "vertical"
                    padding: dp(24)
                    spacing: dp(14)
                    size_hint_y: None
                    height: self.minimum_height
"""

Builder.load_string(KV)


class DashboardScreen(Screen):
    history_metric = "price"
    history_crop_id = None
    history_crop_name = None

    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        self.app = MDApp.get_running_app()
        self.user = self.app.current_user
        self.crops = get_all_crops()
        pref_ids = get_user_preferred_crop_ids(self.user["user_id"])
        self.followed_crop_ids = pref_ids or [c[0] for c in self.crops]
        if self.crops:
            self.history_crop_id, self.history_crop_name = self.crops[0]
        self.load_home()

    # ---------------- HOME ----------------
    def load_home(self):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel
        from kivymd.uix.boxlayout import MDBoxLayout

        box = self.ids.home_box
        box.clear_widgets()

        role = self.user["user_type"]
        welcome = MDLabel(
            text=f"Hi {self.user['first_name']} 👋",
            font_style="H5", bold=True, theme_text_color="Custom",
            text_color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=dp(36),
        )
        tagline = MDLabel(
            text=ROLE_TAGLINE.get(role, ""), theme_text_color="Custom",
            text_color=(0.42, 0.42, 0.42, 1), font_style="Caption",
            size_hint_y=None, height=dp(20),
        )
        region_lbl = MDLabel(
            text=f"📍 {self.user.get('district') or 'No district set'}",
            theme_text_color="Custom", text_color=(0.3, 0.6, 0.35, 1),
            font_style="Caption", size_hint_y=None, height=dp(20),
        )
        box.add_widget(welcome)
        box.add_widget(tagline)
        box.add_widget(region_lbl)

        section = MDLabel(
            text="Market snapshot — your followed crops", bold=True,
            theme_text_color="Custom", text_color=(0.1, 0.1, 0.1, 1),
            size_hint_y=None, height=dp(30),
        )
        box.add_widget(section)

        summary = get_market_summary(region_id=self.user.get("region_id"))
        followed_names = {c[1] for c in self.crops if c[0] in self.followed_crop_ids}
        cards = []
        for row in summary:
            if row["crop"] not in followed_names:
                continue
            card = MDCard(
                orientation="horizontal", size_hint_y=None, height=dp(64),
                padding=dp(12), spacing=dp(10), radius=[14, 14, 14, 14],
                md_bg_color=(0.933, 0.965, 0.933, 1), elevation=0,
            )
            name_lbl = MDLabel(text=row["crop"], theme_text_color="Custom",
                                 text_color=(0.1, 0.1, 0.1, 1), bold=True)
            price_txt = f"LKR {row['price']:.0f}/kg" if row["price"] else "No data"
            change = row["change_pct"]
            if change is None:
                change_txt = ""
                change_color = (0.42, 0.42, 0.42, 1)
            elif change >= 0:
                change_txt = f"▲ {change}%"
                change_color = (0.26, 0.63, 0.28, 1)
            else:
                change_txt = f"▼ {change}%"
                change_color = (0.9, 0.22, 0.21, 1)
            price_lbl = MDLabel(text=price_txt, halign="right", theme_text_color="Custom",
                                  text_color=(0.1, 0.1, 0.1, 1))
            change_lbl = MDLabel(text=change_txt, halign="right", size_hint_x=0.4,
                                   theme_text_color="Custom", text_color=change_color)
            card.add_widget(name_lbl)
            card.add_widget(price_lbl)
            card.add_widget(change_lbl)
            box.add_widget(card)
            cards.append(card)

        stagger_fade_in(cards, step=0.05, duration=0.28)
        center_scroll_content(box.parent, box)

    # ---------------- RECOMMENDATIONS ----------------
    def load_recommendations(self):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel

        box = self.ids.rec_box
        box.clear_widgets()
        recs = get_recommendations_for_user(self.user["user_id"])
        if not recs:
            box.add_widget(MDLabel(text="No recommendations yet — check back after your next model update.",
                                     theme_text_color="Custom", text_color=(0.42, 0.42, 0.42, 1)))
            center_scroll_content(box.parent, box)
            return
        cards = []
        for r in recs:
            card = MDCard(
                orientation="vertical", size_hint_y=None, height=dp(80),
                padding=dp(12), radius=[14, 14, 14, 14],
                md_bg_color=(0.933, 0.965, 0.933, 1), elevation=0,
            )
            card.add_widget(MDLabel(text=r["message"], theme_text_color="Custom",
                                      text_color=(0.1, 0.1, 0.1, 1)))
            card.add_widget(MDLabel(text=r["created_at"].strftime("%d %b %Y"),
                                      font_style="Caption", theme_text_color="Custom",
                                      text_color=(0.42, 0.42, 0.42, 1)))
            box.add_widget(card)
            cards.append(card)
        stagger_fade_in(cards, step=0.05, duration=0.28)
        center_scroll_content(box.parent, box)

    # ---------------- ALERTS ----------------
    def load_alerts(self):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel
        from kivymd.uix.button import MDIconButton

        box = self.ids.alert_box
        box.clear_widgets()
        alerts = get_alerts_for_user(self.user["user_id"])
        if not alerts:
            box.add_widget(MDLabel(text="No alerts right now. We'll notify you of price spikes or drops.",
                                     theme_text_color="Custom", text_color=(0.42, 0.42, 0.42, 1)))
            center_scroll_content(box.parent, box)
            return
        cards = []
        for a in alerts:
            card = MDCard(
                orientation="horizontal", size_hint_y=None, height=dp(76),
                padding=dp(12), spacing=dp(8), radius=[14, 14, 14, 14],
                md_bg_color=(1, 1, 1, 1) if a["is_read"] else (0.933, 0.965, 0.933, 1),
                elevation=1 if not a["is_read"] else 0,
            )
            icon = MDIconButton(icon="alert-circle-outline" if not a["is_read"] else "check-circle-outline",
                                  theme_text_color="Custom",
                                  text_color=(0.94, 0.55, 0, 1) if not a["is_read"] else (0.6, 0.6, 0.6, 1),
                                  disabled=True)
            msg = MDLabel(text=a["message"], theme_text_color="Custom", text_color=(0.1, 0.1, 0.1, 1))
            card.add_widget(icon)
            card.add_widget(msg)
            if not a["is_read"]:
                mark_btn = MDIconButton(icon="close", on_release=lambda x, aid=a["id"]: self.dismiss_alert(aid))
                card.add_widget(mark_btn)
            box.add_widget(card)
            cards.append(card)
        stagger_fade_in(cards, step=0.05, duration=0.28)
        center_scroll_content(box.parent, box)

    def dismiss_alert(self, alert_id):
        mark_alert_read(alert_id)
        self.load_alerts()

    # ---------------- HISTORY ----------------
    def open_crop_menu(self):
        from kivymd.uix.menu import MDDropdownMenu
        followed = [c for c in self.crops if c[0] in self.followed_crop_ids]
        menu = MDDropdownMenu(
            caller=self.ids.crop_button,
            items=[{"text": name, "viewclass": "OneLineListItem",
                     "on_release": lambda cid=cid, name=name: self.pick_history_crop(cid, name, menu)}
                    for cid, name in followed],
        )
        menu.open()

    def pick_history_crop(self, crop_id, name, menu):
        self.history_crop_id = crop_id
        self.history_crop_name = name
        self.ids.crop_button.text = f"{name}  ▾"
        menu.dismiss()
        self.load_history()

    def toggle_metric(self):
        self.history_metric = "production" if self.history_metric == "price" else "price"
        self.ids.metric_button.text = "Production" if self.history_metric == "production" else "Price"
        self.load_history()

    def load_history(self):
        from utils.chart_utils import build_line_chart, build_bar_chart
        from kivymd.uix.label import MDLabel

        box = self.ids.history_box
        box.clear_widgets()
        if not self.history_crop_id:
            return

        region_id = self.user.get("region_id")
        if self.history_metric == "price":
            data = get_price_history(self.history_crop_id, region_id=region_id, weeks=16)
            if not data:
                box.add_widget(MDLabel(text="No price history available yet.",
                                         theme_text_color="Custom", text_color=(0.42, 0.42, 0.42, 1),
                                         halign="center"))
                center_scroll_content(box.parent, box)
                return
            dates, values = zip(*data)
            chart = build_line_chart(list(dates), list(values),
                                       title=f"{self.history_crop_name} price — last 16 weeks",
                                       y_label="LKR / kg")
        else:
            data = get_production_history(self.history_crop_id, region_id=region_id, weeks=16)
            if not data:
                box.add_widget(MDLabel(text="No production history available yet.",
                                         theme_text_color="Custom", text_color=(0.42, 0.42, 0.42, 1),
                                         halign="center"))
                center_scroll_content(box.parent, box)
                return
            dates, values = zip(*data)
            chart = build_bar_chart(list(dates), list(values),
                                      title=f"{self.history_crop_name} production — last 16 weeks",
                                      y_label="kg")
        chart.size_hint_y = None
        chart.height = dp(320)
        chart.size_hint_x = 1
        chart.pos_hint = {"center_x": 0.5}
        box.add_widget(chart)
        fade_in(chart, duration=0.3)
        center_scroll_content(box.parent, box)

    # ---------------- PROFILE ----------------
    def load_profile(self):
        from kivymd.uix.label import MDLabel
        from kivymd.uix.button import MDRaisedButton
        from kivymd.uix.card import MDCard

        box = self.ids.profile_box
        box.clear_widgets()

        card = MDCard(orientation="vertical", padding=dp(16), spacing=dp(6),
                        size_hint_y=None, height=dp(150), radius=[16, 16, 16, 16],
                        md_bg_color=(0.933, 0.965, 0.933, 1), elevation=0)
        card.add_widget(MDLabel(text=f"{self.user['first_name']} {self.user['last_name']}",
                                  font_style="H6", bold=True, theme_text_color="Custom",
                                  text_color=(0.1, 0.1, 0.1, 1)))
        card.add_widget(MDLabel(text=self.user["email"], theme_text_color="Custom",
                                  text_color=(0.42, 0.42, 0.42, 1)))
        card.add_widget(MDLabel(text=f"Role: {self.user['user_type'].capitalize()}",
                                  theme_text_color="Custom", text_color=(0.3, 0.6, 0.35, 1)))
        card.add_widget(MDLabel(text=f"District: {self.user.get('district') or '-'}",
                                  theme_text_color="Custom", text_color=(0.3, 0.6, 0.35, 1)))
        box.add_widget(card)

        edit_profile_btn = MDRaisedButton(text="Edit Profile Details", size_hint_x=1,
                                            md_bg_color=(0.3, 0.6, 0.35, 1),
                                            on_release=self.open_edit_profile_dialog)
        edit_btn = MDRaisedButton(text="Edit followed crops", size_hint_x=1,
                                    md_bg_color=(0.4, 0.73, 0.42, 1), on_release=self.edit_crops)
        feedback_btn = MDRaisedButton(text="Send feedback", size_hint_x=1,
                                        md_bg_color=(0.91, 0.96, 0.91, 1), text_color=(0.1, 0.1, 0.1, 1),
                                        on_release=self.go_feedback)
        logout_btn = MDRaisedButton(text="Log out", size_hint_x=1,
                                      md_bg_color=(0.9, 0.22, 0.21, 1), on_release=self.logout)
        box.add_widget(edit_profile_btn)
        box.add_widget(edit_btn)
        box.add_widget(feedback_btn)
        box.add_widget(logout_btn)
        stagger_fade_in([card, edit_profile_btn, edit_btn, feedback_btn, logout_btn], step=0.05, duration=0.25)
        center_scroll_content(box.parent, box)

    def open_edit_profile_dialog(self, *args):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton, MDRaisedButton
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.menu import MDDropdownMenu
        from database.data_service import get_all_regions, update_user_profile

        dialog_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(12), dp(12), dp(12), dp(12)],
            size_hint_y=None,
            height=dp(200),
        )

        fn_input = MDTextField(
            text=self.user.get("first_name", ""),
            hint_text="First Name",
            size_hint_y=None,
            height=dp(50),
        )
        ln_input = MDTextField(
            text=self.user.get("last_name", ""),
            hint_text="Last Name",
            size_hint_y=None,
            height=dp(50),
        )

        regions = get_all_regions()
        selected_region = {"id": self.user.get("region_id")}

        curr_dist = self.user.get("district") or "Select District"
        region_btn = MDRaisedButton(
            text=f"District: {curr_dist}  ▾",
            size_hint_x=1,
            md_bg_color=(0.91, 0.96, 0.91, 1),
            text_color=(0.1, 0.1, 0.1, 1),
        )

        def pick_region(r_id, r_dist, menu):
            selected_region["id"] = r_id
            region_btn.text = f"District: {r_dist}  ▾"
            menu.dismiss()

        def open_region_menu(*_):
            items = [
                {
                    "text": f"{dist} ({rname})",
                    "viewclass": "OneLineListItem",
                    "on_release": lambda rid=rid, rdist=dist: pick_region(rid, rdist, menu)
                }
                for rid, rname, dist in regions
            ]
            menu = MDDropdownMenu(caller=region_btn, items=items, width_mult=4)
            menu.open()

        region_btn.on_release = open_region_menu

        dialog_box.add_widget(fn_input)
        dialog_box.add_widget(ln_input)
        dialog_box.add_widget(region_btn)

        def save_profile(*_):
            fn = fn_input.text.strip()
            ln = ln_input.text.strip()
            if not fn or not ln:
                show_snackbar("First and Last name cannot be empty.")
                return
            ok, res = update_user_profile(
                self.user["user_id"],
                first_name=fn,
                last_name=ln,
                region_id=selected_region["id"],
            )
            if ok:
                self.user = res
                self.app.current_user = res
                self.edit_dialog.dismiss()
                self.load_profile()
                show_snackbar("Profile updated successfully!")
            else:
                show_snackbar(f"Failed to update profile: {res}")

        self.edit_dialog = MDDialog(
            title="Edit Profile Details",
            type="custom",
            content_cls=dialog_box,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.edit_dialog.dismiss()),
                MDRaisedButton(text="SAVE", md_bg_color=(0.3, 0.6, 0.35, 1), on_release=save_profile),
            ],
        )
        self.edit_dialog.open()

    def edit_crops(self, *args):
        self.manager.transition.direction = "left"
        self.manager.current = "crop_selection"

    def go_feedback(self, *args):
        self.manager.transition.direction = "left"
        self.manager.current = "feedback"

    def logout(self, *args):
        self.app.current_user = None
        self.manager.transition.direction = "right"
        self.manager.current = "login"
        show_snackbar("Logged out successfully.")
