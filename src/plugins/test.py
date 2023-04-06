from nonebot import on_message
from nonebot.adapters.github import IssueCommentCreated

test = on_message()


@test.handle()
async def _(event: IssueCommentCreated):
    print(event)
