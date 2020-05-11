import re

from discord import Message
from discord.ext.commands import *

class Database:
    def __init__(self, wordsfile):
        self.file = wordsfile
        with open(self.file) as fh:
            self.words = fh.read().splitlines()

    def add_word(self, word):
        if word not in self.words:
            self.words.append(word)
            self.update()
            return True
        return False

    def del_word(self, word):
        if word in self.words:
            self.words.remove(word)
            self.update()
            return True
        return False

    def update(self):
        with open(self.file, 'w') as fh:
            fh.write("\n".join(self.words))


class Keywords(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.keywords = Database('./words.txt')

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        
        # Send a DM if keyword is mentioned. Currently only for OWNER.
        user = self.bot.get_user(self.bot.config['owner'])
        assert user is not None
        if message.author != user and message.guild is not None:
            for word in self.keywords.words:
                if re.search("(^|\W)" + re.escape(word) + "($|\W)", message.content, re.I):

                    # Ignore keyword if it is nick in IRC bot
                    if f"<{word.lower()}>" in message.content.lower():
                        continue

                    # Escape backticks to avoid breaking output markdown
                    quote = message.clean_content.replace("`", "'")
                    
                    await user.send(
                            f".\n**#{message.channel.name}**  {message.channel.guild}```markdown\n"
                            f"<{message.author.display_name}> {quote}"
                            f"```{message.jump_url}")
                    break

    """
    IRC-style keyword highlighting for word or phrases.
    Will not highlight partial match, only full word or phrase match.
    Highlight is represented as a DM from Senko with a jumplink.
    Currently only OWNER is permitted to use this command.
    """
    @command()
    async def notify(self, ctx: Context, cmd: str, *args) -> None:

        # Currently only for OWNER.
        user = self.bot.get_user(self.bot.config['owner'])
        assert user is not None
        if ctx.author != user:
            return

        message = None

        # Add a keyword to list
        if cmd == "add" and len(args) > 0:
            added = []
            for a in args:
                if self.keywords.add_word(a.lower()):
                    added.append(a.lower())
            if len(added) > 0:
                message = "Added: " + ", ".join(added)
            else:
                message = "No keywords added."

        # Remove a keyword from list
        elif cmd == "rem" and len(args) > 0:
            removed = []
            for a in args:
                if self.keywords.del_word(a.lower()):
                    removed.append(a.lower())
            if len(removed) > 0:
                message = "Removed: " + ", ".join(removed)
            else:
                message = "No keywords removed."

        # Remove all keywords from list
        if cmd == "clear":
            old_words = self.keywords.words.copy()
            for w in old_words:
                self.keywords.del_word(w)
            if len(old_words) > 0:
                message = "Removed: " + ", ".join(old_words)
            else:
                message = "No keywords to remove."

        # Print out keywords list
        elif len(self.keywords.words) == 0:
            message = "You have no keywords."
        elif cmd == "list":
            message = "Keywords: " + ", ".join(self.keywords.words)

        if message is not None:
            await user.send(f'```{message}```')


def setup(bot: Bot) -> None:
    bot.add_cog(Keywords(bot))
