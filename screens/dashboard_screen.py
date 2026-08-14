"""
Dashboard screen – full interactive overhaul.
• Gradient header banner in Home tab with weather badge and refresh button
• Slide-up-fade-in card animations on every tab load
• Recommendations: accordion expand/collapse on tap
• Alerts: animated dismiss + pulse for unread + mark-all-read button
• History: pill toggle switch + chip crop selector
• Profile: avatar circle with initials, bounce-scale buttons
"""
from datetime import datetime
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from database.data_service import (
    get_market_summary, get_recommendations_for_user, get_alerts_for_user,
    mark_alert_read, get_all_crops, get_price_history, get_production_history,
    get_user_preferred_crop_ids, get_market_demand_trends, get_weather_impact_analysis,
)
from utils.animations import (
    fade_in, stagger_fade_in, bounce_scale, ripple_flash,
    pulse_color, fade_out_remove,
)
from utils.layout_helpers import center_scroll_content, show_snackbar

ROLE_TAGLINE = {
    "farmer": "Plan your harvest with confidence",
    "trader": "Track market prices before you buy or sell",
    "policymaker": "Regional supply & price overview",
}

KV = """
<DashboardScreen>:
    canvas.before:
        Color:
            rgba: 0.96, 0.99, 0.96, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBottomNavigation:
        id: bottom_nav
        panel_color: 1, 1, 1, 1
        selected_color_background: 0.88, 0.97, 0.88, 1
        text_color_active: 0.22, 0.60, 0.28, 1
        text_color_normal: 0.62, 0.62, 0.62, 1

        MDBottomNavigationItem:
            name: "home"
            text: "Home"
            icon: "view-dashboard"
            on_tab_press: root.load_home()

            ScrollView:
                MDBoxLayout:
                    id: home_box
                    orientation: "vertical"
                    padding: 0, 0, 0, dp(16)
                    spacing: dp(0)
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
                    padding: dp(14), dp(14), dp(14), dp(14)
                    spacing: dp(10)
                    size_hint_y: None
                    height: self.minimum_height

        MDBottomNavigationItem:
            name: "alerts"
            text: "Alerts"
            icon: "bell-ring"
            on_tab_press: root.load_alerts()

            MDBoxLayout:
                orientation: "vertical"
                spacing: 0

                # Alerts header row with mark-all button
                MDBoxLayout:
                    id: alerts_header_row
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(48)
                    padding: dp(16), dp(8), dp(16), dp(4)

                    MDLabel:
                        text: "Alerts"
                        font_style: "H6"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.08, 0.08, 0.08, 1

                    MDTextButton:
                        id: mark_all_btn
                        text: "Mark all read"
                        pos_hint: {"center_y": 0.5}
                        theme_text_color: "Custom"
                        text_color: 0.22, 0.60, 0.28, 1
                        on_release: root.mark_all_alerts_read()

                ScrollView:
                    MDBoxLayout:
                        id: alert_box
                        orientation: "vertical"
                        padding: dp(14), dp(4), dp(14), dp(14)
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
                padding: dp(14), dp(10), dp(14), dp(4)
                spacing: dp(8)

                # Crop chips row
                MDLabel:
                    text: "Select crop"
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.45, 0.45, 0.45, 1
                    size_hint_y: None
                    height: dp(18)

                ScrollView:
                    size_hint_y: None
                    height: dp(44)
                    do_scroll_y: False
                    MDBoxLayout:
                        id: history_crop_chips
                        orientation: "horizontal"
                        spacing: dp(8)
                        size_hint_x: None
                        width: self.minimum_width
                        padding: dp(2), dp(4), dp(2), dp(4)

                # Pill-style Price / Production toggle
                MDCard:
                    size_hint_y: None
                    height: dp(40)
                    radius: [20, 20, 20, 20]
                    elevation: 0
                    md_bg_color: 0.90, 0.95, 0.90, 1
                    padding: dp(4)

                    MDBoxLayout:
                        orientation: "horizontal"
                        spacing: 0

                        MDRaisedButton:
                            id: pill_price_btn
                            text: "Price"
                            size_hint_x: 0.5
                            elevation: 0
                            _radius: 18
                            md_bg_color: 0.25, 0.62, 0.30, 1
                            on_release: root.set_metric("price")

                        MDRaisedButton:
                            id: pill_prod_btn
                            text: "Production"
                            size_hint_x: 0.5
                            elevation: 0
                            _radius: 18
                            md_bg_color: 0.90, 0.95, 0.90, 1
                            text_color: 0.3, 0.3, 0.3, 1
                            on_release: root.set_metric("production")

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
                    padding: dp(20), dp(16), dp(20), dp(20)
                    spacing: dp(12)
                    size_hint_y: None
                    height: self.minimum_height
"""

Builder.load_string(KV)


