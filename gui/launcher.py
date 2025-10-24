import sys
import subprocess
import importlib.util
import time
import os
import threading
import urllib.request
import warnings
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QProgressBar, QMessageBox
)
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
import qdarkstyle

warnings.filterwarnings("ignore", category=UserWarning)

# === Correction de PATH pour NodeJS ===
NODE_PATHS = [
    r"C:\Program Files\nodejs",
    r"C:\Program Files (x86)\nodejs",
    os.path.expandvars(r"%AppData%\npm")
]
for path in NODE_PATHS:
    if os.path.exists(path):
        os.environ["PATH"] += os.pathsep + path

# === Vérification et installation automatique des dépendances Python ===
def install_package(pkg_name):
    print(f"🔧 Installation de {pkg_name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name, "--quiet"])

def ensure_dependencies():
    required = ["PyQt6", "qdarkstyle"]
    for pkg in required:
        if importlib.util.find_spec(pkg) is None:
            install_package(pkg)

ensure_dependencies()

# === Définition des chemins de base ===
BASE_DIR = os.path.dirname(__file__)
BOT_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "bot", "index.js"))
BOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "bot"))
IMG_PATH = os.path.abspath(os.path.join(BASE_DIR, "assets", "images.png"))
DASHBOARD_PATH = os.path.abspath(os.path.join(BASE_DIR, "dashboard.py"))

# === Fonctions utilitaires ===
def run_pip_install(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_node_installed():
    try:
        subprocess.check_output(["node", "-v"])
        return True
    except Exception:
        return False

def check_npm_path():
    candidates = [
        r"C:\Program Files\nodejs\npm.cmd",
        r"C:\Program Files\nodejs\npm",
        r"C:\Program Files (x86)\nodejs\npm.cmd",
        r"C:\Program Files (x86)\nodejs\npm",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def install_nodejs_silent(label_widget):
    if check_node_installed():
        label_widget.setText("✅ Node.js déjà installé, passage à l'étape suivante...")
        time.sleep(1)
        return

    try:
        node_installer = os.path.join(BASE_DIR, "node_installer.msi")
        node_url = "https://nodejs.org/dist/v22.11.0/node-v22.11.0-x64.msi"

        label_widget.setText("📦 Téléchargement de Node.js...")
        urllib.request.urlretrieve(node_url, node_installer)

        label_widget.setText("⚙️ Installation de Node.js (1 à 2 min)...")
        result = subprocess.run(
            ["msiexec", "/i", node_installer, "/quiet", "/norestart"],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            label_widget.setText("⚠️ Node.js semble déjà installé. Étape ignorée.")
            time.sleep(1)
            return

        os.remove(node_installer)
        label_widget.setText("✅ Node.js installé avec succès !")
        time.sleep(1)

    except Exception as e:
        label_widget.setText("⚠️ Impossible de vérifier Node.js, poursuite de l'installation...")
        print(f"[WARN] {e}")
        time.sleep(1)

def check_directories():
    missing = []
    required_dirs = [
        BOT_DIR,
        os.path.join(BASE_DIR, "assets")
    ]
    for d in required_dirs:
        if not os.path.exists(d):
            missing.append(d)
    return missing


# === Thread de travail ===
class InstallerWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def run(self):
        try:
            self.progress.emit(0, "Initialisation...")
            if not check_node_installed():
                self.progress.emit(0, "Installation de Node.js...")
                install_nodejs_silent(self)
            else:
                self.progress.emit(10, "✅ Node.js déjà présent")

            npm_path = check_npm_path()
            if not npm_path:
                raise Exception("❌ npm introuvable. Vérifie ton installation de Node.js.")

            steps = [
                ("Vérification de PyQt6", lambda: run_pip_install("PyQt6")),
                ("Vérification de qdarkstyle", lambda: run_pip_install("qdarkstyle")),
                ("Installation de discord.js", lambda: subprocess.run(
                    f'"{npm_path}" install discord.js --prefix "{BOT_DIR}"',
                    shell=True, check=True
                )),
                ("Installation de express", lambda: subprocess.run(
                    f'"{npm_path}" install express --prefix "{BOT_DIR}"',
                    shell=True, check=True
                )),
            ]

            for i, (text, func) in enumerate(steps, 1):
                self.progress.emit(int(i * 20), text)
                func()
                time.sleep(0.3)

            self.progress.emit(100, "✅ Installation terminée !")
            time.sleep(0.5)
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


# === Fenêtre principale ===
class MenuWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YnovBot - Launcher")
        self.resize(600, 400)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#d3d3d3"))
        self.setPalette(pal)

        layout = QVBoxLayout()

        if os.path.exists(IMG_PATH):
            pix = QPixmap(IMG_PATH)
            logo = QLabel()
            logo.setPixmap(pix.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo)
        else:
            lbl = QLabel("⚠️ Logo non trouvé : /gui/assets/images.png")
            lbl.setStyleSheet("color:red;font-weight:bold;")
            layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("YnovBot Launcher")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        self.start_btn = QPushButton("🚀 Lancer l'installation")
        self.start_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.start_btn.setStyleSheet(
            "QPushButton {background:#5865F2;color:white;border-radius:8px;padding:10px;} "
            "QPushButton:hover{background:#4752C4;}"
        )
        self.start_btn.clicked.connect(self.launch_loader)
        layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def launch_loader(self):
        missing = check_directories()
        if missing:
            msg = "Certains dossiers sont manquants :\n" + "\n".join(missing)
            QMessageBox.critical(self, "Erreur de structure", msg)
            return

        self.loader = LoaderWindow()
        self.loader.show()
        self.close()


# === Fenêtre de chargement ===
class LoaderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Installation des dépendances")
        self.resize(500, 200)

        layout = QVBoxLayout()
        self.label = QLabel("Préparation du système...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.setLayout(layout)
        self.thread = QThread()
        self.worker = InstallerWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.installation_finished)
        self.worker.error.connect(self.installation_failed)

        self.thread.start()

    def update_progress(self, value, text):
        self.progress.setValue(value)
        self.label.setText(text)

    def installation_finished(self):
        self.label.setText("Démarrage du tableau de bord...")
        self.progress.setValue(100)
        QApplication.processEvents()
        time.sleep(0.5)

        try:
            subprocess.Popen([sys.executable, DASHBOARD_PATH])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lancer le dashboard : {e}")

        self.thread.quit()
        self.thread.wait()
        self.close()
        self.deleteLater()

    def installation_failed(self, message):
        QMessageBox.critical(self, "Erreur critique", message)
        self.thread.quit()
        self.thread.wait()
        self.close()


# === Lancement principal ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    win = MenuWindow()
    win.show()
    sys.exit(app.exec())
