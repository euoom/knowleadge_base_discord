import discord
from discord import app_commands, ui
import os
import aiohttp
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

# 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True

class TaskView(ui.View):
    """'새 프로젝트 시작' 버튼을 포함하는 뷰"""
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="새 프로젝트 시작 ➕", style=discord.ButtonStyle.success, custom_id="start_new_project_button")
    async def start_project(self, interaction: discord.Interaction, button: ui.Button):
        thread_name = f"{interaction.user.display_name}님의 새 프로젝트"
        thread = await interaction.channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.public_thread
        )
        await interaction.response.send_message(f'{thread.mention}에서 새 프로젝트를 시작하세요!', ephemeral=True)
        await thread.send(f"{interaction.user.mention}, 안녕하세요! 어떤 프로젝트를 시작할까요?")

class SetupModal(ui.Modal, title='초기 대시보드 설정'):
    """README URL을 입력받기 위한 모달"""
    readme_url = ui.TextInput(
        label='GitHub 저장소 URL 또는 README Raw URL',
        placeholder='https://github.com/user/repo'
    )

    def resolve_github_url(self, url: str) -> str:
        """입력된 URL을 GitHub Raw 콘텐츠 URL로 변환합니다."""
        if "raw.githubusercontent.com" in url:
            return url
        if "github.com" in url:
            # .git 접미사 및 마지막 슬래시 제거
            cleaned_url = url.removesuffix(".git").rstrip("/")
            parts = cleaned_url.split("/")
            if len(parts) >= 5:
                user = parts[3]
                repo = parts[4]
                # 기본 브랜치를 main으로 가정
                return f"https://raw.githubusercontent.com/{user}/{repo}/main/README.md"
        return url # 변환 불가 시 원본 반환

    async def on_submit(self, interaction: discord.Interaction):
        raw_url = self.resolve_github_url(self.readme_url.value)
        
        headers = {}
        if GITHUB_ACCESS_TOKEN:
            headers["Authorization"] = f"token {GITHUB_ACCESS_TOKEN}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(raw_url, headers=headers) as response:
                    if response.status == 200:
                        readme_content = await response.text()
                    else:
                        await interaction.response.send_message(f"URL에서 콘텐츠를 가져오는 데 실패했습니다. (상태 코드: {response.status})", ephemeral=True)
                        return
        except Exception as e:
            await interaction.response.send_message(f"URL 처리 중 오류 발생: {e}", ephemeral=True)
            return

        guild = interaction.guild
        channel_name = "how-to-use"
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not existing_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(send_messages=False),
                guild.me: discord.PermissionOverwrite(send_messages=True)
            }
            channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
        else:
            channel = existing_channel

        view = TaskView()
        # 기존 메시지 삭제 후 새로 게시 (항상 최신 상태 유지)
        await channel.purge(limit=100, check=lambda m: m.author == client.user)
        await channel.send(readme_content, view=view)
        await interaction.response.send_message(f"`#{channel_name}` 채널 설정이 완료되었습니다.", ephemeral=True)

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f'{self.user} (으)로 로그인했습니다.')

client = MyClient(intents=intents)

@client.tree.command(name="setup", description="초기 설정을 시작합니다.")
@app_commands.default_permissions(administrator=True)
async def setup_command(interaction: discord.Interaction):
    await interaction.response.send_modal(SetupModal())

# 봇 실행
client.run(DISCORD_BOT_TOKEN)