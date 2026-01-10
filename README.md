💀 The Mortality Engine
"Data that isn't remembered deserves to die."

The Mortality Engine is an experimental decentralized archive that introduces biological decay to digital information. It is hosted entirely on GitHub Pages, with logic driven by GitHub Actions and the Avalanche Blockchain.

> ENTER THE ARCHIVE

📜 The Protocol
Most blockchains promise immutability (forever). We promise mortality.

Life: Users upload a memory (Text or Image URL) by sending 0.02 AVAX to the Treasury.

Decay: Every hour, an entropy script runs. It increases the "Chaos Level" of every item in the database.

Text begins to glitch, swap characters, and redact itself.

Images blur, lose color, and distort.

Death: If an item reaches 24 Hours of Entropy, it is permanently overwritten with [DATA_LOST_TO_ENTROPY].

Healing: Any user can save a memory by sending 0.01 AVAX. This resets the entropy to 0, restoring the file to perfect clarity.

🏗 Architecture (The "Zero-Cost" Stack)
This project runs without a backend server. It relies on a "Transaction-Driven GitOps" workflow.

Frontend: Static HTML/JS (Hosted on GitHub Pages).

Database: A simple db.json file committed to the repo.

The Engine: A Python script running on GitHub Actions (Cron Job).

It checks the Avalanche Ledger (Fuji Testnet) for incoming transactions.

It decodes the Hex Data input to find new posts or heal signals.

It updates db.json and commits the decay back to the repo.

The Blockchain: Avalanche Fuji Testnet (for signaling and value transfer).

🛠 Setup & Installation
If you want to fork this project or run your own instance:

1. Prerequisites
A GitHub Account.

An Avalanche Wallet (MetaMask/Core).

(Optional) An API Key for Snowtrace/Routescan if traffic is high.

2. Configuration
Fork this Repository.

Enable GitHub Actions in the "Settings" tab (Read/Write permissions required).

Enable GitHub Pages in "Settings > Pages" (Deploy from main branch).

Update scripts/engine.py with your own Treasury Wallet Address.

Update index.html with your Wallet Address (for the Frontend UI).

3. Usage
Posting: Connect wallet -> Type message -> Sign Transaction.

Syncing: The engine runs automatically at the top of every hour (XX:00). You can manually trigger it via the "Actions" tab for testing.

⚠️ System Notice
Network: Avalanche Fuji Testnet

Treasury Address: 0x43CAF8c948235Ed5e08608D5A7642910E3f82Fb9

Latency: This is a "Slow Web" app. Changes appear after the hourly Github Action cycle completes. Do not panic if your post does not appear instantly.

📄 License
This project is open-source under the MIT License. Concept & Architecture by [Your Name/Damian Griggs]
