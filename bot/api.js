const express = require("express");
const config = require("./config.json");

module.exports = (client, log) => {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Endpoint pour arrêter le bot depuis le GUI
  app.post("/shutdown", async (req, res) => {
    try {
      const consoleChannel = await client.channels.fetch(config.channels.console);
      if (consoleChannel) {
        await consoleChannel.send("🛑 **Le bot va se déconnecter (commande envoyée depuis l’interface).**");
      }

      log(`[API] Arrêt demandé depuis le GUI.`);
      await client.destroy();
      res.json({ success: true, message: "Bot arrêté proprement." });
      process.exit(0);
    } catch (err) {
      log(`[API ERROR] ${err.message}`);
      res.status(500).json({ error: err.message });
    }
  });

  app.listen(PORT, () => log(`[API] Serveur REST en écoute sur le port ${PORT}`));
};