# ═══════════════════════════════════════════════════════════════════════════
class DashboardScreen(Screen):
    history_metric = "price"
    history_crop_id = None
    history_crop_name = None
    _history_chip_widgets = {}   # crop_id -> chip card

    def on_pre_enter(self, *args):
        from kivymd.app import MDApp
        self.app = MDApp.get_running_app()
        self.user = self.app.current_user
        if not self.user:
            if self.manager:
                self.manager.transition.direction = "right"
                self.manager.current = "login"
            return
        self.crops = get_all_crops()
        pref_ids = get_user_preferred_crop_ids(self.user["user_id"])
        self.followed_crop_ids = pref_ids or ([c[0] for c in self.crops] if self.crops else [])
        if self.crops:
            self.history_crop_id, self.history_crop_name = self.crops[0]
        else:
            self.history_crop_id, self.history_crop_name = None, None
        self.load_home()
        self._build_history_crop_chips()

    # ══════════════════════════════════════════════════════════════════════
    # HOME TAB
    # ══════════════════════════════════════════════════════════════════════
    def load_home(self):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton, MDTextButton
        from kivy.graphics import Color, Ellipse

        box = self.ids.home_box
        box.clear_widgets()
        box.padding = (dp(16), dp(16), dp(16), dp(24))
        box.spacing = dp(14)
        cards = []

        # ── 1. HEADER SECTION (WELCOME BACK / Hello, Farmer + Profile Avatar) ──
        header_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(54),
            spacing=dp(10),
        )

        title_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2),
        )
        welcome_lbl = MDLabel(
            text="WELCOME BACK",
            font_style="Caption",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.18, 0.52, 0.32, 1),
            size_hint_y=None, height=dp(16),
        )
        first_name = self.user.get("first_name", "Farmer") if self.user else "Farmer"
        greet_lbl = MDLabel(
            text=f"Hello, {first_name}",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.05, 0.23, 0.18, 1),
            size_hint_y=None, height=dp(32),
        )
        title_box.add_widget(welcome_lbl)
        title_box.add_widget(greet_lbl)

        # Right Avatar Circle with Red Notification Dot
        avatar_card = MDCard(
            size_hint=(None, None), size=(dp(46), dp(46)),
            radius=[23, 23, 23, 23],
            md_bg_color=(0.22, 0.60, 0.28, 1),
            elevation=2,
            pos_hint={"center_y": 0.5},
        )
        initials = (first_name[0] if first_name else "F").upper()
        avatar_lbl = MDLabel(
            text=initials,
            halign="center",
            bold=True, font_style="H6",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        avatar_card.add_widget(avatar_lbl)

        # Draw small red badge dot on top right of avatar
        with avatar_card.canvas.after:
            Color(0.92, 0.25, 0.25, 1)
            avatar_card._dot = Ellipse(pos=(avatar_card.right - dp(10), avatar_card.top - dp(10)), size=(dp(10), dp(10)))

        def _upd_dot(inst, *_):
            inst._dot.pos = (inst.right - dp(10), inst.top - dp(10))
        avatar_card.bind(pos=_upd_dot, size=_upd_dot)

        header_row.add_widget(title_box)
        header_row.add_widget(avatar_card)
        box.add_widget(header_row)
        cards.append(header_row)

        # ── 2. "MY CROPS" SECTION ─────────────────────────────────────
        crops_header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(28),
        )
        crops_title = MDLabel(
            text="My Crops",
            font_style="Subtitle1", bold=True,
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
        )
        view_all_btn = MDTextButton(
            text="View All",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.13, 0.77, 0.37, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.edit_crops(),
        )
        crops_header.add_widget(crops_title)
        crops_header.add_widget(view_all_btn)
        box.add_widget(crops_header)
        cards.append(crops_header)

        # Followed crops list
        followed_names = [c[1] for c in self.crops if c[0] in self.followed_crop_ids] if (self.crops and hasattr(self, "followed_crop_ids")) else []
        if not followed_names:
            followed_names = ["Okra", "Cabbage", "Carrots"]

        crop_health_map = {
            "Okra": ("Health: Excellent", "GROWING", (0.88, 0.97, 0.88, 1), (0.13, 0.65, 0.22, 1)),
            "Cabbage": ("Health: Good", "GROWING", (0.88, 0.97, 0.88, 1), (0.13, 0.65, 0.22, 1)),
            "Carrots": ("Health: Optimal", "HARVESTING", (0.98, 0.95, 0.82, 1), (0.75, 0.48, 0.05, 1)),
            "Beans": ("Health: Excellent", "GROWING", (0.88, 0.97, 0.88, 1), (0.13, 0.65, 0.22, 1)),
            "Leeks": ("Health: Good", "PLANTED", (0.90, 0.94, 0.98, 1), (0.12, 0.42, 0.75, 1)),
        }

        for cname in followed_names[:2]:
            h_text, status_tag, tag_bg, tag_fg = crop_health_map.get(
                cname, ("Health: Good", "GROWING", (0.88, 0.97, 0.88, 1), (0.13, 0.65, 0.22, 1))
            )
            crop_card = MDCard(
                orientation="horizontal",
                size_hint_y=None, height=dp(68),
                padding=(dp(10), dp(8), dp(12), dp(8)),
                spacing=dp(12),
                radius=[16, 16, 16, 16],
                md_bg_color=(1, 1, 1, 1),
                elevation=1,
                ripple_behavior=True,
            )

            # Left crop icon container
            icon_box = MDCard(
                size_hint=(None, None), size=(dp(48), dp(48)),
                radius=[12, 12, 12, 12],
                md_bg_color=(0.14, 0.40, 0.28, 0.12),
                elevation=0,
                pos_hint={"center_y": 0.5},
            )
            crop_icon_name = "sprout"
            if cname.lower() == "okra":
                crop_icon_name = "leaf"
            elif cname.lower() == "cabbage":
                crop_icon_name = "flower-tulip"
            elif cname.lower() == "carrots":
                crop_icon_name = "carrot"
            elif cname.lower() == "beans":
                crop_icon_name = "seed"
            elif cname.lower() == "leeks":
                crop_icon_name = "tree"

            icon_lbl = MDIcon(
                icon=crop_icon_name,
                halign="center",
                font_size="26sp",
                theme_text_color="Custom",
                text_color=(0.12, 0.48, 0.28, 1),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
            )
            icon_box.add_widget(icon_lbl)

            info_box = MDBoxLayout(
                orientation="vertical",
                spacing=dp(2),
                pos_hint={"center_y": 0.5},
            )
            c_name_lbl = MDLabel(
                text=cname,
                bold=True, font_style="Subtitle2",
                theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
                size_hint_y=None, height=dp(20),
            )
            c_health_lbl = MDLabel(
                text=f"● {h_text}",
                font_style="Caption",
                theme_text_color="Custom", text_color=(0.02, 0.58, 0.40, 1),
                size_hint_y=None, height=dp(16),
            )
            info_box.add_widget(c_name_lbl)
            info_box.add_widget(c_health_lbl)

            tag_card = MDCard(
                size_hint=(None, None), size=(dp(78), dp(24)),
                radius=[8, 8, 8, 8],
                md_bg_color=tag_bg,
                elevation=0,
                pos_hint={"center_y": 0.5},
                padding=(dp(4), dp(2)),
            )
            tag_lbl = MDLabel(
                text=status_tag,
                halign="center",
                bold=True, font_style="Caption",
                theme_text_color="Custom", text_color=tag_fg,
            )
            tag_card.add_widget(tag_lbl)

            crop_card.add_widget(icon_box)
            crop_card.add_widget(info_box)
            crop_card.add_widget(tag_card)
            box.add_widget(crop_card)
            cards.append(crop_card)

        # ── 3. "QUICK ACTIONS" SECTION ─────────────────────────────────
        actions_title = MDLabel(
            text="Quick Actions",
            font_style="Subtitle1", bold=True,
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
            size_hint_y=None, height=dp(26),
        )
        box.add_widget(actions_title)
        cards.append(actions_title)

        actions_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(105),
            spacing=dp(10),
        )

        quick_actions_data = [
            ("camera-outline", "Check\nHealth", (0.22, 0.85, 0.35, 1), "recommendations"),
            ("comment-text-outline", "Get\nAdvice", (0.22, 0.85, 0.35, 1), "recommendations"),
            ("trending-up", "Market\nPrices", (0.22, 0.85, 0.35, 1), "history"),
        ]

        for icon_name, label_text, circle_clr, target_tab in quick_actions_data:
            act_card = MDCard(
                orientation="vertical",
                size_hint=(0.33, 1),
                radius=[16, 16, 16, 16],
                md_bg_color=(1, 1, 1, 1),
                elevation=1,
                padding=(dp(6), dp(10), dp(6), dp(8)),
                spacing=dp(6),
                ripple_behavior=True,
            )

            circle_icon_box = MDCard(
                size_hint=(None, None), size=(dp(44), dp(44)),
                radius=[22, 22, 22, 22],
                md_bg_color=circle_clr,
                elevation=1,
                pos_hint={"center_x": 0.5},
            )
            act_icon = MDIcon(
                icon=icon_name,
                halign="center",
                font_size="22sp",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
            )
            circle_icon_box.add_widget(act_icon)

            act_lbl = MDLabel(
                text=label_text,
                halign="center",
                bold=True, font_style="Caption",
                theme_text_color="Custom", text_color=(0.10, 0.14, 0.20, 1),
                size_hint_y=None, height=dp(28),
            )
            act_card.add_widget(circle_icon_box)
            act_card.add_widget(act_lbl)

            def _switch_tab(inst, tab_name=target_tab):
                if self.ids.bottom_nav:
                    self.ids.bottom_nav.switch_tab(tab_name)
            act_card.bind(on_release=_switch_tab)
            actions_row.add_widget(act_card)

        box.add_widget(actions_row)
        cards.append(actions_row)

        # ── 4. "NEXT SEASON INSIGHT" CARD ──────────────────────────────
        insight_card = MDCard(
            orientation="vertical",
            size_hint_y=None, height=dp(170),
            radius=[20, 20, 20, 20],
            md_bg_color=(0.04, 0.31, 0.24, 1),
            elevation=2,
            padding=dp(16),
            spacing=dp(8),
        )

        ins_head_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(26),
            spacing=dp(8),
        )
        leaf_icon = MDIcon(
            icon="leaf",
            theme_text_color="Custom", text_color=(0.29, 0.87, 0.50, 1),
            font_size="20sp",
            size_hint=(None, None), size=(dp(24), dp(24)),
        )
        ins_title_lbl = MDLabel(
            text="Next Season Insight",
            bold=True, font_style="Subtitle1",
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
        )
        ins_head_row.add_widget(leaf_icon)
        ins_head_row.add_widget(ins_title_lbl)

        ins_desc_lbl = MDLabel(
            text="Based on current soil conditions and weather forecasts for your region.",
            font_style="Caption",
            theme_text_color="Custom", text_color=(0.78, 0.88, 0.82, 1),
            size_hint_y=None, height=dp(28),
        )

        inner_ins_card = MDCard(
            orientation="vertical",
            size_hint_y=None, height=dp(74),
            radius=[14, 14, 14, 14],
            md_bg_color=(0.08, 0.38, 0.30, 1),
            elevation=0,
            padding=(dp(12), dp(8), dp(12), dp(8)),
            spacing=dp(2),
        )

        opt_head_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(20),
        )
        opt_lbl = MDLabel(
            text="OPTIMAL PLANTING TIME",
            bold=True, font_style="Caption",
            theme_text_color="Custom", text_color=(0.65, 0.85, 0.72, 1),
        )
        yield_tag = MDCard(
            size_hint=(None, None), size=(dp(76), dp(18)),
            radius=[6, 6, 6, 6],
            md_bg_color=(0.13, 0.77, 0.37, 1),
            elevation=0,
        )
        yield_lbl = MDLabel(
            text="HIGH YIELD",
            halign="center",
            bold=True, font_style="Caption",
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
        )
        yield_tag.add_widget(yield_lbl)
        opt_head_row.add_widget(opt_lbl)
        opt_head_row.add_widget(yield_tag)

        crop_highlight_lbl = MDLabel(
            text="Carrots",
            bold=True, font_style="Subtitle1",
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
            size_hint_y=None, height=dp(22),
        )
        date_range_lbl = MDLabel(
            text="Oct 15 - Oct 22",
            bold=True, font_style="Body2",
            theme_text_color="Custom", text_color=(0.29, 0.87, 0.50, 1),
            size_hint_y=None, height=dp(18),
        )

        inner_ins_card.add_widget(opt_head_row)
        inner_ins_card.add_widget(crop_highlight_lbl)
        inner_ins_card.add_widget(date_range_lbl)

        insight_card.add_widget(ins_head_row)
        insight_card.add_widget(ins_desc_lbl)
        insight_card.add_widget(inner_ins_card)

        box.add_widget(insight_card)
        cards.append(insight_card)

        # ── 5. WEATHER BANNER AT BOTTOM ───────────────────────────────
        w_data = get_weather_impact_analysis(region_id=self.user.get("region_id")) if self.user else {}
        w_cond = w_data.get("condition", "Sunny Interval")
        w_temp = w_data.get("avg_temp_c", 28.0)

        weather_card = MDCard(
            orientation="horizontal",
            size_hint_y=None, height=dp(70),
            radius=[16, 16, 16, 16],
            md_bg_color=(0.91, 0.98, 0.94, 1),
            elevation=0,
            padding=(dp(14), dp(10), dp(14), dp(10)),
            spacing=dp(10),
        )

        sun_icon = MDIcon(
            icon="weather-sunny",
            font_size="32sp",
            theme_text_color="Custom", text_color=(0.96, 0.62, 0.07, 1),
            size_hint=(None, None), size=(dp(36), dp(36)),
            pos_hint={"center_y": 0.5},
        )

        w_text_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2),
            pos_hint={"center_y": 0.5},
        )
        w_title = MDLabel(
            text=w_cond if w_cond else "Sunny Interval",
            bold=True, font_style="Subtitle2",
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
            size_hint_y=None, height=dp(20),
        )
        w_sub = MDLabel(
            text="Low humidity, good for spraying",
            font_style="Caption",
            theme_text_color="Custom", text_color=(0.40, 0.55, 0.45, 1),
            size_hint_y=None, height=dp(18),
        )
        w_text_box.add_widget(w_title)
        w_text_box.add_widget(w_sub)

        w_right_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(0),
            size_hint_x=None, width=dp(70),
            pos_hint={"center_y": 0.5},
        )
        temp_lbl = MDLabel(
            text=f"{w_temp:.0f}°C",
            halign="right", bold=True, font_style="H5",
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
            size_hint_y=None, height=dp(28),
        )
        today_lbl = MDLabel(
            text="TODAY",
            halign="right", bold=True, font_style="Caption",
            theme_text_color="Custom", text_color=(0.20, 0.70, 0.40, 1),
            size_hint_y=None, height=dp(14),
        )
        w_right_box.add_widget(temp_lbl)
        w_right_box.add_widget(today_lbl)

        weather_card.add_widget(sun_icon)
        weather_card.add_widget(w_text_box)
        weather_card.add_widget(w_right_box)

        box.add_widget(weather_card)
        cards.append(weather_card)

        # Fix inner height
        def _fix(*_):
            box.height = box.minimum_height
        Clock.schedule_once(_fix, 0)

        stagger_fade_in(cards[1:], step=0.04, duration=0.28)
        center_scroll_content(box.parent, box)

    def _refresh_home(self, *_):
        show_snackbar("Refreshing market data…")
        Clock.schedule_once(lambda dt: self.load_home(), 0.3)

    def _make_price_card(self, row):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel

        change = row["change_pct"]
        if change is None:
            change_txt, chg_color = "", (0.42, 0.42, 0.42, 1)
            bg = (0.93, 0.97, 0.93, 1)
        elif change >= 0:
            change_txt = f"▲ {change}%"
            chg_color = (0.22, 0.60, 0.28, 1)
            bg = (0.92, 0.98, 0.92, 1)
        else:
            change_txt = f"▼ {change}%"
            chg_color = (0.85, 0.20, 0.20, 1)
            bg = (1, 0.95, 0.95, 1)

        card = MDCard(
            orientation="horizontal", size_hint_y=None, height=dp(60),
            padding=dp(14), spacing=dp(10),
            radius=[14, 14, 14, 14],
            md_bg_color=bg, elevation=0,
            ripple_behavior=True,
        )
        # left accent strip
        from kivy.graphics import Color, Rectangle
        accent_clr = chg_color[:3] + (0.7,)
        with card.canvas.before:
            Color(*accent_clr)
            card._accent = Rectangle(pos=card.pos, size=(dp(4), card.height))

        def _update_accent(*_):
            card._accent.pos = card.pos
            card._accent.size = (dp(4), card.height)
        card.bind(pos=_update_accent, size=_update_accent)

        name_lbl = MDLabel(
            text=row["crop"], bold=True,
            theme_text_color="Custom", text_color=(0.08, 0.08, 0.08, 1),
        )
        price_txt = f"LKR {row['price']:.0f}/kg" if row["price"] else "No data"
        price_lbl = MDLabel(
            text=price_txt, halign="right",
            theme_text_color="Custom", text_color=(0.18, 0.18, 0.18, 1),
        )
        change_lbl = MDLabel(
            text=change_txt, halign="right", bold=True,
            size_hint_x=0.38,
            theme_text_color="Custom", text_color=chg_color,
        )
        card.add_widget(name_lbl)
        card.add_widget(price_lbl)
        card.add_widget(change_lbl)

        orig_bg = bg
        card.bind(on_release=lambda inst: ripple_flash(
            inst, (0.80, 0.95, 0.82, 1), orig_bg))
        return card

    def _build_weather_cards(self, w_data):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel
        from kivymd.uix.boxlayout import MDBoxLayout

        widgets = []

        # Snapshot card (rain / temp / humidity)
        snap = MDCard(
            orientation="vertical", size_hint_y=None, height=dp(90),
            padding=dp(14), spacing=dp(6),
            radius=[14, 14, 14, 14],
            md_bg_color=(0.90, 0.94, 0.99, 1), elevation=0,
        )
        top_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        top_row.add_widget(MDLabel(
            text=f"Condition: {w_data.get('condition', '')}",
            bold=True, theme_text_color="Custom", text_color=(0.10, 0.20, 0.38, 1),
        ))
        top_row.add_widget(MDLabel(
            text=f"● {w_data.get('record_date', '')}",
            halign="right", font_style="Caption",
            theme_text_color="Custom", text_color=(0.42, 0.47, 0.57, 1),
        ))

        stat_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        for txt in [
            f"● Rain\n{w_data.get('rainfall_mm', 0):.0f} mm",
            f"● Temp\n{w_data.get('avg_temp_c', 0):.1f} °C",
            f"● Humidity\n{w_data.get('humidity_pct', 0):.0f} %",
        ]:
            stat_row.add_widget(MDLabel(
                text=txt, font_style="Caption", halign="center",
                theme_text_color="Custom", text_color=(0.15, 0.25, 0.42, 1),
            ))

        snap.add_widget(top_row)
        snap.add_widget(stat_row)
        widgets.append(snap)

        # Risk / irrigation / yield cards
        advisory_items = [
            {
                "icon": "●", "title": "Disease Risk",
                "value": w_data.get("harvest_risk", ""),
                "detail": w_data.get("harvest_risk_detail", ""),
                "bg": (1, 0.95, 0.92, 1), "title_color": (0.78, 0.28, 0.10, 1),
            },
            {
                "icon": "●", "title": "Irrigation Advisory",
                "value": w_data.get("irrigation_advice", ""),
                "detail": w_data.get("irrigation_advice_detail", ""),
                "bg": (0.91, 0.95, 1, 1), "title_color": (0.12, 0.38, 0.72, 1),
            },
            {
                "icon": "●", "title": "Yield Outlook",
                "value": w_data.get("yield_impact", ""),
                "detail": w_data.get("yield_impact_detail", ""),
                "bg": (0.91, 0.97, 0.91, 1), "title_color": (0.18, 0.52, 0.22, 1),
            },
        ]
        for itm in advisory_items:
            c = MDCard(
                orientation="vertical", size_hint_y=None, height=dp(72),
                padding=(dp(12), dp(8), dp(12), dp(8)), spacing=dp(2),
                radius=[12, 12, 12, 12],
                md_bg_color=itm["bg"], elevation=0, ripple_behavior=True,
            )
            c.add_widget(MDLabel(
                text=f"{itm['icon']} {itm['title']}: {itm['value']}",
                bold=True, font_style="Body2",
                theme_text_color="Custom", text_color=itm["title_color"],
                size_hint_y=None, height=dp(22),
            ))
            c.add_widget(MDLabel(
                text=itm["detail"], font_style="Caption",
                theme_text_color="Custom", text_color=(0.38, 0.38, 0.38, 1),
            ))
            widgets.append(c)

        return widgets

    def _make_divider(self):
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        d = MDBoxLayout(size_hint_y=None, height=dp(1),
                        md_bg_color=(0.88, 0.88, 0.88, 1))
        return d

    # ══════════════════════════════════════════════════════════════════════
    # RECOMMENDATIONS TAB
    # ══════════════════════════════════════════════════════════════════════
    def load_recommendations(self):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton

        box = self.ids.rec_box
        box.clear_widgets()
        recs = get_recommendations_for_user(self.user["user_id"])

        if not recs:
            # Animated empty state
            empty_box = MDBoxLayout(
                orientation="vertical", spacing=dp(12),
                size_hint_y=None, height=dp(200),
                padding=(dp(20), dp(40), dp(20), dp(20)),
            )
            icon_lbl = MDLabel(
                text="●", halign="center", font_style="H2",
                size_hint_y=None, height=dp(60),
            )
            msg_lbl = MDLabel(
                text="No recommendations yet.\nCheck back after your crops are updated.",
                halign="center", theme_text_color="Custom",
                text_color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None, height=dp(60),
            )
            empty_box.add_widget(icon_lbl)
            empty_box.add_widget(msg_lbl)
            box.add_widget(empty_box)
            fade_in(empty_box, duration=0.4)
            center_scroll_content(box.parent, box)
            return

        cards = []
        for idx, r in enumerate(recs):
            accent_colors = [
                (0.22, 0.60, 0.28, 1),
                (0.12, 0.38, 0.72, 1),
                (0.78, 0.50, 0.10, 1),
            ]
            accent = accent_colors[idx % len(accent_colors)]

            card = MDCard(
                orientation="vertical", size_hint_y=None, height=dp(68),
                padding=(dp(16), dp(10), dp(16), dp(10)), spacing=dp(2),
                radius=[14, 14, 14, 14],
                md_bg_color=(1, 1, 1, 1), elevation=1,
                ripple_behavior=True,
            )

            # left accent bar
            from kivy.graphics import Color, Rectangle
            with card.canvas.before:
                Color(*accent)
                card._acc = Rectangle(pos=card.pos, size=(dp(4), card.height))

            def _upd(inst, *_):
                inst._acc.pos = inst.pos
                inst._acc.size = (dp(4), inst.height)
            card.bind(pos=_upd, size=_upd)

            msg_lbl = MDLabel(
                text=r["message"], theme_text_color="Custom",
                text_color=(0.10, 0.10, 0.10, 1),
            )
            date_lbl = MDLabel(
                text=r["created_at"].strftime("%d %b %Y"),
                font_style="Caption", theme_text_color="Custom",
                text_color=(0.55, 0.55, 0.55, 1),
                size_hint_y=None, height=dp(16),
            )
            card.add_widget(msg_lbl)
            card.add_widget(date_lbl)

            # Accordion expand on tap
            card._collapsed = True
            card._msg_lbl = msg_lbl
            card.bind(on_release=lambda inst: self._toggle_rec_card(inst))

            box.add_widget(card)
            cards.append(card)

        stagger_fade_in(cards, step=0.06, duration=0.30)
        center_scroll_content(box.parent, box)

    def _toggle_rec_card(self, card):
        if card._collapsed:
            Animation(height=dp(110), duration=0.22, t="out_quad").start(card)
            card._collapsed = False
        else:
            Animation(height=dp(68), duration=0.18, t="in_quad").start(card)
            card._collapsed = True
        bounce_scale(card)

    # ══════════════════════════════════════════════════════════════════════
    # ALERTS TAB
    # ══════════════════════════════════════════════════════════════════════
    def load_alerts(self):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel
        from kivymd.uix.button import MDIconButton

        box = self.ids.alert_box
        box.clear_widgets()
        alerts = get_alerts_for_user(self.user["user_id"])

        if not alerts:
            empty = MDLabel(
                text="●  All caught up! No alerts right now.",
                halign="center", theme_text_color="Custom",
                text_color=(0.45, 0.45, 0.45, 1),
                size_hint_y=None, height=dp(60),
            )
            box.add_widget(empty)
            fade_in(empty, duration=0.35)
            center_scroll_content(box.parent, box)
            return

        cards = []
        for a in alerts:
            is_unread = not a["is_read"]
            bg = (0.92, 0.98, 0.92, 1) if is_unread else (0.97, 0.97, 0.97, 1)

            card = MDCard(
                orientation="horizontal", size_hint_y=None, height=dp(72),
                padding=(dp(12), dp(10), dp(8), dp(10)), spacing=dp(8),
                radius=[14, 14, 14, 14],
                md_bg_color=bg,
                elevation=2 if is_unread else 0,
            )

            icon_name = "alert-circle" if is_unread else "check-circle-outline"
            icon_clr = (0.90, 0.50, 0.10, 1) if is_unread else (0.65, 0.65, 0.65, 1)
            icon = MDIconButton(
                icon=icon_name,
                theme_text_color="Custom", text_color=icon_clr,
                disabled=True, size_hint_x=None, width=dp(36),
            )
            msg_lbl = MDLabel(
                text=a["message"], theme_text_color="Custom",
                text_color=(0.10, 0.10, 0.10, 1) if is_unread else (0.50, 0.50, 0.50, 1),
            )
            card.add_widget(icon)
            card.add_widget(msg_lbl)

            if is_unread:
                dismiss_btn = MDIconButton(
                    icon="close-circle-outline",
                    theme_text_color="Custom", text_color=(0.65, 0.65, 0.65, 1),
                    size_hint_x=None, width=dp(36),
                    on_release=lambda x, aid=a["id"], c=card: self.dismiss_alert(aid, c),
                )
                card.add_widget(dismiss_btn)
                # pulse unread card
                Clock.schedule_once(
                    lambda dt, c=card, bg=bg: pulse_color(
                        c,
                        bg,
                        (0.82, 0.96, 0.82, 1),
                        duration=1.2,
                    ), 0.5
                )

            box.add_widget(card)
            cards.append(card)

        stagger_fade_in(cards, step=0.06, duration=0.28)
        center_scroll_content(box.parent, box)

    def dismiss_alert(self, alert_id, card):
        def _remove():
            mark_alert_read(alert_id)
            if card.parent:
                card.parent.remove_widget(card)

        fade_out_remove(card, duration=0.25, callback=_remove)

    def mark_all_alerts_read(self):
        alerts = get_alerts_for_user(self.user["user_id"])
        for a in alerts:
            if not a["is_read"]:
                mark_alert_read(a["id"])
        show_snackbar("All alerts marked as read.")
        self.load_alerts()

    # ══════════════════════════════════════════════════════════════════════
    # HISTORY TAB
    # ══════════════════════════════════════════════════════════════════════
    def _build_history_crop_chips(self):
        """Build the scrollable chip row for History tab."""
        row = self.ids.history_crop_chips
        row.clear_widgets()
        self._history_chip_widgets = {}
        followed = [c for c in (self.crops or []) if c[0] in self.followed_crop_ids]

        for crop_id, crop_name in followed:
            chip = self._make_hist_chip(crop_id, crop_name)
            row.add_widget(chip)
            self._history_chip_widgets[crop_id] = chip

        # select first
        if followed:
            self.history_crop_id, self.history_crop_name = followed[0]
            self._select_history_chip(followed[0][0])
        else:
            self.history_crop_id, self.history_crop_name = None, None

    def _make_hist_chip(self, crop_id, crop_name):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel

        chip = MDCard(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(80), height=dp(34),
            radius=[17, 17, 17, 17],
            elevation=0, ripple_behavior=True,
            md_bg_color=(0.90, 0.95, 0.90, 1),
            padding=(dp(8), dp(4), dp(8), dp(4)),
        )
        lbl = MDLabel(
            text=crop_name, halign="center",
            font_style="Caption", bold=False,
            theme_text_color="Custom", text_color=(0.22, 0.55, 0.25, 1),
        )
        chip.add_widget(lbl)
        chip._lbl = lbl
        chip.bind(on_release=lambda inst, cid=crop_id, cn=crop_name:
                  self._pick_history_chip(cid, cn))
        return chip

    def _select_history_chip(self, crop_id):
        for cid, chip in self._history_chip_widgets.items():
            sel = cid == crop_id
            Animation(md_bg_color=(0.22, 0.60, 0.28, 1) if sel else (0.90, 0.95, 0.90, 1),
                      duration=0.18).start(chip)
            chip._lbl.text_color = (1, 1, 1, 1) if sel else (0.22, 0.55, 0.25, 1)
            chip._lbl.bold = sel

    def _pick_history_chip(self, crop_id, crop_name):
        self.history_crop_id = crop_id
        self.history_crop_name = crop_name
        self._select_history_chip(crop_id)
        bounce_scale(self._history_chip_widgets[crop_id])
        self.load_history()

    def set_metric(self, metric):
        self.history_metric = metric
        price_bg = (0.22, 0.60, 0.28, 1) if metric == "price" else (0.90, 0.95, 0.90, 1)
        prod_bg  = (0.22, 0.60, 0.28, 1) if metric == "production" else (0.90, 0.95, 0.90, 1)
        price_txt = (1, 1, 1, 1) if metric == "price" else (0.3, 0.3, 0.3, 1)
        prod_txt  = (1, 1, 1, 1) if metric == "production" else (0.3, 0.3, 0.3, 1)
        Animation(md_bg_color=price_bg, duration=0.2).start(self.ids.pill_price_btn)
        Animation(md_bg_color=prod_bg, duration=0.2).start(self.ids.pill_prod_btn)
        self.ids.pill_price_btn.text_color = price_txt
        self.ids.pill_prod_btn.text_color = prod_txt
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
                box.add_widget(MDLabel(
                    text="No price history available yet.",
                    theme_text_color="Custom", text_color=(0.45, 0.45, 0.45, 1),
                    halign="center",
                ))
                center_scroll_content(box.parent, box)
                return
            dates, values = zip(*data)
            chart = build_line_chart(
                list(dates), list(values),
                title=f"{self.history_crop_name} — price (last 16 weeks)",
                y_label="LKR / kg",
            )
        else:
            data = get_production_history(self.history_crop_id, region_id=region_id, weeks=16)
            if not data:
                box.add_widget(MDLabel(
                    text="No production history available yet.",
                    theme_text_color="Custom", text_color=(0.45, 0.45, 0.45, 1),
                    halign="center",
                ))
                center_scroll_content(box.parent, box)
                return
            dates, values = zip(*data)
            chart = build_bar_chart(
                list(dates), list(values),
                title=f"{self.history_crop_name} — production (last 16 weeks)",
                y_label="kg",
            )

        chart.size_hint_y = None
        chart.height = dp(320)
        chart.size_hint_x = 1
        chart.pos_hint = {"center_x": 0.5}
        chart.opacity = 0
        box.add_widget(chart)
        # Fade in after slight delay
        fade_in(chart, delay=0.15, duration=0.35)
        center_scroll_content(box.parent, box)

    # ══════════════════════════════════════════════════════════════════════
    # PROFILE TAB
    # ══════════════════════════════════════════════════════════════════════
    def load_profile(self):
        from kivymd.uix.label import MDLabel
        from kivymd.uix.button import MDRaisedButton
        from kivymd.uix.card import MDCard
        from kivymd.uix.boxlayout import MDBoxLayout

        box = self.ids.profile_box
        box.clear_widgets()

        # ── avatar circle with initials ───────────────────────────────
        avatar_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(100),
            spacing=dp(4),
        )
        avatar_card = MDCard(
            size_hint=(None, None), size=(dp(72), dp(72)),
            radius=[36, 36, 36, 36],
            md_bg_color=(0.22, 0.60, 0.28, 1),
            elevation=4,
            pos_hint={"center_x": 0.5},
        )
        initials = (
            (self.user.get("first_name", "?")[0] +
             self.user.get("last_name", "?")[0]).upper()
        )
        init_lbl = MDLabel(
            text=initials, halign="center", valign="middle",
            font_style="H5", bold=True,
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
        )
        avatar_card.add_widget(init_lbl)
        avatar_box.add_widget(avatar_card)
        avatar_box.add_widget(MDLabel(
            text=f"{self.user['first_name']} {self.user['last_name']}",
            halign="center", font_style="Subtitle1", bold=True,
            theme_text_color="Custom", text_color=(0.10, 0.10, 0.10, 1),
            size_hint_y=None, height=dp(24),
        ))
        box.add_widget(avatar_box)

        # ── profile info card ────────────────────────────────────────
        info_card = MDCard(
            orientation="vertical", padding=dp(16), spacing=dp(6),
            size_hint_y=None, height=dp(100), radius=[16, 16, 16, 16],
            md_bg_color=(0.93, 0.98, 0.93, 1), elevation=0,
        )
        info_card.add_widget(MDLabel(
            text=self.user["email"],
            theme_text_color="Custom", text_color=(0.40, 0.40, 0.40, 1),
            font_style="Caption",
        ))
        info_card.add_widget(MDLabel(
            text=f"Role: {self.user['user_type'].capitalize()}",
            theme_text_color="Custom", text_color=(0.22, 0.60, 0.28, 1),
        ))
        info_card.add_widget(MDLabel(
            text=f"District: {self.user.get('district') or '—'}",
            theme_text_color="Custom", text_color=(0.22, 0.60, 0.28, 1),
        ))
        box.add_widget(info_card)

        # ── action buttons ────────────────────────────────────────────
        def _btn(text, bg, callback, txt_color=(1, 1, 1, 1)):
            b = MDRaisedButton(
                text=text, size_hint_x=1,
                md_bg_color=bg, text_color=txt_color,
                elevation=2, _radius=12,
                on_release=callback,
            )
            return b

        edit_btn      = _btn("●  Edit Profile Details",  (0.22, 0.60, 0.28, 1), self.open_edit_profile_dialog)
        crops_btn     = _btn("●  Edit Followed Crops",    (0.38, 0.75, 0.40, 1), self.edit_crops)
        feedback_btn  = _btn("●  Send Feedback",          (0.91, 0.96, 0.91, 1), self.go_feedback,
                              txt_color=(0.10, 0.10, 0.10, 1))
        logout_btn    = _btn("●  Log Out",                (0.85, 0.20, 0.20, 1), self.logout)

        for b in [edit_btn, crops_btn, feedback_btn, logout_btn]:
            box.add_widget(b)

        stagger_fade_in([avatar_box, info_card, edit_btn, crops_btn, feedback_btn, logout_btn],
                        step=0.06, duration=0.28)
        center_scroll_content(box.parent, box)

    # ══════════════════════════════════════════════════════════════════════
    # EDIT PROFILE DIALOG
    # ══════════════════════════════════════════════════════════════════════
    def open_edit_profile_dialog(self, *args):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton, MDRaisedButton
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.menu import MDDropdownMenu
        from database.data_service import get_all_regions, update_user_profile

        dialog_box = MDBoxLayout(
            orientation="vertical", spacing=dp(12),
            padding=[dp(12), dp(12), dp(12), dp(12)],
            size_hint_y=None, height=dp(200),
        )
        fn_input = MDTextField(
            text=self.user.get("first_name", ""), hint_text="First Name",
            size_hint_y=None, height=dp(50),
            line_color_focus=(0.25, 0.62, 0.30, 1),
        )
        ln_input = MDTextField(
            text=self.user.get("last_name", ""), hint_text="Last Name",
            size_hint_y=None, height=dp(50),
            line_color_focus=(0.25, 0.62, 0.30, 1),
        )
        regions = get_all_regions()
        selected_region = {"id": self.user.get("region_id")}
        curr_dist = self.user.get("district") or "Select District"
        region_btn = MDRaisedButton(
            text=f"District: {curr_dist}  ▾", size_hint_x=1,
            md_bg_color=(0.91, 0.96, 0.91, 1), text_color=(0.1, 0.1, 0.1, 1),
        )

        def pick_region(r_id, r_dist, menu):
            selected_region["id"] = r_id
            region_btn.text = f"District: {r_dist}  ▾"
            menu.dismiss()

        def open_region_menu(*_):
            items = [
                {"text": f"{dist} ({rname})", "viewclass": "OneLineListItem",
                 "on_release": lambda rid=rid, rdist=dist: pick_region(rid, rdist, menu)}
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
                self.user["user_id"], first_name=fn, last_name=ln,
                region_id=selected_region["id"],
            )
            if ok:
                self.user = res
                self.app.current_user = res
                self.edit_dialog.dismiss()
                self.load_profile()
                self.load_home()
                show_snackbar("Profile updated successfully!")
            else:
                show_snackbar(f"Failed to update: {res}")

        self.edit_dialog = MDDialog(
            title="Edit Profile Details", type="custom",
            content_cls=dialog_box,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.edit_dialog.dismiss()),
                MDRaisedButton(text="SAVE", md_bg_color=(0.25, 0.62, 0.30, 1),
                               on_release=save_profile),
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
