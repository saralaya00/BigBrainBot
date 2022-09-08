import discord
import os

from replit import db
from discord.ext import tasks
from datetime import date
from Helper import Helper
from RedditUtil import RedditUtil

class DiscordClient(discord.Client):
    # big-brain-coding channel id
    CHANNEL_ID = 1003624397749354506

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # start the task to run in the background
        self.redditUtil = RedditUtil()
        self.write_daily_question.start()

    def cleanup_db(self):
        self.print_db()
        for key in db.keys():
            del db[key]

    def print_db(self):
        print("List of replit db Keys", db.keys())

    async def on_ready(self):
        print(f'{self.user} has logged in.')

    @tasks.loop(minutes=60 * 3)
    async def write_daily_question(self):
        helper = Helper()
        todate = f"{date.today()}"

        for source in Helper.sources:
            source_name = source["name"]
            if not source_name in Helper.sources_to_use:
                # print(f"'{source_name}' is not present in sources_to_use={Helper.sources_to_use}, skipping source.")
                continue

            if not source_name in db.keys():
                db[source_name] = "False"

            if not db[source_name] == todate:
                problem = helper.scrape_daily_problem(source)
                msg = problem['msg']

                channel = self.get_channel(self.CHANNEL_ID)
                print(f"Sending {source_name} message {todate}")
                db[source_name] = todate
                await channel.send(msg)
                break
            else:
                print(
                    f"DB entry for {source_name} is present [{db[source_name]}], skipping post.")

    @write_daily_question.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        message_content = message.content.lower()

        if "pls" in message_content:
            if "meme" == message_content.replace("pls ", ''):
                post_url = self.redditUtil.get_reddit_post(
                    RedditUtil.MEMES_STR)
                await message.channel.send(post_url)
                return

            if "comic" == message_content.replace("pls ", ''):
                post_url = self.redditUtil.get_reddit_post(
                    RedditUtil.COMICS_STR)
                await message.channel.send(post_url)
                return

        if "bot" in message_content:
            if ":help" in message_content:
                await message.channel.send(Helper.HELP_MSG_STRING)
                return

            if ":get" in message_content:
                helper = Helper()
                source_name_list = [
                    "leetcode", "legacy-leetcode", "codechef", "codeforces"]
                for source_name in source_name_list:
                    if "bot :get " == message_content.replace(source_name, ''):
                        index = source_name_list.index(source_name)
                        source = Helper.sources[index]
                        problem = helper.scrape_daily_problem(source)
                        msg = problem['msg']
                        await message.channel.send(msg)
                        return

            # todo: UwU make this sentient, MR.I KnOw wHaT I WaNt iN LiFe can fix this
            if any(element in message_content for element in ["thank you", "thanks", "arigato", "good"]):
                await message.channel.send(":D")
                return

            if any(element in message_content for element in ["bad"]):
                await message.channel.send(":(")
                return

client = DiscordClient()
client.print_db()
client.run(os.getenv('TOKEN'))