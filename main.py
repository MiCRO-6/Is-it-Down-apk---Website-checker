from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import mainthread
from kivy.graphics import Color, RoundedRectangle
import threading
import requests
import random
import socket
import dns.resolver
import re
from requests.exceptions import SSLError
import time
from kivy.core.clipboard import Clipboard

# User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1"
]

DELAY = 2
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=3)
session.mount("https://", adapter)

# Helper functions
def get_a_record(domain):
    try:
        return socket.gethostbyname(domain)
    except:
        return "N/A"

def get_nameservers(domain):
    try:
        answers = dns.resolver.resolve(domain, "NS")
        return ", ".join(sorted([ns.to_text() for ns in answers]))
    except:
        return "N/A"

def get_wp_theme(url):
    if not url.startswith("http"):
        url = "https://" + url
    try:
        response = session.get(url, timeout=10, headers={"User-Agent": random.choice(USER_AGENTS)})
        match = re.search(r'/wp-content/themes/([^/]+)/', response.text)
        if match:
            theme_name = match.group(1)
            theme_url = f"{url}/wp-content/themes/{theme_name}/style.css"
            theme_response = session.get(theme_url, timeout=10, headers={"User-Agent": random.choice(USER_AGENTS)})
            if theme_response.status_code == 200:
                info_match = re.search(r'Theme Name:\s*(.+)', theme_response.text)
                if info_match:
                    theme_name = info_match.group(1).strip()
            return theme_name
        return "No WP Theme"
    except:
        return "Error Detecting"

# Domain result card with small centered rounded SHARE button
class DomainCard(BoxLayout):
    def __init__(self, domain, status_code, a_record, ns, wp_theme, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=5, size_hint_y=None, **kwargs)

        # Background color based on status
        if status_code.startswith("2"):
            color = (0.6, 1, 0.6, 1)
        elif status_code.startswith("4") or status_code.startswith("5"):
            color = (1, 0.6, 0.6, 1)
        else:
            color = (1, 1, 0.6, 1)

        with self.canvas.before:
            Color(*color)
            self.rect = RoundedRectangle(radius=[10])
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Helper to create center-aligned, wrapped labels
        def create_label(text):
            lbl = Label(
                text=text,
                markup=True,
                color=(0, 0, 0, 1),
                size_hint_y=None,
                height=20,
                text_size=(self.width - 20, None),
                halign='center',
                valign='middle'
            )
            lbl.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
            lbl.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
            return lbl

        # Add labels
        self.add_widget(create_label(f"[b]{domain}[/b]"))
        self.add_widget(create_label(f"Status = {status_code}"))
        self.add_widget(create_label(f"A = {a_record}"))
        self.add_widget(create_label(f"NS = {ns}"))
        self.add_widget(create_label(f"WP THEME = {wp_theme}"))

        # Small centered SHARE button with border radius
        self.share_btn = Button(
            text="SHARE",
            size_hint=(None, None),
            size=(100, 35),
            pos_hint={'center_x': 0.5},
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            background_normal=''  # remove default image
        )

        # Rounded rectangle behind button text
        with self.share_btn.canvas.before:
            Color(0.2, 0.6, 1, 1)
            self.share_btn.rect = RoundedRectangle(
                pos=self.share_btn.pos,
                size=self.share_btn.size,
                radius=[10]
            )

        # Update rectangle position/size dynamically
        self.share_btn.bind(pos=lambda instance, value: setattr(instance.rect, 'pos', value))
        self.share_btn.bind(size=lambda instance, value: setattr(instance.rect, 'size', value))

        self.share_btn.bind(on_press=lambda x: self.copy_to_clipboard(
            f"{domain}\nStatus: {status_code}\nA: {a_record}\nNS: {ns}\nWP THEME: {wp_theme}"
        ))

        self.add_widget(self.share_btn)

        # Adjust card height dynamically
        self.height = sum(child.height for child in self.children) + self.padding[1]*2 + self.spacing*5

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def copy_to_clipboard(self, text):
        Clipboard.copy(text)
        self.show_toast("Copied!")

    def show_toast(self, message):
        from kivy.uix.label import Label
        from kivy.clock import Clock
        from kivy.graphics import Color, RoundedRectangle
        from kivy.app import App

        toast = Label(
            text=message,
            size_hint=(None, None),
            size=(200, 40),
            pos=(self.x + (self.width - 200) / 2, self.top + 10),
            color=(1, 1, 1, 1),
            bold=True,
            halign='center',
            valign='middle'
        )

        # Background rectangle
        with toast.canvas.before:
            Color(0, 0, 0, 0.7)
            toast.rect = RoundedRectangle(pos=toast.pos, size=toast.size, radius=[10])
        toast.bind(pos=lambda instance, val: setattr(toast.rect, 'pos', val))
        toast.bind(size=lambda instance, val: setattr(toast.rect, 'size', val))

        App.get_running_app().root.add_widget(toast)
        Clock.schedule_once(lambda dt: App.get_running_app().root.remove_widget(toast), 1.5)

