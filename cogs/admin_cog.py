import discord
from discord import app_commands, ui
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

    async def tag_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        try:
            channel = interaction.channel
            if isinstance(channel, discord.Thread):
                channel = channel.parent

            if not isinstance(channel, discord.ForumChannel):
                return []
            
            tags = [tag.name for tag in channel.available_tags]
            filtered_tags = [tag for tag in tags if current.lower() in tag.lower()]
            
            return [app_commands.Choice(name=tag, value=tag) for tag in filtered_tags[:25]]
        except Exception as e:
            print(f"ERROR in tag_autocomplete: {e}")
            return []

    # --- Command Groups ---
    project_group = app_commands.Group(name="project", description="프로젝트 관련 명령어를 관리합니다.")
    tag_subgroup = app_commands.Group(name="tag", description="포럼 채널의 태그를 관리합니다.", parent=project_group)

    # --- Commands ---
    @project_group.command(name="rename", description="프로젝트의 이름을 변경합니다.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.autocomplete(old_name=active_project_autocomplete)
    @app_commands.describe(old_name="변경할 현재 프로젝트 이름", new_name="새로운 프로젝트 이름")
    async def rename_project_command(self, interaction: discord.Interaction, old_name: str, new_name: str):
        await interaction.response.send_message("이 기능은 현재 개발 중입니다.")

    @app_commands.command(name="sync", description="GitHub 저장소 기준으로 Discord 채널 상태를 강제 동기화합니다.")
    @app_commands.default_permissions(administrator=True)
    async def sync_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("이 기능은 현재 개발 중입니다.")

    @app_commands.command(name="update_guideline", description="프로젝트의 가이드라인을 최신 버전으로 업데이트합니다.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.autocomplete(project=active_project_autocomplete)
    @app_commands.describe(project="가이드라인을 업데이트할 프로젝트를 선택하세요.")
    async def update_guideline_command(self, interaction: discord.Interaction, project: str):
        await interaction.response.send_message("이 기능은 현재 개발 중입니다.")

    @tag_subgroup.command(name="list", description="현재 포럼 채널의 모든 태그를 보여줍니다.")
    async def list_tags(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            channel = interaction.channel
            if isinstance(channel, discord.Thread):
                channel = channel.parent

            if not isinstance(channel, discord.ForumChannel):
                await interaction.followup.send("오류: 이 명령어는 포럼 채널 또는 그 게시물 안에서만 사용할 수 있습니다.")
                return

            if not channel.available_tags:
                await interaction.followup.send("이 채널에는 설정된 태그가 없습니다.")
                return

            tag_list = "\n".join([f"- {tag.name} ({tag.emoji})" for tag in channel.available_tags])
            await interaction.followup.send(f"**현재 채널 태그 목록:**\n{tag_list}")
        except Exception as e:
            print(f"ERROR in /tag list: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"명령어 실행 중 오류 발생: {e}")

    @tag_subgroup.command(name="add", description="현재 포럼 채널에 새 태그를 추가합니다.")
    @app_commands.describe(name="태그 이름", emoji="태그에 사용할 이모지 (선택사항)")
    async def add_tag(self, interaction: discord.Interaction, name: str, emoji: str = None):
        try:
            await interaction.response.defer()
            channel = interaction.channel
            if isinstance(channel, discord.Thread):
                channel = channel.parent
            
            if not isinstance(channel, discord.ForumChannel):
                await interaction.followup.send("오류: 이 명령어는 포럼 채널 또는 그 게시물 안에서만 사용할 수 있습니다.")
                return

            new_tag = discord.ForumTag(name=name, emoji=emoji)
            current_tags = list(channel.available_tags)
            current_tags.append(new_tag)

            await channel.edit(available_tags=current_tags)
            await interaction.followup.send(f"태그 '{name}'을(를) 추가했습니다.")

        except Exception as e:
            print(f"ERROR in /tag add: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"명령어 실행 중 심각한 오류 발생: {e}")

    @tag_subgroup.command(name="remove", description="현재 포럼 채널에서 태그를 삭제합니다.")
    @app_commands.autocomplete(name=tag_autocomplete)
    @app_commands.describe(name="삭제할 태그 이름")
    async def remove_tag(self, interaction: discord.Interaction, name: str):
        try:
            await interaction.response.defer()
            channel = interaction.channel
            if isinstance(channel, discord.Thread):
                channel = channel.parent

            if not isinstance(channel, discord.ForumChannel):
                await interaction.followup.send("오류: 이 명령어는 포럼 채널 또는 그 게시물 안에서만 사용할 수 있습니다.")
                return

            new_tags = [tag for tag in channel.available_tags if tag.name != name]
            
            if len(new_tags) == len(channel.available_tags):
                await interaction.followup.send(f"'{name}' 태그를 찾을 수 없습니다.")
                return

            await channel.edit(available_tags=new_tags)
            await interaction.followup.send(f"태그 '{name}'을(를) 삭제했습니다.")
        except Exception as e:
            print(f"ERROR in /tag remove: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"명령어 실행 중 오류 발생: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))