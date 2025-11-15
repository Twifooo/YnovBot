// =============================
// YnovBot - Main file
// =============================

const { Client, GatewayIntentBits } = require("discord.js");
const fs = require("fs");
const path = require("path");
const express = require("express");
const bodyParser = require("body-parser");
const config = require("./config.json");

// Create Discord client
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

// -------------------------------------------
// Simple logger (file + console)
// -------------------------------------------
function log(text) {
  const line = `[${new Date().toISOString()}] ${text}\n`;
  const logPath = path.join(__dirname, "logs", "bot.log");
  fs.appendFileSync(logPath, line);
  console.log(line.trim());
}

// -------------------------------------------
// Ready event
// -------------------------------------------
client.once("ready", async () => {
  log(`[INFO] Logged in as ${client.user.tag}`);

  try {
    const consoleChannel = await client.channels.fetch(config.channels.console);
    await consoleChannel.send(`✅ **${client.user.username} is now online!**`);
  } catch {
    log("[WARN] Could not send startup message.");
  }

  console.log("Bot ready. API active.");
});

// -------------------------------------------
// PREFIX Commands (only in commands channel)
// -------------------------------------------
client.on("messageCreate", async (message) => {
  if (message.author.bot) return;

  const prefix = config.settings.prefix;
  if (!message.content.startsWith(prefix)) return;

  // Parse command
  const parts = message.content.slice(prefix.length).trim().split(/ +/);
  const command = parts.shift().toLowerCase();

  // Global rule → all prefix commands only in "commands" channel
  if (message.channel.id !== config.channels.commands) {
    return message.reply("❌ Commands are only allowed in the commands channel.");
  }

// ---------------------------------------
// STOP COMMAND (admin only)
// ---------------------------------------
if (command === "stop" || command === "disconnect") {

  // Commands allowed only in commands channel
  if (message.channel.id !== config.channels.commands) {
    return message.reply("❌ You can only use this command in the commands channel.");
  }

  // Must be admin
  if (!message.member.roles.cache.has(config.roles.admin)) {
    return message.reply("❌ You do not have permission to stop the bot.");
  }

  // Send shutdown info to console channel
  try {
    const consoleChannel = await client.channels.fetch(config.channels.console);
    if (consoleChannel) {
      await consoleChannel.send(
        `🛑 **${client.user.username} is shutting down (requested by ${message.author.tag})**`
      );
    }
  } catch (err) {
    log("[WARN] Could not send shutdown message to console channel.");
  }

  // Reply in commands channel
  await message.reply("🔴 Bot shutting down in 3 seconds...");

  log(`[SYSTEM] Bot stopped by ${message.author.tag}`);

  setTimeout(() => {
    client.destroy();
    process.exit(0);
  }, 3000);

  return;
}

  // ---------------------------------------
  // !help
  // ---------------------------------------
  if (command === "help") {
    return message.reply(
      "📌 **Available commands:**\n" +
      "`!help` - Show this help\n" +
      "`!stop` - Stop the bot (admin only)\n"
    );
  }

});

// -------------------------------------------
// ERROR HANDLERS
// -------------------------------------------
client.on("error", (err) => log(`[ERROR] ${err.message}`));
client.on("warn", (warn) => log(`[WARN] ${warn}`));

// -------------------------------------------
// SIMPLE API FOR DASHBOARD (messages + shutdown)
// -------------------------------------------
const app = express();
app.use(bodyParser.json());

// Return messages from "message" channel
app.get("/messages", async (req, res) => {
  try {
    const channel = await client.channels.fetch(config.channels.message);
    const msgs = await channel.messages.fetch({ limit: 25 });

    const data = msgs.reverse().map(msg => ({
      author: msg.author.username,
      content: msg.content
    }));

    res.json(data);
  } catch {
    res.status(500).json({ error: "Could not load messages." });
  }
});

// Send message to "message" channel
app.post("/messages/send", async (req, res) => {
  const text = req.body.text;

  if (!text || text.trim() === "") {
    return res.status(400).json({ error: "Message is empty." });
  }

  try {
    const channel = await client.channels.fetch(config.channels.message);
    await channel.send(text);
    res.json({ status: "sent" });
  } catch {
    res.status(500).json({ error: "Could not send message." });
  }
});

// Shutdown API (used by dashboard)
app.post("/shutdown", (req, res) => {
  res.json({ status: "ok" });

  setTimeout(() => {
    client.destroy();
    process.exit(0);
  }, 1000);
});

// Start HTTP server
app.listen(3000, () => console.log("API running on port 3000"));

// Login bot
client.login(config.token).catch(err => {
  log(`[ERROR] Login failed: ${err.message}`);
});
