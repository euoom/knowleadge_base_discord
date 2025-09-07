import discord
from discord import app_commands, ui
from discord.ext import commands

# --- Modals ---
class NewProjectModal(ui.Modal, title='새 프로젝트 생성'):
    project_name_en = ui.TextInput(label='프로젝트 영문명 (채널명으로 사용)', placeholder='e.g., my_awesome_project', required=True)
    short_description = ui.TextInput(label='한 줄 설명', style=discord.TextStyle.paragraph, placeholder='비워두시면 프로젝트 영문명을 기반으로 자동 생성됩니다.', required=False)
    start_date = ui.TextInput(label='시작일 (YYYY-MM-DD, 생략 가능)', required=False)
    target_date = ui.TextInput(label='목표일 (YYYY-MM-DD, 생략 가능)', required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild

        category_name = "--- Active Projects ---"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            await interaction.followup.send(f"오류: '{category_name}' 카테고리를 먼저 /setup으로 생성해야 합니다.")
            return

        channel_name = self.project_name_en.value
        try:
            forum_channel = await guild.create_forum(name=channel_name, category=category)
        except discord.Forbidden:
            await interaction.followup.send("오류: 포럼 채널을 생성할 권한이 없습니다.")
            return
        except Exception as e:
            await interaction.followup.send(f"채널 생성 중 오류 발생: {e}")
            return

        guideline_content = (
            f"# {self.project_name_en.value}\n\n"
            f"**설명**: {self.short_description.value or '(설명 없음)'}\n"
            f"**시작일**: {self.start_date.value or '미지정'}\n"
            f"**목표일**: {self.target_date.value or '미지정'}\n---"
            f"이 포럼은 '{self.project_name_en.value}' 프로젝트의 모든 이슈를 관리하기 위한 공간입니다."
        )

        try:
            await forum_channel.create_thread(name="📌 가이드라인 (README)", content=guideline_content)
        except Exception as e:
            await interaction.followup.send(f"가이드라인 게시물 작성 중 오류 발생: {e}")
            return

        await interaction.followup.send(f"프로젝트 포럼 채널 {forum_channel.mention} 생성이 완료되었습니다.")

class ProjectCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Autocomplete Functions ---
    async def active_project_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        projects = []
        try:
            category = discord.utils.get(interaction.guild.categories, name="--- Active Projects ---")
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
            category = discord.utils.get(interaction.guild.categories, name="--- Completed Projects ---")
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
    @app_commands.command(name="new_project", description="새로운 프로젝트를 생성합니다.")
    async def new_project_command(self, interaction: discord.Interaction):
        await interaction.response.send_modal(NewProjectModal())

    @app_commands.command(name="complete_project", description="진행중인 프로젝트를 완료 처리합니다.")
    @app_commands.autocomplete(project=active_project_autocomplete)
    @app_commands.describe(project="완료 처리할 프로젝트의 이름을 선택하세요.")
    async def complete_project_command(self, interaction: discord.Interaction, project: str):
        await interaction.response.defer(ephemeral=True)
        active_category = discord.utils.get(interaction.guild.categories, name="--- Active Projects ---")
        completed_category = discord.utils.get(interaction.guild.categories, name="--- Completed Projects ---")
        # 채널 이름으로 채널 객체를 찾습니다.
        channel_to_move = discord.utils.get(interaction.guild.channels, name=project)

        if not channel_to_move or not active_category or not completed_category or channel_to_move.category != active_category:
            await interaction.followup.send(f"'{project}' 프로젝트를 찾을 수 없거나, 이미 완료된 상태입니다.")
            return

        # 디스코드 채널을 Completed 카테고리로 이동
        await channel_to_move.edit(category=completed_category)
        
        # n8n에 요청할 작업 내용을 사용자에게 알림
        await interaction.followup.send(f"'{project}' 프로젝트를 완료 처리했습니다. 백엔드에서 해당 프로젝트의 README.md 상태를 'Completed'로, 'completion_date'를 오늘 날짜로 업데이트합니다.")

    @app_commands.command(name="reactivate_project", description="완료된 프로젝트를 다시 활성화합니다.")
    @app_commands.autocomplete(project=completed_project_autocomplete)
    @app_commands.describe(project="다시 활성화할 프로젝트의 이름을 선택하세요.")
    async def reactivate_project_command(self, interaction: discord.Interaction, project: str):
        await interaction.response.defer(ephemeral=True)
        active_category = discord.utils.get(interaction.guild.categories, name="--- Active Projects ---")
        completed_category = discord.utils.get(interaction.guild.categories, name="--- Completed Projects ---")
        channel_to_move = discord.utils.get(interaction.guild.channels, name=project)

        if not channel_to_move or not active_category or not completed_category or channel_to_move.category != completed_category:
            await interaction.followup.send(f"'{project}' 프로젝트를 찾을 수 없거나, 이미 활성화된 상태입니다.")
            return
        
        # 디스코드 채널을 Active 카테고리로 이동
        await channel_to_move.edit(category=active_category)

        # n8n에 요청할 작업 내용을 사용자에게 알림
        await interaction.followup.send(f"'{project}' 프로젝트를 다시 활성화했습니다. 백엔드에서 README.md의 상태를 'On track'으로 업데이트하고, 'completion_date'를 제거합니다. 새로운 목표일은 필요시 직접 수정해주세요.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ProjectCog(bot))