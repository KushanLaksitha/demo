"""
Dashboard screen – full interactive overhaul.
• Gradient header banner in Home tab with weather badge and refresh button
• Slide-up-fade-in card animations on every tab load
• Recommendations: accordion expand/collapse on tap
• Alerts: animated dismiss + pulse for unread + mark-all-read button
• History: pill toggle switch + chip crop selector
• Profile: avatar circle with initials, bounce-scale buttons
"""
from datetime import datetime, timedelta, date
import threading
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from kivymd.uix.pickers import MDDatePicker
from database.data_service import (
    get_market_summary, get_recommendations_for_user, get_alerts_for_user,
    mark_alert_read, get_all_crops, get_price_history, get_production_history,
    get_user_preferred_crop_ids, get_market_demand_trends, get_weather_impact_analysis,
    get_latest_prices_for_crops, get_lag_features_for_crops, get_current_weather,
    save_ml_alert, save_ml_recommendation, get_last_ml_run_time,
    clear_old_ml_data, get_crop_name_to_id_map, get_region_district,
    get_price_by_date, get_production_by_date, get_latest_record_date,
    get_earliest_record_date, get_available_record_years,
    get_price_history_by_year, get_production_history_by_year,
    get_trader_inventory_summary, save_trader_stock, get_trader_stocks,
    ensure_sample_alerts_if_empty, ensure_sample_recommendations_if_empty,
    get_policymaker_dashboard_data,
)
from utils.ml_engine import predict_price, predict_production
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

            MDBoxLayout:
                orientation: "vertical"
                spacing: 0

                # Header row with AI badge — BLUE/INDIGO theme
                MDBoxLayout:
                    id: rec_header_row
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(58)
                    padding: dp(16), dp(8), dp(16), dp(2)
                    spacing: dp(2)

                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: dp(32)
                        spacing: dp(8)

                        MDCard:
                            size_hint: None, None
                            size: dp(32), dp(24)
                            radius: [6, 6, 6, 6]
                            md_bg_color: 0.22, 0.42, 0.85, 1
                            elevation: 0
                            pos_hint: {"center_y": 0.5}

                            MDLabel:
                                text: "AI"
                                halign: "center"
                                bold: True
                                font_style: "Caption"
                                theme_text_color: "Custom"
                                text_color: 1, 1, 1, 1

                        MDIcon:
                            icon: "lightbulb-on"
                            theme_text_color: "Custom"
                            text_color: 0.22, 0.42, 0.85, 1
                            font_size: "22sp"
                            size_hint: None, None
                            size: dp(22), dp(22)
                            pos_hint: {"center_y": 0.5}

                        MDLabel:
                            text: "Personalised Advisory"
                            font_style: "H6"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: 0.15, 0.15, 0.25, 1

                    MDLabel:
                        text: "Smart insights tailored for your crops & market"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.45, 0.50, 0.65, 1
                        size_hint_y: None
                        height: dp(16)
                        padding: dp(40), 0, 0, 0

                # Category filter chip row — BLUE theme
                ScrollView:
                    size_hint_y: None
                    height: dp(46)
                    do_scroll_y: False
                    bar_width: 0
                    MDBoxLayout:
                        id: rec_category_chips
                        orientation: "horizontal"
                        spacing: dp(8)
                        size_hint: None, None
                        height: dp(46)
                        width: self.minimum_width
                        padding: dp(14), dp(4), dp(14), dp(6)

                ScrollView:
                    MDBoxLayout:
                        id: rec_box
                        orientation: "vertical"
                        padding: dp(14), dp(4), dp(14), dp(14)
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

                # Alerts header row — RED/AMBER theme
                MDBoxLayout:
                    id: alerts_header_row
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(58)
                    padding: dp(16), dp(8), dp(16), dp(2)
                    spacing: dp(2)

                    MDBoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: dp(32)
                        spacing: dp(6)

                        MDCard:
                            size_hint: None, None
                            size: dp(28), dp(24)
                            radius: [6, 6, 6, 6]
                            md_bg_color: 0.85, 0.25, 0.18, 1
                            elevation: 0
                            pos_hint: {"center_y": 0.5}

                            MDIcon:
                                icon: "shield-alert"
                                halign: "center"
                                font_size: "14sp"
                                theme_text_color: "Custom"
                                text_color: 1, 1, 1, 1
                                pos_hint: {"center_x": 0.5, "center_y": 0.5}

                        MDIcon:
                            icon: "bell-ring"
                            theme_text_color: "Custom"
                            text_color: 0.85, 0.25, 0.18, 1
                            font_size: "22sp"
                            size_hint: None, None
                            size: dp(22), dp(22)
                            pos_hint: {"center_y": 0.5}

                        MDLabel:
                            text: "Alerts & Warnings"
                            font_style: "H6"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: 0.25, 0.08, 0.08, 1

                        MDTextButton:
                            id: mark_all_btn
                            text: "Mark all read"
                            pos_hint: {"center_y": 0.5}
                            theme_text_color: "Custom"
                            text_color: 0.85, 0.30, 0.18, 1
                            on_release: root.mark_all_alerts_read()

                    MDLabel:
                        text: "Time-critical notifications requiring your attention"
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0.65, 0.40, 0.35, 1
                        size_hint_y: None
                        height: dp(16)
                        padding: dp(34), 0, 0, 0

                # Category filter chip row — RED/AMBER theme
                ScrollView:
                    size_hint_y: None
                    height: dp(46)
                    do_scroll_y: False
                    bar_width: 0
                    MDBoxLayout:
                        id: alert_category_chips
                        orientation: "horizontal"
                        spacing: dp(8)
                        size_hint: None, None
                        height: dp(46)
                        width: self.minimum_width
                        padding: dp(14), dp(4), dp(14), dp(6)

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
    history_selected_date = None
    history_selected_date_str = None
    history_inspect_mode = "ai_forecast"  # "ai_forecast" or "historical_actual"
    history_selected_year = 2025

    selected_alert_category = "all"
    _alert_category_widgets = {}
    _all_alerts_cache = []

    selected_rec_category = "all"
    _rec_category_widgets = {}
    _all_recs_cache = []

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
        """Load policymaker home: fetch DB data in background, build UI on main thread."""
        from kivymd.uix.label import MDLabel
        from kivymd.uix.boxlayout import MDBoxLayout

        box.clear_widgets()
        box.padding = (dp(16), dp(14), dp(16), dp(24))
        box.spacing = dp(14)

        # Show loading state immediately
        loading_lbl = MDLabel(
            text="Loading real-time data...",
            halign="center",
            font_style="Caption",
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
            size_hint_y=None, height=dp(40),
        )
        box.add_widget(loading_lbl)

        def _fetch():
            data = get_policymaker_dashboard_data()
            if not data:
                data = {
                    "food_security_score": 0.0, "food_security_change": 0.0,
                    "yield_growth_pct": 0.0, "yield_growth_label": "-- N/A",
                    "heatmap_regions": [], "pvd_crops": [],
                    "insight": "Unable to load data. Check database connection.",
                    "sync_time": "--", "total_regions": 0,
                }
            Clock.schedule_once(lambda dt: self._build_policymaker_ui(box, data), 0)

        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def _build_policymaker_ui(self, box, data):
        """Build the full policymaker home UI on the main thread with real data."""
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.button import MDIconButton, MDRaisedButton
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivy.graphics import Color, RoundedRectangle
        from kivy.uix.widget import Widget

        box.clear_widgets()
        cards = []

        food_sec = data["food_security_score"]
        food_chg = data["food_security_change"]
        yield_pct = data["yield_growth_pct"]
        yield_label = data["yield_growth_label"]
        hmap_regions = data["heatmap_regions"]
        pvd_crops = data["pvd_crops"]
        insight_text = data["insight"]
        sync_time = data["sync_time"]

        # ── 1. HEADER ────────────────────────────────────────────────
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
            text=f"REAL-TIME  |  Synced {sync_time}",
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
            elevation=1, pos_hint={"center_y": 0.5},
        )
        first_name = self.user.get("first_name", "P") if self.user else "P"
        avatar_card.add_widget(MDLabel(
            text=first_name[0].upper(),
            halign="center", bold=True, font_style="H6",
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
        ))
        header_row.add_widget(hdr_text)
        header_row.add_widget(avatar_card)
        box.add_widget(header_row)
        cards.append(header_row)

        # ── 2. STAT CARDS ────────────────────────────────────────────
        stats_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(86),
            spacing=dp(12),
        )
        food_chg_color = (0.13, 0.65, 0.22, 1) if food_chg >= 0 else (0.85, 0.20, 0.20, 1)
        yield_color = (0.13, 0.65, 0.22, 1) if yield_pct >= 0 else (0.85, 0.20, 0.20, 1)

        for s_label, s_val, s_sub, s_sub_c, s_icon in [
            ("FOOD SECURITY", str(food_sec),
             f"+{food_chg}%" if food_chg >= 0 else f"{food_chg}%",
             food_chg_color, "shield-check"),
            ("YIELD GROWTH", f"{yield_pct:+.1f}%", yield_label, yield_color, "chart-bar"),
        ]:
            sc = MDCard(
                orientation="vertical",
                size_hint=(0.5, 1),
                radius=[14, 14, 14, 14],
                md_bg_color=(1, 1, 1, 1),
                elevation=1,
                padding=(dp(12), dp(10), dp(10), dp(10)),
                spacing=dp(2),
                ripple_behavior=True,
            )
            top_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
            top_row.add_widget(MDLabel(
                text=s_label, font_style="Caption", bold=True,
                theme_text_color="Custom", text_color=(0.13, 0.65, 0.22, 1),
            ))
            top_row.add_widget(MDIcon(
                icon=s_icon, font_size="18sp",
                theme_text_color="Custom", text_color=(0.22, 0.80, 0.30, 1),
                size_hint=(None, None), size=(dp(22), dp(22)),
            ))
            sc.add_widget(top_row)
            sc.add_widget(MDLabel(
                text=s_val, font_style="H5", bold=True,
                theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
                size_hint_y=None, height=dp(30),
            ))
            sc.add_widget(MDLabel(
                text=s_sub, font_style="Caption",
                theme_text_color="Custom", text_color=s_sub_c,
                size_hint_y=None, height=dp(16),
            ))
            stats_row.add_widget(sc)

        box.add_widget(stats_row)
        cards.append(stats_row)

        # ── 2.5. OFFICIAL ADMIN SECURE DISPATCH CARD ─────────────────
        comm_card = MDCard(
            orientation="horizontal",
            size_hint_y=None, height=dp(68),
            radius=[14, 14, 14, 14],
            md_bg_color=(0.12, 0.24, 0.18, 1),
            elevation=1,
            padding=(dp(12), dp(8), dp(12), dp(8)),
            spacing=dp(10),
            ripple_behavior=True,
            on_release=lambda *args: self.go_to_policy_communications(),
        )
        comm_icon_bg = MDCard(
            size_hint=(None, None), size=(dp(40), dp(40)),
            radius=[20, 20, 20, 20],
            md_bg_color=(0.22, 0.65, 0.35, 1),
            elevation=0, pos_hint={"center_y": 0.5},
        )
        comm_icon_bg.add_widget(MDIcon(
            icon="shield-lock", font_size="22sp",
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        ))
        comm_card.add_widget(comm_icon_bg)

        comm_text_box = MDBoxLayout(orientation="vertical", spacing=dp(2), pos_hint={"center_y": 0.5})
        comm_text_box.add_widget(MDLabel(
            text="MINISTRY DISPATCH DESK",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.55, 0.88, 0.65, 1),
            size_hint_y=None, height=dp(16),
        ))
        comm_text_box.add_widget(MDLabel(
            text="Secure memos, supply queries & official actions",
            font_style="Caption",
            theme_text_color="Custom", text_color=(0.90, 0.95, 0.90, 0.9),
            size_hint_y=None, height=dp(16),
        ))
        comm_card.add_widget(comm_text_box)

        comm_open_btn = MDIconButton(
            icon="chevron-right",
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda *args: self.go_to_policy_communications(),
        )
        comm_card.add_widget(comm_open_btn)

        box.add_widget(comm_card)
        cards.append(comm_card)

        # ── 3. HEATMAP HEADER ────────────────────────────────────────
        hmap_header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(26),
        )
        hmap_header.add_widget(MDLabel(
            text="REGIONAL PRODUCTION HEATMAP",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.10, 0.14, 0.20, 1),
        ))
        pill = MDCard(
            size_hint=(None, None), size=(dp(80), dp(22)),
            radius=[8, 8, 8, 8],
            md_bg_color=(0.92, 0.97, 0.92, 1),
            elevation=0, pos_hint={"center_y": 0.5},
            padding=(dp(2), dp(2)),
        )
        pill.add_widget(MDLabel(
            text=f"{len(hmap_regions)} Regions",
            halign="center", font_style="Caption",
            theme_text_color="Custom", text_color=(0.22, 0.60, 0.28, 1),
        ))
        hmap_header.add_widget(pill)
        box.add_widget(hmap_header)
        cards.append(hmap_header)

        # ── 3. HEATMAP GRID ──────────────────────────────────────────
        grid_row_h = dp(52)
        cols = 2
        region_rows = [hmap_regions[i:i+cols] for i in range(0, max(len(hmap_regions), 1), cols)]
        n_rows = len(region_rows)
        hmap_card_h = n_rows * (grid_row_h + dp(4)) + dp(48) + dp(28)

        hmap_card = MDCard(
            size_hint_y=None, height=hmap_card_h,
            radius=[16, 16, 16, 16],
            md_bg_color=(1, 1, 1, 1),
            elevation=1,
            padding=(dp(10), dp(10), dp(10), dp(10)),
            spacing=dp(8),
            orientation="vertical",
        )

        grid_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=n_rows * (grid_row_h + dp(4)),
            spacing=dp(4),
        )

        for reg_row in region_rows:
            row_box = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=grid_row_h,
                spacing=dp(6),
            )
            for reg in reg_row:
                intensity = reg["intensity"]
                r_val = 0.80 - intensity * 0.50
                g_val = 0.35 + intensity * 0.40
                b_val = 0.50 - intensity * 0.35
                cell = MDCard(
                    size_hint=(1, 1),
                    radius=[10, 10, 10, 10],
                    md_bg_color=(r_val, g_val, b_val, 1),
                    elevation=0,
                    padding=(dp(4), dp(4)),
                )
                cell_inner = MDBoxLayout(orientation="vertical", spacing=dp(1))
                t_col = (1, 1, 1, 0.95) if intensity > 0.45 else (0.15, 0.20, 0.15, 1)
                v_col = (1, 1, 1, 0.80) if intensity > 0.45 else (0.20, 0.35, 0.20, 1)
                cell_inner.add_widget(MDLabel(
                    text=reg["district"],
                    halign="center", font_style="Caption", bold=True,
                    theme_text_color="Custom", text_color=t_col,
                    size_hint_y=None, height=dp(16),
                ))
                cell_inner.add_widget(MDLabel(
                    text=f"{reg['total_mt']/1000:.1f}k Mt",
                    halign="center", font_style="Caption",
                    theme_text_color="Custom", text_color=v_col,
                    size_hint_y=None, height=dp(14),
                ))
                cell.add_widget(cell_inner)
                row_box.add_widget(cell)
            if len(reg_row) < cols:
                row_box.add_widget(Widget())
            grid_box.add_widget(row_box)

        # Legend with clean 2-side label to prevent wrapping
        legend_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(34),
            spacing=dp(4),
        )
        legend_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(8),
            spacing=dp(2),
        )
        for i in range(6):
            t = i / 5.0
            legend_bar.add_widget(MDCard(
                size_hint=(0.16, 1), radius=[3, 3, 3, 3],
                md_bg_color=(0.80 - t*0.50, 0.35 + t*0.40, 0.50 - t*0.35, 1),
                elevation=0,
            ))
        legend_lbls = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(16),
        )
        legend_lbls.add_widget(MDLabel(
            text="Low Volume", font_style="Caption",
            halign="left",
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
        ))
        legend_lbls.add_widget(MDLabel(
            text="High Volume (Mt)", font_style="Caption",
            halign="right",
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
        ))
        legend_box.add_widget(legend_bar)
        legend_box.add_widget(legend_lbls)

        hmap_card.add_widget(grid_box)
        hmap_card.add_widget(legend_box)
        box.add_widget(hmap_card)
        cards.append(hmap_card)

        # ── 4. PROD VS AI DEMAND TITLE ───────────────────────────────
        pvd_title = MDLabel(
            text="PRODUCTION VS. AI-PREDICTED DEMAND (Mt)",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.10, 0.14, 0.20, 1),
            size_hint_y=None, height=dp(22),
        )
        box.add_widget(pvd_title)
        cards.append(pvd_title)

        # ── 5. PROD VS DEMAND BARS ───────────────────────────────────
        prod_color = (0.22, 0.80, 0.30, 1)
        dem_color = (0.55, 0.60, 0.75, 1)

        for pd in pvd_crops:
            max_bar = float(max(pd["prod_mt"], pd["pred_mt"]) or 1.0)
            prod_frac = min(pd["prod_mt"] / max_bar, 1.0)
            dem_frac = min(pd["pred_mt"] / max_bar, 1.0)

            pd_card = MDCard(
                orientation="vertical",
                size_hint_y=None, height=dp(90),
                radius=[14, 14, 14, 14],
                md_bg_color=(1, 1, 1, 1),
                elevation=1,
                padding=(dp(12), dp(10), dp(12), dp(10)),
                spacing=dp(5),
            )

            # Crop name + legend row
            top = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(16))
            top.add_widget(MDLabel(
                text=pd["crop"], font_style="Caption", bold=True,
                theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
            ))
            leg = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(14), spacing=dp(8))
            leg.add_widget(MDLabel(text="● Prod.", font_style="Caption",
                                   theme_text_color="Custom", text_color=prod_color))
            leg.add_widget(MDLabel(text="● AI Demand", font_style="Caption",
                                   theme_text_color="Custom", text_color=dem_color))
            top.add_widget(leg)
            pd_card.add_widget(top)

            # Production bar (green)
            prod_bg = MDCard(size_hint_y=None, height=dp(10),
                             radius=[5, 5, 5, 5], md_bg_color=(0.91, 0.96, 0.91, 1), elevation=0)
            with prod_bg.canvas.after:
                Color(*prod_color)
                prod_bg._fill = RoundedRectangle(pos=prod_bg.pos, size=(0, prod_bg.height), radius=[5, 5, 5, 5])
            def _bind_prod(inst, val, frac=prod_frac):
                inst._fill.pos = inst.pos
                inst._fill.size = (inst.width * frac, inst.height)
            prod_bg.bind(pos=_bind_prod, size=_bind_prod)
            pd_card.add_widget(prod_bg)

            # AI demand bar (blue/purple)
            dem_bg = MDCard(size_hint_y=None, height=dp(10),
                            radius=[5, 5, 5, 5], md_bg_color=(0.92, 0.92, 0.96, 1), elevation=0)
            with dem_bg.canvas.after:
                Color(*dem_color)
                dem_bg._fill = RoundedRectangle(pos=dem_bg.pos, size=(0, dem_bg.height), radius=[5, 5, 5, 5])
            def _bind_dem(inst, val, frac=dem_frac):
                inst._fill.pos = inst.pos
                inst._fill.size = (inst.width * frac, inst.height)
            dem_bg.bind(pos=_bind_dem, size=_bind_dem)
            pd_card.add_widget(dem_bg)

            # Shortfall / surplus label
            sf_color = (0.85, 0.20, 0.20, 1) if "Shortfall" in pd["shortfall_label"] else (0.13, 0.65, 0.22, 1)
            pd_card.add_widget(MDLabel(
                text=pd["shortfall_label"], font_style="Caption", bold=True,
                theme_text_color="Custom", text_color=sf_color,
                size_hint_y=None, height=dp(14),
            ))
            box.add_widget(pd_card)
            cards.append(pd_card)

        # ── 6. AI STRATEGIC INSIGHT ──────────────────────────────────
        insight_card = MDCard(
            orientation="horizontal",
            size_hint_y=None, height=dp(96),
            radius=[14, 14, 14, 14],
            md_bg_color=(0.93, 0.97, 0.93, 1),
            elevation=0,
            padding=(dp(12), dp(10), dp(12), dp(10)),
            spacing=dp(10),
        )
        insight_card.add_widget(MDIcon(
            icon="lightbulb-on", font_size="28sp",
            theme_text_color="Custom", text_color=(0.22, 0.75, 0.30, 1),
            size_hint=(None, None), size=(dp(30), dp(30)),
            pos_hint={"center_y": 0.5},
        ))
        itb = MDBoxLayout(orientation="vertical", spacing=dp(2), pos_hint={"center_y": 0.5})
        itb.add_widget(MDLabel(
            text="AI STRATEGIC INSIGHT", font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.15, 0.55, 0.25, 1),
            size_hint_y=None, height=dp(16),
        ))
        itb.add_widget(MDLabel(
            text=insight_text, font_style="Caption",
            theme_text_color="Custom", text_color=(0.28, 0.35, 0.30, 1),
        ))
        insight_card.add_widget(itb)
        box.add_widget(insight_card)
        cards.append(insight_card)

        stagger_fade_in(cards[1:], step=0.03, duration=0.22)

    def _load_trader_home(self, box):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
        from kivymd.uix.textfield import MDTextField
        from kivy.graphics import Color, RoundedRectangle

        box.clear_widgets()
        box.padding = (dp(16), dp(12), dp(16), dp(24))
        box.spacing = dp(14)
        cards = []

        # ── Fetch real data from DB ──────────────────────────────────────
        uid = self.user.get("user_id") if self.user else None
        rid = self.user.get("region_id") if self.user else None
        summary = get_trader_inventory_summary(user_id=uid, region_id=rid)
        if not summary:
            summary = {"total_value_str": "Rs. 0.00", "total_categories": 0,
                       "district": "Unknown", "sync_time": "--", "items": []}

        trader_items = summary.get("items", [])
        total_val_str = summary.get("total_value_str", "Rs. 0.00")
        num_categories = summary.get("total_categories", 0)
        district = summary.get("district", "")
        sync_time = summary.get("sync_time", "")

        # Keep reference for search filtering & sync
        self._trader_items = trader_items
        self._trader_cards_container = None  # set later

        # ── 1. TOP BAR ("Stocks" title + district badge) ─────────────
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

        # ── 2. SEARCH BAR FIELD CARD ─────────────────────────────────
        search_card = MDCard(
            orientation="horizontal",
            size_hint_y=None, height=dp(46),
            padding=(dp(12), dp(4), dp(12), dp(4)),
            radius=[12, 12, 12, 12],
            md_bg_color=(1, 1, 1, 1),
            elevation=1,
        )
        search_field = MDTextField(
            hint_text="Search stocks...",
            icon_left="magnify",
            mode="line",
            line_color_normal=(0, 0, 0, 0),
            line_color_focus=(0, 0, 0, 0),
            size_hint_y=None, height=dp(44),
            pos_hint={"center_y": 0.5},
        )
        search_field.bind(text=self._on_trader_search)
        search_card.add_widget(search_field)
        box.add_widget(search_card)
        cards.append(search_card)

        # ── 3. INVENTORY SUMMARY HERO BANNER CARD ────────────────────
        summary_card = MDCard(
            orientation="vertical",
            size_hint_y=None, height=dp(210),
            radius=[16, 16, 16, 16],
            md_bg_color=(1, 1, 1, 1),
            elevation=2,
            padding=0,
            spacing=0,
        )

        # Top banner gradient
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

        # Banner content: district name + live badge
        banner_content = MDBoxLayout(
            orientation="vertical",
            padding=(dp(16), dp(14), dp(16), dp(8)),
            spacing=dp(4),
        )
        district_lbl = MDLabel(
            text=f"{district} Market",
            font_style="H6", bold=True,
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
            size_hint_y=None, height=dp(28),
        )
        sync_lbl = MDLabel(
            text=f"Last synced: {sync_time}",
            font_style="Caption",
            theme_text_color="Custom", text_color=(1, 1, 1, 0.70),
            size_hint_y=None, height=dp(16),
        )
        # Live indicator row
        live_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(20),
            spacing=dp(6),
        )
        live_dot = MDCard(
            size_hint=(None, None), size=(dp(8), dp(8)),
            radius=[4, 4, 4, 4],
            md_bg_color=(0.30, 1.0, 0.50, 1),
            elevation=0,
            pos_hint={"center_y": 0.5},
        )
        live_lbl = MDLabel(
            text="LIVE  |  Real-time DB prices",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.75, 1.0, 0.85, 1),
            size_hint_y=None, height=dp(16),
        )
        live_row.add_widget(live_dot)
        live_row.add_widget(live_lbl)

        banner_content.add_widget(district_lbl)
        banner_content.add_widget(sync_lbl)
        banner_content.add_widget(live_row)
        top_banner.add_widget(banner_content)

        # Bottom content area - total value
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
        self._trader_val_lbl = MDLabel(
            text=total_val_str,
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
        sum_text_box.add_widget(self._trader_val_lbl)
        sum_text_box.add_widget(inv_sub_lbl)

        sync_btn = MDRaisedButton(
            text="Sync Data",
            md_bg_color=(0.22, 0.85, 0.28, 1),
            text_color=(1, 1, 1, 1),
            elevation=1, _radius=10,
            pos_hint={"center_y": 0.4},
            on_release=lambda x: self._sync_trader_home(),
        )

        summary_body.add_widget(sum_text_box)
        summary_body.add_widget(sync_btn)

        summary_card.add_widget(top_banner)
        summary_card.add_widget(summary_body)

        box.add_widget(summary_card)
        cards.append(summary_card)

        # ── 4. "CURRENT INVENTORY" SECTION HEADER ────────────────────
        inv_header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(28),
        )
        inv_title = MDLabel(
            text="Current Inventory",
            font_style="Subtitle1", bold=True,
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
        )
        self._trader_cat_lbl = MDLabel(
            text=f"{num_categories} Categories",
            halign="center",
            bold=True, font_style="Caption",
            theme_text_color="Custom", text_color=(0.10, 0.45, 0.20, 1),
        )
        cat_pill = MDCard(
            size_hint=(None, None), size=(dp(90), dp(24)),
            radius=[8, 8, 8, 8],
            md_bg_color=(0.88, 0.96, 0.88, 1),
            elevation=0,
            pos_hint={"center_y": 0.5},
            padding=(dp(4), dp(2)),
        )
        cat_pill.add_widget(self._trader_cat_lbl)

        inv_header.add_widget(inv_title)
        inv_header.add_widget(cat_pill)
        box.add_widget(inv_header)
        cards.append(inv_header)

        # ── 5. INVENTORY ITEM CARDS (dynamic from DB) ────────────────
        # Container for inventory cards (for search filtering)
        inv_cards_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
        )
        inv_cards_box.bind(minimum_height=inv_cards_box.setter("height"))
        self._trader_cards_container = inv_cards_box

        self._build_trader_item_cards(inv_cards_box, trader_items, cards)

        box.add_widget(inv_cards_box)

        # Fix inner height
        def _fix(*_):
            box.height = box.minimum_height
        Clock.schedule_once(_fix, 0)

        stagger_fade_in(cards[1:], step=0.04, duration=0.28)
        center_scroll_content(box.parent, box)

    def _build_trader_item_cards(self, container, items, cards=None):
        """Build individual inventory item cards from data items into container."""
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout

        container.clear_widgets()

        for item in items:
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
            # Bind tap to open stock edit dialog
            itm_card.bind(on_release=lambda x, itm=item: self._open_trader_stock_dialog(itm))

            # Left Icon Box
            ic_box = MDCard(
                size_hint=(None, None), size=(dp(50), dp(50)),
                radius=[14, 14, 14, 14],
                md_bg_color=(0.91, 0.98, 0.93, 1),
                elevation=0,
                pos_hint={"center_y": 0.5},
            )
            ic_lbl = MDIcon(
                icon=item.get("icon", "leaf"),
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
                text=item.get("crop", ""),
                bold=True, font_style="Subtitle2",
                theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
                size_hint_y=None, height=dp(20),
            )
            c_qty = MDLabel(
                text=item.get("qty_str", f'{item.get("qty", 0)} kg'),
                font_style="Caption",
                theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
                size_hint_y=None, height=dp(16),
            )
            # Show real price-based value
            c_val = MDLabel(
                text=item.get("value_str", item.get("value", "")),
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
            tag_text = item.get("tag", "FAIR")
            t_card = MDCard(
                size_hint=(None, None), size=(dp(72), dp(22)),
                radius=[8, 8, 8, 8],
                md_bg_color=item.get("tag_bg", (0.99, 0.96, 0.82, 1)),
                elevation=0,
                pos_hint={"center_y": 0.5},
                padding=(dp(2), dp(2)),
            )
            t_lbl = MDLabel(
                text=tag_text,
                halign="center",
                bold=True, font_style="Caption",
                theme_text_color="Custom", text_color=item.get("tag_fg", (0.75, 0.50, 0.05, 1)),
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
            container.add_widget(itm_card)
            if cards is not None:
                cards.append(itm_card)

    def _on_trader_search(self, instance, query):
        """Filter trader inventory cards by crop name search query."""
        if not hasattr(self, "_trader_items") or not self._trader_cards_container:
            return
        q = query.strip().lower()
        if not q:
            filtered = self._trader_items
        else:
            filtered = [itm for itm in self._trader_items if q in itm.get("crop", "").lower()]
        self._build_trader_item_cards(self._trader_cards_container, filtered)
        # Update container height
        def _fix(*_):
            box = self.ids.home_box
            box.height = box.minimum_height
        Clock.schedule_once(_fix, 0.05)

    def _sync_trader_home(self):
        """Re-fetch trader inventory from DB and update the dashboard."""
        show_snackbar("Syncing inventory data...")
        uid = self.user.get("user_id") if self.user else None
        rid = self.user.get("region_id") if self.user else None
        summary = get_trader_inventory_summary(user_id=uid, region_id=rid)
        if summary:
            self._trader_items = summary.get("items", [])
            if hasattr(self, "_trader_val_lbl"):
                self._trader_val_lbl.text = summary.get("total_value_str", "Rs. 0.00")
            if hasattr(self, "_trader_cat_lbl"):
                self._trader_cat_lbl.text = f'{summary.get("total_categories", 0)} Categories'
            if self._trader_cards_container:
                self._build_trader_item_cards(self._trader_cards_container, self._trader_items)
            def _fix(*_):
                box = self.ids.home_box
                box.height = box.minimum_height
            Clock.schedule_once(_fix, 0.05)
        show_snackbar("Inventory synced with latest market data!")

    def _open_trader_stock_dialog(self, item):
        """Open a dialog showing item market details and allowing stock qty edit."""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton, MDRaisedButton
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        from kivymd.uix.textfield import MDTextField

        crop_name = item.get("crop", "")
        price_str = item.get("price_str", f'Rs. {item.get("price", 0):,.2f} / kg')
        chg_pct = item.get("price_change_pct", 0.0)
        supply_mt = item.get("regional_supply_mt", 0.0)
        rec_date = item.get("recorded_date", "")
        current_qty = item.get("qty", 0)

        chg_color = (0.13, 0.65, 0.22, 1) if chg_pct >= 0 else (0.85, 0.20, 0.20, 1)
        chg_arrow = "+" if chg_pct >= 0 else ""

        # Build dialog content
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(220),
            padding=(dp(4), dp(8), dp(4), dp(4)),
        )

        # Market price row
        price_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28), spacing=dp(8))
        price_row.add_widget(MDLabel(
            text="Market Price:", font_style="Body2", bold=True,
            theme_text_color="Custom", text_color=(0.30, 0.35, 0.40, 1),
            size_hint_x=0.45,
        ))
        price_row.add_widget(MDLabel(
            text=price_str, font_style="Body2", bold=True,
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
        ))
        content.add_widget(price_row)

        # Price change row
        chg_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24), spacing=dp(8))
        chg_row.add_widget(MDLabel(
            text="Price Change:", font_style="Caption",
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
            size_hint_x=0.45,
        ))
        chg_row.add_widget(MDLabel(
            text=f"{chg_arrow}{chg_pct}%", font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=chg_color,
        ))
        content.add_widget(chg_row)

        # Regional supply row
        supply_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24), spacing=dp(8))
        supply_row.add_widget(MDLabel(
            text="Regional Supply:", font_style="Caption",
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
            size_hint_x=0.45,
        ))
        supply_row.add_widget(MDLabel(
            text=f"{supply_mt:,.1f} Mt", font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
        ))
        content.add_widget(supply_row)

        # Date row
        date_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24), spacing=dp(8))
        date_row.add_widget(MDLabel(
            text="Data Date:", font_style="Caption",
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
            size_hint_x=0.45,
        ))
        date_row.add_widget(MDLabel(
            text=rec_date, font_style="Caption",
            theme_text_color="Custom", text_color=(0.07, 0.10, 0.15, 1),
        ))
        content.add_widget(date_row)

        # Divider
        divider = MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=(0.88, 0.88, 0.88, 1))
        content.add_widget(divider)

        # Edit stock qty field
        qty_lbl = MDLabel(
            text="Your Stock Quantity (kg):",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.20, 0.72, 0.28, 1),
            size_hint_y=None, height=dp(20),
        )
        content.add_widget(qty_lbl)

        qty_field = MDTextField(
            text=str(int(current_qty)),
            input_filter="int",
            hint_text="Enter quantity in kg",
            mode="rectangle",
            size_hint_y=None, height=dp(44),
        )
        content.add_widget(qty_field)

        dialog = MDDialog(
            title=f"{crop_name} - Stock Details",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=(0.55, 0.55, 0.55, 1),
                ),
                MDRaisedButton(
                    text="SAVE",
                    md_bg_color=(0.22, 0.72, 0.28, 1),
                    text_color=(1, 1, 1, 1),
                ),
            ],
        )

        def _cancel(*_):
            dialog.dismiss()

        def _save(*_):
            try:
                new_qty = int(qty_field.text.strip())
            except (ValueError, AttributeError):
                show_snackbar("Please enter a valid number")
                return
            uid = self.user.get("user_id") if self.user else None
            save_trader_stock(uid, crop_name, new_qty)
            dialog.dismiss()
            show_snackbar(f"{crop_name} stock updated to {new_qty} kg")
            # Refresh the dashboard
            Clock.schedule_once(lambda dt: self._sync_trader_home(), 0.2)

        dialog.buttons[0].bind(on_release=_cancel)
        dialog.buttons[1].bind(on_release=_save)
        dialog.open()

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
    # RECOMMENDATIONS TAB (Categorized: Market, Weather, Harvest, Advisory)
    # ══════════════════════════════════════════════════════════════════════
    REC_CATEGORIES = [
        ("all", "All", "lightbulb-on-outline"),
        ("price", "Market", "trending-up"),
        ("weather", "Weather", "weather-partly-cloudy"),
        ("production", "Harvest", "sprout"),
        ("combined", "Advisory", "compass-outline"),
    ]

    REC_CATEGORY_STYLES = {
        "price": {
            "title": "MARKET",
            "tag_bg": (0.90, 0.98, 0.92, 1),
            "tag_fg": (0.12, 0.60, 0.28, 1),
            "accent": (0.15, 0.65, 0.30, 1),
            "bg": (0.95, 0.99, 0.95, 1),
            "icon": "trending-up",
            "icon_clr": (0.12, 0.58, 0.26, 1),
        },
        "weather": {
            "title": "WEATHER",
            "tag_bg": (0.90, 0.94, 1.0, 1),
            "tag_fg": (0.15, 0.42, 0.82, 1),
            "accent": (0.20, 0.45, 0.82, 1),
            "bg": (0.94, 0.97, 1, 1),
            "icon": "weather-partly-cloudy",
            "icon_clr": (0.18, 0.45, 0.85, 1),
        },
        "production": {
            "title": "HARVEST",
            "tag_bg": (0.95, 0.90, 0.99, 1),
            "tag_fg": (0.50, 0.20, 0.80, 1),
            "accent": (0.55, 0.25, 0.85, 1),
            "bg": (0.97, 0.94, 1, 1),
            "icon": "sprout",
            "icon_clr": (0.50, 0.20, 0.80, 1),
        },
        "combined": {
            "title": "ADVISORY",
            "tag_bg": (1.0, 0.95, 0.86, 1),
            "tag_fg": (0.85, 0.50, 0.08, 1),
            "accent": (0.88, 0.52, 0.10, 1),
            "bg": (1, 0.98, 0.92, 1),
            "icon": "compass-outline",
            "icon_clr": (0.85, 0.50, 0.08, 1),
        },
    }

    @staticmethod
    def get_rec_category(rec_type, message=""):
        t = (rec_type or "").lower().strip()
        m = (message or "").lower().strip()

        # 1. Exact type match
        if t in ("price", "market"):
            return "price"
        if t in ("weather", "rain", "climate"):
            return "weather"
        if t in ("production", "supply", "harvest"):
            return "production"
        if t in ("combined", "advisory", "strategy"):
            return "combined"

        # 2. Score-based message classification (count keyword hits)
        # Split title (before ':') vs body for weighted scoring
        if ":" in m:
            title_part = m.split(":", 1)[0]
            body_part = m.split(":", 1)[1]
        else:
            title_part = ""
            body_part = m

        kw = {
            "price":      ["price surge", "price drop", "price rising", "price forecast", "rs.", "/kg", "wholesale", "selling price", "profit margin"],
            "weather":    ["rain", "weather", "rainfall", "drought", "dry spell", "irrigation", "drainage", "flood", "fungal", "monsoon", "climate"],
            "production": ["production", "harvest", "shortage", "surplus", "supply", "yield", "cultivation", "output", "regional output"],
            "combined":   ["advisory", "diversification", "optimization", "policy", "strategy", "recommend", "inter-crop", "opportunity", "long-term"],
        }

        scores = {"price": 0, "weather": 0, "production": 0, "combined": 0}
        for cat, words in kw.items():
            for w in words:
                if w in title_part:
                    scores[cat] += 3  # title match = heavy weight
                if w in body_part:
                    scores[cat] += 1

        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
        return "combined"

    def load_recommendations(self):
        role = self.user.get("user_type", "farmer") if self.user else "farmer"
        district = self.user.get("region", "Matale") if self.user else "Matale"
        user_id = self.user["user_id"]

        # Ensure seed recommendations exist
        ensure_sample_recommendations_if_empty(user_id, role, district)

        # Collect ML recs and DB recs
        ml_recs = self._get_ml_recommendations() or []
        db_recs = get_recommendations_for_user(user_id) or []

        all_items = []

        # 1. Add ML recommendations if available
        for r in ml_recs:
            rtype = r.get("type", "combined")
            cat = self.get_rec_category(rtype, r.get("message", ""))
            all_items.append({
                "id": None,
                "category": cat,
                "type": rtype,
                "severity": r.get("severity", "info"),
                "icon": r.get("icon"),
                "title": r.get("title") or f"{cat.title()} Advisory",
                "message": r.get("message", ""),
                "vegetable": r.get("vegetable"),
                "created_at": None,
                "is_ml": True,
            })

        # 2. Add DB recommendations
        for r in db_recs:
            msg = r.get("message", "")
            if ":" in msg:
                raw_title, raw_msg = msg.split(":", 1)
                title = raw_title.strip()
                body = raw_msg.strip()
            else:
                title = "Agricultural Advisory"
                body = msg.strip()

            cat = self.get_rec_category(None, msg)
            created_at = r.get("created_at")
            if hasattr(created_at, "strftime"):
                date_str = created_at.strftime("%d %b %Y")
            else:
                date_str = str(created_at) if created_at else ""

            all_items.append({
                "id": r.get("id"),
                "category": cat,
                "type": cat,
                "severity": "info",
                "icon": None,
                "title": title,
                "message": body,
                "vegetable": None,
                "created_at": date_str,
                "is_ml": False,
            })

        self._all_recs_cache = all_items

        # Category counts
        counts = {
            "all": len(self._all_recs_cache),
            "price": 0,
            "weather": 0,
            "production": 0,
            "combined": 0,
        }
        for item in self._all_recs_cache:
            c = item["category"]
            counts[c] = counts.get(c, 0) + 1

        # Build chips & render
        self._build_rec_category_chips(counts)
        self._render_filtered_recommendations()

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

    def _build_rec_category_chips(self, counts):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon

        chip_row = self.ids.rec_category_chips
        chip_row.clear_widgets()
        self._rec_category_widgets = {}

        for cat_key, cat_name, cat_icon in self.REC_CATEGORIES:
            count = counts.get(cat_key, 0)
            text_str = f"{cat_name} ({count})"
            chip_width = max(dp(76), dp(36) + len(text_str) * dp(6.8))
            chip = MDCard(
                orientation="horizontal",
                size_hint=(None, None),
                size=(chip_width, dp(34)),
                radius=[17, 17, 17, 17],
                elevation=0,
                ripple_behavior=True,
                padding=(dp(8), dp(4), dp(8), dp(4)),
                spacing=dp(4),
                pos_hint={"center_y": 0.5},
            )

            icon = MDIcon(
                icon=cat_icon,
                font_size="16sp",
                size_hint=(None, None),
                size=(dp(18), dp(18)),
                pos_hint={"center_y": 0.5},
            )
            lbl = MDLabel(
                text=text_str,
                font_style="Caption",
                halign="center",
                pos_hint={"center_y": 0.5},
            )

            chip.add_widget(icon)
            chip.add_widget(lbl)
            chip._icon = icon
            chip._lbl = lbl

            chip.bind(on_release=lambda inst, k=cat_key: self.pick_rec_category(k))
            chip_row.add_widget(chip)
            self._rec_category_widgets[cat_key] = chip

        self._update_rec_category_chips_ui()

    def _update_rec_category_chips_ui(self):
        for k, chip in self._rec_category_widgets.items():
            sel = (k == self.selected_rec_category)
            # BLUE/INDIGO theme for Recommendations
            bg = (0.22, 0.42, 0.85, 1) if sel else (0.92, 0.94, 0.99, 1)
            fg = (1, 1, 1, 1) if sel else (0.25, 0.35, 0.60, 1)
            chip.md_bg_color = bg
            chip._lbl.text_color = fg
            chip._lbl.theme_text_color = "Custom"
            chip._lbl.bold = sel
            chip._icon.text_color = fg
            chip._icon.theme_text_color = "Custom"

    def pick_rec_category(self, cat_key):
        if self.selected_rec_category == cat_key:
            return
        self.selected_rec_category = cat_key
        self._update_rec_category_chips_ui()
        self._render_filtered_recommendations()

    def _render_filtered_recommendations(self):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivy.graphics import Color, RoundedRectangle

        box = self.ids.rec_box
        box.clear_widgets()

        if not self._all_recs_cache:
            # Empty state for whole tab
            empty_box = MDBoxLayout(
                orientation="vertical", spacing=dp(10),
                size_hint_y=None, height=dp(200),
                padding=(dp(20), dp(35), dp(20), dp(20)),
            )
            icon_lbl = MDIcon(
                icon="lightbulb-on-outline",
                halign="center", font_size="44sp",
                theme_text_color="Custom",
                text_color=(0.65, 0.75, 0.90, 1),
                size_hint_y=None, height=dp(52),
            )
            title_lbl = MDLabel(
                text="No recommendations yet",
                halign="center", bold=True, font_style="Subtitle1",
                theme_text_color="Custom",
                text_color=(0.35, 0.35, 0.35, 1),
                size_hint_y=None, height=dp(26),
            )
            msg_lbl = MDLabel(
                text="AI is analysing your crops, weather and market trends.\nCheck back shortly for personalised advice.",
                halign="center", theme_text_color="Custom",
                text_color=(0.55, 0.55, 0.55, 1),
                size_hint_y=None, height=dp(44),
            )
            empty_box.add_widget(icon_lbl)
            empty_box.add_widget(title_lbl)
            empty_box.add_widget(msg_lbl)
            box.add_widget(empty_box)
            fade_in(empty_box, duration=0.35)
            return

        cat = self.selected_rec_category
        if cat == "all":
            recs = self._all_recs_cache
        else:
            recs = [r for r in self._all_recs_cache if r["category"] == cat]

        if not recs:
            # Empty state for selected category
            cat_display = next((name for k, name, _ in self.REC_CATEGORIES if k == cat), cat.title())
            empty_box = MDBoxLayout(
                orientation="vertical", spacing=dp(8),
                size_hint_y=None, height=dp(170),
                padding=(dp(20), dp(35), dp(20), dp(20)),
            )
            empty_icon = MDIcon(
                icon="lightbulb-outline",
                halign="center", font_size="40sp",
                theme_text_color="Custom",
                text_color=(0.55, 0.65, 0.85, 1),
                size_hint_y=None, height=dp(48),
            )
            empty_title = MDLabel(
                text=f"No {cat_display} Recommendations",
                halign="center", bold=True, font_style="Subtitle1",
                theme_text_color="Custom",
                text_color=(0.35, 0.35, 0.35, 1),
                size_hint_y=None, height=dp(24),
            )
            empty_msg = MDLabel(
                text=f"Currently no specific {cat_display.lower()} advisories active. AI is monitoring incoming data.",
                halign="center", theme_text_color="Custom",
                text_color=(0.55, 0.55, 0.55, 1),
                size_hint_y=None, height=dp(36),
            )
            empty_box.add_widget(empty_icon)
            empty_box.add_widget(empty_title)
            empty_box.add_widget(empty_msg)
            box.add_widget(empty_box)
            fade_in(empty_box, duration=0.3)
            return

        cards = []
        for r in recs:
            cat_style = self.REC_CATEGORY_STYLES.get(r["category"], self.REC_CATEGORY_STYLES["combined"])
            icon_name = r.get("icon") or cat_style["icon"]

            card = MDCard(
                orientation="vertical",
                size_hint_y=None,
                height=dp(94),
                padding=(dp(12), dp(10), dp(12), dp(10)),
                spacing=dp(6),
                radius=[14, 14, 14, 14],
                md_bg_color=cat_style["bg"],
                elevation=1,
                ripple_behavior=True,
            )

            # Left accent bar
            with card.canvas.before:
                Color(*cat_style["accent"])
                card._acc = RoundedRectangle(
                    pos=card.pos,
                    size=(dp(4), card.height),
                    radius=[2, 2, 2, 2],
                )
            def _upd_accent(inst, *_, acc=card._acc):
                acc.pos = inst.pos
                acc.size = (dp(4), inst.height)
            card.bind(pos=_upd_accent, size=_upd_accent)

            # Top row: icon + (title + tag) + chevron
            top_row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(38),
                spacing=dp(10),
            )

            # Icon
            icon_card = MDCard(
                size_hint=(None, None), size=(dp(36), dp(36)),
                radius=[18, 18, 18, 18],
                md_bg_color=(*cat_style["accent"][:3], 0.15),
                elevation=0,
                pos_hint={"center_y": 0.5},
            )
            icon_widget = MDIcon(
                icon=icon_name,
                halign="center",
                font_size="20sp",
                theme_text_color="Custom",
                text_color=cat_style["icon_clr"],
                pos_hint={"center_x": 0.5, "center_y": 0.5},
            )
            icon_card.add_widget(icon_widget)
            top_row.add_widget(icon_card)

            # Header info column
            info_col = MDBoxLayout(
                orientation="vertical",
                spacing=dp(2),
                pos_hint={"center_y": 0.5},
            )
            title_lbl = MDLabel(
                text=r["title"],
                bold=True,
                font_style="Subtitle2",
                theme_text_color="Custom",
                text_color=(0.08, 0.08, 0.08, 1),
                size_hint_y=None, height=dp(18),
                shorten=True, shorten_from="right",
            )
            info_col.add_widget(title_lbl)

            # Tags row (Category Tag + Vegetable / Source)
            tags_row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(16),
                spacing=dp(6),
            )
            cat_pill = MDCard(
                size_hint=(None, None), size=(dp(58), dp(16)),
                radius=[4, 4, 4, 4],
                md_bg_color=cat_style["tag_bg"],
                elevation=0,
            )
            cat_lbl = MDLabel(
                text=cat_style["title"],
                halign="center", bold=True,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=cat_style["tag_fg"],
            )
            cat_pill.add_widget(cat_lbl)
            tags_row.add_widget(cat_pill)

            sub_txt = r.get("vegetable") or ("AI ML Model" if r["is_ml"] else (r.get("created_at") or "Advisor"))
            sub_lbl = MDLabel(
                text=sub_txt,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=cat_style["icon_clr"],
                size_hint_y=None, height=dp(16),
            )
            tags_row.add_widget(sub_lbl)
            info_col.add_widget(tags_row)
            top_row.add_widget(info_col)

            # Chevron indicator
            chevron = MDIcon(
                icon="chevron-down",
                size_hint=(None, None), size=(dp(22), dp(22)),
                theme_text_color="Custom",
                text_color=(0.50, 0.50, 0.50, 1),
                pos_hint={"center_y": 0.5},
            )
            top_row.add_widget(chevron)
            card.add_widget(top_row)

            # Message label
            msg_text = r["message"]
            msg_lbl = MDLabel(
                text=msg_text,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=(0.28, 0.28, 0.28, 1),
                size_hint_y=None,
                height=dp(36),
                shorten=True,
                shorten_from="right",
            )
            card.add_widget(msg_lbl)

            # Accordion expand / collapse state
            card._is_expanded = False
            card._chevron = chevron
            card._msg_lbl = msg_lbl
            card._collapsed_h = dp(94)

            # Calculate expanded height based on text length
            msg_len = len(msg_text)
            if msg_len < 90:
                card._expanded_h = dp(130)
            elif msg_len < 160:
                card._expanded_h = dp(155)
            else:
                card._expanded_h = dp(180)

            card.bind(on_release=lambda inst: self._toggle_rec_card(inst))

            box.add_widget(card)
            cards.append(card)

        stagger_fade_in(cards, step=0.05, duration=0.25)

    def _toggle_rec_card(self, card):
        try:
            card._is_expanded = not getattr(card, "_is_expanded", False)
            if card._is_expanded:
                card.height = card._expanded_h
                card._msg_lbl.height = card._expanded_h - dp(54)
                card._msg_lbl.shorten = False
                card._chevron.icon = "chevron-up"
            else:
                card.height = card._collapsed_h
                card._msg_lbl.height = dp(36)
                card._msg_lbl.shorten = True
                card._chevron.icon = "chevron-down"
        except Exception as e:
            print(f"[RecCard] toggle error: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # ALERTS TAB (Categorized: Price, Weather, Supply, Official Notices)
    # ══════════════════════════════════════════════════════════════════════
    ALERT_CATEGORIES = [
        ("all", "All", "bell-ring-outline"),
        ("price", "Price", "trending-up"),
        ("weather", "Weather", "weather-partly-cloudy"),
        ("production", "Supply", "package-variant"),
        ("official", "Notices", "bullhorn-outline"),
    ]

    ALERT_CATEGORY_STYLES = {
        "price": {
            "title": "PRICE",
            "tag_bg": (0.98, 0.90, 0.90, 1),
            "tag_fg": (0.85, 0.18, 0.18, 1),
        },
        "weather": {
            "title": "WEATHER",
            "tag_bg": (0.90, 0.94, 1.0, 1),
            "tag_fg": (0.15, 0.42, 0.82, 1),
        },
        "production": {
            "title": "SUPPLY",
            "tag_bg": (0.93, 0.91, 0.99, 1),
            "tag_fg": (0.42, 0.22, 0.78, 1),
        },
        "official": {
            "title": "OFFICIAL",
            "tag_bg": (1.0, 0.94, 0.86, 1),
            "tag_fg": (0.85, 0.44, 0.08, 1),
        },
    }

    @staticmethod
    def get_alert_category(alert_type, message=""):
        t = (alert_type or "").lower().strip()
        m = (message or "").lower().strip()
        if any(k in t for k in ["price", "spike", "drop", "surge", "cost"]):
            return "price"
        if any(k in t for k in ["rain", "weather", "drought", "temp", "flood", "storm", "climate"]):
            return "weather"
        if any(k in t for k in ["production", "surplus", "shortage", "supply", "harvest", "oversupply"]):
            return "production"
        if any(k in t for k in ["admin", "official", "notice", "announcement", "broadcast", "gov", "advisory"]):
            return "official"

        if any(k in m for k in ["price", "rs.", "/kg"]):
            return "price"
        if any(k in m for k in ["rainfall", "rain", "drought", "precipitation", "weather"]):
            return "weather"
        if any(k in m for k in ["production", "surplus", "shortage", "harvest", "supply", "mt"]):
            return "production"
        if any(k in m for k in ["admin", "department", "advisory", "notice", "centre", "task force"]):
            return "official"
        return "price"

    def load_alerts(self):
        # 1. Ensure realistic categorized alerts exist if first-time / empty
        role = self.user.get("user_type", "farmer") if self.user else "farmer"
        district = self.user.get("region", "Matale") if self.user else "Matale"
        user_id = self.user["user_id"]
        ensure_sample_alerts_if_empty(user_id, role, district)

        # 2. Fetch all alerts for user
        self._all_alerts_cache = get_alerts_for_user(user_id) or []

        # 3. Compute category counts
        counts = {
            "all": len(self._all_alerts_cache),
            "price": 0,
            "weather": 0,
            "production": 0,
            "official": 0,
        }
        for a in self._all_alerts_cache:
            cat = self.get_alert_category(a.get("type"), a.get("message"))
            counts[cat] = counts.get(cat, 0) + 1

        # 4. Build scrollable category chips
        self._build_alert_category_chips(counts)

        # 5. Render filtered alerts
        self._render_filtered_alerts()

    def _build_alert_category_chips(self, counts):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon

        chip_row = self.ids.alert_category_chips
        chip_row.clear_widgets()
        self._alert_category_widgets = {}

        for cat_key, cat_name, cat_icon in self.ALERT_CATEGORIES:
            count = counts.get(cat_key, 0)
            text_str = f"{cat_name} ({count})"
            chip_width = max(dp(76), dp(36) + len(text_str) * dp(6.8))
            chip = MDCard(
                orientation="horizontal",
                size_hint=(None, None),
                size=(chip_width, dp(34)),
                radius=[17, 17, 17, 17],
                elevation=0,
                ripple_behavior=True,
                padding=(dp(8), dp(4), dp(8), dp(4)),
                spacing=dp(4),
                pos_hint={"center_y": 0.5},
            )

            icon = MDIcon(
                icon=cat_icon,
                font_size="16sp",
                size_hint=(None, None),
                size=(dp(18), dp(18)),
                pos_hint={"center_y": 0.5},
            )
            lbl = MDLabel(
                text=text_str,
                font_style="Caption",
                halign="center",
                pos_hint={"center_y": 0.5},
            )

            chip.add_widget(icon)
            chip.add_widget(lbl)
            chip._icon = icon
            chip._lbl = lbl

            chip.bind(on_release=lambda inst, k=cat_key: self.pick_alert_category(k))
            chip_row.add_widget(chip)
            self._alert_category_widgets[cat_key] = chip

        self._update_alert_category_chips_ui()

    def _update_alert_category_chips_ui(self):
        for k, chip in self._alert_category_widgets.items():
            sel = (k == self.selected_alert_category)
            # RED/AMBER theme for Alerts
            bg = (0.82, 0.22, 0.15, 1) if sel else (1.0, 0.94, 0.92, 1)
            fg = (1, 1, 1, 1) if sel else (0.60, 0.25, 0.18, 1)
            Animation(md_bg_color=bg, duration=0.15).start(chip)
            chip._lbl.text_color = fg
            chip._lbl.theme_text_color = "Custom"
            chip._lbl.bold = sel
            chip._icon.text_color = fg
            chip._icon.theme_text_color = "Custom"

    def pick_alert_category(self, cat_key):
        if self.selected_alert_category == cat_key:
            return
        self.selected_alert_category = cat_key
        if cat_key in self._alert_category_widgets:
            bounce_scale(self._alert_category_widgets[cat_key])
        self._update_alert_category_chips_ui()
        self._render_filtered_alerts()

    def _render_filtered_alerts(self):
        from kivymd.uix.card import MDCard
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDIconButton

        box = self.ids.alert_box
        box.clear_widgets()

        if not self._all_alerts_cache:
            # Empty state for whole tab
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
            return

        cat = self.selected_alert_category
        if cat == "all":
            alerts = self._all_alerts_cache
        else:
            alerts = [a for a in self._all_alerts_cache if self.get_alert_category(a.get("type"), a.get("message")) == cat]

        if not alerts:
            # Empty state for selected category
            cat_display = next((name for k, name, _ in self.ALERT_CATEGORIES if k == cat), cat.title())
            empty_box = MDBoxLayout(
                orientation="vertical", spacing=dp(8),
                size_hint_y=None, height=dp(170),
                padding=(dp(20), dp(35), dp(20), dp(20)),
            )
            empty_icon = MDIcon(
                icon="shield-check-outline",
                halign="center", font_size="40sp",
                theme_text_color="Custom",
                text_color=(0.60, 0.80, 0.65, 1),
                size_hint_y=None, height=dp(48),
            )
            empty_title = MDLabel(
                text=f"No {cat_display} Alerts",
                halign="center", bold=True, font_style="Subtitle1",
                theme_text_color="Custom",
                text_color=(0.35, 0.35, 0.35, 1),
                size_hint_y=None, height=dp(24),
            )
            empty_msg = MDLabel(
                text=f"All clear in {cat_display.lower()} monitoring. No critical thresholds exceeded.",
                halign="center", theme_text_color="Custom",
                text_color=(0.55, 0.55, 0.55, 1),
                size_hint_y=None, height=dp(36),
            )
            empty_box.add_widget(empty_icon)
            empty_box.add_widget(empty_title)
            empty_box.add_widget(empty_msg)
            box.add_widget(empty_box)
            fade_in(empty_box, duration=0.3)
            return

        ALERT_STYLES = {
            "price_spike":        {"severity": "high",   "icon": "arrow-up-bold-circle",  "bg": (1, 0.94, 0.94, 1),  "icon_clr": (0.85, 0.18, 0.18, 1), "badge_bg": (0.85, 0.18, 0.18, 1)},
            "price_drop":         {"severity": "medium", "icon": "arrow-down-bold-circle","bg": (1, 0.97, 0.90, 1),  "icon_clr": (0.85, 0.55, 0.08, 1), "badge_bg": (0.90, 0.60, 0.10, 1)},
            "heavy_rain":         {"severity": "high",   "icon": "weather-pouring",       "bg": (0.92, 0.95, 1, 1),  "icon_clr": (0.15, 0.40, 0.80, 1), "badge_bg": (0.20, 0.45, 0.82, 1)},
            "drought_risk":       {"severity": "medium", "icon": "weather-sunny-alert",   "bg": (1, 0.97, 0.90, 1),  "icon_clr": (0.85, 0.55, 0.08, 1), "badge_bg": (0.90, 0.60, 0.10, 1)},
            "production_surplus":  {"severity": "medium", "icon": "package-variant-plus", "bg": (0.95, 0.97, 1, 1),  "icon_clr": (0.30, 0.45, 0.70, 1), "badge_bg": (0.35, 0.50, 0.75, 1)},
            "production_shortage": {"severity": "high",   "icon": "package-variant-minus","bg": (1, 0.94, 0.94, 1),  "icon_clr": (0.85, 0.18, 0.18, 1), "badge_bg": (0.85, 0.18, 0.18, 1)},
            "admin_broadcast":     {"severity": "medium", "icon": "bullhorn",             "bg": (0.94, 0.96, 1, 1),  "icon_clr": (0.18, 0.45, 0.85, 1), "badge_bg": (0.20, 0.48, 0.88, 1)},
            "official_notice":     {"severity": "high",   "icon": "shield-alert-outline", "bg": (1.0, 0.95, 0.88, 1), "icon_clr": (0.88, 0.42, 0.08, 1), "badge_bg": (0.90, 0.45, 0.10, 1)},
        }
        DEFAULT_STYLE = {"severity": "medium", "icon": "alert-circle", "bg": (0.97, 0.97, 0.97, 1), "icon_clr": (0.65, 0.65, 0.65, 1), "badge_bg": (0.65, 0.65, 0.65, 1)}

        cards = []
        for a in alerts:
            is_unread = not a["is_read"]
            atype = a.get("type", "")
            style = ALERT_STYLES.get(atype, DEFAULT_STYLE)
            bg = style["bg"] if is_unread else (0.97, 0.97, 0.97, 1)

            card = MDCard(
                orientation="horizontal", size_hint_y=None, height=dp(88),
                padding=(dp(12), dp(10), dp(8), dp(10)), spacing=dp(10),
                radius=[14, 14, 14, 14],
                md_bg_color=bg,
                elevation=2 if is_unread else 0,
            )

            # Icon circle
            icon_circle = MDCard(
                size_hint=(None, None), size=(dp(42), dp(42)),
                radius=[21, 21, 21, 21],
                md_bg_color=(*style["icon_clr"][:3], 0.15),
                elevation=0,
                pos_hint={"center_y": 0.5},
            )
            icon_widget = MDIcon(
                icon=style["icon"] if is_unread else "check-circle-outline",
                halign="center", font_size="22sp",
                theme_text_color="Custom",
                text_color=style["icon_clr"] if is_unread else (0.65, 0.65, 0.65, 1),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
            )
            icon_circle.add_widget(icon_widget)

            # Content box
            content_box = MDBoxLayout(
                orientation="vertical",
                spacing=dp(3),
                pos_hint={"center_y": 0.5},
            )

            # Tags row: Category Pill + Severity Pill + Type Label
            item_cat = self.get_alert_category(atype, a.get("message", ""))
            cat_style = self.ALERT_CATEGORY_STYLES.get(item_cat, self.ALERT_CATEGORY_STYLES["price"])

            tags_row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(18),
                spacing=dp(5),
            )

            # 1. Category Tag Pill
            cat_pill = MDCard(
                size_hint=(None, None), size=(dp(58), dp(16)),
                radius=[4, 4, 4, 4],
                md_bg_color=cat_style["tag_bg"] if is_unread else (0.90, 0.90, 0.90, 1),
                elevation=0,
            )
            cat_lbl = MDLabel(
                text=cat_style["title"], halign="center",
                bold=True, font_style="Caption",
                theme_text_color="Custom",
                text_color=cat_style["tag_fg"] if is_unread else (0.45, 0.45, 0.45, 1),
            )
            cat_pill.add_widget(cat_lbl)
            tags_row.add_widget(cat_pill)

            # 2. Severity Pill
            sev_badge = MDCard(
                size_hint=(None, None), size=(dp(48), dp(16)),
                radius=[4, 4, 4, 4],
                md_bg_color=style["badge_bg"] if is_unread else (0.78, 0.78, 0.78, 1),
                elevation=0,
            )
            sev_lbl = MDLabel(
                text=style["severity"].upper(), halign="center",
                bold=True, font_style="Caption",
                theme_text_color="Custom", text_color=(1, 1, 1, 1),
            )
            sev_badge.add_widget(sev_lbl)
            tags_row.add_widget(sev_badge)

            # 3. Type heading
            type_title = atype.replace("_", " ").title() if atype else "Alert"
            type_lbl = MDLabel(
                text=type_title,
                font_style="Caption", bold=True,
                theme_text_color="Custom",
                text_color=style["icon_clr"] if is_unread else (0.50, 0.50, 0.50, 1),
            )
            tags_row.add_widget(type_lbl)

            msg_lbl = MDLabel(
                text=a["message"], theme_text_color="Custom",
                text_color=(0.10, 0.10, 0.10, 1) if is_unread else (0.50, 0.50, 0.50, 1),
                font_style="Caption",
            )

            content_box.add_widget(tags_row)
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

    def dismiss_alert(self, alert_id, card):
        def _remove():
            mark_alert_read(alert_id)
            if card.parent:
                card.parent.remove_widget(card)
            # Update cache and re-count
            for a in self._all_alerts_cache:
                if a["id"] == alert_id:
                    a["is_read"] = True
            # Refresh category chips count
            counts = {
                "all": len(self._all_alerts_cache),
                "price": 0,
                "weather": 0,
                "production": 0,
                "official": 0,
            }
            for a in self._all_alerts_cache:
                cat = self.get_alert_category(a.get("type"), a.get("message"))
                counts[cat] = counts.get(cat, 0) + 1
            for cat_key, _, _ in self.ALERT_CATEGORIES:
                chip = self._alert_category_widgets.get(cat_key)
                if chip:
                    cat_name = next(name for k, name, _ in self.ALERT_CATEGORIES if k == cat_key)
                    chip._lbl.text = f"{cat_name} ({counts.get(cat_key, 0)})"

        fade_out_remove(card, duration=0.25, callback=_remove)

    def mark_all_alerts_read(self):
        for a in self._all_alerts_cache:
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

    def select_history_year(self, year):
        self.history_selected_year = int(year)
        self.load_history()

    def set_history_inspect_mode(self, mode):
        self.history_inspect_mode = mode
        if mode == "ai_forecast":
            # Future forecast: default to next week if in past
            if not self.history_selected_date or self.history_selected_date < date.today():
                self.history_selected_date = date.today() + timedelta(days=7)
                self.history_selected_date_str = self.history_selected_date.strftime("%d %b %Y")
        else:
            # Historical actual: default to latest record date if in future
            latest_dt = get_latest_record_date(self.history_crop_id) or (date.today() - timedelta(days=1))
            if not self.history_selected_date or self.history_selected_date >= date.today():
                self.history_selected_date = latest_dt
                self.history_selected_date_str = latest_dt.strftime("%d %b %Y")
        self.load_history()

    def open_history_date_picker(self):
        try:
            if self.history_inspect_mode == "ai_forecast":
                # AI forecast: future dates only from today onwards
                min_d = date.today()
                max_d = date.today() + timedelta(days=365)
                init_d = self.history_selected_date if (self.history_selected_date and self.history_selected_date >= min_d) else (date.today() + timedelta(days=7))
                picker = MDDatePicker(
                    min_date=min_d,
                    max_date=max_d,
                    year=init_d.year,
                    month=init_d.month,
                    day=init_d.day,
                )
            else:
                # Historical: actual record date range only
                latest_dt = get_latest_record_date(self.history_crop_id) or (date.today() - timedelta(days=1))
                earliest_dt = get_earliest_record_date(self.history_crop_id) or date(2020, 1, 1)
                init_d = self.history_selected_date if (self.history_selected_date and earliest_dt <= self.history_selected_date <= latest_dt) else latest_dt
                picker = MDDatePicker(
                    min_date=earliest_dt,
                    max_date=latest_dt,
                    year=init_d.year,
                    month=init_d.month,
                    day=init_d.day,
                )
            picker.bind(on_save=self._on_history_date_picked)
            picker.open()
        except Exception as e:
            print(f"[DashboardScreen] DatePicker error: {e}")

    def _on_history_date_picked(self, instance, value, date_range):
        self.history_selected_date = value
        self.history_selected_date_str = value.strftime("%d %b %Y")
        self.load_history()

    def open_price_history_screen(self):
        if self.manager and "price_history" in self.manager.screen_names:
            self.manager.transition.direction = "left"
            scr = self.manager.get_screen("price_history")
            scr.selected_crop_id = self.history_crop_id
            scr.selected_crop_name = self.history_crop_name
            scr.inspect_mode = self.history_inspect_mode
            if self.history_selected_date:
                scr.selected_date = self.history_selected_date
                scr.selected_date_str = self.history_selected_date_str
            self.manager.current = "price_history"
            scr.load_data()

    def load_history(self):
        from utils.chart_utils import build_line_chart, build_bar_chart
        from kivymd.uix.label import MDLabel
        from kivymd.uix.card import MDCard
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton

        box = self.ids.history_box
        box.clear_widgets()
        if not self.history_crop_id:
            return

        region_id = self.user.get("region_id") if self.user else None
        district = (get_region_district(region_id) if region_id else None) or "Kandy"
        ai_active = (self.history_inspect_mode == "ai_forecast")

        # 1. Date Inspector Card (Exclusively shows either AI Prediction or Historical Records)
        if not self.history_selected_date:
            if ai_active:
                self.history_selected_date = date.today() + timedelta(days=7)
            else:
                self.history_selected_date = get_latest_record_date(self.history_crop_id) or (date.today() - timedelta(days=1))
            self.history_selected_date_str = self.history_selected_date.strftime("%d %b %Y")

        inspect_card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            radius=[16, 16, 16, 16],
            elevation=1,
            padding=dp(14),
            spacing=dp(10),
            md_bg_color=(1, 1, 1, 1),
        )
        inspect_card.bind(minimum_height=inspect_card.setter("height"))

        # Mode Selector Buttons (Segmented Contained Pill Container)
        mode_card = MDCard(
            size_hint_y=None,
            height=dp(42),
            radius=[12, 12, 12, 12],
            elevation=0,
            md_bg_color=(0.93, 0.96, 0.93, 1),
            padding=dp(3),
        )
        mode_row = MDBoxLayout(orientation="horizontal", spacing=dp(4))
        ai_btn = MDRaisedButton(
            text="AI Predictions",
            elevation=0,
            _radius=10,
            size_hint_x=0.5,
            font_size="13sp",
            md_bg_color=(0.25, 0.62, 0.30, 1) if ai_active else (0.93, 0.96, 0.93, 1),
            text_color=(1, 1, 1, 1) if ai_active else (0.2, 0.45, 0.2, 1),
            on_release=lambda *args: self.set_history_inspect_mode("ai_forecast"),
        )
        hist_btn = MDRaisedButton(
            text="Historical Data",
            elevation=0,
            _radius=10,
            size_hint_x=0.5,
            font_size="13sp",
            md_bg_color=(0.25, 0.62, 0.30, 1) if not ai_active else (0.93, 0.96, 0.93, 1),
            text_color=(1, 1, 1, 1) if not ai_active else (0.2, 0.45, 0.2, 1),
            on_release=lambda *args: self.set_history_inspect_mode("historical_actual"),
        )
        mode_row.add_widget(ai_btn)
        mode_row.add_widget(hist_btn)
        mode_card.add_widget(mode_row)
        inspect_card.add_widget(mode_card)


        # Header Row with Date picker
        hdr = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(34), spacing=dp(6))
        hdr_icon = MDIconButton(
            icon="crystal-ball" if ai_active else "database-clock",
            theme_text_color="Custom",
            text_color=(0.15, 0.45, 0.75, 1) if ai_active else (0.22, 0.55, 0.25, 1),
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            pos_hint={"center_y": 0.5},
        )
        hdr_lbl = MDLabel(
            text="AI Future Predictions" if ai_active else "Historical Actual Records",
            font_style="Subtitle2",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.10, 0.30, 0.60, 1) if ai_active else (0.15, 0.40, 0.18, 1),
            pos_hint={"center_y": 0.5},
        )
        pick_btn = MDRaisedButton(
            text="Pick Future Date" if ai_active else "Pick Past Date",
            elevation=0,
            _radius=10,
            size_hint=(None, None),
            height=dp(30),
            md_bg_color=(0.90, 0.94, 1.0, 1) if ai_active else (0.90, 0.95, 0.90, 1),
            text_color=(0.10, 0.35, 0.70, 1) if ai_active else (0.15, 0.45, 0.20, 1),
            pos_hint={"center_y": 0.5},
            on_release=lambda *args: self.open_history_date_picker(),
        )
        hdr.add_widget(hdr_icon)
        hdr.add_widget(hdr_lbl)
        hdr.add_widget(pick_btn)
        inspect_card.add_widget(hdr)

        # Subtitle
        date_lbl = MDLabel(
            text=f"Selected: {self.history_selected_date_str}   •   {self.history_crop_name}   •   {district}",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.45, 0.45, 0.45, 1),
            size_hint_y=None,
            height=dp(18),
        )
        inspect_card.add_widget(date_lbl)

        if ai_active:
            # 🔮 ONLY AI PREDICTIONS SHOWN (Actual market box is completely removed)
            hist_rows = get_price_history(self.history_crop_id, region_id=region_id, weeks=14)
            p_history = [p for _, p in hist_rows] if hist_rows else None
            curr_p = p_history[-1] if p_history else 200.0
            pred_price = predict_price(crop=self.history_crop_name, district=district, price_history=p_history, current_price=curr_p)
            pred_prod = predict_production(vegetable=self.history_crop_name, district=district)

            pred_box = MDCard(
                orientation="vertical",
                size_hint_y=None,
                radius=[12, 12, 12, 12],
                elevation=0,
                md_bg_color=(0.92, 0.96, 1.0, 1),
                padding=(dp(12), dp(10)),
                spacing=dp(6),
            )
            pred_box.bind(minimum_height=pred_box.setter("height"))

            pred_title = MDLabel(
                text=f"AI Forecast for {self.history_selected_date_str} ({district}):",
                font_style="Caption",
                bold=True,
                theme_text_color="Custom",
                text_color=(0.15, 0.35, 0.65, 1),
                size_hint_y=None,
                height=dp(18),
            )
            pred_box.add_widget(pred_title)

            pred_p_text = f"• Predicted Price: Rs. {pred_price:,.2f} / kg" if pred_price is not None else "• Predicted Price: Unavailable"
            pred_p_lbl = MDLabel(
                text=pred_p_text,
                font_style="Body2",
                bold=True,
                theme_text_color="Custom",
                text_color=(0.10, 0.28, 0.60, 1),
                size_hint_y=None,
                height=dp(20),
            )
            pred_box.add_widget(pred_p_lbl)

            pred_prod_text = f"• Predicted Production: {pred_prod:,.2f} Mt" if pred_prod is not None else "• Predicted Production: Unavailable"
            pred_prod_lbl = MDLabel(
                text=pred_prod_text,
                font_style="Body2",
                bold=True,
                theme_text_color="Custom",
                text_color=(0.10, 0.28, 0.60, 1),
                size_hint_y=None,
                height=dp(20),
            )
            pred_box.add_widget(pred_prod_lbl)

            pred_note = MDLabel(
                text="Powered by LSTM Neural Network & Random Forest Regressor",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=(0.35, 0.45, 0.55, 1),
                size_hint_y=None,
                height=dp(16),
            )
            pred_box.add_widget(pred_note)
            inspect_card.add_widget(pred_box)
        else:
            # 📜 ONLY ACTUAL MARKET RECORDS SHOWN (AI forecast box is completely removed)
            actual_price = get_price_by_date(self.history_crop_id, self.history_selected_date, region_id=region_id)
            actual_prod = get_production_by_date(self.history_crop_id, self.history_selected_date, region_id=region_id)

            actual_box = MDCard(
                orientation="vertical",
                size_hint_y=None,
                radius=[12, 12, 12, 12],
                elevation=0,
                md_bg_color=(0.94, 0.98, 0.94, 1),
                padding=(dp(12), dp(10)),
                spacing=dp(6),
            )
            actual_box.bind(minimum_height=actual_box.setter("height"))

            actual_title = MDLabel(
                text=f"Actual Market Records on {self.history_selected_date_str}:",
                font_style="Caption",
                bold=True,
                theme_text_color="Custom",
                text_color=(0.20, 0.50, 0.22, 1),
                size_hint_y=None,
                height=dp(18),
            )
            actual_box.add_widget(actual_title)

            p_text = f"• Actual Price: Rs. {actual_price:,.2f} / kg" if actual_price is not None else "• Actual Price: No record on this date"
            actual_p_lbl = MDLabel(
                text=p_text,
                font_style="Body2",
                bold=(actual_price is not None),
                theme_text_color="Custom",
                text_color=(0.12, 0.35, 0.15, 1) if actual_price is not None else (0.55, 0.45, 0.35, 1),
                size_hint_y=None,
                height=dp(20),
            )
            actual_box.add_widget(actual_p_lbl)

            prod_text = f"• Actual Production: {actual_prod:,.2f} Mt" if actual_prod is not None else "• Actual Production: No record on this date"
            actual_prod_lbl = MDLabel(
                text=prod_text,
                font_style="Body2",
                bold=(actual_prod is not None),
                theme_text_color="Custom",
                text_color=(0.12, 0.35, 0.15, 1) if actual_prod is not None else (0.55, 0.45, 0.35, 1),
                size_hint_y=None,
                height=dp(20),
            )
            actual_box.add_widget(actual_prod_lbl)

            actual_note = MDLabel(
                text="Verified wholesale market transaction records",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=(0.35, 0.50, 0.35, 1),
                size_hint_y=None,
                height=dp(16),
            )
            actual_box.add_widget(actual_note)
            inspect_card.add_widget(actual_box)

        # Detailed View button
        detail_btn = MDFlatButton(
            text="Open Full AI Forecast Explorer →" if ai_active else "Open Full Historical Records Explorer →",
            theme_text_color="Custom",
            text_color=(0.15, 0.45, 0.70, 1) if ai_active else (0.20, 0.55, 0.25, 1),
            size_hint_x=1,
            on_release=lambda *args: self.open_price_history_screen(),
        )
        inspect_card.add_widget(detail_btn)
        box.add_widget(inspect_card)

        # 2. Year-by-Year Historical Trend Analysis
        from kivy.uix.scrollview import ScrollView
        from kivymd.uix.gridlayout import MDGridLayout

        years = get_available_record_years(self.history_crop_id)
        if not years:
            years = [2025, 2024, 2023, 2022, 2021]
        if self.history_selected_year not in years:
            self.history_selected_year = years[0]

        trend_hdr = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28), spacing=dp(6))
        trend_icon = MDIconButton(
            icon="chart-timeline-variant",
            theme_text_color="Custom",
            text_color=(0.22, 0.55, 0.25, 1),
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={"center_y": 0.5},
        )
        trend_title = MDLabel(
            text=f"Yearly Trend Analysis ({self.history_metric.title()}):",
            font_style="Subtitle2",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.20, 0.45, 0.22, 1),
            pos_hint={"center_y": 0.5},
        )
        trend_hdr.add_widget(trend_icon)
        trend_hdr.add_widget(trend_title)
        box.add_widget(trend_hdr)

        # Year Chips Selector
        chip_scroll = ScrollView(size_hint_y=None, height=dp(40), do_scroll_y=False, bar_width=0)
        chip_row = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_x=None, padding=(dp(2), dp(2), dp(2), dp(2)))
        chip_row.bind(minimum_width=chip_row.setter("width"))

        for yr in years:
            is_active = (yr == self.history_selected_year)
            yr_btn = MDRaisedButton(
                text=str(yr),
                size_hint=(None, None),
                height=dp(32),
                elevation=0,
                _radius=10,
                md_bg_color=(0.22, 0.55, 0.25, 1) if is_active else (0.92, 0.95, 0.92, 1),
                text_color=(1, 1, 1, 1) if is_active else (0.20, 0.45, 0.20, 1),
                font_size="13sp",
                on_release=lambda x, y=yr: self.select_history_year(y),
            )
            chip_row.add_widget(yr_btn)

        chip_scroll.add_widget(chip_row)
        box.add_widget(chip_scroll)

        # Summary Metrics Card & Chart Data
        if self.history_metric == "price":
            data, stats = get_price_history_by_year(self.history_crop_id, self.history_selected_year, region_id=region_id)
            if not data:
                box.add_widget(MDLabel(
                    text=f"No price data recorded for {self.history_crop_name} in {self.history_selected_year}.",
                    theme_text_color="Custom", text_color=(0.45, 0.45, 0.45, 1),
                    halign="center",
                ))
                center_scroll_content(box.parent, box)
                return

            if stats:
                stats_card = MDCard(
                    size_hint_y=None,
                    height=dp(54),
                    radius=[10, 10, 10, 10],
                    elevation=0,
                    md_bg_color=(0.95, 0.97, 0.95, 1),
                    padding=(dp(6), dp(4)),
                )
                grid = MDGridLayout(cols=3, spacing=dp(4))
                c1 = MDBoxLayout(orientation="vertical")
                c1.add_widget(MDLabel(text="Annual Average", font_style="Caption", halign="center", theme_text_color="Custom", text_color=(0.45, 0.45, 0.45, 1)))
                c1.add_widget(MDLabel(text=f"Rs. {stats['avg']:,.1f}", font_style="Caption", bold=True, halign="center", theme_text_color="Custom", text_color=(0.15, 0.45, 0.20, 1)))
                grid.add_widget(c1)

                c2 = MDBoxLayout(orientation="vertical")
                c2.add_widget(MDLabel(text="Peak (Highest)", font_style="Caption", halign="center", theme_text_color="Custom", text_color=(0.45, 0.45, 0.45, 1)))
                c2.add_widget(MDLabel(text=f"Rs. {stats['max']:,.0f} ({stats['max_month']})", font_style="Caption", bold=True, halign="center", theme_text_color="Custom", text_color=(0.12, 0.50, 0.20, 1)))
                grid.add_widget(c2)

                c3 = MDBoxLayout(orientation="vertical")
                c3.add_widget(MDLabel(text="Floor (Lowest)", font_style="Caption", halign="center", theme_text_color="Custom", text_color=(0.45, 0.45, 0.45, 1)))
                c3.add_widget(MDLabel(text=f"Rs. {stats['min']:,.0f} ({stats['min_month']})", font_style="Caption", bold=True, halign="center", theme_text_color="Custom", text_color=(0.75, 0.25, 0.20, 1)))
                grid.add_widget(c3)
                stats_card.add_widget(grid)
                box.add_widget(stats_card)

            dates, values = zip(*data)
            chart = build_line_chart(
                list(dates), list(values),
                title=f"{self.history_crop_name} — {self.history_selected_year} Price Trend ({district})",
                y_label="LKR / kg",
            )
        else:
            data, stats = get_production_history_by_year(self.history_crop_id, self.history_selected_year, region_id=region_id)
            if not data:
                box.add_widget(MDLabel(
                    text=f"No production data recorded for {self.history_crop_name} in {self.history_selected_year}.",
                    theme_text_color="Custom", text_color=(0.45, 0.45, 0.45, 1),
                    halign="center",
                ))
                center_scroll_content(box.parent, box)
                return

            if stats:
                stats_card = MDCard(
                    size_hint_y=None,
                    height=dp(54),
                    radius=[10, 10, 10, 10],
                    elevation=0,
                    md_bg_color=(0.95, 0.97, 0.95, 1),
                    padding=(dp(6), dp(4)),
                )
                grid = MDGridLayout(cols=3, spacing=dp(4))
                c1 = MDBoxLayout(orientation="vertical")
                c1.add_widget(MDLabel(text="Annual Harvest", font_style="Caption", halign="center", theme_text_color="Custom", text_color=(0.45, 0.45, 0.45, 1)))
                c1.add_widget(MDLabel(text=f"{stats['total']:,.0f} Mt", font_style="Caption", bold=True, halign="center", theme_text_color="Custom", text_color=(0.15, 0.45, 0.20, 1)))
                grid.add_widget(c1)

                c2 = MDBoxLayout(orientation="vertical")
                c2.add_widget(MDLabel(text="Peak Harvest", font_style="Caption", halign="center", theme_text_color="Custom", text_color=(0.45, 0.45, 0.45, 1)))
                c2.add_widget(MDLabel(text=f"{stats['max']:,.0f} Mt ({stats['max_month']})", font_style="Caption", bold=True, halign="center", theme_text_color="Custom", text_color=(0.12, 0.50, 0.20, 1)))
                grid.add_widget(c2)

                c3 = MDBoxLayout(orientation="vertical")
                c3.add_widget(MDLabel(text="Lowest Month", font_style="Caption", halign="center", theme_text_color="Custom", text_color=(0.45, 0.45, 0.45, 1)))
                c3.add_widget(MDLabel(text=f"{stats['min']:,.0f} Mt ({stats['min_month']})", font_style="Caption", bold=True, halign="center", theme_text_color="Custom", text_color=(0.75, 0.25, 0.20, 1)))
                grid.add_widget(c3)
                stats_card.add_widget(grid)
                box.add_widget(stats_card)

            dates, values = zip(*data)
            chart = build_bar_chart(
                list(dates), list(values),
                title=f"{self.history_crop_name} — {self.history_selected_year} Harvest Volume ({district})",
                y_label="Mt",
            )

        chart.size_hint_y = None
        chart.height = dp(320)
        chart.size_hint_x = 1
        chart.pos_hint = {"center_x": 0.5}
        chart.opacity = 0
        box.add_widget(chart)
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
            size_hint_y=None, height=dp(105),
            spacing=dp(4),
            pos_hint={"center_x": 0.5},
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
            orientation="vertical", padding=dp(14), spacing=dp(4),
            size_hint=(None, None), width=dp(260), height=dp(90),
            radius=[16, 16, 16, 16],
            md_bg_color=(0.93, 0.98, 0.93, 1), elevation=0,
            pos_hint={"center_x": 0.5},
        )
        info_card.add_widget(MDLabel(
            text=self.user["email"],
            theme_text_color="Custom", text_color=(0.40, 0.40, 0.40, 1),
            font_style="Caption", halign="center",
        ))
        info_card.add_widget(MDLabel(
            text=f"Role: {self.user['user_type'].capitalize()}",
            theme_text_color="Custom", text_color=(0.22, 0.60, 0.28, 1),
            font_style="Subtitle2", bold=True, halign="center",
        ))
        info_card.add_widget(MDLabel(
            text=f"District: {self.user.get('district') or '—'}",
            theme_text_color="Custom", text_color=(0.22, 0.60, 0.28, 1),
            font_style="Subtitle2", bold=True, halign="center",
        ))
        box.add_widget(info_card)

        # ── action buttons ────────────────────────────────────────────
        from kivymd.uix.button import MDFillRoundFlatIconButton

        def _btn(text, icon, bg, callback, txt_color=(1, 1, 1, 1)):
            b = MDFillRoundFlatIconButton(
                text=text,
                icon=icon,
                md_bg_color=bg,
                text_color=txt_color,
                icon_color=txt_color,
                size_hint=(None, None),
                width=dp(230),
                height=dp(40),
                pos_hint={"center_x": 0.5},
                on_release=callback,
            )
            return b

        edit_btn      = _btn("Edit Profile Details", "account-edit-outline", (0.22, 0.60, 0.28, 1), self.open_edit_profile_dialog)
        crops_btn     = _btn("Edit Followed Crops",   "sprout-outline",       (0.32, 0.68, 0.35, 1), self.edit_crops)
        feedback_btn  = _btn("Send Feedback",         "comment-text-outline", (0.90, 0.96, 0.90, 1), self.go_feedback,
                              txt_color=(0.12, 0.35, 0.16, 1))
        logout_btn    = _btn("Log Out",               "logout",               (0.88, 0.22, 0.22, 1), self.logout)

        profile_action_btns = [edit_btn, crops_btn]
        if self.user.get("user_type") == "policymaker":
            policy_comm_btn = _btn("Admin Communications", "shield-account", (0.12, 0.24, 0.18, 1), self.go_to_policy_communications)
            profile_action_btns.append(policy_comm_btn)

        profile_action_btns.extend([feedback_btn, logout_btn])

        for b in profile_action_btns:
            box.add_widget(b)

        stagger_fade_in([avatar_box, info_card] + profile_action_btns,
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

    def go_to_policy_communications(self, *args):
        self.manager.transition.direction = "left"
        self.manager.current = "policy_communication"

    def logout(self, *args):
        self.app.current_user = None
        self.manager.transition.direction = "right"
        self.manager.current = "login"
        show_snackbar("Logged out successfully.")
