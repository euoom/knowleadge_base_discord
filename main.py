import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# .env 로드
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True

# Bot 클래스를 상속받아 MyBot 클래스 정의
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # cogs 폴더에서 .py로 끝나는 모든 파일을 찾아 코그로 로드
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        # 로드된 모든 커맨드를 특정 서버에 즉시 동기화 (개발용)
        my_guild = discord.Object(id=1411265287491158018)
        self.tree.copy_global_to(guild=my_guild)
        await self.tree.sync(guild=my_guild)

    async def on_ready(self):
        print(f'{self.user} (으)로 로그인했습니다.')

    async def on_message(self, message):
        # 봇 자신의 메시지는 무시
        if message.author == self.user:
            return
        
        # 스레드 안의 메시지만 n8n으로 전달 (향후 구현)
        if isinstance(message.channel, discord.Thread):
            print(f"Thread message from {message.author}: {message.content}")
            await message.add_reaction("✅") # 접수 확인 표시

async def main():
    bot = MyBot()
    await bot.start(DISCORD_BOT_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())