import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from typing import Optional, List
import aiohttp
import re

# --- New Imports for API Server ---
from fastapi import FastAPI, HTTPException
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel
import uvicorn

# --- Initial Setup ---
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1411265287491158018 # 테스트 서버 ID
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

intents = discord.Intents.default()
intents.message_content = True

# --- FastAPI Setup ---
app = FastAPI(
    title="title",
    summary="summary",
    description="description",
    version="0.1.0",
)
mcp = FastApiMCP(
    app,
    name="name",
    description="description",
)
mcp.mount_http()

# --- Bot Client Definition ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # cogs 폴더에서 .py로 끝나는 모든 파일을 찾아 코그로 로드
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        # 특정 서버에만 커맨드를 즉시 동기화 (개발용)
        my_guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=my_guild)
        await self.tree.sync(guild=my_guild)

    async def on_ready(self):
        print(f'{self.user} (으)로 로그인했습니다.')

    async def on_message(self, message):
        if message.author == self.user:
            return

        should_send = False
        message_type = None

        # 1. DM 채널인지 가장 먼저 확인
        if isinstance(message.channel, discord.DMChannel):
            should_send = True
            message_type = "DM"
        # 2. 그 다음에 서버 채널에서의 멘션 또는 스레드인지 확인
        elif self.user.mentioned_in(message):
            should_send = True
            message_type = "MENTION"
        # elif isinstance(message.channel, discord.Thread):
        #     should_send = True
        #     message_type = "THREAD_MESSAGE"

        if should_send:
            history = []
            async for prev_message in message.channel.history(limit=20):
                role = "assistant" if prev_message.author == self.user else "user"
                speaker_name = prev_message.author.display_name.replace('"', "'")
                history.append({
                    "role": role,
                    "name": speaker_name,
                    "content": prev_message.content
                })
            history.reverse()

            payload = {
                "userId": str(message.author.id),
                "userName": message.author.name,
                "channelId": str(message.channel.id),
                "history": history,
                "type": message_type
            }

            if message_type == "THREAD_MESSAGE":
                payload["threadId"] = str(message.channel.id)
                payload["threadName"] = message.channel.name

            print(f"[TO n8n] {payload}")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(N8N_WEBHOOK_URL, json=payload) as response:
                        if response.status == 200:
                            await message.add_reaction("✅")
                        else:
                            await message.add_reaction("❌")
                            print(f"n8n webhook returned status: {response.status}")
            except Exception as e:
                await message.add_reaction("🔥")
                print(f"Error sending to n8n: {e}")

# --- Global Bot Instance ---
bot = MyBot()

# --- API Models ---
class ProjectChannelRequest(BaseModel):
    channel_name: str
    category_name: str = "Active Projects"
    guideline: str

class ProjectStatusRequest(BaseModel):
    channel_name: str

class ProjectInfo(BaseModel):
    id: int
    name: str

# --- API Endpoints ---
@app.post("/new_project", operation_id="new_project")
async def new_project(request: ProjectChannelRequest) -> dict:
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        raise HTTPException(status_code=500, detail="Bot is not in the specified guild.")
    category = discord.utils.get(guild.categories, name=request.category_name)
    if not category:
        raise HTTPException(status_code=404, detail=f"Category '{request.category_name}' not found.")
    default_tags = [discord.ForumTag(name=n, emoji=e) for n, e in [("bug","🐛"),("documentation","📄"),("duplicate","👯"),("enhancement","✨"),("good first issue","👍"),("help wanted","🙋"),("invalid","❗"),("question","❓"),("wontfix","🤷")]]
    try:
        forum_channel = await guild.create_forum(name=request.channel_name, category=category, topic=request.guideline, available_tags=default_tags, default_reaction_emoji="✅")
        return {"status": "success", "channel_id": forum_channel.id, "channel_mention": forum_channel.mention}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/complete_project", operation_id="complete_project")
async def complete_project(request: ProjectStatusRequest) -> dict:
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        raise HTTPException(status_code=500, detail="Bot is not in the specified guild.")
    channel_to_move = discord.utils.get(guild.forums, name=request.channel_name)
    if not channel_to_move:
        raise HTTPException(status_code=404, detail=f"Forum channel '{request.channel_name}' not found.")
    completed_category = discord.utils.get(guild.categories, name="Completed Projects")
    if not completed_category:
        raise HTTPException(status_code=404, detail="Category 'Completed Projects' not found.")
    try:
        await channel_to_move.edit(category=completed_category)
        return {"status": "success", "message": f"Project '{request.channel_name}' has been moved to Completed Projects."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reactivate_project", operation_id="reactivate_project")
async def reactivate_project(request: ProjectStatusRequest) -> dict:
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        raise HTTPException(status_code=500, detail="Bot is not in the specified guild.")
    channel_to_move = discord.utils.get(guild.forums, name=request.channel_name)
    if not channel_to_move:
        raise HTTPException(status_code=404, detail=f"Forum channel '{request.channel_name}' not found.")
    active_category = discord.utils.get(guild.categories, name="Active Projects")
    if not active_category:
        raise HTTPException(status_code=404, detail="Category 'Active Projects' not found.")
    try:
        await channel_to_move.edit(category=active_category)
        return {"status": "success", "message": f"Project '{request.channel_name}' has been moved to Active Projects."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_projects", operation_id="list_projects", response_model=List[ProjectInfo])
async def list_projects(status: str = "active") -> List[ProjectInfo]:
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        raise HTTPException(status_code=500, detail="Bot is not in the specified guild.")
    category_name = "Active Projects" if status == "active" else "Completed Projects"
    category = discord.utils.get(guild.categories, name=category_name)
    if not category:
        return []
    projects = [ProjectInfo(id=channel.id, name=channel.name) for channel in category.forums]
    return projects

# --- Main Execution Logic ---
async def run_bot():
    await bot.start(DISCORD_BOT_TOKEN)

async def run_api():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    mcp.setup_server()
    await server.serve()

async def main():
    await asyncio.gather(run_bot(), run_api())

if __name__ == "__main__":
    asyncio.run(main())
