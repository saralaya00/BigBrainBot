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
  SPACE_STR = ' '
  EMPTY_STR = ''
  INFO_INDEX = 2
  META_INDEX = 3
  
  class Commands(Enum):
    (
      pls, meme, dank, comic, snac, debug,
      todo, done,
      get, leetcode, codeforces, 
      good, bad, 
      help, bot, code
    ) = range(16)
    
  def __init__(self):
    self.commands = self.Commands
    pls = self.commands.pls

    self.GROUPS = {
      self.commands.help: [
        [self.commands.pls, self.commands.help, "Use **pls help** to get memes and utility commands"],
        [self.commands.code, self.commands.help, "Use **code help** to get coding problems related commands"],
        [self.commands.todo, self.commands.help, "Use **todo help** to get todo-list related commands"],
        [self.commands.bot, self.commands.help, "Use **bot help** to display parent message"],
      ],
      self.commands.code: [
        [pls, self.commands.get, "Use **pls get** and sources to get coding problems"],
        [pls, self.commands.leetcode, "Use **pls get leetcode** to get a random leetcode problem"],
        [pls, self.commands.codeforces, "Use **pls get codeforces** to get a random codeforces problem"],
        [self.commands.bot, self.commands.help, "Use **bot help** to display parent message"],
      ],
      self.commands.pls: [
        [pls, self.commands.meme, "Use **pls meme** for a r/memes"],
        [pls, self.commands.dank, "Use **pls dank** for a r/dankmemes"],
        [pls, self.commands.comic, "Use **pls comic** for a r/comics"],
        [pls, self.commands.snac, "Use **pls snac** for a r/animemes"],
        [pls, self.commands.debug, "Use **pls debug** to show debug info"],
        [self.commands.bot, self.commands.help, "Use **bot help** to display parent message"],
      ],
      self.commands.todo: [
        [pls, self.commands.todo, "To create a simple todo-list use\n**pls todo\n<target-1>\n<target-2>\n....**"],
        [pls, self.commands.done, "To create a simple done-list use\n**pls done\n<item-1>\n<item-2>\n....**"],
        [self.commands.bot, self.commands.help, "Use **bot help** to display parent message"],
      ]
    }
  
  def is_simple_command(self, prefix, cmd, message_content):
      return cmd.name == message_content.replace(prefix.name, self.EMPTY_STR).strip()

  def get_help(self, group):
    message = ""
    for item in self.GROUPS[group]:
      message += item[self.INFO_INDEX] + "\n"
    return message
    
class DiscordClient(discord.Client):
    # big-brain-coding channel id
    CHANNEL_ID = 1003624397749354506
    HELP_MSG_STRING = """
*BigBrainBot* is a discord bot made to replace warwolf.
Automatically drops daily coding problems on a predefined channel.

[Major code changes in progress]
[Commands are not guaranteed to work]
[@radcakes for excuses]\n
"""

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
                print(f"DB entry for {source_name} is present [{db[source_name]}], skipping post.")

    @write_daily_question.before_loop
    async def before_my_task(self):
        # wait until the bot logs in
        await self.wait_until_ready()

    async def send_message(self, content, message_util, delete_after=0):
      if delete_after:
        msg = await message_util.channel.send(content)
        await asyncio.sleep(delete_after)
        await msg.delete()
      else:
        await message_util.channel.send(content)
        
    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
          return
  
        message_content = message.content.lower().strip()
        multiline_message = message.content.strip()

        cmd = SimpleCommandHelper()
        commands = cmd.commands

        if "gandalf" in message_content:
          await message.channel.send("Fool of a Took!")
          return
          
        if commands.help.name in message_content:
          if cmd.is_simple_command(commands.bot, commands.help, message_content):
            content = self.HELP_MSG_STRING + cmd.get_help(commands.help)
            await self.send_message(content, message, 60)
            return
          
          for prefix in [commands.pls, commands.code, commands.todo]:
            if cmd.is_simple_command(prefix, commands.help, message_content):
              await self.send_message(cmd.get_help(prefix), message, 60)
              return
            
        if cmd.is_simple_command(commands.bot, commands.good, message_content):
            await self.send_message(":D", message)
            return

        if cmd.is_simple_command(commands.bot, commands.bad, message_content):
            await self.send_message(":(", message)  
            return
          
        if cmd.is_simple_command(commands.pls, commands.meme, message_content):
            post = self.redditUtil.get_reddit_post(RedditUtil.MEMES_STR)
            await message.channel.send(post)
            return

        if cmd.is_simple_command(commands.pls, commands.dank, message_content):
          post = self.redditUtil.get_reddit_post(RedditUtil.DANK_STR)
          await message.channel.send(post)
          return

        if cmd.is_simple_command(commands.pls, commands.snac, message_content):
          post = self.redditUtil.get_reddit_post(RedditUtil.SNAC_STR)
          await message.channel.send(post)
          return
              
        if cmd.is_simple_command(commands.pls, commands.comic, message_content):
            post = self.redditUtil.get_reddit_post(RedditUtil.COMICS_STR)
            await message.channel.send(post)
            return

        if cmd.is_simple_command(commands.pls, commands.debug, message_content):
            info = self.redditUtil.debug_info()
            print(info)
            self.print_db()
            await message.channel.send(info)
            return

        if commands.pls.name in message_content:
          if commands.get.name in message_content:
            helper = Helper()
            source_name_list = [commands.leetcode, commands.codeforces]
            for source_name in source_name_list:
              already_checked = commands.pls.name + cmd.SPACE_STR
              if cmd.is_simple_command(commands.get, source_name, message_content.replace(already_checked, cmd.EMPTY_STR)):
                index = source_name_list.index(source_name)
                source = Helper.sources[index]
                problem = helper.get_daily_problem(source)
                msg = problem['msg']
                await message.channel.send(msg)
                return
          if commands.todo.name in message_content:
            lines = message_content.splitlines()[0].split(cmd.SPACE_STR)
            msg_command = lines[0] + ' ' + lines[1]
        
            if cmd.is_simple_command(commands.pls, commands.todo, msg_command):
              targets = ""
              for todo in multiline_message.splitlines()[1:]:
                if todo == cmd.EMPTY_STR:
                  continue
                targets += "> " + todo.replace("> ", '', 1) + "\n"
                
              formatted_msg = f"""
** {date.today().strftime("%A %b %d %Y")} **
:dart: **Target**
{targets}:fire: **Done**
> ~~Make todo~~"""
              warn_msg = "*Hold to copy the above message!\nRemoving in 15 seconds...*"
              msg = await message.channel.send(formatted_msg)
              warning = await message.channel.send(warn_msg)
              await asyncio.sleep(15)
              await warning.delete()
              await msg.delete()
              return

client = DiscordClient()
try:
  client.run(os.getenv('TOKEN'))
except discord.errors.HTTPException:
  print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
  system('kill 1')
  system("python Restart.py")