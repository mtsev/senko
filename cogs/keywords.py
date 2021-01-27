import re

from discord import Guild, Member, Message, Forbidden
from discord.ext.commands import Bot, Cog, Context, group

from utils import log
from utils.database import Database


class Keywords(Cog):
    """
    IRC-style keyword highlighting for word or phrases.
    Won't highlight partial word match, only full word or phrase match.
    Highlight is represented as a DM from Senko with a jumplink.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.db = Database(bot.db)

    def _clean_mentions(self, message: str) -> str:
        # remove the ! or & in mentions
        if message:
            return re.sub(r"<@[!&]?([\d]+)>", r"<@\1>", message)
        else:
            return ""

    def _has_word(self, word: str, message: str) -> bool:
        return re.search(r"\b" + re.escape(word) + r"\b", self._clean_mentions(message), re.I)

    @Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        # log.debug(f'{member.display_name} joined {member.guild.name}')
        self.db.add_guild_member(member.guild.id, member.id)

    @Cog.listener()
    async def on_member_remove(self, member: Member) -> None:
        # log.debug(f'{member.display_name} left {member.guild.name}')
        self.db.remove_guild_member(member.guild.id, member.id)

    @Cog.listener()
    async def on_guild_join(self, guild: Guild) -> None:
        log.console(f'Joined new server {guild.name} ({guild.id})')
        self.db.add_guild(guild)

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild) -> None:
        log.console(f'Removed from server {guild.name} ({guild.id})')
        self.db.remove_guild(guild)

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        # Ignore DMs
        if message.guild is None:
            return

        # Ignore messages from Senko herself
        if message.author.id == self.bot.user.id:
            return

        # Ignore messages that look like a command
        if message.content.startswith(self.bot.command_prefix):
            return

        # Get all users and their words in guild
        words = self.db.get_guild(message.guild.id)
        for user_id in words.keys():

            # Ignore messages from the user themselves
            if message.author.id == int(user_id):
                continue

            # Check if user is in the channel that the message was sent in
            if int(user_id) not in [m.id for m in message.channel.members]:
                continue

            # Send notification if any words match in message or embed
            await self._notif_loop(user_id, words[user_id], message)
            

    async def _notif_loop(self, user_id: str, keywords: list, message: Message) -> None:
        for word in keywords:
            if self._has_word(word, message.content):
                await self._send_notification(user_id, message, message.clean_content, word)
                return
            else:
                for embed in message.embeds:
                    if self._has_word(word, embed.description):
                        await self._send_notification(user_id, message, embed.description, word)
                        return
                    elif self._has_word(word, embed.title):
                        await self._send_notification(user_id, message, embed.title, word)
                        return
                    elif embed.fields is not embed.Empty:
                        for field in embed.fields:
                            if self._has_word(word, field.name):
                                await self._send_notification(user_id, message, field.name, word)
                                return
                            elif self._has_word(word, field.value):
                                await self._send_notification(user_id, message, field.value, word)
                                return

    async def _send_notification(self, user_id: str, message: Message, quote: str, word: str) -> None:
        # Get user to send message to
        user = self.bot.get_user(int(user_id))

        # Escape backticks to avoid breaking output markdown
        quote = quote.replace("`", "'")

        try:
            # Send DM to user without formatting for push notification
            msg = await user.send(f"<{message.author.display_name}> {quote}")

            # Edit DM with nicer formatting
            await msg.edit(content = 
                f".\n**#{message.channel.name}**  {message.channel.guild}```markdown\n"
                f"<{message.author.display_name}> {quote}"
                f"```{message.jump_url}")

            # Log message to console
            log.debug(f"Notify {user.name}#{user.discriminator} on keyword '{word}'")

        except Forbidden as err:
            if err.code == 50007:
                log.debug(f"Couldn't notify user {user.name}")
            else:
                log.console(err)


    @group(aliases=['keyword', 'keywords', 'kw'])
    async def notify(self, ctx: Context) -> None:
        pass

    @notify.group(name='add', aliases=['new'])
    async def notify_add(self, ctx: Context, *args: str) -> None:
        """Add new keywords to list."""
        log.command(ctx)

        # This could potentially be a member's first time adding words.
        # Then we want to also add their guild mappings to database.
        if self.db.is_new_user(ctx.author.id):
            log.debug(f'Adding new user {ctx.author.display_name} to database')
            guilds = [g.id for g in self.bot.guilds if g.get_member(ctx.author.id) is not None]
            self.db.add_new_user(guilds, ctx.author.id)

        # Then we'll add the words for this user
        words = [self._clean_mentions(a.lower()) for a in args]
        self.db.add_words(ctx.author.id, words)
        words = self.db.get_words(ctx.author.id)
        await self._send(ctx, words)

    @notify.group(name='rem', aliases=['remove', 'del', 'delete'])
    async def notify_rem(self, ctx: Context, *args: str) -> None:
        """Remove keywords from list."""
        log.command(ctx)
        words = [self._clean_mentions(a.lower()) for a in args]
        self.db.remove_words(ctx.author.id, words)
        words = self.db.get_words(ctx.author.id)
        await self._send(ctx, words)

    @notify.group(name='clear')
    async def notify_clear(self, ctx: Context) -> None:
        """Remove all keywords."""
        log.command(ctx)
        words = self.db.get_words(ctx.author.id)
        self.db.remove_words(ctx.author.id, words)
        words = self.db.get_words(ctx.author.id)
        await self._send(ctx, words)

    @notify.group(name='list', aliases=['all'])
    async def notify_list(self, ctx: Context) -> None:
        """List all keywords."""
        log.command(ctx)
        words = self.db.get_words(ctx.author.id)
        await self._send(ctx, words)

    async def _send(self, ctx: Context, words: list) -> None:
        """Send formatted output to Discord."""
        if not words:
            message = 'You have no keywords.'
        else:
            message = 'Keywords: ' + ', '.join(sorted(words))

        try:
            await ctx.author.send(f'```{message}```')
        except Forbidden as err:
            if err.code == 50007:
                log.debug(f"Couldn't DM user {ctx.author.name}")
                await ctx.send(f"<@!{ctx.author.id}>, I couldn't send you a DM. Please go to 'Privacy Settings' for this server and allow direct messages from server members.")
            else:
                log.console(err)


def setup(bot: Bot) -> None:
    """Load cog into bot."""
    bot.add_cog(Keywords(bot))
