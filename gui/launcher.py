import sys
import subprocess
import importlib.util
import time
import os
import urllib.request
import warnings

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QProgressBar, QMessageBox
)
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
import qdarkstyle


warnings.filterwarnings("ignore", category=UserWarning)

# === Portable paths ===
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))      # gui/
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))   # root project

BOT_DIR = os.path.join(ROOT_DIR, "bot")
DASHBOARD_PATH = os.path.join(CURRENT_DIR, "dashboard.py")
IMG_PATH = os.path.join(CURRENT_DIR, "assets", "images.png")


# === Python dependency check ===
def install_python_package(name):
    print(f"Installing {name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", name])


def ensure_python_dependencies():
    required = ["PyQt6", "qdarkstyle"]
    for pkg in required:
        if importlib.util.find_spec(pkg) is None:
            install_python_package(pkg)


ensure_python_dependencies()


# === Node.js & npm utils ===
def node_available():
    try:
        subprocess.check_output(["node", "-v"])
        return True
    except:
        return False


def find_npm():
    candidates = [
        r"C:\Program Files\nodejs\npm.cmd",
        r"C:\Program Files (x86)\nodejs\npm.cmd",
        os.path.expandvars(r"%AppData%\npm\npm.cmd")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


# === Thread worker ===
class InstallerWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def run(self):
        try:

            self.progress.emit(0, "Checking environment...")

            # Node.js
            if not node_available():
                self.progress.emit(5, "Node.js missing. Please install it manually.")
                time.sleep(1)
            else:
                self.progress.emit(15, "Node.js detected.")

            # npm
            npm = find_npm()
            if npm is None:
                raise Exception("npm not found. Check Node.js installation.")

            # Python modules
            self.progress.emit(30, "Checking Python modules...")
            ensure_python_dependencies()

            # Node modules
            steps = [
                ("Installing discord.js...", f'"{npm}" install discord.js --prefix "{BOT_DIR}"'),
                ("Installing express...", f'"{npm}" install express --prefix "{BOT_DIR}"'),
            ]

            p = 45
            for text, cmd in steps:
                self.progress.emit(p, text)
                subprocess.run(cmd, shell=True, check=True)
                p += 25
                time.sleep(0.4)

            self.progress.emit(100, "Installation complete.")
            time.sleep(0.5)
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


# === Launcher window ===
class Launcher(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YnovBot Launcher")
        self.resize(600, 400)

        bg = self.palette()
        bg.setColor(QPalette.Window, QColor("#d3d3d3"))
        self.setPalette(bg)

        layout = QVBoxLayout(self)

        # Logo
        if os.path.exists(IMG_PATH):
            img = QPixmap(IMG_PATH)
            logo = QLabel()
            logo.setPixmap(img.scaled(180, 180, Qt.KeepAspectRatio))
            logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo)
        else:
            lbl = QLabel("⚠ Image missing (gui/assets/images.png)")
            lbl.setStyleSheet("color:red;font-weight:bold;")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

        title = QLabel("YnovBot Launcher")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        btn = QPushButton("Start installation")
        btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        btn.setStyleSheet("""
            QPushButton {
                background:#5865F2;
                color:white;
                border-radius:8px;
                padding:10px;
            }
            QPushButton:hover { background:#4752C4; }
        """)

        btn.clicked.connect(self.start_installation)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

    def start_installation(self):
        # Basic folder checks
        required = [BOT_DIR, os.path.join(CURRENT_DIR, "assets")]
        missing = [d for d in required if not os.path.exists(d)]

        if missing:
            QMessageBox.critical(self, "Structure error",
                                 "Required folders missing:\n" + "\n".join(missing))
            return

        self.loader = LoaderWindow()
        self.loader.show()
        self.hide()  # Don't close: avoid thread crash


# === Loader window ===
class LoaderWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Installing dependencies...")
        self.resize(500, 220)

        layout = QVBoxLayout(self)

        self.label = QLabel("Preparing...")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Thread setup
        self.thread = QThread()
        self.worker = InstallerWorker()
        self.worker.moveToThread(self.thread)

        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.install_finished)
        self.worker.error.connect(self.install_failed)
        self.thread.started.connect(self.worker.run)

        self.thread.start()

    def update_status(self, value, text):
        self.progress.setValue(value)
        self.label.setText(text)

    def install_finished(self):
        self.label.setText("Launching dashboard...")
        QApplication.processEvents()
        time.sleep(0.4)

        try:
            subprocess.Popen([sys.executable, DASHBOARD_PATH])
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

        self.thread.quit()
        self.thread.wait()  # CRITICAL FIX
        self.close()

    def install_failed(self, msg):
        QMessageBox.critical(self, "Installation failed", msg)
        self.thread.quit()
        self.thread.wait()  # CRITICAL FIX
        self.close()


# === Entry point ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())

    window = Launcher()
    window.show()

    sys.exit(app.exec())
