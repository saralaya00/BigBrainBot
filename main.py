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
  
  class Commands(Enum):
    (
      pls, meme, dank, comic, snac, debug, #6
      misc, hello, todo, done, todopc, donepc, #6
      get, leetcode, sqleetcode, codeforces,  #4
      good, bad, #2
      help, bot, code, #3
    ) = range(21)
    
  def __init__(self):
    self.commands = self.Commands
    pls = self.commands.pls

    self.GROUPS = {
      self.commands.help: [
        [self.commands.pls, self.commands.help, "Use **pls help** to get memes and utility commands"],
        [self.commands.code, self.commands.help, "Use **code help** to get coding problems related commands"],
        [self.commands.misc, self.commands.help, "Use **misc help** to get miscellaneous commands"],
        [self.commands.bot, self.commands.help, "Use **bot help** to display parent message"],
      ],
      self.commands.code: [
        [pls, self.commands.get, self.commands.leetcode, "Use **pls get leetcode** to get a random leetcode problem"],
        [pls, self.commands.get, self.commands.sqleetcode, "Use **pls get sqleetcode** to get a random leetcode sql problem"],
        [pls, self.commands.get, self.commands.codeforces, "Use **pls get codeforces** to get a random codeforces problem"],
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
      self.commands.misc: [
        [pls, self.commands.hello, "Say hello to a user"],
        [pls, self.commands.todo, "To create a simple todo-list use\n**pls todo\n<target-1>\n<target-2>\n...**"],
        [pls, self.commands.done, "To create a simple done-list use\n**pls done\n<item-1>\n<item-2>\n...**"],
        [pls, self.commands.todopc, "Same as todo-list, but returns a raw format for PC users"],
        [pls, self.commands.donepc, "Same as done-list, but returns a raw format for PC users"],
        [self.commands.bot, self.commands.help, "Use **bot help** to display parent message"],
      ]
    }
  
  def is_simple_command(self, prefix, cmd, message_content):
      return cmd.name == message_content.replace(prefix.name, self.EMPTY_STR).strip()

  def get_help(self, group):
    message = ""
    for item in self.GROUPS[group]:
      cmds = " ".join([cmd.name for cmd in item[:-1]])
      message += f"`{cmds}`\n"
      message += item[-1] + "\n"
    return message
    
class DiscordClient(discord.Client):
    # big-brain-coding channel id
    CHANNEL_ID = 1003624397749354506
    HELP_MSG_STRING = """
*BigBrainBot* is a General Purpose Useless Toy (discord bot) made to replace warwolf.
Automatically drops daily coding problems on a predefined channel.

[Major code changes in progress]
[Commands are not guaranteed to work]
[@radcakes for excuses]\n
"""
    TODO_format = f"""
** {date.today().strftime("%A %b %d %Y")} **
>>> :dart: **Target**
$targets:fire: **Done**
$done"""

    DONE_format = f"""
** {date.today().strftime("%A %b %d %Y")} **
>>> :100: **Things Done**
$targets"""

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

    async def send_messages(self, contents, message_util, delete_after=0):
      sent_msg = []
      for content in contents:
        msg = await message_util.channel.send(content)
        sent_msg.append(msg)
        
      if delete_after:
        await asyncio.sleep(delete_after)
        while sent_msg:
          msg = sent_msg.pop()
          await msg.delete()
        
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
          
        # Thor: Hey, let’s do “Get Help.” Come on, you love it.
        # Loki: I hate it.
        # Thor: It’s great. It works every time.
        # Loki: It’s humiliating.
        # Thor: We’re doing it.
        if commands.help.name in message_content:
          if cmd.is_simple_command(commands.bot, commands.help, message_content):
            content = self.HELP_MSG_STRING + cmd.get_help(commands.help)
            await self.send_messages([content], message, 60)
            return
          
          for prefix in [commands.pls, commands.code, commands.misc]:
            if cmd.is_simple_command(prefix, commands.help, message_content):
              await self.send_messages([cmd.get_help(prefix)], message, 60)
              return
            
        if cmd.is_simple_command(commands.bot, commands.good, message_content):
            await self.send_messages([":D"], message)
            return

        if cmd.is_simple_command(commands.bot, commands.bad, message_content):
          await self.send_messages([":("], message)
          return

        # Get mems from reddit
        reddit_meta = {
          commands.meme: RedditUtil.MEMES_STR,
          commands.dank: RedditUtil.DANK_STR,
          commands.snac: RedditUtil.SNAC_STR,
          commands.comic: RedditUtil.COMICS_STR,
        }

        for type in [commands.meme, commands.dank, commands.snac, commands.comic]:
          if cmd.is_simple_command(commands.pls, type, message_content):
            post = self.redditUtil.get_reddit_post(reddit_meta[type])
            await self.send_messages([post], message)
            return
            
        if cmd.is_simple_command(commands.pls, commands.debug, message_content):
            info = self.redditUtil.debug_info()
            print(info)
            self.print_db()
            await message.channel.send(info)
            return

        if commands.pls.name in message_content:
          # Custom problem questions
          if commands.get.name in message_content:
            helper = Helper()
            source_name_list = [commands.leetcode, commands.sqleetcode, commands.codeforces]
            for source_name in source_name_list:
              already_checked = commands.pls.name + cmd.SPACE_STR
              if cmd.is_simple_command(commands.get, source_name, message_content.replace(already_checked, cmd.EMPTY_STR)):
                index = source_name_list.index(source_name)
                source = Helper.sources[index]
                problem = helper.get_daily_problem(source)
                msg = problem['msg']
                await message.channel.send(msg)
                return
                
          # todo generators 
          if commands.todo.name in message_content or commands.done.name in message_content:
            first_line = message_content.splitlines()[0].split(cmd.SPACE_STR)
            msg_command = first_line[0] + ' ' + first_line[1]
            
            warn_msg = "*Hold to copy the above message!\nRemoving in 15 seconds...*"
            templates = {
              commands.todo: self.TODO_format,
              commands.done: self.DONE_format,
              commands.todopc: self.TODO_format,
              commands.donepc: self.DONE_format,
            }
            
            for type in [commands.todo, commands.done]:
              if cmd.is_simple_command(commands.pls, type, msg_command):
                todo_msg = self.create_todo(multiline_message.splitlines()[1:], templates[type], False)
                await self.send_messages([todo_msg, warn_msg], message, 15)
                return
              
            for type in [commands.todopc, commands.donepc]:
              if cmd.is_simple_command(commands.pls, type, msg_command):
                todo_msg = self.create_todo(multiline_message.splitlines()[1:], templates[type], True)
                await self.send_messages([todo_msg, warn_msg], message, 15)
                return
              

    def create_todo(self, todos, msg_template, return_rawfmt=False):
      default_todo = "Make todo"
      quote_fmt = "> "
      blquote_fmt = ">>> "
      targets = ""
      for todo in todos:
        if todo == SimpleCommandHelper.EMPTY_STR:
          continue
        if todo[:2] == quote_fmt or todo[:4] == blquote_fmt:
          todo = todo.replace(blquote_fmt, SimpleCommandHelper.EMPTY_STR, 1)
          todo = todo.replace(quote_fmt, SimpleCommandHelper.EMPTY_STR, 1)
        targets += todo + "\n"

      todolist = msg_template
      if todos:
        todolist = todolist.replace("$targets", targets)
        todolist = todolist.replace("$done", "~~" + default_todo + "~~\n")
        # todolist = todolist.replace("$targets", quote_fmt + targets)
        # todolist = todolist.replace("$done", quote_fmt + "~~" + default_todo + "~~\n")
      else:
        todolist = todolist.replace("$targets", default_todo + "\n")
        todolist = todolist.replace("$done", "...\n")
        # todolist = todolist.replace("$targets", quote_fmt + default_todo + "\n")
        # todolist = todolist.replace("$done", quote_fmt + "...\n")
        
      if return_rawfmt:
        return "```" + todolist + "\n```"
      return todolist
      
client = DiscordClient()
try:
  client.run(os.getenv('TOKEN'))
except discord.errors.HTTPException:
  print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
  system('kill 1')
  system("python Restart.py")