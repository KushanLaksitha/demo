"""
AgriSense — AI-driven vegetable production & price optimization app.
Run with:  python main.py
"""
import os
import threading
from kivy.config import Config

# Simulate a phone screen when testing on desktop (comment out for real Android build)
Config.set("graphics", "width", "360")
Config.set("graphics", "height", "640")
Config.set("graphics", "resizable", "0")

from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivymd.app import MDApp

from database.db_connection import test_connection
from screens.loading_screen import LoadingScreen
from screens.login_screen import LoginScreen
from screens.register_screen import RegisterScreen
from screens.crop_selection_screen import CropSelectionScreen
from screens.dashboard_screen import DashboardScreen
from screens.admin_dashboard_screen import AdminDashboardScreen
from screens.feedback_screen import FeedbackScreen


class AgriSenseApp(MDApp):
    current_user = None  # dict set on successful login, cleared on logout

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.accent_palette = "LightGreen"
        self.title = "AgriSense"

        if test_connection():
            try:
                from database.models import Base, User
                from database.db_connection import engine, get_session
                from database.seed_demo_data import run as seed_data

                Base.metadata.create_all(engine)
                db = get_session()
                try:
                    if db.query(User).count() == 0:
                        print("[AgriSense] Database is empty. Populating demo data...")
                        seed_data()
                finally:
                    db.close()
            except Exception as e:
                print(f"[AgriSense] DB setup check error: {e}")
        else:
            print("[AgriSense] WARNING: Database connection failed.")

        # Preload ML models in background so they're warm by dashboard open
        self._preload_ml_models_async()

        sm = ScreenManager(transition=SlideTransition(duration=0.28))
        sm.add_widget(LoadingScreen(name="loading"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(CropSelectionScreen(name="crop_selection"))
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(AdminDashboardScreen(name="admin_dashboard"))
        sm.add_widget(FeedbackScreen(name="feedback"))
        return sm

    def _preload_ml_models_async(self):
        """Load ML models in background so the first prediction is instant."""
        def _load():
            try:
                from utils.ml_engine import preload_models
                ok = preload_models()
                print(f"[AgriSense] ML models preloaded: {ok}")
            except Exception as e:
                print(f"[AgriSense] ML preload error (non-fatal): {e}")
        threading.Thread(target=_load, daemon=True).start()

    def route_to_dashboard(self):
        """Called by LoginScreen after a successful login — sends each role
        to the right screen (admin skips crop-selection entirely, and
        anyone who somehow has no followed crops yet gets sent to pick some)."""
        from database.data_service import get_user_preferred_crop_ids

        sm = self.root
        sm.transition.direction = "left"
        if self.current_user["user_type"] == "admin":
            sm.current = "admin_dashboard"
            return
        if self.current_user["user_type"] in ("trader", "policymaker"):
            sm.current = "dashboard"
            return
        has_crops = bool(get_user_preferred_crop_ids(self.current_user["user_id"]))
        sm.current = "dashboard" if has_crops else "crop_selection"


if __name__ == "__main__":
    AgriSenseApp().run()
