import sys
import subprocess
import importlib.util
import time
import os
import threading
import urllib.request
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QProgressBar, QMessageBox
)
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import qdarkstyle


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

def check_npm_installed():
    try:
        subprocess.check_output(["npm", "-v"])
        return True
    except Exception:
        return False


# === Installation automatique de Node.js si manquant ===
def install_nodejs_silent(label_widget):
    try:
        # --- Vérifie si Node existe déjà ---
        if check_node_installed() and check_npm_installed():
            label_widget.setText("✅ Node.js déjà installé, passage à l'étape suivante...")
            time.sleep(1)
            return

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
            raise Exception(
                f"Le programme d'installation Node.js a renvoyé le code {result.returncode}. "
                "Node est peut-être déjà installé ou une version incompatible est présente. "
                "Désinstalle Node.js manuellement puis relance le launcher."
            )

        os.remove(node_installer)
        label_widget.setText("✅ Node.js installé avec succès !")
        time.sleep(1)

    except Exception as e:
        raise Exception(f"Échec de l'installation automatique de Node.js : {e}")


# === Vérification structure ===
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


# === Fenêtre principale ===
class MenuWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HelperBot - Lanceur")
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

        title = QLabel("HelperBot Launcher")
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
    # Signaux pour interagir avec l'UI depuis le thread d'installation
    show_info_signal = pyqtSignal(str, str, str)   # (titre, message, mode)
    show_error_signal = pyqtSignal(str, str)

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
        self.percent = 0
        self.error_happened = False

        # Connecte les signaux
        self.show_info_signal.connect(self._show_info)
        self.show_error_signal.connect(self._show_error)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(60)

        # Lancement de l'installation dans un thread séparé
        threading.Thread(target=self.install_dependencies, daemon=True).start()

    # --- Affichage thread-safe ---
    def _show_info(self, title, message, mode):
        if mode == "info":
            QMessageBox.information(self, title, message)
        elif mode == "warning":
            QMessageBox.warning(self, title, message)
        elif mode == "critical":
            QMessageBox.critical(self, title, message)

    def _show_error(self, title, message):
        QMessageBox.critical(self, title, message)

    # --- Processus principal d'installation ---
    def install_dependencies(self):
        try:
            print("=== DEBUG: Début installation ===")

            # Vérifie si Node est présent
            node_ok = check_node_installed()
            npm_ok = check_npm_installed()

            if not node_ok or not npm_ok:
                self.show_info_signal.emit("Installation automatique",
                    "Node.js n'est pas détecté.\nIl va être téléchargé et installé automatiquement.\nMerci de lancer le launcher en administrateur.",
                    "info")
                install_nodejs_silent(self.label)
            else:
                self.label.setText("✅ Node.js détecté, passage à l'étape suivante...")

            steps = [
                ("Vérification de PyQt6", lambda: run_pip_install("PyQt6")),
                ("Vérification de qdarkstyle", lambda: run_pip_install("qdarkstyle")),
                ("Installation de discord.js", lambda: subprocess.check_call(
                    ["npm", "install", "discord.js", "--prefix", BOT_DIR])),
                ("Installation de express", lambda: subprocess.check_call(
                    ["npm", "install", "express", "--prefix", BOT_DIR])),
            ]

            for i, (text, func) in enumerate(steps, 1):
                print(f"➡️ Étape {i}/{len(steps)} : {text}")
                self.label.setText(text)
                func()
                time.sleep(0.3)
                self.percent = int((i / len(steps)) * 100)
                print(f"✅ Terminé : {text}")

            self.percent = 100
            time.sleep(0.5)
            self.open_dashboard()

        except Exception as e:
            print(f"❌ Erreur attrapée : {e}")
            self.error_happened = True
            self.label.setText("❌ Erreur pendant l'installation")
            self.show_error_signal.emit("Erreur critique", str(e))

    def update_progress(self):
        if not self.error_happened:
            if self.percent < 100:
                self.percent = min(100, self.percent + 1)
                self.progress.setValue(self.percent)
            else:
                self.timer.stop()
        else:
            self.timer.stop()

    def _show_error(self, title, message):
        QMessageBox.critical(self, title, message)

    def open_dashboard(self):
        self.label.setText("Démarrage du tableau de bord...")
        try:
            subprocess.Popen([sys.executable, DASHBOARD_PATH])
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
        self.close()


# === Lancement principal ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    win = MenuWindow()
    win.show()
    sys.exit(app.exec())
