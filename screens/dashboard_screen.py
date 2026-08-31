"""
Dashboard screen – full interactive overhaul.
• Gradient header banner in Home tab with weather badge and refresh button
• Slide-up-fade-in card animations on every tab load
• Recommendations: accordion expand/collapse on tap
• Alerts: animated dismiss + pulse for unread + mark-all-read button
• History: pill toggle switch + chip crop selector
• Profile: avatar circle with initials, bounce-scale buttons
"""
from datetime import datetime, timedelta
import threading
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from database.data_service import (
    get_market_summary, get_recommendations_for_user, get_alerts_for_user,
    mark_alert_read, get_all_crops, get_price_history, get_production_history,
    get_user_preferred_crop_ids, get_market_demand_trends, get_weather_impact_analysis,
    get_latest_prices_for_crops, get_lag_features_for_crops, get_current_weather,
    save_ml_alert, save_ml_recommendation, get_last_ml_run_time,
    clear_old_ml_data, get_crop_name_to_id_map, get_region_district,
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

    _ml_predictions_cache = None   # cached ML predictions dict
    _ml_running = False            # guard against parallel ML runs

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
        if self.ids.get("bottom_nav"):
            self.ids.bottom_nav.switch_tab("home")
        self.load_home()
        self._build_history_crop_chips()
        # Trigger ML predictions in background
        self._run_ml_predictions_async()

    def _run_ml_predictions_async(self):
        """Run ML predictions in a background thread, then persist
        recommendations & alerts to the DB.  Uses 24h caching."""
        if self._ml_running:
            return
        user_id = self.user["user_id"]
        # Check 24h cache
        last_run = get_last_ml_run_time(user_id)
        if last_run and (datetime.utcnow() - last_run) < timedelta(hours=24):
            print("[ML] Using cached predictions (< 24h old).")
            return
        self._ml_running = True
        t = threading.Thread(target=self._ml_worker, daemon=True)
        t.start()

    def _ml_worker(self):
        """Background thread: run models, generate recs & alerts, save to DB."""
        try:
            from utils.ml_engine import run_all_predictions
            from utils.recommendation_engine import generate_recommendations
            from utils.alert_engine import generate_alerts

            user_id = self.user["user_id"]
            region_id = self.user.get("region_id")
            district = get_region_district(region_id) if region_id else "Kandy"

            # Gather crop names the user follows
            crop_names = [c[1] for c in self.crops
                          if c[0] in self.followed_crop_ids]
            if not crop_names:
                crop_names = [c[1] for c in self.crops] if self.crops else []

            # Fetch live data from DB for model features
            weather = get_current_weather(region_id)
            lag_data = get_lag_features_for_crops(region_id)
            current_prices = get_latest_prices_for_crops(region_id)

            # Run all 3 models
            predictions = run_all_predictions(
                district=district,
                vegetable_names=crop_names,
                current_weather=weather,
                lag_data=lag_data,
            )
            self._ml_predictions_cache = predictions

            # Generate recommendations & alerts
            recs = generate_recommendations(predictions, current_prices)
            alerts = generate_alerts(predictions, current_prices)

            # Clear old data and save fresh
            clear_old_ml_data(user_id)

            for rec in recs:
                save_ml_recommendation(
                    message=rec["message"],
                    user_id=user_id,
                    region_id=region_id,
                )

            for alert in alerts:
                save_ml_alert(
                    alert_type=alert["alert_type"],
                    message=alert["message"],
                    user_id=user_id,
                )

            print(f"[ML] Generated {len(recs)} recommendations, {len(alerts)} alerts.")
        except Exception as e:
            print(f"[ML] Background prediction error: {e}")
        finally:
            self._ml_running = False

    # ══════════════════════════════════════════════════════════════════════
    # HOME TAB
    # ══════════════════════════════════════════════════════════════════════
    def load_home(self):
        box = self.ids.home_box
        role = self.user.get("user_type", "farmer") if self.user else "farmer"
        if role == "trader":
            self._load_trader_home(box)
            return
        if role == "policymaker":
            self._load_policymaker_home(box)
            return
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton, MDTextButton
        from kivy.graphics import Color, Ellipse

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

    def _load_policymaker_home(self, box):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton
        from kivy.graphics import Color, Rectangle, RoundedRectangle
        from kivy.uix.widget import Widget

        box.clear_widgets()
        box.padding = (dp(16), dp(14), dp(16), dp(24))
        box.spacing = dp(14)
        cards = []

        # ── 1. HEADER ─────────────────────────────────────────────────────────
        header_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(52),
            spacing=dp(8),
        )
        hdr_text = MDBoxLayout(orientation="vertical", spacing=dp(2))
        hdr_title = MDLabel(
            text="Policymaker Overview",
            font_style="H6", bold=True,
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
            size_hint_y=None, height=dp(28),
        )
        hdr_sub = MDLabel(
            text="AGRISENSE STRATEGIC DATA",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.42, 0.47, 0.55, 1),
            size_hint_y=None, height=dp(16),
        )
        hdr_text.add_widget(hdr_title)
        hdr_text.add_widget(hdr_sub)

        avatar_card = MDCard(
            size_hint=(None, None), size=(dp(38), dp(38)),
            radius=[19, 19, 19, 19],
            md_bg_color=(0.22, 0.60, 0.28, 1),
            elevation=1,
            pos_hint={"center_y": 0.5},
        )
        first_name = self.user.get("first_name", "P") if self.user else "P"
        avatar_lbl = MDLabel(
            text=first_name[0].upper(),
            halign="center", bold=True, font_style="H6",
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
        )
        avatar_card.add_widget(avatar_lbl)
        header_row.add_widget(hdr_text)
        header_row.add_widget(avatar_card)
        box.add_widget(header_row)
        cards.append(header_row)

        # ── 2. STAT CARDS (Food Security + Yield Growth) ────────────────────
        stats_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(86),
            spacing=dp(12),
        )

        stat_data = [
            {
                "label": "FOOD SECURITY",
                "value": "78.4",
                "sub": "+2.1%",
                "sub_color": (0.13, 0.65, 0.22, 1),
                "icon": "shield-check",
                "icon_color": (0.22, 0.80, 0.30, 1),
                "bg": (1, 1, 1, 1),
            },
            {
                "label": "YIELD GROWTH",
                "value": "4.2%",
                "sub": "↑ Almost",
                "sub_color": (0.13, 0.65, 0.22, 1),
                "icon": "chart-bar",
                "icon_color": (0.22, 0.80, 0.30, 1),
                "bg": (1, 1, 1, 1),
            },
        ]

        for sd in stat_data:
            sc = MDCard(
                orientation="vertical",
                size_hint=(0.5, 1),
                radius=[14, 14, 14, 14],
                md_bg_color=sd["bg"],
                elevation=1,
                padding=(dp(12), dp(10), dp(10), dp(10)),
                spacing=dp(2),
                ripple_behavior=True,
            )
            top_row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(22),
            )
            s_lbl = MDLabel(
                text=sd["label"],
                font_style="Caption", bold=True,
                theme_text_color="Custom", text_color=(0.13, 0.65, 0.22, 1),
            )
            s_icon = MDIcon(
                icon=sd["icon"],
                font_size="18sp",
                theme_text_color="Custom", text_color=sd["icon_color"],
                size_hint=(None, None), size=(dp(22), dp(22)),
            )
            top_row.add_widget(s_lbl)
            top_row.add_widget(s_icon)
            s_val = MDLabel(
                text=sd["value"],
                font_style="H5", bold=True,
                theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
                size_hint_y=None, height=dp(30),
            )
            s_sub = MDLabel(
                text=sd["sub"],
                font_style="Caption",
                theme_text_color="Custom", text_color=sd["sub_color"],
                size_hint_y=None, height=dp(16),
            )
            sc.add_widget(top_row)
            sc.add_widget(s_val)
            sc.add_widget(s_sub)
            stats_row.add_widget(sc)

        box.add_widget(stats_row)
        cards.append(stats_row)

        # ── 3. REGIONAL PRODUCTION HEATMAP ───────────────────────────────────
        hmap_header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(26),
        )
        hmap_title = MDLabel(
            text="REGIONAL PRODUCTION HEATMAP",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.10, 0.14, 0.20, 1),
        )
        filter_pill = MDCard(
            size_hint=(None, None), size=(dp(58), dp(22)),
            radius=[8, 8, 8, 8],
            md_bg_color=(0.92, 0.97, 0.92, 1),
            elevation=0,
            pos_hint={"center_y": 0.5},
            padding=(dp(2), dp(2)),
        )
        filter_lbl = MDLabel(
            text="▾ Filter",
            halign="center", font_style="Caption",
            theme_text_color="Custom", text_color=(0.22, 0.60, 0.28, 1),
        )
        filter_pill.add_widget(filter_lbl)
        hmap_header.add_widget(hmap_title)
        hmap_header.add_widget(filter_pill)
        box.add_widget(hmap_header)
        cards.append(hmap_header)

        # 3x3 heatmap grid
        heatmap_data = [
            # (label, intensity 0.0-1.0, tooltip)
            ("North", 0.75, "High"),
            ("", 0.85, "High"),
            ("", 0.30, "Low"),
            ("Mid", 0.55, "Mid"),
            ("Dist. A\n450 Tons", 0.40, "Mid"),
            ("", 0.60, "Mid"),
            ("", 0.20, "Low"),
            ("", 0.80, "High"),
            ("South", 0.50, "Mid"),
        ]

        hmap_card = MDCard(
            size_hint_y=None, height=dp(248),
            radius=[16, 16, 16, 16],
            md_bg_color=(1, 1, 1, 1),
            elevation=1,
            padding=(dp(10), dp(10), dp(10), dp(10)),
            spacing=dp(8),
            orientation="vertical",
        )

        grid_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(150),
            spacing=dp(4),
        )

        row_idx = 0
        for r in range(3):
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(44),
                spacing=dp(4),
            )
            for c in range(3):
                item = heatmap_data[row_idx]
                intensity = item[1]
                # Map intensity to green shade: low = light, high = dark
                green = 0.35 + intensity * 0.40
                r_val = 0.80 - intensity * 0.50
                g_val = green
                b_val = 0.50 - intensity * 0.35
                cell = MDCard(
                    size_hint=(0.33, 1),
                    radius=[8, 8, 8, 8],
                    md_bg_color=(r_val, g_val, b_val, 1),
                    elevation=0,
                    padding=(dp(2), dp(2)),
                )
                cell_lbl = MDLabel(
                    text=item[0],
                    halign="center", font_style="Caption",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 0.92) if intensity > 0.45 else (0.20, 0.20, 0.20, 1),
                )
                cell.add_widget(cell_lbl)
                row.add_widget(cell)
                row_idx += 1
            grid_box.add_widget(row)

        # Legend bar below the grid
        legend_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(46),
            spacing=dp(3),
        )
        legend_bar_box = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(10),
            spacing=dp(2),
        )
        for shade_i in range(6):
            t = shade_i / 5.0
            shade_card = MDCard(
                size_hint=(0.16, 1),
                radius=[3, 3, 3, 3],
                md_bg_color=(0.80 - t * 0.50, 0.35 + t * 0.40, 0.50 - t * 0.35, 1),
                elevation=0,
            )
            legend_bar_box.add_widget(shade_card)

        legend_labels = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(14),
        )
        legend_labels.add_widget(MDLabel(
            text="Low",
            font_style="Caption", halign="left",
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
        ))
        legend_labels.add_widget(MDLabel(
            text="High",
            font_style="Caption", halign="right",
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
        ))
        legend_lbl_top = MDLabel(
            text="PRODUCTION VOLUME",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
            size_hint_y=None, height=dp(13),
        )
        legend_box.add_widget(legend_lbl_top)
        legend_box.add_widget(legend_bar_box)
        legend_box.add_widget(legend_labels)

        hmap_card.add_widget(grid_box)
        hmap_card.add_widget(legend_box)
        box.add_widget(hmap_card)
        cards.append(hmap_card)

        # ── 4. PRODUCTION VS DEMAND BARS ──────────────────────────────────────
        pvd_title = MDLabel(
            text="PRODUCTION VS. DEMAND (MT)",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.10, 0.14, 0.20, 1),
            size_hint_y=None, height=dp(22),
        )
        box.add_widget(pvd_title)
        cards.append(pvd_title)

        pvd_data = [
            {
                "crop": "Cabbage",
                "prod": 4.8, "prod_max": 6.0,
                "dem": 6.5, "dem_max": 6.5,
                "shortfall": "Shortfall: -1.0k MT",
                "prod_color": (0.22, 0.80, 0.30, 1),
                "dem_color": (0.78, 0.78, 0.78, 1),
            },
            {
                "crop": "Leeks",
                "prod": 6.2, "dem": 5.3,
                "prod_max": 7.0, "dem_max": 7.0,
                "shortfall": "Surplus: +0.9k MT",
                "prod_color": (0.22, 0.80, 0.30, 1),
                "dem_color": (0.78, 0.78, 0.78, 1),
            },
        ]

        for pd in pvd_data:
            pd_card = MDCard(
                orientation="vertical",
                size_hint_y=None, height=dp(90),
                radius=[14, 14, 14, 14],
                md_bg_color=(1, 1, 1, 1),
                elevation=1,
                padding=(dp(12), dp(10), dp(12), dp(10)),
                spacing=dp(6),
            )
            crop_row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(16),
            )
            crop_name_lbl = MDLabel(
                text=pd["crop"],
                font_style="Caption", bold=True,
                theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
            )
            legend_row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(14),
                spacing=dp(8),
            )
            for leg_text, leg_color in [("● Prod.", pd["prod_color"]), ("Dem.", (0.55, 0.55, 0.55, 1))]:
                ll = MDLabel(
                    text=leg_text, font_style="Caption",
                    theme_text_color="Custom", text_color=leg_color,
                )
                legend_row.add_widget(ll)
            crop_row.add_widget(crop_name_lbl)
            crop_row.add_widget(legend_row)

            # Prod bar
            prod_bar_bg = MDCard(
                size_hint_y=None, height=dp(10),
                radius=[5, 5, 5, 5],
                md_bg_color=(0.91, 0.96, 0.91, 1),
                elevation=0,
            )
            prod_fill_frac = min(pd["prod"] / pd["prod_max"], 1.0)
            with prod_bar_bg.canvas.after:
                Color(*pd["prod_color"])
                prod_bar_bg._fill = RoundedRectangle(
                    pos=prod_bar_bg.pos,
                    size=(0, prod_bar_bg.height),
                    radius=[5, 5, 5, 5],
                )
            def _upd_prod(inst, val, frac=prod_fill_frac):
                inst._fill.pos = inst.pos
                inst._fill.size = (inst.width * frac, inst.height)
            prod_bar_bg.bind(pos=_upd_prod, size=_upd_prod)

            # Dem bar
            dem_bar_bg = MDCard(
                size_hint_y=None, height=dp(10),
                radius=[5, 5, 5, 5],
                md_bg_color=(0.93, 0.93, 0.93, 1),
                elevation=0,
            )
            dem_fill_frac = min(pd["dem"] / pd["dem_max"], 1.0)
            with dem_bar_bg.canvas.after:
                Color(0.65, 0.65, 0.65, 1)
                dem_bar_bg._fill = RoundedRectangle(
                    pos=dem_bar_bg.pos,
                    size=(0, dem_bar_bg.height),
                    radius=[5, 5, 5, 5],
                )
            def _upd_dem(inst, val, frac=dem_fill_frac):
                inst._fill.pos = inst.pos
                inst._fill.size = (inst.width * frac, inst.height)
            dem_bar_bg.bind(pos=_upd_dem, size=_upd_dem)

            # Shortfall label
            sf_color = (0.85, 0.20, 0.20, 1) if "Shortfall" in pd["shortfall"] else (0.13, 0.65, 0.22, 1)
            sf_lbl = MDLabel(
                text=pd["shortfall"],
                font_style="Caption", bold=True,
                theme_text_color="Custom", text_color=sf_color,
                size_hint_y=None, height=dp(14),
            )

            pd_card.add_widget(crop_row)
            pd_card.add_widget(prod_bar_bg)
            pd_card.add_widget(dem_bar_bg)
            pd_card.add_widget(sf_lbl)

            box.add_widget(pd_card)
            cards.append(pd_card)

        # ── 5. STRATEGIC INSIGHT CARD ──────────────────────────────────────────
        insight_card = MDCard(
            orientation="horizontal",
            size_hint_y=None, height=dp(90),
            radius=[14, 14, 14, 14],
            md_bg_color=(0.93, 0.97, 0.93, 1),
            elevation=0,
            padding=(dp(12), dp(10), dp(12), dp(10)),
            spacing=dp(10),
        )
        bulb_icon = MDIcon(
            icon="lightbulb-on",
            font_size="28sp",
            theme_text_color="Custom", text_color=(0.22, 0.75, 0.30, 1),
            size_hint=(None, None), size=(dp(30), dp(30)),
            pos_hint={"center_y": 0.5},
        )
        insight_text_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2),
            pos_hint={"center_y": 0.5},
        )
        insight_hdr = MDLabel(
            text="STRATEGIC INSIGHT",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.15, 0.55, 0.25, 1),
            size_hint_y=None, height=dp(16),
        )
        insight_body = MDLabel(
            text="Cabbage production is 12% below forecasted demand in the Central district. Recommend activating the emergency import buffer for Q4.",
            font_style="Caption",
            theme_text_color="Custom", text_color=(0.28, 0.35, 0.30, 1),
        )
        insight_text_box.add_widget(insight_hdr)
        insight_text_box.add_widget(insight_body)
        insight_card.add_widget(bulb_icon)
        insight_card.add_widget(insight_text_box)
        box.add_widget(insight_card)
        cards.append(insight_card)

        # Fix height
        def _fix(*_):
            box.height = box.minimum_height
        Clock.schedule_once(_fix, 0)

        stagger_fade_in(cards[1:], step=0.04, duration=0.28)
        center_scroll_content(box.parent, box)

    def _load_trader_home(self, box):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton, MDRaisedButton
        from kivymd.uix.textfield import MDTextField
        from kivy.graphics import Color, RoundedRectangle

        box.clear_widgets()
        box.padding = (dp(16), dp(12), dp(16), dp(24))
        box.spacing = dp(14)
        cards = []

        # ── 1. TOP BAR ("Stocks" title only) ──────────────────────────
        top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(40),
        )
        title_lbl = MDLabel(
            text="Stocks",
            font_style="H6", bold=True, halign="center",
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
            pos_hint={"center_y": 0.5},
        )
        top_bar.add_widget(title_lbl)
        box.add_widget(top_bar)
        cards.append(top_bar)

        # ── 2. SEARCH BAR FIELD CARD ─────────────────────────────────────────
        search_card = MDCard(
            orientation="horizontal",
            size_hint_y=None, height=dp(46),
            padding=(dp(12), dp(4), dp(12), dp(4)),
            radius=[12, 12, 12, 12],
            md_bg_color=(1, 1, 1, 1),
            elevation=1,
        )
        search_field = MDTextField(
            hint_text="Search stocks…",
            icon_left="magnify",
            mode="line",
            line_color_normal=(0, 0, 0, 0),
            line_color_focus=(0, 0, 0, 0),
            size_hint_y=None, height=dp(44),
            pos_hint={"center_y": 0.5},
        )
        search_card.add_widget(search_field)
        box.add_widget(search_card)
        cards.append(search_card)

        # ── 3. INVENTORY SUMMARY HERO BANNER CARD ────────────────────────────
        summary_card = MDCard(
            orientation="vertical",
            size_hint_y=None, height=dp(210),
            radius=[16, 16, 16, 16],
            md_bg_color=(1, 1, 1, 1),
            elevation=2,
            padding=0,
            spacing=0,
        )

        # Top banner image / gradient graphic
        top_banner = MDCard(
            size_hint_y=None, height=dp(100),
            radius=[16, 16, 0, 0],
            md_bg_color=(0.14, 0.40, 0.22, 1),
            elevation=0,
        )
        with top_banner.canvas.before:
            Color(0.24, 0.58, 0.28, 0.85)
            top_banner._bg_rect = RoundedRectangle(pos=top_banner.pos, size=top_banner.size, radius=[16, 16, 0, 0])
        def _upd_rect(inst, *_):
            inst._bg_rect.pos = inst.pos
            inst._bg_rect.size = inst.size
        top_banner.bind(pos=_upd_rect, size=_upd_rect)

        banner_lbl = MDIcon(
            icon="image-filter-hdr",
            font_size="64sp",
            halign="center",
            theme_text_color="Custom", text_color=(1, 1, 1, 0.35),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        top_banner.add_widget(banner_lbl)

        # Bottom content area
        summary_body = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(110),
            padding=(dp(16), dp(12), dp(16), dp(14)),
            spacing=dp(10),
        )

        sum_text_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(2),
            pos_hint={"center_y": 0.5},
        )
        inv_title_lbl = MDLabel(
            text="INVENTORY SUMMARY",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.20, 0.72, 0.28, 1),
            size_hint_y=None, height=dp(16),
        )
        inv_val_lbl = MDLabel(
            text="Rs. 2,450,750.00",
            font_style="H5", bold=True,
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
            size_hint_y=None, height=dp(30),
        )
        inv_sub_lbl = MDLabel(
            text="Total Inventory Value",
            font_style="Caption",
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
            size_hint_y=None, height=dp(16),
        )
        sum_text_box.add_widget(inv_title_lbl)
        sum_text_box.add_widget(inv_val_lbl)
        sum_text_box.add_widget(inv_sub_lbl)

        sync_btn = MDRaisedButton(
            text="Sync Data",
            md_bg_color=(0.22, 0.85, 0.28, 1),
            text_color=(1, 1, 1, 1),
            elevation=1, _radius=10,
            pos_hint={"center_y": 0.4},
            on_release=lambda x: show_snackbar("Inventory data synced successfully!"),
        )

        summary_body.add_widget(sum_text_box)
        summary_body.add_widget(sync_btn)

        summary_card.add_widget(top_banner)
        summary_card.add_widget(summary_body)

        box.add_widget(summary_card)
        cards.append(summary_card)

        # ── 4. "CURRENT INVENTORY" SECTION HEADER ────────────────────────────
        inv_header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(28),
        )
        inv_title = MDLabel(
            text="Current Inventory",
            font_style="Subtitle1", bold=True,
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
        )
        cat_pill = MDCard(
            size_hint=(None, None), size=(dp(90), dp(24)),
            radius=[8, 8, 8, 8],
            md_bg_color=(0.88, 0.96, 0.88, 1),
            elevation=0,
            pos_hint={"center_y": 0.5},
            padding=(dp(4), dp(2)),
        )
        cat_lbl = MDLabel(
            text="5 Categories",
            halign="center",
            bold=True, font_style="Caption",
            theme_text_color="Custom", text_color=(0.10, 0.45, 0.20, 1),
        )
        cat_pill.add_widget(cat_lbl)

        inv_header.add_widget(inv_title)
        inv_header.add_widget(cat_pill)
        box.add_widget(inv_header)
        cards.append(inv_header)

        # ── 5. INVENTORY ITEM CARDS LIST (Okra, Cabbage, Beans, Carrots, Leeks)
        trader_inventory = [
            {
                "crop": "Okra", "qty": "450 kg", "value": "Rs. 135,000.00",
                "tag": "OPTIMAL", "tag_bg": (0.88, 0.96, 0.88, 1), "tag_fg": (0.13, 0.65, 0.22, 1),
                "icon": "leaf",
            },
            {
                "crop": "Cabbage", "qty": "120 kg", "value": "Rs. 48,000.00",
                "tag": "LOW STOCK", "tag_bg": (0.99, 0.88, 0.88, 1), "tag_fg": (0.85, 0.20, 0.20, 1),
                "icon": "flower-tulip",
            },
            {
                "crop": "Beans", "qty": "850 kg", "value": "Rs. 425,000.00",
                "tag": "OPTIMAL", "tag_bg": (0.88, 0.96, 0.88, 1), "tag_fg": (0.13, 0.65, 0.22, 1),
                "icon": "seed",
            },
            {
                "crop": "Carrots", "qty": "2.1 tons", "value": "Rs. 945,000.00",
                "tag": "OPTIMAL", "tag_bg": (0.88, 0.96, 0.88, 1), "tag_fg": (0.13, 0.65, 0.22, 1),
                "icon": "carrot",
            },
            {
                "crop": "Leeks", "qty": "600 kg", "value": "Rs. 180,000.00",
                "tag": "FAIR", "tag_bg": (0.99, 0.96, 0.82, 1), "tag_fg": (0.75, 0.50, 0.05, 1),
                "icon": "tree",
            },
        ]

        for item in trader_inventory:
            itm_card = MDCard(
                orientation="horizontal",
                size_hint_y=None, height=dp(74),
                padding=(dp(12), dp(10), dp(12), dp(10)),
                spacing=dp(12),
                radius=[16, 16, 16, 16],
                md_bg_color=(1, 1, 1, 1),
                elevation=1,
                ripple_behavior=True,
            )

            # Left Icon Box
            ic_box = MDCard(
                size_hint=(None, None), size=(dp(50), dp(50)),
                radius=[14, 14, 14, 14],
                md_bg_color=(0.91, 0.98, 0.93, 1),
                elevation=0,
                pos_hint={"center_y": 0.5},
            )
            ic_lbl = MDIcon(
                icon=item["icon"],
                halign="center",
                font_size="26sp",
                theme_text_color="Custom", text_color=(0.20, 0.72, 0.28, 1),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
            )
            ic_box.add_widget(ic_lbl)

            # Middle Info Box
            mid_box = MDBoxLayout(
                orientation="vertical",
                spacing=dp(2),
                pos_hint={"center_y": 0.5},
            )
            c_name = MDLabel(
                text=item["crop"],
                bold=True, font_style="Subtitle2",
                theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
                size_hint_y=None, height=dp(20),
            )
            c_qty = MDLabel(
                text=item["qty"],
                font_style="Caption",
                theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
                size_hint_y=None, height=dp(16),
            )
            c_val = MDLabel(
                text=item["value"],
                bold=True, font_style="Caption",
                theme_text_color="Custom", text_color=(0.20, 0.72, 0.28, 1),
                size_hint_y=None, height=dp(18),
            )
            mid_box.add_widget(c_name)
            mid_box.add_widget(c_qty)
            mid_box.add_widget(c_val)

            # Right Tag & Chevron Box
            right_box = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(6),
                size_hint_x=None, width=dp(95),
                pos_hint={"center_y": 0.5},
            )
            t_card = MDCard(
                size_hint=(None, None), size=(dp(72), dp(22)),
                radius=[8, 8, 8, 8],
                md_bg_color=item["tag_bg"],
                elevation=0,
                pos_hint={"center_y": 0.5},
                padding=(dp(2), dp(2)),
            )
            t_lbl = MDLabel(
                text=item["tag"],
                halign="center",
                bold=True, font_style="Caption",
                theme_text_color="Custom", text_color=item["tag_fg"],
            )
            t_card.add_widget(t_lbl)

            chevron = MDIcon(
                icon="chevron-right",
                font_size="22sp",
                theme_text_color="Custom", text_color=(0.65, 0.70, 0.75, 1),
                size_hint=(None, None), size=(dp(16), dp(16)),
                pos_hint={"center_y": 0.5},
            )
            right_box.add_widget(t_card)
            right_box.add_widget(chevron)

            itm_card.add_widget(ic_box)
            itm_card.add_widget(mid_box)
            itm_card.add_widget(right_box)
            box.add_widget(itm_card)
            cards.append(itm_card)

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
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton

        box = self.ids.rec_box
        box.clear_widgets()

        # --- Try ML-generated recs first, fall back to DB ---
        ml_recs = self._get_ml_recommendations()
        db_recs = get_recommendations_for_user(self.user["user_id"])

        if ml_recs:
            self._render_ml_recommendations(box, ml_recs)
        elif db_recs:
            self._render_db_recommendations(box, db_recs)
        else:
            # Animated empty state
            empty_box = MDBoxLayout(
                orientation="vertical", spacing=dp(12),
                size_hint_y=None, height=dp(240),
                padding=(dp(20), dp(40), dp(20), dp(20)),
            )
            icon_lbl = MDIcon(
                icon="lightbulb-on-outline",
                halign="center", font_size="48sp",
                theme_text_color="Custom",
                text_color=(0.75, 0.85, 0.75, 1),
                size_hint_y=None, height=dp(60),
            )
            title_lbl = MDLabel(
                text="No recommendations yet",
                halign="center", bold=True, font_style="Subtitle1",
                theme_text_color="Custom",
                text_color=(0.35, 0.35, 0.35, 1),
                size_hint_y=None, height=dp(28),
            )
            msg_lbl = MDLabel(
                text="AI is analysing your crops and market data.\nCheck back shortly for personalised advice.",
                halign="center", theme_text_color="Custom",
                text_color=(0.55, 0.55, 0.55, 1),
                size_hint_y=None, height=dp(60),
            )
            empty_box.add_widget(icon_lbl)
            empty_box.add_widget(title_lbl)
            empty_box.add_widget(msg_lbl)
            box.add_widget(empty_box)
            fade_in(empty_box, duration=0.4)
            center_scroll_content(box.parent, box)
            return

    def _get_ml_recommendations(self):
        """Generate ML recommendations from cached predictions (if available)."""
        if not self._ml_predictions_cache:
            return []
        try:
            from utils.recommendation_engine import generate_recommendations
            region_id = self.user.get("region_id")
            current_prices = get_latest_prices_for_crops(region_id)
            return generate_recommendations(self._ml_predictions_cache, current_prices)
        except Exception as e:
            print(f"[ML] Rec generation error: {e}")
            return []

    def _render_ml_recommendations(self, box, recs):
        """Render AI-powered recommendation cards with severity styling."""
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivy.graphics import Color, RoundedRectangle

        # Section header with AI badge
        header_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(36),
            spacing=dp(8),
            padding=(0, dp(4), 0, dp(8)),
        )
        ai_badge = MDCard(
            size_hint=(None, None), size=(dp(28), dp(22)),
            radius=[6, 6, 6, 6],
            md_bg_color=(0.12, 0.60, 0.35, 1),
            elevation=0,
        )
        ai_lbl = MDLabel(
            text="AI", halign="center", bold=True,
            font_style="Caption",
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
        )
        ai_badge.add_widget(ai_lbl)
        header_title = MDLabel(
            text="Smart Recommendations",
            bold=True, font_style="H6",
            theme_text_color="Custom",
            text_color=(0.08, 0.08, 0.08, 1),
        )
        header_row.add_widget(ai_badge)
        header_row.add_widget(header_title)
        box.add_widget(header_row)

        SEVERITY_COLORS = {
            "critical": {"accent": (0.85, 0.18, 0.18, 1), "bg": (1, 0.95, 0.95, 1), "icon_clr": (0.85, 0.18, 0.18, 1)},
            "warning":  {"accent": (0.90, 0.60, 0.10, 1), "bg": (1, 0.98, 0.92, 1), "icon_clr": (0.85, 0.55, 0.08, 1)},
            "positive": {"accent": (0.15, 0.65, 0.30, 1), "bg": (0.93, 0.99, 0.93, 1), "icon_clr": (0.12, 0.58, 0.26, 1)},
            "info":     {"accent": (0.22, 0.50, 0.78, 1), "bg": (0.94, 0.97, 1, 1), "icon_clr": (0.20, 0.45, 0.72, 1)},
        }

        cards = []
        for rec in recs:
            sev = rec.get("severity", "info")
            colors = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["info"])

            card = MDCard(
                orientation="horizontal",
                size_hint_y=None, height=dp(90),
                padding=(dp(12), dp(10), dp(12), dp(10)),
                spacing=dp(10),
                radius=[14, 14, 14, 14],
                md_bg_color=colors["bg"],
                elevation=1,
                ripple_behavior=True,
            )

            # Left accent bar
            with card.canvas.before:
                Color(*colors["accent"])
                card._acc = RoundedRectangle(
                    pos=card.pos,
                    size=(dp(4), card.height),
                    radius=[2, 2, 2, 2],
                )
            def _upd_accent(inst, *_, acc=card._acc):
                acc.pos = inst.pos
                acc.size = (dp(4), inst.height)
            card.bind(pos=_upd_accent, size=_upd_accent)

            # Icon
            icon_card = MDCard(
                size_hint=(None, None), size=(dp(40), dp(40)),
                radius=[20, 20, 20, 20],
                md_bg_color=(*colors["accent"][:3], 0.15),
                elevation=0,
                pos_hint={"center_y": 0.5},
            )
            icon_widget = MDIcon(
                icon=rec.get("icon", "lightbulb-on"),
                halign="center",
                font_size="20sp",
                theme_text_color="Custom",
                text_color=colors["icon_clr"],
                pos_hint={"center_x": 0.5, "center_y": 0.5},
            )
            icon_card.add_widget(icon_widget)

            # Text content
            text_box = MDBoxLayout(
                orientation="vertical",
                spacing=dp(2),
                pos_hint={"center_y": 0.5},
            )
            title_lbl = MDLabel(
                text=rec.get("title", "Recommendation"),
                bold=True, font_style="Subtitle2",
                theme_text_color="Custom",
                text_color=(0.08, 0.08, 0.08, 1),
                size_hint_y=None, height=dp(20),
            )
            # Type badge
            rec_type = rec.get("type", "info").upper()
            type_lbl = MDLabel(
                text=f"{rec_type}  •  {rec.get('vegetable', 'General') or 'General'}",
                font_style="Caption", bold=True,
                theme_text_color="Custom",
                text_color=colors["icon_clr"],
                size_hint_y=None, height=dp(14),
            )
            msg_lbl = MDLabel(
                text=rec.get("message", ""),
                font_style="Caption",
                theme_text_color="Custom",
                text_color=(0.30, 0.30, 0.30, 1),
                size_hint_y=None, height=dp(36),
            )
            text_box.add_widget(title_lbl)
            text_box.add_widget(type_lbl)
            text_box.add_widget(msg_lbl)

            card.add_widget(icon_card)
            card.add_widget(text_box)

            # Accordion expand on tap
            card._collapsed = True
            card._msg_lbl = msg_lbl
            card.bind(on_release=lambda inst: self._toggle_rec_card(inst))

            box.add_widget(card)
            cards.append(card)

        stagger_fade_in(cards, step=0.06, duration=0.30)
        center_scroll_content(box.parent, box)

    def _render_db_recommendations(self, box, recs):
        """Fallback: render DB-stored recommendations (legacy style)."""
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel
        from kivy.graphics import Color, Rectangle

        cards = []
        accent_colors = [
            (0.22, 0.60, 0.28, 1),
            (0.12, 0.38, 0.72, 1),
            (0.78, 0.50, 0.10, 1),
        ]
        for idx, r in enumerate(recs):
            accent = accent_colors[idx % len(accent_colors)]
            card = MDCard(
                orientation="vertical", size_hint_y=None, height=dp(68),
                padding=(dp(16), dp(10), dp(16), dp(10)), spacing=dp(2),
                radius=[14, 14, 14, 14],
                md_bg_color=(1, 1, 1, 1), elevation=1,
                ripple_behavior=True,
            )
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
            card._collapsed = True
            card._msg_lbl = msg_lbl
            card.bind(on_release=lambda inst: self._toggle_rec_card(inst))
            box.add_widget(card)
            cards.append(card)

        stagger_fade_in(cards, step=0.06, duration=0.30)
        center_scroll_content(box.parent, box)

    def _toggle_rec_card(self, card):
        if card._collapsed:
            Animation(height=dp(130), duration=0.22, t="out_quad").start(card)
            card._collapsed = False
        else:
            Animation(height=dp(90), duration=0.18, t="in_quad").start(card)
            card._collapsed = True
        bounce_scale(card)

    # ══════════════════════════════════════════════════════════════════════
    # ALERTS TAB
    # ══════════════════════════════════════════════════════════════════════
    def load_alerts(self):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton

        box = self.ids.alert_box
        box.clear_widgets()
        alerts = get_alerts_for_user(self.user["user_id"])

        if not alerts:
            # Empty state with icon
            empty_box = MDBoxLayout(
                orientation="vertical", spacing=dp(8),
                size_hint_y=None, height=dp(180),
                padding=(dp(20), dp(40), dp(20), dp(20)),
            )
            empty_icon = MDIcon(
                icon="bell-check-outline",
                halign="center", font_size="44sp",
                theme_text_color="Custom",
                text_color=(0.70, 0.82, 0.70, 1),
                size_hint_y=None, height=dp(52),
            )
            empty_title = MDLabel(
                text="All clear!",
                halign="center", bold=True, font_style="Subtitle1",
                theme_text_color="Custom",
                text_color=(0.35, 0.35, 0.35, 1),
                size_hint_y=None, height=dp(24),
            )
            empty_msg = MDLabel(
                text="No alerts right now. AI is monitoring your\ncrops, weather and market conditions.",
                halign="center", theme_text_color="Custom",
                text_color=(0.55, 0.55, 0.55, 1),
                size_hint_y=None, height=dp(44),
            )
            empty_box.add_widget(empty_icon)
            empty_box.add_widget(empty_title)
            empty_box.add_widget(empty_msg)
            box.add_widget(empty_box)
            fade_in(empty_box, duration=0.35)
            center_scroll_content(box.parent, box)
            return

        # Alert type → severity styling
        ALERT_STYLES = {
            "price_spike":        {"severity": "high",   "icon": "arrow-up-bold-circle",  "bg": (1, 0.93, 0.93, 1),  "icon_clr": (0.85, 0.18, 0.18, 1), "badge_bg": (0.85, 0.18, 0.18, 1)},
            "price_drop":         {"severity": "medium", "icon": "arrow-down-bold-circle","bg": (1, 0.97, 0.90, 1),  "icon_clr": (0.85, 0.55, 0.08, 1), "badge_bg": (0.90, 0.60, 0.10, 1)},
            "heavy_rain":         {"severity": "high",   "icon": "weather-pouring",       "bg": (0.92, 0.95, 1, 1),  "icon_clr": (0.15, 0.40, 0.80, 1), "badge_bg": (0.20, 0.45, 0.82, 1)},
            "drought_risk":       {"severity": "medium", "icon": "weather-sunny-alert",   "bg": (1, 0.97, 0.90, 1),  "icon_clr": (0.85, 0.55, 0.08, 1), "badge_bg": (0.90, 0.60, 0.10, 1)},
            "production_surplus":  {"severity": "medium", "icon": "package-variant-plus", "bg": (0.95, 0.97, 1, 1),  "icon_clr": (0.30, 0.45, 0.70, 1), "badge_bg": (0.35, 0.50, 0.75, 1)},
            "production_shortage": {"severity": "high",   "icon": "package-variant-minus","bg": (1, 0.93, 0.93, 1),  "icon_clr": (0.85, 0.18, 0.18, 1), "badge_bg": (0.85, 0.18, 0.18, 1)},
        }
        DEFAULT_STYLE = {"severity": "medium", "icon": "alert-circle", "bg": (0.97, 0.97, 0.97, 1), "icon_clr": (0.65, 0.65, 0.65, 1), "badge_bg": (0.65, 0.65, 0.65, 1)}

        cards = []
        for a in alerts:
            is_unread = not a["is_read"]
            style = ALERT_STYLES.get(a.get("type", ""), DEFAULT_STYLE)
            bg = style["bg"] if is_unread else (0.97, 0.97, 0.97, 1)

            card = MDCard(
                orientation="horizontal", size_hint_y=None, height=dp(82),
                padding=(dp(12), dp(10), dp(8), dp(10)), spacing=dp(10),
                radius=[14, 14, 14, 14],
                md_bg_color=bg,
                elevation=2 if is_unread else 0,
            )

            # Icon circle
            icon_circle = MDCard(
                size_hint=(None, None), size=(dp(40), dp(40)),
                radius=[20, 20, 20, 20],
                md_bg_color=(*style["icon_clr"][:3], 0.15),
                elevation=0,
                pos_hint={"center_y": 0.5},
            )
            icon_widget = MDIcon(
                icon=style["icon"] if is_unread else "check-circle-outline",
                halign="center", font_size="20sp",
                theme_text_color="Custom",
                text_color=style["icon_clr"] if is_unread else (0.65, 0.65, 0.65, 1),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
            )
            icon_circle.add_widget(icon_widget)

            # Content
            content_box = MDBoxLayout(
                orientation="vertical",
                spacing=dp(2),
                pos_hint={"center_y": 0.5},
            )

            # Severity badge
            sev_text = style["severity"].upper()
            sev_row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(18),
                spacing=dp(6),
            )
            sev_badge = MDCard(
                size_hint=(None, None), size=(dp(50), dp(16)),
                radius=[4, 4, 4, 4],
                md_bg_color=style["badge_bg"] if is_unread else (0.75, 0.75, 0.75, 1),
                elevation=0,
            )
            sev_lbl = MDLabel(
                text=sev_text, halign="center",
                bold=True, font_style="Caption",
                theme_text_color="Custom", text_color=(1, 1, 1, 1),
            )
            sev_badge.add_widget(sev_lbl)
            alert_type_lbl = MDLabel(
                text=a.get("type", "alert").replace("_", " ").title(),
                font_style="Caption", bold=True,
                theme_text_color="Custom",
                text_color=style["icon_clr"] if is_unread else (0.55, 0.55, 0.55, 1),
            )
            sev_row.add_widget(sev_badge)
            sev_row.add_widget(alert_type_lbl)

            msg_lbl = MDLabel(
                text=a["message"], theme_text_color="Custom",
                text_color=(0.10, 0.10, 0.10, 1) if is_unread else (0.50, 0.50, 0.50, 1),
                font_style="Caption",
            )

            content_box.add_widget(sev_row)
            content_box.add_widget(msg_lbl)

            card.add_widget(icon_circle)
            card.add_widget(content_box)

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
                    lambda dt, c=card, bg_clr=bg: pulse_color(
                        c, bg_clr,
                        (*style["icon_clr"][:3], 0.12),
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
