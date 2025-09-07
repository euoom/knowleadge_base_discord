import discord
from discord import app_commands
from discord.ext import commands

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Autocomplete Functions ---
    async def active_project_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        category = discord.utils.get(interaction.guild.categories, name="--- Active Projects ---")
        if not category:
            return []
        projects = [channel.name for channel in category.forums]
        filtered_projects = [project for project in projects if current.lower() in project.lower()]
        return [app_commands.Choice(name=project, value=project) for project in filtered_projects[:25]]

    # --- Commands ---
    @app_commands.command(name="rename_project", description="프로젝트의 이름을 변경합니다. (로컬, GitHub, Discord 모두 변경)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.autocomplete(old_name=active_project_autocomplete)
    @app_commands.describe(old_name="변경할 현재 프로젝트 이름", new_name="새로운 프로젝트 이름")
    async def rename_project_command(self, interaction: discord.Interaction, old_name: str, new_name: str):
        response_message = (
            f"**프로젝트 이름 변경을 요청했습니다!**\n"
            f"> 이 요청은 `n8n`으로 전달되어 아래 작업들을 순차적으로 수행합니다.\n\n"
            f"- **대상 프로젝트**: {old_name}\n"
            f"- **새 이름**: {new_name}\n"
            f"- **수행 작업**: 로컬 폴더명 변경, GitHub 저장소명 변경, Discord 채널명 변경"
        )
        await interaction.response.send_message(response_message, ephemeral=True)

    @app_commands.command(name="sync", description="GitHub 저장소 기준으로 Discord 채널 상태를 강제 동기화합니다.")
    @app_commands.default_permissions(administrator=True)
    async def sync_command(self, interaction: discord.Interaction):
        response_message = (
            f"**강제 동기화를 요청했습니다!**\n"
            f"> 이 요청은 `n8n`으로 전달되어 GitHub 저장소 상태를 기준으로 Discord 채널을 재정렬합니다."
        )
        await interaction.response.send_message(response_message, ephemeral=True)

    @app_commands.command(name="update_guideline", description="프로젝트의 가이드라인(README)을 최신 버전으로 업데이트합니다.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.autocomplete(project=active_project_autocomplete)
    @app_commands.describe(project="가이드라인을 업데이트할 프로젝트를 선택하세요.")
    async def update_guideline_command(self, interaction: discord.Interaction, project: str):
        response_message = (
            f"**가이드라인 업데이트를 요청했습니다!**\n"
            f"> 이 요청은 `n8n`으로 전달되어 `{project}` 프로젝트의 README.md 파일을 다시 읽고<br>해당 포럼 채널의 가이드라인 게시물을 업데이트합니다."
        )
        await interaction.response.send_message(response_message, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))