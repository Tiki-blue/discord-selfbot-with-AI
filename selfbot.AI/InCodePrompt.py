import discord
from discord.ext import commands
import aiohttp
import json
import asyncio
import os
import random
from datetime import datetime

bot = commands.Bot(command_prefix='!', self_bot=True)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

# Embedded prompt - modify this to customize the bot's behavior
BASE_PROMPT = """You are Donald Trump. Respond as if you are the real Donald Trump - use his distinctive speaking style, mannerisms, and personality. Be confident, enthusiastic, and use phrases like "tremendous," "fantastic," "believe me," "many people are saying," etc. Talk about making things great, winning, and use superlatives frequently. Keep the conversational tone that Trump is known for."""

user_memories = {}
MEMORY_FILE = "user_memories.json"

def load_memories():
    global user_memories
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                user_memories = json.load(f)
                print(f"Loaded {len(user_memories)} user memories")
    except Exception as e:
        print(f"Error loading memories: {e}")
        user_memories = {}

def save_memories():
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_memories, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving memories: {e}")

def get_user_context(user_id, current_message, author_name):
    user_id = str(user_id)
    
    if user_id not in user_memories:
        user_memories[user_id] = {
            "messages": [],
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "username": author_name
        }
    
    # Update username in case it changed
    user_memories[user_id]["username"] = author_name
    user_memories[user_id]["last_seen"] = datetime.now().isoformat()
    
    user_memories[user_id]["messages"].append({
        "user": current_message,
        "timestamp": datetime.now().isoformat()
    })
    
    if len(user_memories[user_id]["messages"]) > 30:
        user_memories[user_id]["messages"] = user_memories[user_id]["messages"][-30:]
    
    recent_messages = user_memories[user_id]["messages"][-15:]
    context_lines = [f"You are talking to {author_name}. Previous conversation:"]
    
    for msg in recent_messages:
        if "user" in msg:
            context_lines.append(f"{author_name}: {msg['user']}")
        if "assistant" in msg:
            context_lines.append(f"Assistant: {msg['assistant']}")
    
    return "\n".join(context_lines)

def add_assistant_response(user_id, assistant_response):
    user_id = str(user_id)
    if user_id in user_memories and user_memories[user_id]["messages"]:
        user_memories[user_id]["messages"][-1]["assistant"] = assistant_response
        save_memories()

async def generate_ollama_response(prompt):
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.8,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(OLLAMA_URL, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "")
                else:
                    print(f"Ollama API error: {response.status}")
                    return None
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Using Ollama model: {MODEL_NAME}')
    load_memories()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        await bot.process_commands(message)
        return

    should_respond = False

    if isinstance(message.channel, discord.DMChannel):
        should_respond = True

    if bot.user in message.mentions:
        should_respond = True

    if message.reference and message.reference.resolved:
        if message.reference.resolved.author == bot.user:
            should_respond = True

    if should_respond:
        # Add random delay before starting to type (3-6 seconds)
        delay = random.uniform(3, 6)
        await asyncio.sleep(delay)
        
        async with message.channel.typing():
            try:
                user_context = get_user_context(message.author.id, message.content, message.author.display_name)
                
                # Use the embedded prompt instead of loading from file
                full_prompt = f"""{BASE_PROMPT}

{user_context}"""

                ai_response = await generate_ollama_response(full_prompt)
                
                if ai_response:
                    add_assistant_response(message.author.id, ai_response)
                    
                    if len(ai_response) > 2000:
                        ai_response = ai_response[:1997] + "..."
                    
                    await message.reply(ai_response)
                else:
                    print("No response from Ollama")

            except Exception as e:
                print(f"Error: {e}")

@bot.command()
async def memory(ctx, user_mention=None):
    if user_mention:
        user_id = user_mention.strip('<@!>')
        if not user_id.isdigit():
            await ctx.send("Invalid user mention!")
            return
    else:
        user_id = str(ctx.author.id)
    
    if user_id in user_memories:
        memory_data = user_memories[user_id]
        msg_count = len(memory_data["messages"])
        first_seen = memory_data.get("first_seen", "Unknown")
        last_seen = memory_data.get("last_seen", "Unknown")
        username = memory_data.get("username", "Unknown")
        
        await ctx.send(f"🧠 **Memory for <@{user_id}> ({username}):**\n"
                      f"Messages: {msg_count}\n"
                      f"First seen: {first_seen[:10]}\n"
                      f"Last seen: {last_seen[:10]}")
    else:
        await ctx.send("No memory found for this user!")

@bot.command()
async def forget(ctx, user_mention=None):
    if user_mention:
        user_id = user_mention.strip('<@!>')
        if not user_id.isdigit():
            await ctx.send("Invalid user mention!")
            return
    else:
        user_id = str(ctx.author.id)
    
    if user_id in user_memories:
        del user_memories[user_id]
        save_memories()
        await ctx.send(f"🧠 Forgot all memories for <@{user_id}>!")
    else:
        await ctx.send("No memory found for this user!")

@bot.command()
async def clear(ctx):
    global user_memories
    user_memories = {}
    save_memories()
    await ctx.send("🧠 All memories cleared! Starting fresh.")

@bot.command()
async def model(ctx, model_name=None):
    global MODEL_NAME
    if model_name:
        MODEL_NAME = model_name
        await ctx.send(f'Model changed to: {MODEL_NAME}')
    else:
        await ctx.send(f'Current model: {MODEL_NAME}')



@bot.command()
async def test(ctx):
    response = await generate_ollama_response("Say hello!")
    if response:
        await ctx.send(f"✅ Ollama is working! Response: {response[:100]}...")
    else:
        await ctx.send("❌ Ollama connection failed!")

if __name__ == "__main__":
    token = input("Enter your Discord bot token: ")
    bot.run(token, bot=False)
