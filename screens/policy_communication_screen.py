"""
Official Policy & Admin Communication Screen for AgriSense.
Enables secure, authenticated, direct two-way messaging between Policymakers
and Agricultural Administration.
• End-to-end official memos, price stabilization dispatches & supply interventions
• Real-time priority tagging: Urgent/Confidential, High Priority, Normal
• Threaded reply history with official administrative action tracking
• Role-aware: Seamlessly serves both Policymaker and Admin Console users
"""
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.scrollview import MDScrollView

from database.data_service import (
    get_policymaker_communications, get_admin_communications,
    send_official_communication, reply_official_communication,
    mark_communication_read, ensure_sample_communications_if_empty
)
from utils.animations import stagger_fade_in
from utils.layout_helpers import show_snackbar, center_scroll_content


KV = """
<PolicyCommunicationScreen>:
    canvas.before:
        Color:
            rgba: 0.95, 0.97, 0.95, 1
        Rectangle:
            pos: self.pos
            size: self.size

    MDBoxLayout:
        orientation: "vertical"
        spacing: 0

        # ── TOP APP BAR ──────────────────────────────────────────────────
        MDBoxLayout:
            size_hint_y: None
            height: dp(58)
            padding: dp(6), dp(4), dp(12), dp(4)
            spacing: dp(4)
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
                Color:
                    rgba: 0.88, 0.88, 0.88, 1
                Line:
                    points: self.x, self.y, self.x + self.width, self.y
                    width: 1

            MDIconButton:
                icon: "arrow-left"
                theme_text_color: "Custom"
                text_color: 0.20, 0.55, 0.28, 1
                pos_hint: {"center_y": 0.5}
                on_release: root.go_back()

            MDBoxLayout:
                orientation: "vertical"
                spacing: 0
                pos_hint: {"center_y": 0.5}

                MDLabel:
                    id: header_title
                    text: "Policy Desk"
                    font_style: "Subtitle1"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 0.10, 0.14, 0.20, 1
                    size_hint_y: None
                    height: dp(22)

                MDLabel:
                    id: header_subtitle
                    text: "OFFICIAL ADMIN DESK"
                    font_style: "Caption"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 0.22, 0.60, 0.28, 1
                    size_hint_y: None
                    height: dp(16)

            MDIconButton:
                id: refresh_btn
                icon: "refresh"
                theme_text_color: "Custom"
                text_color: 0.20, 0.55, 0.28, 1
                tooltip_text: "Refresh"
                pos_hint: {"center_y": 0.5}
                on_release: root.load_communications()

            MDRaisedButton:
                id: compose_btn
                text: "+ Memo"
                font_size: "11sp"
                size_hint: None, None
                size: dp(76), dp(32)
                _radius: 8
                elevation: 0
                md_bg_color: 0.15, 0.45, 0.25, 1
                text_color: 1, 1, 1, 1
                pos_hint: {"center_y": 0.5}
                on_release: root.open_compose_dialog()

        # ── OFFICIAL SECURITY BANNER ─────────────────────────────────────
        MDBoxLayout:
            id: security_banner
            size_hint_y: None
            height: dp(64)
            padding: dp(14), dp(8), dp(14), dp(8)
            spacing: dp(10)
            canvas.before:
                Color:
                    rgba: 0.12, 0.24, 0.18, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            MDCard:
                size_hint: None, None
                size: dp(34), dp(34)
                radius: [17, 17, 17, 17]
                md_bg_color: 0.22, 0.65, 0.35, 1
                elevation: 0
                pos_hint: {"center_y": 0.5}

                MDIcon:
                    icon: "shield-lock"
                    font_size: "20sp"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}

            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(2)
                pos_hint: {"center_y": 0.5}

                MDLabel:
                    id: banner_main_text
                    text: "Direct Ministry & Administration Line"
                    font_style: "Subtitle2"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1

                MDLabel:
                    id: banner_sub_text
                    text: "Authenticated Government Channel  •  End-to-End Encrypted"
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.70, 0.88, 0.75, 1

        # ── FILTER CHIPS ROW ─────────────────────────────────────────────
        ScrollView:
            size_hint_y: None
            height: dp(44)
            do_scroll_y: False
            bar_width: 0
            canvas.before:
                Color:
                    rgba: 0.98, 0.99, 0.98, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            MDBoxLayout:
                id: filter_chips_box
                orientation: "horizontal"
                spacing: dp(8)
                size_hint: None, None
                height: dp(44)
                width: self.minimum_width
                padding: dp(12), dp(6), dp(12), dp(6)

        # ── THREADS SCROLL LIST ──────────────────────────────────────────
        ScrollView:
            id: scroll_container

            MDBoxLayout:
                id: threads_box
                orientation: "vertical"
                padding: dp(14), dp(10), dp(14), dp(24)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
"""

