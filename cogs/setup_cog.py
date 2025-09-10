import discord
from discord import app_commands
from discord.ext import commands

class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="서버에 봇의 기본 환경을 설정합니다.")
    @app_commands.default_permissions(administrator=True)
    async def setup_command(self, interaction: discord.Interaction):
        guild = interaction.guild
        await interaction.response.defer(thinking=True)

        # 1. 카테고리 생성
        for category_name in ["--- Active Projects ---", "--- Completed Projects ---"]:
            if not discord.utils.get(guild.categories, name=category_name):
                await guild.create_category(category_name)

        # 2. how-to-use 채널 생성 및 권한 설정
        channel_name = "how-to-use"
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not existing_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(send_messages=False, create_public_threads=False),
                guild.me: discord.PermissionOverwrite(send_messages=True, manage_messages=True)
            }
            channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
        else:
            channel = existing_channel

        # 3. 기존 메시지 삭제 후 HOW_TO_USE.md 파일 내용 게시
        try:
            with open("HOW_TO_USE.md", "r", encoding="utf-8") as f:
                how_to_use_content = f.read()
        except FileNotFoundError:
            await interaction.followup.send("HOW_TO_USE.md 파일을 찾을 수 없습니다.")
            return

        async for message in channel.history(limit=100):
            if message.author == self.bot.user:
                await message.delete()
                
        await channel.send(how_to_use_content)
        
        await interaction.followup.send(f"`#{channel_name}` 채널과 카테고리 설정이 완료되었습니다.")

async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))