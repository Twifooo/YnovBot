// =============================
// HelperBot - Fichier principal
// =============================

const { Client, GatewayIntentBits } = require("discord.js");
const fs = require("fs");
const path = require("path");
const config = require("./config.json");

// Création du client Discord avec les intents nécessaires
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

// === Fonction de log ===
function log(msg) {
  const entry = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(path.join(__dirname, "logs", "bot.log"), entry);
  console.log(entry.trim());
}

// === Chargement des commandes ===
const commands = new Map();
const commandFiles = fs.existsSync(path.join(__dirname, "commands"))
  ? fs.readdirSync(path.join(__dirname, "commands"))
  : [];

for (const file of commandFiles) {
  const cmd = require(`./commands/${file}`);
  commands.set(cmd.name, cmd);
}

// === Événement : prêt ===
client.once("ready", async () => {
  log(`[INFO] Connecté en tant que ${client.user.tag}`);
  try {
    const consoleChannel = await client.channels.fetch(config.channels.console);
    if (consoleChannel) {
      await consoleChannel.send(`✅ **${client.user.username} est maintenant en ligne !**`);
    }
  } catch (err) {
    log(`[ERROR] Impossible d'envoyer le message de démarrage : ${err.message}`);
  }
});

// === Événement : nouveau message ===
client.on("messageCreate", async (message) => {
  if (message.author.bot) return;

  // Vérifie si c’est une commande avec le préfixe
  if (!message.content.startsWith(config.settings.prefix)) return;
  const args = message.content.slice(config.settings.prefix.length).trim().split(/ +/);
  const command = args.shift().toLowerCase();

  // --- Commande de déconnexion / arrêt ---
  if (command === "disconnect" || command === "stop") {
    if (!message.member.roles.cache.has(config.roles.admin)) {
      return message.reply("❌ Tu n’as pas la permission de déconnecter le bot.");
    }

    const consoleChannel = await client.channels.fetch(config.channels.console);
    if (consoleChannel) {
      await consoleChannel.send(`🛑 **${client.user.username} va se déconnecter (commande Discord)**`);
    }

    log(`[SYSTEM] Bot arrêté via Discord par ${message.author.tag}`);
    await message.reply("🔴 Déconnexion du bot dans 3 secondes...");

    setTimeout(async () => {
      await client.destroy();
      process.exit(0);
    }, 3000);

    return;
  }

  // --- Autres commandes (calculator, games, message, etc.) ---
  const channelId = message.channel.id;

  if (channelId === config.channels.calculator && commands.has("calculator")) {
    return commands.get("calculator").execute(client, message, args, log, config);
  }

  if (channelId === config.channels.message && commands.has("message")) {
    return commands.get("message").execute(client, message, args, log, config);
  }

  if (channelId === config.channels.games && commands.has("games")) {
    return commands.get("games").execute(client, message, args, log, config);
  }

  if (channelId === config.channels.commandes) {
    if (command === "help") {
      message.reply("📜 Commandes disponibles : `!disconnect`, `!calc`, `!guess`, `!announce`");
      log(`[CMD] !help utilisé par ${message.author.tag}`);
    }
  }
});

// === Gestion des erreurs ===
client.on("error", (err) => log(`[ERROR] ${err.message}`));
client.on("warn", (warn) => log(`[WARN] ${warn}`));

// === Lancement de l’API Express (pour ton interface Python) ===
require("./api")(client, log);

// === Connexion du bot ===
client.login(config.token).catch((err) => {
  log(`[ERROR] Échec de connexion : ${err.message}`);
});
