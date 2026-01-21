import discord
from discord.ext import tasks, commands
import db, func, datetime

# db 칼럼 값
discord_id = 0
boj_id = 1
week_score = 2
total_score = 3
day_score = 4

not_registered_message = (
    "```" + 
    "{}님의 BOJ 아이디가 아직 등록되지 않았습니다.\n"
    "/등록 [BOJ아이디] 명령어를 통해 등록해 주세요.\n"
    "등록 이후부터 점수가 집계됩니다!"
    + "```"
)

intent=discord.Intents(message_content=True, messages=True, guilds=True, members=True)
bot=commands.Bot(command_prefix='/', intents=intent)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("부산대학교 정보컴퓨터공학부 백준 문제 확인봇입니다."))
    day_check.start()

# @bot.command()
# async def 테스트(ctx):
#     await day_check()

@bot.command()
async def 등록(ctx, msg):
    print("등록", ctx.author, msg)
    await ctx.message.delete() # ctx.message는 원 코드의 message와 같다.
    # print(str(ctx.author), type(ctx.author)) # ctx.author는 discord.Member 객체이다. str이 아님.
    chk = db.user_init(ctx, msg)
    if chk == 1:
        await ctx.send("```" + f"{str(ctx.author.display_name)}님의 아이디가 수정되었습니다." + "```")
    elif chk == 2:
        await ctx.send(f"```{str(ctx.author.display_name)}님의 디스코드 아이디가 수정되었습니다.```")
    elif chk == -1:
        await ctx.send("```" + "API 호출에 실패하였습니다.\n 입력하신 아이디를 다시 확인해주시거나, 문제가 지속될 경우 담당자에게 문의해주세요." + "```")
    else:
        await ctx.send("```" + f"{str(ctx.author.display_name)}님의 아이디가 등록되었습니다." + "```")

@bot.command()
async def 나의오늘점수(ctx):
    print("나의오늘점수", ctx.author)
    await ctx.message.delete()
    user = db.user_read(ctx)
    if type(user) == type(None):
        await ctx.send(not_registered_message.format(str(ctx.author.display_name)))
    else:
        await ctx.send(
            "```" + 
            f"{str(ctx.author.display_name)}님의 오늘 점수는 {db.user_update_day_score(user[boj_id])}점입니다.\n"
            f"오늘 점수는 오늘 푼 문제 중 가장 높은 난이도의 1문제만 반영됩니다.\n"
            f"(브론즈 5 → 1점 ~ 루비 1 → 30점)"
            + "```"
        )

@bot.command()
async def 나의주간점수(ctx):
    print("나의주간점수", ctx.author)
    await ctx.message.delete()
    user = db.user_read(ctx)
    if type(user) == type(None):
        await ctx.send(not_registered_message.format(str(ctx.author.display_name)))
    else:
        await ctx.send(
            "```" + 
            f"{str(ctx.author.display_name)}님의 주간 점수는 {user[week_score]}점입니다.\n"
            f"주간 점수는 매일 00시에 업데이트되며,\n"
            f"이번 주 동안의 오늘 점수를 합산하여 계산됩니다."
            + "```"
        )

@bot.command()
async def 나의전체점수(ctx):
    print("나의전체점수", ctx.author)
    await ctx.message.delete()
    user = db.user_read(ctx)
    if type(user) == type(None):
        await ctx.send(not_registered_message.format(str(ctx.author.display_name)))
    else:
        await ctx.send(
            "```" + 
            f"{str(ctx.author.display_name)}님의 전체 누적 점수는 {user[total_score]}점입니다.\n"
            f"전체 점수는 매주 월요일 00시에 업데이트되며,\n"
            f"매주의 주간 점수 등수에 따라 점수가 부여되어 누적됩니다."
            + "```"
        )

@bot.command()
async def 주간랭킹(ctx):
    print("주간랭킹", ctx.author)
    await ctx.message.delete()
    output = await get_ranking(week_score, "주간 랭킹")
    await ctx.send(output)

@bot.command()
async def 전체랭킹(ctx):
    print("전체랭킹", ctx.author)
    await ctx.message.delete()
    output = await get_ranking(total_score, "전체 랭킹")
    await ctx.send(output)

    
async def get_ranking(score_type: int, title: str):
    if score_type == week_score:
        for i in db.user_read_all():
            db.user_update_week_score(i[1])
    users = db.user_read_all()
    # 동순위 고려
    ranked_users = func.get_ranked_users(users, score_type)
    output = f"{title}\n"
    for i in ranked_users:
        discord_user = bot.get_guild(server_id).get_member_named(i[0])
        if discord_user:
            # 동순위 고려한 순위가 index 5에 있음
            output += f"{i[-1]}. {discord_user.display_name} : {i[score_type]}점\n"

    return "```" + output + "```"

@tasks.loop(time=[datetime.time(hour=0, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=9)))])
async def day_check():
    today = datetime.date.today()
    date_str = today.strftime("%y년 %m월 %d일")
    weekday_str = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'][today.weekday()]
    date_header = f"{date_str} {weekday_str}"
    
    # 디스코드 채널에 위클리 랭킹 전송
    week_output = await get_ranking(week_score, "주간 랭킹")
    await bot.get_channel(today_boj).send(f"## {date_header}\n{week_output}")
    
    # 월요일 00시 전체 랭크 업데이트
    if(datetime.date.today().weekday() == 0):
        # total_score(전체) 점수 업데이트
        func.user_calculate_total_score()
        
        # 디스코드 채널에 전체 랭킹 전송
        total_output = await get_ranking(total_score, "전체 랭킹")
        await bot.get_channel(today_boj).send(f"## {date_header}\n{total_output}")  

today_boj, test_boj, test_server_id, server_id = map(int, open('id.txt', 'r').readline().split())

#디스코드 봇 토큰
token = open('token.txt', 'r').readline()
bot.run(token)