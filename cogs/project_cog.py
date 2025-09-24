import discord
from discord import app_commands, ui
from discord.ext import commands

class ProjectCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Autocomplete Functions ---
    async def active_project_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        projects = []
        try:
            category = discord.utils.get(interaction.guild.categories, name="Active Projects")
            if category:
                projects = [channel.name for channel in category.forums]
        except Exception as e:
            print(f"Error in active_project_autocomplete: {e}")
        
        filtered_projects = [project for project in projects if current.lower() in project.lower()]
        return [
            app_commands.Choice(name=project, value=project)
            for project in filtered_projects[:25]
        ]

    async def completed_project_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        projects = []
        try:
            category = discord.utils.get(interaction.guild.categories, name="Completed Projects")
            if category:
                projects = [channel.name for channel in category.forums]
        except Exception as e:
            print(f"Error in completed_project_autocomplete: {e}")

        filtered_projects = [project for project in projects if current.lower() in project.lower()]
        return [
            app_commands.Choice(name=project, value=project)
            for project in filtered_projects[:25]
        ]

    # --- Commands ---
    @app_commands.command(name="new_project", description="새로운 프로젝트를 생성하는 방법을 안내합니다.")
    async def new_project_command(self, interaction: discord.Interaction):
        guidance_message = (
            f"✅ **새 프로젝트를 시작하려면, 저를 멘션해서 말씀해주세요!**\n\n"
            f"**예시:**\n"
            f"> {self.bot.user.mention} 새로운 웹사이트 프로젝트를 시작하고 싶어."
        )
        await interaction.response.send_message(guidance_message)

    @app_commands.command(name="complete_project", description="진행중인 프로젝트를 완료 처리합니다.")
    @app_commands.autocomplete(project=active_project_autocomplete)
    @app_commands.describe(project="완료 처리할 프로젝트의 이름을 선택하세요.")
    async def complete_project_command(self, interaction: discord.Interaction, project: str):
        # 이 명령어의 응답도 공개적으로 변경합니다.
        await interaction.response.defer()
        active_category = discord.utils.get(interaction.guild.categories, name="Active Projects")
        completed_category = discord.utils.get(interaction.guild.categories, name="Completed Projects")
        channel_to_move = discord.utils.get(interaction.guild.channels, name=project)

        if not channel_to_move or not active_category or not completed_category or channel_to_move.category != active_category:
            await interaction.followup.send(f"'{project}' 프로젝트를 찾을 수 없거나, 이미 완료된 상태입니다.")
            return

        await channel_to_move.edit(category=completed_category)
        await interaction.followup.send(f"'{project}' 프로젝트를 완료 처리했습니다.")

    @app_commands.command(name="reactivate_project", description="완료된 프로젝트를 다시 활성화합니다.")
    @app_commands.autocomplete(project=completed_project_autocomplete)
    @app_commands.describe(project="다시 활성화할 프로젝트의 이름을 선택하세요.")
    async def reactivate_project_command(self, interaction: discord.Interaction, project: str):
        await interaction.response.defer()
        active_category = discord.utils.get(interaction.guild.categories, name="Active Projects")
        completed_category = discord.utils.get(interaction.guild.categories, name="Completed Projects")
        channel_to_move = discord.utils.get(interaction.guild.channels, name=project)

        if not channel_to_move or not active_category or not completed_category or channel_to_move.category != completed_category:
            await interaction.followup.send(f"'{project}' 프로젝트를 찾을 수 없거나, 이미 활성화된 상태입니다.")
            return
        
        await channel_to_move.edit(category=active_category)
        await interaction.followup.send(f"'{project}' 프로젝트를 다시 활성화했습니다.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ProjectCog(bot))