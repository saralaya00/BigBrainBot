import asyncio
import datetime
import discord
import os

from enum import auto
from enum import Enum
from replit import db
from discord.ext import tasks
from datetime import date
from Helper import Helper
from os import system
from RedditUtil import RedditUtil

class SimpleCommandHelper(): 
  class Commands(Enum):
    pls = auto()
    meme = auto()
    comic = auto()
    snac = auto()
    
  def __init__(self):
    self.commands = self.Commands
    pass

  def get_command_group(self, group):
    if self.commands.pls == group:
      print(self.commands.pls)
      return self.commands.pls 
  
  
class DiscordClient(discord.Client):
    # big-brain-coding channel id
    CHANNEL_ID = 1003624397749354506
    EMPTY_STR = ''
    HELP_MSG_STRING = """
*BigBrainBot* is a discord bot made to replace warwolf.
Automatically drops daily coding problems on a predefined channel.

[Major code changes in progress]
[Commands are not guaranteed to work]
[@radcakes for excuses]

Use **pls help** to get memes and utility commands
Use **code help** to get coding problems related commands
Use **bot help** to display this message"""

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
            if source_name not in Helper.sources_to_use:
                # print(f"'{source_name}' is not present in sources_to_use={Helper.sources_to_use}, skipping source.")
                continue

            if source_name not in db.keys():
                db[source_name] = "False"

            if not db[source_name] == todate:
                problem = helper.get_daily_problem(source)
                msg = problem['msg']

                channel = self.get_channel(self.CHANNEL_ID)
                print(f"Sending {source_name} message {todate}")
                db[source_name] = todate
                await channel.send(msg)
                break
            else:
                print(
                    f"DB entry for {source_name} is present [{db[source_name]}], skipping post."
                )

    @write_daily_question.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

    def is_simple_command(self, prefix, cmd, message_content):
        return cmd == message_content.replace(prefix, self.EMPTY_STR).strip()

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        message_content = message.content.lower().strip()
        multiline_message = message.content.strip()
          
        if "pls" in message_content:
            command = message_content.splitlines()[0].split(' ')
            command = command[0] + ' ' + command[1]
            if self.is_simple_command("pls", "todo", command):
              targets = ""
              for todo in multiline_message.splitlines()[1:]:
                if todo == self.EMPTY_STR:
                  continue
                targets += "> " + todo.replace("> ", '', 1) + "\n"
              msg = f"""** {date.today().strftime("%A %b %d %Y")} **
:dart: **Target**
{targets}:fire: **Done**
> ~~Make todo~~"""
              sent = await message.channel.send(msg)
              info = await message.channel.send("*This message will auto delete in 15 seconds..*")
              await asyncio.sleep(15)
              await info.delete()
              await sent.delete()
              # await message.delete()
              return
              
            if self.is_simple_command("pls", "meme", message_content):
                post = self.redditUtil.get_reddit_post(
                    RedditUtil.MEMES_STR)
                await message.channel.send(post)
                return

            if self.is_simple_command("pls", "dank", message_content):
              post = self.redditUtil.get_reddit_post(RedditUtil.DANK_STR)
              await message.channel.send(post)
              return

            if self.is_simple_command("pls", "snac", message_content):
              post = self.redditUtil.get_reddit_post(RedditUtil.SNAC_STR)
              await message.channel.send(post)
              return
              
            if self.is_simple_command("pls", "comic", message_content):
                post = self.redditUtil.get_reddit_post(
                    RedditUtil.COMICS_STR)
                await message.channel.send(post)
                return

            if self.is_simple_command("pls", "debug", message_content):
                # info = self.redditUtil.debug_info()
                # print(info)
                # self.print_db()
                sph = SimpleCommandHelper()
                info = sph.get_command_group(sph.commands.pls)
                await message.channel.send(info)
                return

        if "bot" in message_content:
            if self.is_simple_command("bot", "help", message_content):
                await message.channel.send(self.HELP_MSG_STRING)
                return

            if ":get" in message_content:
                helper = Helper()
                source_name_list = [
                    "leetcode", "legacy-leetcode", "codeforces"
                ]
                for source_name in source_name_list:
                    if self.is_simple_command("bot :get", source_name,
                                              message_content):
                        index = source_name_list.index(source_name)
                        source = Helper.sources[index]
                        problem = helper.get_daily_problem(source)
                        msg = problem['msg']
                        await message.channel.send(msg)
                        return

            if self.is_simple_command("bot", "good", message_content):
                await message.channel.send(":D")
                return

            if self.is_simple_command("bot", "bad", message_content):
                await message.channel.send(":(")
                return

        if "gandalf" in message_content:
          await message.channel.send("Fool of a Took!")
          return

client = DiscordClient()
try:
  client.run(os.getenv('TOKEN'))
except discord.errors.HTTPException:
  print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
  system('kill 1')
  system("python Restart.py")