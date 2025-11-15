import sys
import os
import subprocess
import requests

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QStackedWidget, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# --- Paths based on your project structure ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # gui/
BOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "bot"))
BOT_PATH = os.path.join(BOT_DIR, "index.js")
LOG_PATH = os.path.join(BOT_DIR, "logs", "bot.log")

bot_process = None


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YnovBot Dashboard")
        self.setGeometry(100, 100, 1000, 600)

        # Simple dark style (no qdarkstyle)
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: white; }
            QFrame { background-color: #202225; }
            QLabel { color: white; }
            QTextEdit { background-color: #1e1f22; color: white; border: none; }
            QPushButton {
                background-color: #5865F2;
                color: white;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #4752C4; }
        """)

        main_layout = QHBoxLayout(self)

        self.sidebar = self.build_sidebar()
        self.stack = self.build_pages()

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)

    # ----------------- Sidebar -----------------
    def build_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(220)
        layout = QVBoxLayout(frame)

        title = QLabel("⚙ YnovBot")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)

        buttons = [
            ("🏠 Dashboard", self.show_dashboard),
            ("📜 Logs", self.show_logs),
            ("💬 Messages", self.show_messages),
            ("🧮 Calculator", self.show_calculator),
            ("🎮 Games", self.show_games),
            ("🧾 Commands", self.show_commands),
            ("⚙ Settings", self.show_settings),
        ]

        for text, handler in buttons:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2f3136;
                    color: white;
                    border: none;
                    padding: 10px;
                    text-align: left;
                }
                QPushButton:hover { background-color: #40444b; }
            """)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        layout.addStretch()
        return frame

    # ----------------- Pages -----------------
    def build_pages(self) -> QStackedWidget:
        stack = QStackedWidget()

        # Dashboard page
        dash = QWidget()
        dash_layout = QVBoxLayout(dash)

        self.status_label = QLabel("🔴 YnovBot is stopped")
        self.status_label.setFont(QFont("Segoe UI", 14))
        dash_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        btn_row = QHBoxLayout()
        start_btn = QPushButton("▶ Start YnovBot")
        stop_btn = QPushButton("⛔ Stop YnovBot")

        for btn, color in [(start_btn, "#43b581"), (stop_btn, "#f04747")]:
            btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border-radius: 8px;
                    padding: 12px;
                }}
                QPushButton:hover {{ background-color: #5865F2; }}
            """)

        start_btn.clicked.connect(self.start_bot)
        stop_btn.clicked.connect(self.stop_bot)

        btn_row.addWidget(start_btn)
        btn_row.addWidget(stop_btn)
        dash_layout.addLayout(btn_row)

        stack.addWidget(dash)

        # Logs page
        logs_page = QWidget()
        logs_layout = QVBoxLayout(logs_page)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas", 10))
        logs_layout.addWidget(self.log_box)

        stack.addWidget(logs_page)

        # Messages page (real chat)
        messages_page = QWidget()
        messages_layout = QVBoxLayout(messages_page)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))

        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(50)

        send_button = QPushButton("Send")
        send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        send_button.setStyleSheet("background-color: #5865F2; padding: 8px;")
        send_button.clicked.connect(self.send_chat_message)

        messages_layout.addWidget(self.chat_display)
        messages_layout.addWidget(self.chat_input)
        messages_layout.addWidget(send_button)

        stack.addWidget(messages_page)

        # Placeholder pages
        def placeholder(text: str) -> QWidget:
            w = QWidget()
            l = QVBoxLayout(w)
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 14))
            l.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            return w

        stack.addWidget(placeholder("🧮 Calculator (coming soon...)"))
        stack.addWidget(placeholder("🎮 Games (coming soon...)"))
        stack.addWidget(placeholder("🧾 Command manager (coming soon...)"))
        stack.addWidget(placeholder("⚙ Settings (coming soon...)"))

        self.pages = {
            "dashboard": 0,
            "logs": 1,
            "messages": 2,
            "calculator": 3,
            "games": 4,
            "commands": 5,
            "settings": 6,
        }

        return stack

    # ----------------- Navigation -----------------
    def show_dashboard(self):
        self.stack.setCurrentIndex(self.pages["dashboard"])

    def show_logs(self):
        self.stack.setCurrentIndex(self.pages["logs"])
        self.update_logs()

    def show_messages(self):
        self.stack.setCurrentIndex(self.pages["messages"])
        self.update_chat_messages()

    def show_calculator(self):
        self.stack.setCurrentIndex(self.pages["calculator"])

    def show_games(self):
        self.stack.setCurrentIndex(self.pages["games"])

    def show_commands(self):
        self.stack.setCurrentIndex(self.pages["commands"])

    def show_settings(self):
        self.stack.setCurrentIndex(self.pages["settings"])

    # ----------------- Bot control -----------------
    def start_bot(self):
        global bot_process

        if bot_process is not None:
            self.status_label.setText("⚠ YnovBot is already running.")
            return

        if not os.path.exists(BOT_PATH):
            self.status_label.setText("❌ index.js not found.")
            return

        try:
            # Run node with cwd=BOT_DIR so relative paths work
            bot_process = subprocess.Popen(["node", BOT_PATH], cwd=BOT_DIR)
            self.status_label.setText("🟡 Starting YnovBot...")

            # Start monitoring the process
            QTimer.singleShot(500, self.monitor_bot_process)

            QTimer.singleShot(1500, lambda: self.status_label.setText("🟢 YnovBot is online"))
            QTimer.singleShot(1000, self.update_logs)
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")

    def stop_bot(self):
        global bot_process

        if bot_process is None:
            self.status_label.setText("⚠ No bot instance running.")
            return

        self.status_label.setText("🛑 Stopping YnovBot...")

        try:
            # Ask the bot (HTTP API) to shutdown
            os.system("curl -X POST http://localhost:3000/shutdown")
            # Give the bot time to cleanly shutdown, then force kill if needed
            QTimer.singleShot(3000, self._force_kill_if_needed)
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")

    def _force_kill_if_needed(self):
        global bot_process
        try:
            if bot_process is not None and bot_process.poll() is None:
                bot_process.terminate()
            bot_process = None
            self.status_label.setText("🔴 YnovBot stopped")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")

    def monitor_bot_process(self):
        """Detect when the bot process stops (even via !stop)."""
        global bot_process

        if bot_process is None:
            return

        # If poll() is not None, the process ended
        if bot_process.poll() is not None:
            bot_process = None
            self.status_label.setText("🔴 YnovBot stopped (detected automatically)")
            return

        # Otherwise, check again later
        QTimer.singleShot(500, self.monitor_bot_process)

    # ----------------- Logs -----------------
    def update_logs(self):
        if os.path.exists(LOG_PATH):
            try:
                with open(LOG_PATH, "r", encoding="utf-8") as f:
                    self.log_box.setPlainText(f.read())
            except:
                self.log_box.setPlainText("Error while reading log file.")
        else:
            self.log_box.setPlainText("No logs available.")

        QTimer.singleShot(2000, self.update_logs)

    # ----------------- Messages (Discord chat) -----------------
    def update_chat_messages(self):
        """Load messages from the bot HTTP API and display them."""
        try:
            response = requests.get("http://localhost:3000/messages")
            messages = response.json()

            text = ""
            for msg in messages:
                text += f"[{msg['author']}] {msg['content']}\n"

            self.chat_display.setPlainText(text)
        except:
            self.chat_display.setPlainText("Failed to load messages.")

        # Refresh every 2 seconds
        QTimer.singleShot(2000, self.update_chat_messages)

    def send_chat_message(self):
        """Send a message to the Discord 'message' channel using the bot."""
        text = self.chat_input.toPlainText().strip()
        if text == "":
            return

        try:
            requests.post("http://localhost:3000/messages/send", json={"text": text})
            self.chat_input.setPlainText("")
        except:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec())
True