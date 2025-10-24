import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QStackedWidget, QTextEdit, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont
import qdarkstyle
import subprocess

BOT_PATH = r"C:\Users\OUDOR\Desktop\Autre\Ynov\Bonne pratique Dev\bot\index.js"
LOG_PATH = r"C:\Users\OUDOR\Desktop\Autre\Ynov\Bonne pratique Dev\bot\logs\bot.log"

bot_process = None

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HelperBot Dashboard")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet(qdarkstyle.load_stylesheet())

        self.main_layout = QHBoxLayout(self)
        self.sidebar = self.create_sidebar()
        self.main_content = self.create_main_content()

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.main_content)
        self.setLayout(self.main_layout)

        self.show_animation()

    # === Animations d'apparition ===
    def show_animation(self):
        opacity = QGraphicsOpacityEffect()
        self.setGraphicsEffect(opacity)
        self.animation = QPropertyAnimation(opacity, b"opacity")
        self.animation.setDuration(1500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()

    # === Sidebar ===
    def create_sidebar(self):
        frame = QFrame()
        frame.setStyleSheet("background-color: #202225; border-right: 2px solid #2f3136;")
        layout = QVBoxLayout(frame)

        title = QLabel("⚙️ HelperBot")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 20px;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)

        buttons = [
            ("🏠 Dashboard", self.show_dashboard),
            ("📜 Logs", self.show_logs),
            ("⚙️ Paramètres", self.show_settings)
        ]

        for text, action in buttons:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2f3136;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 6px;
                    font-size: 15px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #40444b;
                }
            """)
            btn.clicked.connect(action)
            layout.addWidget(btn)

        layout.addStretch(1)
        return frame

    # === Contenu principal ===
    def create_main_content(self):
        stack = QStackedWidget()

        # Page Dashboard
        dash = QWidget()
        dash_layout = QVBoxLayout(dash)

        self.status_label = QLabel("🔴 Bot arrêté")
        self.status_label.setFont(QFont("Segoe UI", 14))
        dash_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()
        start_btn = QPushButton("▶️ Lancer le bot")
        stop_btn = QPushButton("🛑 Arrêter le bot")

        for btn, color in [(start_btn, "#43b581"), (stop_btn, "#f04747")]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border-radius: 8px;
                    padding: 12px;
                    min-width: 160px;
                }}
                QPushButton:hover {{
                    background-color: #5865f2;
                }}
            """)

        start_btn.clicked.connect(self.start_bot)
        stop_btn.clicked.connect(self.stop_bot)
        btn_layout.addWidget(start_btn)
        btn_layout.addWidget(stop_btn)
        dash_layout.addLayout(btn_layout)
        stack.addWidget(dash)

        # Page Logs
        logs = QWidget()
        logs_layout = QVBoxLayout(logs)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas", 10))
        logs_layout.addWidget(self.log_box)
        stack.addWidget(logs)

        # Page Paramètres
        settings = QWidget()
        settings_layout = QVBoxLayout(settings)
        settings_layout.addWidget(QLabel("⚙️ Paramètres à venir..."))
        stack.addWidget(settings)

        self.pages = {"dashboard": 0, "logs": 1, "settings": 2}
        self.stack = stack
        return stack

    # === Navigation entre pages ===
    def show_dashboard(self):
        self.stack.setCurrentIndex(self.pages["dashboard"])

    def show_logs(self):
        self.stack.setCurrentIndex(self.pages["logs"])

    def show_settings(self):
        self.stack.setCurrentIndex(self.pages["settings"])

    # === Gestion du bot ===
    def start_bot(self):
        global bot_process
        if bot_process is not None:
            self.status_label.setText("⚠️ Bot déjà lancé")
            return

        self.status_label.setText("🟢 Bot en cours de démarrage...")
        bot_process = subprocess.Popen(["node", BOT_PATH], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        QTimer.singleShot(2000, lambda: self.status_label.setText("🟢 Bot en ligne"))
        QTimer.singleShot(1000, self.update_logs)

    def stop_bot(self):
        global bot_process
        if bot_process is None:
            self.status_label.setText("⚠️ Aucun bot à arrêter.")
            return

        self.status_label.setText("🛑 Arrêt en cours...")
        try:
            os.system("curl -X POST http://localhost:3000/shutdown")
            time.sleep(3)
        except Exception as e:
            print(e)

        try:
            if bot_process.poll() is None:
                os.system(f"taskkill /PID {bot_process.pid} /F")
            bot_process = None
            self.status_label.setText("🔴 Bot arrêté")
        except Exception as e:
            self.status_label.setText(f"❌ Erreur : {e}")

    # === Lecture des logs ===
    def update_logs(self):
        if os.path.exists(LOG_PATH):
            try:
                with open(LOG_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.log_box.setPlainText(content)
            except:
                pass
        QTimer.singleShot(2000, self.update_logs)


# === Lancement de l'app ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec())