# Main app
class CheckerApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Big title banner
        banner_text = "[color=ff0000][b]IS IT DOWN?[/b][/color]\nv5.1"
        banner_label = Label(
            text=banner_text,
            markup=True,
            font_size=32,
            size_hint_y=None,
            height=100,
            halign='center',
            valign='middle'
        )
        banner_label.bind(
            texture_size=lambda lbl, val: setattr(lbl, 'height', val[1] + 20),
            size=lambda lbl, val: setattr(lbl, 'text_size', (val[0], None))
        )
        layout.add_widget(banner_label)

        # Multiline input
        self.input = TextInput(
            hint_text="Enter domains separated by commas",
            size_hint_y=None,
            height=100,
            multiline=True,
            padding=(10, 10),
            scroll_y=1
        )

        MIN_INPUT_HEIGHT = 100
        MAX_INPUT_HEIGHT = 200
        def adjust_input_height(instance, value):
            lines = value.count("\n") + 1
            instance.height = max(MIN_INPUT_HEIGHT, min(lines * 25, MAX_INPUT_HEIGHT))
        self.input.bind(text=adjust_input_height)

        self.submit_btn = Button(
            text="Submit",
            size_hint_y=None,
            height=50,
            on_press=self.start_scan
        )

        # Scrollable results
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll = ScrollView()
        self.scroll.add_widget(self.grid)

        layout.add_widget(self.input)
        layout.add_widget(self.submit_btn)
        layout.add_widget(self.scroll)

        return layout

    @mainthread
    def add_card(self, domain, status_code, a_record, ns, wp_theme):
        card = DomainCard(domain, status_code, a_record, ns, wp_theme)
        self.grid.add_widget(card)

    def start_scan(self, instance):
        self.grid.clear_widgets()
        domains = [d.strip() for d in self.input.text.replace("\n", ",").split(",") if d.strip()]
        threading.Thread(target=self.scan_domains, args=(domains,), daemon=True).start()

    def scan_domains(self, domains):
        for url in domains:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            domain = url.replace("https://", "").replace("http://", "").split("/")[0]
            a_record = get_a_record(domain)
            ns = get_nameservers(domain)
            wp_theme = get_wp_theme(url)

            status_code = "Unknown"
            try:
                resp = session.get(url, headers=headers, timeout=10)
                status_code = str(resp.status_code)
            except SSLError:
                status_code = "SSL Error"
            except requests.ConnectionError:
                status_code = "Down / Unreachable"
            except requests.Timeout:
                status_code = "Timeout"
            except:
                status_code = "Request Error"

            self.add_card(domain, status_code, a_record, ns, wp_theme)
            time.sleep(DELAY)

if __name__ == "__main__":
    CheckerApp().run()