Builder.load_string(KV)


class PolicyCommunicationScreen(Screen):
    """
    Dedicated screen for secure Policy Memos and Direct Admin-Policymaker Communications.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.user = None
        self.is_admin = False
        self.current_filter = "All"
        self.all_threads = []
        self.compose_dialog = None
        self.thread_dialog = None
        self.category_menu = None
        self.selected_category = "Policy Advisory"
        self.selected_priority = "Normal"

    def on_enter(self):
        from kivymd.app import MDApp
        self.app = MDApp.get_running_app()
        self.user = getattr(self.app, "current_user", None) or {}
        self.is_admin = (self.user.get("user_type") == "admin")

        if self.is_admin:
            self.ids.header_title.text = "Admin Desk"
            self.ids.header_subtitle.text = "POLICY REVIEWS & DISPATCHES"
            self.ids.banner_main_text.text = "National Policy Review Console"
            self.ids.banner_sub_text.text = "Direct Communications from District Policymakers"
            self.ids.compose_btn.text = "+ Memo"
        else:
            self.ids.header_title.text = "Policy Desk"
            self.ids.header_subtitle.text = "OFFICIAL ADMIN CHANNEL"
            self.ids.banner_main_text.text = "Direct Ministry & Administration Line"
            self.ids.banner_sub_text.text = "Authenticated Government Channel  •  End-to-End Encrypted"
            self.ids.compose_btn.text = "+ Memo"

        ensure_sample_communications_if_empty()
        self._build_filter_chips()
        self.load_communications()

    def go_back(self):
        self.manager.transition.direction = "right"
        if self.is_admin:
            self.manager.current = "admin_dashboard"
        else:
            self.manager.current = "dashboard"

    def _build_filter_chips(self):
        chips_box = self.ids.filter_chips_box
        chips_box.clear_widgets()

        filters = ["All", "Urgent", "Pending Review", "Action Taken"]
        for f in filters:
            active = (f == self.current_filter)
            btn = MDRaisedButton(
                text=f,
                size_hint=(None, None),
                height=dp(30),
                elevation=0,
                _radius=8,
                font_size="11sp",
                md_bg_color=(0.18, 0.45, 0.25, 1) if active else (0.90, 0.94, 0.90, 1),
                text_color=(1, 1, 1, 1) if active else (0.20, 0.35, 0.22, 1),
                on_release=lambda x, val=f: self.set_filter(val),
            )
            chips_box.add_widget(btn)

    def set_filter(self, filter_name):
        self.current_filter = filter_name
        self._build_filter_chips()
        self.render_threads()

    def load_communications(self):
        """Fetch communications from DB according to current role."""
        if self.is_admin:
            self.all_threads = get_admin_communications() or []
        else:
            user_id = self.user.get("user_id", 0)
            self.all_threads = get_policymaker_communications(user_id) or []
        self.render_threads()

    def render_threads(self):
        box = self.ids.threads_box
        box.clear_widgets()

        filtered = []
        for t in self.all_threads:
            if self.current_filter == "All":
                filtered.append(t)
            elif self.current_filter == "Urgent" and ("Urgent" in t.get("priority", "")):
                filtered.append(t)
            elif self.current_filter == "Pending Review" and ("Pending" in t.get("status", "")):
                filtered.append(t)
            elif self.current_filter == "Action Taken" and ("Action" in t.get("status", "") or "Resolved" in t.get("status", "")):
                filtered.append(t)

        if not filtered:
            empty_card = MDCard(
                orientation="vertical",
                size_hint_y=None, height=dp(130),
                radius=[12, 12, 12, 12],
                md_bg_color=(1, 1, 1, 1),
                elevation=1,
                padding=(dp(16), dp(16)),
                spacing=dp(6),
            )
            empty_card.add_widget(MDIcon(
                icon="shield-check", font_size="32sp",
                theme_text_color="Custom", text_color=(0.30, 0.65, 0.35, 1),
                halign="center",
            ))
            empty_card.add_widget(MDLabel(
                text="No dispatches found in this category",
                font_style="Subtitle2", bold=True, halign="center",
                theme_text_color="Custom", text_color=(0.20, 0.25, 0.30, 1),
            ))
            empty_card.add_widget(MDLabel(
                text="All policy directives and administrative inquiries are up to date.",
                font_style="Caption", halign="center",
                theme_text_color="Custom", text_color=(0.50, 0.55, 0.60, 1),
            ))
            box.add_widget(empty_card)
            return

        cards = []
        for thread in filtered:
            card = self._create_thread_card(thread)
            box.add_widget(card)
            cards.append(card)

        stagger_fade_in(cards, step=0.03, duration=0.22)

    def _create_thread_card(self, thread):
        """Constructs a spacious, well-organized executive card for a policy memo."""
        priority = thread.get("priority", "Normal")
        status = thread.get("status", "Pending Admin Review")
        is_urgent = ("Urgent" in priority)
        is_high = ("High" in priority)

        if is_urgent:
            prio_bg = (0.98, 0.90, 0.90, 1)
            prio_color = (0.85, 0.18, 0.18, 1)
            prio_text = "URGENT"
            prio_w = dp(58)
        elif is_high:
            prio_bg = (0.99, 0.94, 0.88, 1)
            prio_color = (0.85, 0.45, 0.10, 1)
            prio_text = "HIGH"
            prio_w = dp(46)
        else:
            prio_bg = (0.90, 0.95, 0.90, 1)
            prio_color = (0.15, 0.50, 0.22, 1)
            prio_text = "NORMAL"
            prio_w = dp(56)

        status_color = (0.15, 0.55, 0.25, 1) if "Action" in status else (0.75, 0.35, 0.10, 1)

        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(166),
            radius=[12, 12, 12, 12],
            md_bg_color=(1, 1, 1, 1),
            elevation=1,
            padding=(dp(14), dp(10), dp(14), dp(10)),
            spacing=dp(5),
            ripple_behavior=True,
            on_release=lambda *args, t=thread: self.open_thread_dialog(t),
        )

        # ── 1. TAGS ROW (Priority pill + Category pill + Date) ─────────
        top_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22), spacing=dp(6))

        prio_chip = MDCard(
            size_hint=(None, None), size=(prio_w, dp(20)),
            radius=[4, 4, 4, 4], md_bg_color=prio_bg, elevation=0, pos_hint={"center_y": 0.5},
        )
        prio_chip.add_widget(MDLabel(
            text=prio_text, font_style="Caption", bold=True, halign="center",
            theme_text_color="Custom", text_color=prio_color,
        ))
        top_row.add_widget(prio_chip)

        cat_chip = MDCard(
            size_hint=(None, None), size=(dp(105), dp(20)),
            radius=[4, 4, 4, 4], md_bg_color=(0.92, 0.94, 0.98, 1), elevation=0, pos_hint={"center_y": 0.5},
        )
        cat_chip.add_widget(MDLabel(
            text=thread.get("category", "Advisory"), font_style="Caption", bold=True, halign="center",
            theme_text_color="Custom", text_color=(0.20, 0.35, 0.65, 1),
        ))
        top_row.add_widget(cat_chip)

        raw_date = thread.get("created_at", "")
        # Compact cleanly: e.g. "Oct 19 • 5:08 AM"
        short_date = raw_date.replace(", 2026", "").replace(", 2025", "")
        top_row.add_widget(MDLabel(
            text=short_date,
            font_style="Caption", halign="right",
            theme_text_color="Custom", text_color=(0.48, 0.52, 0.58, 1),
            pos_hint={"center_y": 0.5},
        ))
        card.add_widget(top_row)

        # ── 2. SUBJECT ─────────────────────────────────────────────────
        subj_lbl = MDLabel(
            text=thread.get("subject", "No Subject"),
            font_style="Subtitle2", bold=True,
            theme_text_color="Custom", text_color=(0.10, 0.14, 0.20, 1),
            size_hint_y=None, height=dp(38),
            shorten=True, shorten_from="right",
        )
        card.add_widget(subj_lbl)

        # ── 3. SNIPPET ─────────────────────────────────────────────────
        msg_snip = thread.get("message", "")
        if len(msg_snip) > 115:
            msg_snip = msg_snip[:112] + "..."
        card.add_widget(MDLabel(
            text=msg_snip,
            font_style="Caption",
            theme_text_color="Custom", text_color=(0.38, 0.42, 0.48, 1),
            size_hint_y=None, height=dp(32),
            shorten=True,
        ))

        # ── 4. THIN DIVIDER ────────────────────────────────────────────
        divider = MDCard(
            size_hint_y=None, height=dp(1),
            md_bg_color=(0.93, 0.95, 0.93, 1),
            elevation=0,
        )
        card.add_widget(divider)

        # ── 5. FOOTER (Sender / District + Replies + Status) ───────────
        bot_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22), spacing=dp(6))

        sender_text = f"By: {thread.get('sender_name', 'Policymaker')} ({thread.get('sender_district', 'Kandy')})"
        bot_row.add_widget(MDLabel(
            text=sender_text, font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.30, 0.38, 0.48, 1),
            size_hint_x=0.55, shorten=True,
            pos_hint={"center_y": 0.5},
        ))

        reply_count = thread.get("reply_count", 0)
        if reply_count > 0:
            reply_chip = MDCard(
                size_hint=(None, None), size=(dp(54), dp(18)),
                radius=[4, 4, 4, 4], md_bg_color=(0.91, 0.96, 0.91, 1), elevation=0, pos_hint={"center_y": 0.5},
            )
            reply_chip.add_widget(MDLabel(
                text=f"{reply_count} Rep", font_style="Caption", bold=True, halign="center",
                theme_text_color="Custom", text_color=(0.15, 0.50, 0.20, 1),
            ))
            bot_row.add_widget(reply_chip)

        status_lbl = MDLabel(
            text=f"● {status}", font_style="Caption", bold=True, halign="right",
            theme_text_color="Custom", text_color=status_color,
            pos_hint={"center_y": 0.5},
        )
        bot_row.add_widget(status_lbl)
        card.add_widget(bot_row)

        return card

    # ══════════════════════════════════════════════════════════════════════
    # THREAD DETAIL & REPLY MODAL
    # ══════════════════════════════════════════════════════════════════════
    def open_thread_dialog(self, thread):
        """Displays full thread conversation between Policymaker and Admin with reply box."""
        comm_id = thread["comm_id"]
        mark_communication_read(comm_id, is_admin=self.is_admin)

        content = MDBoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        # Memo Subject Banner inside dialog content
        subj_lbl = MDLabel(
            text=thread.get("subject", "Policy Directive"),
            font_style="Subtitle2", bold=True,
            theme_text_color="Custom", text_color=(0.10, 0.15, 0.22, 1),
            size_hint_y=None,
        )
        subj_lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        subj_lbl.bind(texture_size=lambda inst, val: setattr(inst, "height", max(val[1], dp(22))))
        content.add_widget(subj_lbl)

        # Original Dispatch Card
        orig_card = MDBoxLayout(
            orientation="vertical", size_hint_y=None, adaptive_height=True,
            padding=(dp(12), dp(10)), spacing=dp(4),
        )
        from kivy.graphics import Color, RoundedRectangle
        with orig_card.canvas.before:
            Color(0.95, 0.98, 0.95, 1)
            orig_rect = RoundedRectangle(pos=orig_card.pos, size=orig_card.size, radius=[8, 8, 8, 8])
        def _upd_orig(inst, *_):
            orig_rect.pos = inst.pos
            orig_rect.size = inst.size
        orig_card.bind(pos=_upd_orig, size=_upd_orig)

        # Header: Sender & District
        orig_card.add_widget(MDLabel(
            text=f"Dispatch by {thread['sender_name']} ({thread['sender_district']})",
            font_style="Caption", bold=True,
            theme_text_color="Custom", text_color=(0.15, 0.45, 0.20, 1),
            size_hint_y=None, height=dp(18),
        ))
        # Header: Timestamp
        orig_card.add_widget(MDLabel(
            text=thread.get("created_at", ""),
            font_style="Caption",
            theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
            size_hint_y=None, height=dp(16),
        ))

        # Message body with dynamic height & text wrap
        orig_msg = MDLabel(
            text=thread.get("message", ""),
            font_style="Caption",
            theme_text_color="Custom", text_color=(0.15, 0.18, 0.22, 1),
            size_hint_y=None,
        )
        orig_msg.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        orig_msg.bind(texture_size=lambda inst, val: setattr(inst, "height", max(val[1], dp(20))))
        orig_card.add_widget(orig_msg)
        content.add_widget(orig_card)

        # Existing Replies
        replies = thread.get("replies", [])
        if replies:
            content.add_widget(MDLabel(
                text="Official Correspondence History:",
                font_style="Caption", bold=True,
                theme_text_color="Custom", text_color=(0.20, 0.30, 0.40, 1),
                size_hint_y=None, height=dp(20),
            ))
            for rep in replies:
                is_admin_reply = (rep.get("sender_role") == "admin")
                rep_card = MDBoxLayout(
                    orientation="vertical", size_hint_y=None, adaptive_height=True,
                    padding=(dp(10), dp(8)), spacing=dp(3),
                )
                with rep_card.canvas.before:
                    if is_admin_reply:
                        Color(0.92, 0.95, 1.0, 1)
                    else:
                        Color(0.95, 0.98, 0.95, 1)
                    r_rect = RoundedRectangle(pos=rep_card.pos, size=rep_card.size, radius=[8, 8, 8, 8])
                def _upd_r(inst, *_, rect=r_rect):
                    rect.pos = inst.pos
                    rect.size = inst.size
                rep_card.bind(pos=_upd_r, size=_upd_r)

                r_title = "🏛 Central Administration" if is_admin_reply else f"👤 {rep['sender_name']}"
                rep_card.add_widget(MDLabel(
                    text=r_title, font_style="Caption", bold=True,
                    theme_text_color="Custom",
                    text_color=(0.15, 0.35, 0.70, 1) if is_admin_reply else (0.15, 0.50, 0.20, 1),
                    size_hint_y=None, height=dp(18),
                ))
                rep_card.add_widget(MDLabel(
                    text=rep.get("created_at", ""),
                    font_style="Caption",
                    theme_text_color="Custom", text_color=(0.45, 0.50, 0.55, 1),
                    size_hint_y=None, height=dp(16),
                ))
                rep_msg = MDLabel(
                    text=rep.get("message", ""),
                    font_style="Caption",
                    theme_text_color="Custom", text_color=(0.15, 0.18, 0.22, 1),
                    size_hint_y=None,
                )
                rep_msg.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
                rep_msg.bind(texture_size=lambda inst, val: setattr(inst, "height", max(val[1], dp(20))))
                rep_card.add_widget(rep_msg)
                content.add_widget(rep_card)

        # Reply Input Field
        reply_field = MDTextField(
            hint_text="Write administrative response or note...",
            multiline=True,
            size_hint_y=None,
            height=dp(70),
            line_color_focus=(0.20, 0.55, 0.28, 1),
        )
        content.add_widget(reply_field)

        scroll_wrapper = MDScrollView(size_hint_y=None, height=dp(300))
        scroll_wrapper.add_widget(content)

        def do_reply(*args):
            text = reply_field.text.strip()
            if not text:
                show_snackbar("Please enter a response message.")
                return
            sender_id = self.user.get("user_id", 0)
            status_val = "Action Taken" if self.is_admin else "In Review"
            ok, _ = reply_official_communication(sender_id, comm_id, text, new_status=status_val)
            if ok:
                self.thread_dialog.dismiss()
                self.load_communications()
                show_snackbar("Official response recorded & dispatched!")
            else:
                show_snackbar("Failed to send response.")

        self.thread_dialog = MDDialog(
            title=f"Directive #{thread.get('comm_id', '')}",
            type="custom",
            content_cls=scroll_wrapper,
            size_hint=(0.92, None),
            buttons=[
                MDFlatButton(text="CLOSE", on_release=lambda x: self.thread_dialog.dismiss()),
                MDRaisedButton(
                    text="DISPATCH REPLY",
                    md_bg_color=(0.18, 0.48, 0.25, 1),
                    on_release=do_reply,
                ),
            ],
        )
        self.thread_dialog.open()

    # ══════════════════════════════════════════════════════════════════════
    # COMPOSE SECURE DISPATCH DIALOG
    # ══════════════════════════════════════════════════════════════════════
    def open_compose_dialog(self):
        """Allows policymaker or admin to compose a brand new official memo."""
        self.selected_category = "Policy Advisory"
        self.selected_priority = "Normal"

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(330),
            padding=[dp(4), dp(4), dp(4), dp(4)],
        )

        subj_input = MDTextField(
            hint_text="Memo Subject (e.g. Supply Shortage)",
            size_hint_y=None, height=dp(46),
            line_color_focus=(0.20, 0.55, 0.28, 1),
        )

        # Category Selector Button
        cat_btn = MDRaisedButton(
            text=f"Category: {self.selected_category}  ▾",
            size_hint_x=1,
            elevation=0,
            _radius=8,
            md_bg_color=(0.92, 0.95, 0.92, 1),
            text_color=(0.15, 0.40, 0.20, 1),
        )

        categories = [
            "Policy Advisory", "Price Stabilization",
            "Buffer Stock & Shortage", "Import/Export Policy",
            "Subsidy & Agrarian Support", "General Inquiry"
        ]

        def pick_category(c):
            self.selected_category = c
            cat_btn.text = f"Category: {c}  ▾"
            self.category_menu.dismiss()

        menu_items = [
            {"text": c, "viewclass": "OneLineListItem", "on_release": lambda cat=c: pick_category(cat)}
            for c in categories
        ]
        self.category_menu = MDDropdownMenu(caller=cat_btn, items=menu_items, width_mult=4)
        cat_btn.on_release = self.category_menu.open

        # Priority Selector Row with compact button texts to avoid overflow
        prio_row = MDBoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(34))
        prio_buttons = [
            ("Normal", "Normal"),
            ("High Priority", "High"),
            ("Urgent / Confidential", "Urgent")
        ]
        prio_widgets = {}

        def update_prio_ui():
            for full_val, btn in prio_widgets.items():
                if full_val == self.selected_priority:
                    btn.md_bg_color = (0.85, 0.20, 0.20, 1) if "Urgent" in full_val else (0.20, 0.55, 0.28, 1)
                    btn.text_color = (1, 1, 1, 1)
                else:
                    btn.md_bg_color = (0.92, 0.94, 0.92, 1)
                    btn.text_color = (0.25, 0.35, 0.25, 1)

        def pick_prio(val):
            self.selected_priority = val
            update_prio_ui()

        for full_val, short_label in prio_buttons:
            b = MDRaisedButton(
                text=short_label, size_hint_x=0.33, elevation=0, _radius=6, font_size="11sp",
                on_release=lambda x, v=full_val: pick_prio(v),
            )
            prio_widgets[full_val] = b
            prio_row.add_widget(b)
        update_prio_ui()

        # Multiline Message Text
        msg_input = MDTextField(
            hint_text="Details of directive or policy inquiry...",
            multiline=True,
            size_hint_y=None,
            height=dp(100),
            line_color_focus=(0.20, 0.55, 0.28, 1),
        )

        content.add_widget(subj_input)
        content.add_widget(cat_btn)
        content.add_widget(prio_row)
        content.add_widget(msg_input)

        def submit_dispatch(*args):
            subj = subj_input.text.strip()
            msg = msg_input.text.strip()
            if not subj:
                show_snackbar("Please enter a subject.")
                return
            if not msg:
                show_snackbar("Please enter memo details.")
                return

            sender_id = self.user.get("user_id", 0)
            ok, _ = send_official_communication(
                sender_id=sender_id,
                subject=subj,
                message=msg,
                category=self.selected_category,
                priority=self.selected_priority,
            )
            if ok:
                self.compose_dialog.dismiss()
                self.load_communications()
                show_snackbar("Secure policy memo dispatched successfully!")
            else:
                show_snackbar("Failed to submit memo. Check connection.")

        self.compose_dialog = MDDialog(
            title="Compose Official Policy Dispatch",
            type="custom",
            content_cls=content,
            size_hint=(0.92, None),
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.compose_dialog.dismiss()),
                MDRaisedButton(
                    text="DISPATCH MEMO",
                    md_bg_color=(0.18, 0.48, 0.25, 1),
                    on_release=submit_dispatch,
                ),
            ],
        )
        self.compose_dialog.open()

