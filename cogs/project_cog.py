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
        await interaction.response.defer(thinking=True)
        guild = interaction.guild

        # 1. Active Projects 카테고리 찾기
        category_name = "--- Active Projects ---"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            await interaction.followup.send(f"오류: '{category_name}' 카테고리를 먼저 /setup으로 생성해야 합니다.")
            return

        # 2. 가이드라인 및 기본 태그 내용 생성
        guideline_content = (
            f"# {self.project_name_en.value}\n\n"
            f"**설명**: {self.short_description.value or '(설명 없음)'}\n"
            f"**시작일**: {self.start_date.value or '미지정'}\n"
            f"**목표일**: {self.target_date.value or '미지정'}\n---"
            f"이 포럼은 '{self.project_name_en.value}' 프로젝트의 모든 이슈를 관리하기 위한 공간입니다."
        )
        default_tags = [
            discord.ForumTag(name="bug", emoji="🐛"),
            discord.ForumTag(name="documentation", emoji="📄"),
            discord.ForumTag(name="duplicate", emoji="👯"),
            discord.ForumTag(name="enhancement", emoji="✨"),
            discord.ForumTag(name="good first issue", emoji="👍"),
            discord.ForumTag(name="help wanted", emoji="🙋"),
            discord.ForumTag(name="invalid", emoji="❗"),
            discord.ForumTag(name="question", emoji="❓"),
            discord.ForumTag(name="wontfix", emoji="🤷"),
        ]

        # 3. 포럼 채널 생성
        channel_name = self.project_name_en.value
        try:
            forum_channel = await guild.create_forum(
                name=channel_name, 
                category=category, 
                topic=guideline_content,
                available_tags=default_tags
            )
        except discord.Forbidden:
            await interaction.followup.send("오류: 포럼 채널을 생성할 권한이 없습니다.")
            return
        except Exception as e:
            await interaction.followup.send(f"채널 생성 중 오류 발생: {e}")
            return

        # 4. 포럼에 첫 게시물(가이드라인) 작성
        try:
            await forum_channel.create_thread(name="📌 가이드라인 (README)", content="채널 상단의 가이드라인을 확인해주세요.")
        except Exception as e:
            await interaction.followup.send(f"가이드라인 게시물 작성 중 오류 발생: {e}")
            return

        await interaction.followup.send(f"프로젝트 포럼 채널 {forum_channel.mention} 생성이 완료되었습니다.")

class ProjectCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ... (rest of the class) ...

async def setup(bot: commands.Bot):
    await bot.add_cog(ProjectCog(bot))