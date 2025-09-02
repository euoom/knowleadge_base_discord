import discord
from discord import app_commands, ui
import os
from dotenv import load_dotenv

# .env 로드
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True

# --- Modals ---
class NewProjectModal(ui.Modal, title='새 프로젝트 생성'):
    project_name_en = ui.TextInput(label='프로젝트 영문명 (폴더명으로 사용)', placeholder='e.g., my_awesome_project', required=True)
    short_description = ui.TextInput(label='한 줄 설명', style=discord.TextStyle.paragraph, placeholder='비워두시면 프로젝트 영문명을 기반으로 자동 생성됩니다.', required=False)
    start_date = ui.TextInput(label='시작일 (YYYY-MM-DD, 생략 가능)', required=False)
    target_date = ui.TextInput(label='목표일 (YYYY-MM-DD, 생략 가능)', required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild

        # 1. Active Projects 카테고리 찾기
        category_name = "--- Active Projects ---"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            await interaction.followup.send(f"오류: '{category_name}' 카테고리를 먼저 /setup으로 생성해야 합니다.")
            return

        # 2. 포럼 채널 생성
        channel_name = f"proj-{self.project_name_en.value}"
        try:
            forum_channel = await guild.create_forum(name=channel_name, category=category)
        except discord.Forbidden:
            await interaction.followup.send("오류: 포럼 채널을 생성할 권한이 없습니다.")
            return
        except Exception as e:
            await interaction.followup.send(f"채널 생성 중 오류 발생: {e}")
            return

        # 3. 가이드라인 게시물 내용 생성
        guideline_content = (
            f"# {self.project_name_en.value}\n\n"
            f"**설명**: {self.short_description.value or '(설명 없음)'}\n"
            f"**시작일**: {self.start_date.value or '미지정'}\n"
            f"**목표일**: {self.target_date.value or '미지정'}\n---"
        )

        # 4. 포럼에 첫 게시물(가이드라인) 작성 및 고정
        try:
            # 포럼 채널에서 스레드(게시물)를 생성합니다.
            thread_with_message = await forum_channel.create_thread(name="README", content=guideline_content)
            # 생성된 게시물(스레드)을 고정합니다.
            await thread_with_message.thread.pin()
        except Exception as e:
            await interaction.followup.send(f"가이드라인 게시물 작성 또는 고정 중 오류 발생: {e}")
            return

        await interaction.followup.send(f"프로젝트 채널 {forum_channel.mention} 생성이 완료되었습니다.")

# --- Bot Client ---
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        my_guild = discord.Object(id=1411265287491158018)
        self.tree.copy_global_to(guild=my_guild)
        await self.tree.sync(guild=my_guild)

    async def on_ready(self):
        print(f'{self.user} (으)로 로그인했습니다.')

client = MyClient(intents=intents)

# --- Slash Commands ---
@client.tree.command(name="setup", description="서버에 봇의 기본 환경을 설정합니다.")
@app_commands.default_permissions(administrator=True)
async def setup_command(interaction: discord.Interaction):
    guild = interaction.guild
    await interaction.response.defer(ephemeral=True, thinking=True)

    for category_name in ["--- Active Projects ---", "--- Completed Projects ---"]:
        if not discord.utils.get(guild.categories, name=category_name):
            await guild.create_category(category_name)

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

    try:
        with open("HOW_TO_USE.md", "r", encoding="utf-8") as f:
            how_to_use_content = f.read()
    except FileNotFoundError:
        await interaction.followup.send("HOW_TO_USE.md 파일을 찾을 수 없습니다.")
        return

    async for message in channel.history(limit=100):
        if message.author == client.user:
            await message.delete()
            
    await channel.send(how_to_use_content)
    
    await interaction.followup.send(f"`#{channel_name}` 채널과 카테고리 설정이 완료되었습니다.")

@client.tree.command(name="new_project", description="새로운 프로젝트를 생성합니다.")
async def new_project_command(interaction: discord.Interaction):
    await interaction.response.send_modal(NewProjectModal())

# 봇 실행
client.run(DISCORD_BOT_TOKEN)