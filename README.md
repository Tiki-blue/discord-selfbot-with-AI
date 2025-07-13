# Self botting with local AI

A Discord bot that responds with a **custom prompt** and maintains **user conversation history** using **Ollama** for AI-generated replies.

---

##  Features

The bot automatically responds when users:

- Mention it via `@botname`
- Reply to its messages
- Send it direct messages (DMs)

Remembers previous conversations for better context.  
Each user has their **own persistent conversation history**.

---

## 📜 Commands

| Command              | Description                                              |
|----------------------|----------------------------------------------------------|
| `!memory`            | View your conversation history with the bot              |
| `!memory @user`      | View another user's conversation stats                   |
| `!forget @user`      | Delete **another user's** history                        |
| `!clear`             | Clear **all** user histories from the system             |
| `!model`             | Show the current Ollama model                            |
| `!test`              | Test the connection with Ollama                          |

---

## 🛠️ Setup Requirements

- **Ollama** running locally at `http://localhost:11434` with the **mistral** model downloaded  
- `discord.py` version **1.7.3** (Newer versions **do not** support self bots)
- python 3.8
---

