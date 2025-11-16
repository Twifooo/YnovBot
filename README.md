# YnovBot

YnovBot is a hybrid **Python + Node.js** application designed to manage a Discord bot through a **PyQt6 graphical interface**.<br>
The project includes :<br>
- A bot developed in JavaScript (Node.js)<br>
- A graphical interface in Python (PyQt) to launch, configure, and monitor the bot<br>
- An automated Node.js installation system<br>
- A modern dark-themed dashboard<br>

# Project structure
YnovBot/<br>
│<br>
├── bot/ # Node.js bot<br>
│ ├── api.js<br>
│ ├── index.js<br>
│ ├── package.json<br>
│ └── package-lock.json<br>
│<br>
├── gui/ # Python GUI (PyQt)<br>
│ ├── assets/<br>
│ ├── build/<br>
│ ├── dist/<br>
│ │ ├── dashboard.py<br>
│ │ ├── launcher.py<br>
│ │ ├── launcher.spec<br>
│ │ ├── node_installer.msi<br>
│ │ └── requirements.txt<br>
│ │<br>
│ └── launcher.py # Main Python launcher<br>
│<br>
├── .gitignore<br>
├── README.md<br>

# Logs
- Bot start/stop event and which user triggered it (from server or GUI).<br>
- Error messages.<br>
- Commands and the users who executed them.<br>
All logs are stored in the file bot.log<br>

# Message
In the message tab, you can read and send messages.<br>

# TO SEE COMMANDS : !help

# To DO :
- Calculator.<br>
- Games.<br>
- Command manager.<br>
- Settings.<br>

# Installation prerequisites :
- Clone the project : git clone https://github.com/Twifooo/YnovBot.git<br>
- Install Node.js<br>
- npm install discord.js express<br>
- Install Python 3.7<br>
- pip install PyQt6 qdarkstyle<br>

# Run the program
- open interface in C:\Users\...\YnovBot\gui
- in the interface enter : python launcher.py<br>

# Additional information
The Discord token cannot be included on GitHub for security reasons.<br>
The token and the Discord link are provided in the file submitted on Moodle.<br>

# Naming
- Variables : explicit names.<br>
- Functions : verb-based.<br>
- Classes : PascalCase.<br>
- Constants : UPPER_SNAKE_CASE.<br>
- Files & folders : consistent style (e.g. user_profile/).<br>
- Units : include the unit (timeoutMs, priceEUR).<br>
- Plurals : be careful with singular/plural (users, userId).<br>

# Formatting and lint
- PyLint<br>

