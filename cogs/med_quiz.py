from discord.ext import commands
import discord
import asyncpg
import asyncio
import random

MAX_POINTS = 100
TIMEOUT = 25

class Quiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._db = bot.db
        self.in_play = False
        self.prepare_db.start()
        self._current = []

    @tasks.loop(count=1)
    async def prepare_db(self):
        await self._db.execute("""CREATE TABLE IF NOT EXISTS quiz_config (id SERIAL PRIMARY KEY, name TEXT, description TEXT);
        CREATE TABLE IF NOT EXISTS questions (id SERIAL PRIMARY KEY, quiz_id INTEGER, question TEXT, option1 TEXT, option2 TEXT, option3 TEXT, option4 TEXT, correct INTEGER);""")
        self.ids = []
        records = self._db.fetch("SELECT * FROM quiz_config")
        for record in records:
            self.ids.append(record['id'])
        print("================\nMed Quiz Cog loaded")

    @prepare_db.before_loop
    async def before_prepare_db(self):
        await self.bot.wait_until_ready()

    @commands.command(name="load")
    @commands.guild_only()
    async def _load(self, ctx, *, desc=None):
        """Load a quiz from a CSV file"""
        if not ctx.message.attachments or not ctx.message.attachments[0].filename.endswith('.csv'):
            return await ctx.send("Please attach a .csv file to load questions from.")
        if len(ctx.message.attachments) > 1:
            return await ctx.send("Please attach a single file.")
        data = await ctx.message.attachments[0].read().split('\n')[1:]
        records = [record.split(',') for record in data]
        async with self._db.acquire() as conn:
            id = await conn.fetchval("INSERT INTO quiz_config (name, description) VALUES ($1, $2) RETURNING id", ctx.message.attachments[0].filename[:-4], desc)
            for record in records:
                try:
                    await self._db.execute("INSERT INTO questions (quiz_id, question, correct, option1, option2, option3, option4) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                            id, record[0], int(record[5]), record[1], record[2], record[3], record[4])
                except:
                    await self._db.execute("DELETE FROM quiz_config WHERE id = $1", id)
                    await self._db.execute("DELETE FROM questions WHERE quiz_id = $1", id)
                    return await ctx.send("Something went wrong while processing your file. Please try again.")
        self.ids.append(id)
        await ctx.send(f"Loaded quiz into database with id **{id}**. Please make note of this as it is needed while starting the quiz.")

    @commands.command(name="start")
    @commands.guild_only()
    async def _start(self, ctx, id, score_type='static'):
        """Starts the quiz with the specified ID. It is recommended to do this is a channel where members don't have 'Add reactions' permissions"""
        if self.in_play:
            return await ctx.send("A quiz is already in progress")
        try:
            if int(id) not in self.ids:
                return await ctx.send("Quiz with this ID does not exist.")
        except ValueError:
            return await ctx.send("Please enter a valid number for ID.")
        if score_type.lower() not in ['static', 'dynamic']:
            return await ctx.send("Specify a valid scoring type (static/dynamic)")

        quiz_data = await self._db.fetchrow("SELECT * FROM quiz_config WHERE id = $1", id)
        name = quiz_data['name']
        desc = quiz_data['description'] or "\u200b"
        self.questions = []
        ques_records = await self._db.fetch("SELECT * FROM questions WHERE quiz_id = $1", id)
        for record in ques_records:
            self.questions.append({
                'question' : record['question'],
                '1' : record['option1'],
                '2' : record['option2'],
                '3' : record['option3'],
                '4' : record['option4'],
                'Correct' : record['correct']})
        random.shuffle(self.questions)
        await ctx.send("Questions loaded. Starting in 5 seconds", embed=discord.Embed(title=name, description=desc, colour=discord.Colour.blurple()))
        self.in_play = True
        self._lb = dict()
        await asyncio.sleep(5)
        for num, question in enumerate(self.questions, 1):
            # If this loop is interrupted, big F
            reactions = []
            self._score = MAX_POINTS
            embed = discord.Embed(title=f"Question {num}:", description=question['question'], colour=discord.Colour.green())
            if question['1'] != '':
                embed.add_field(name="1\N{variation selector-16}\N{combining enclosing keycap}", value=question['1'])
                reactions.append("1\N{variation selector-16}\N{combining enclosing keycap}")
            if question['2'] != '':
                embed.add_field(name="2\N{variation selector-16}\N{combining enclosing keycap}", value=question['2'])
                reactions.append("2\N{variation selector-16}\N{combining enclosing keycap}")
            if question['3'] != ''
                embed.add_field(name="3\N{variation selector-16}\N{combining enclosing keycap}", value=question['3'])
                reactions.append("3\N{variation selector-16}\N{combining enclosing keycap}")
            if question['4'] != '':
                embed.add_field(name="4\N{variation selector-16}\N{combining enclosing keycap}", value=question['4'])
                reactions.append("4\N{variation selector-16}\N{combining enclosing keycap}")
            msg = await ctx.send(embed=embed)
            self._current = [msg.id, question['Correct'], []]
            for reaction in reactions:
                await msg.add_reaction(reaction)
            for _ in range(TIMEOUT):
                await asyncio.sleep(1)
                if score_type.lower() == 'dynamic':
                    self._score -= MAX_POINTS / TIMEOUT
            # Time up here
            time_up_text = f"""**Time up!**\nThe answers of the following members have been recorded:

            {chr(10).join([ctx.guild.get_member(member_id).mention for member_id in self._current[2]])}"""
            self._current = []
            await msg.edit(content=time_up_text, embed=discord.Embed(title=f"Question {num}:", description=f"{question['question']}\n\n:white_check_mark: {question['correct']}", colour=discord.Colour.red()))
            await msg.clear_reactions()

        await self._publish(ctx)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not self._current:
            # time up, or not in play
            return
        if not payload.message_id == self._current[0] or not self.in_play:
            # wrong message, or not in play
            return
        if payload.user_id in self._current[2]:
            # already answered
            await self.bot.get_channel(payload.channel_id).get_message(payload.message_id).remove_reaction(str(reaction.emoji), self.bot.get_user(payload.user_id))
            return
        message_dict = {
                "1\N{variation selector-16}\N{combining enclosing keycap}" : 1,
                "2\N{variation selector-16}\N{combining enclosing keycap}" : 2,
                "3\N{variation selector-16}\N{combining enclosing keycap}" : 3,
                "4\N{variation selector-16}\N{combining enclosing keycap}" : 4}
        if message_dict.get(str(payload.emoji)) == self._current[1] and payload.user_id != self.bot.user.id:
            # answered in time, and got it right
            self._lb[payload.user_id] = self._lb.get(payload.user_id, 0) + self._score
        if not payload.user_id == self.bot.user.id:
            # in all cases, except the bot's default reaction
            await self.bot.get_channel(payload.channel_id).get_message(payload.message_id).remove_reaction(str(reaction.emoji), self.bot.get_user(payload.user_id))
            self._current[2].append(payload.user_id)

    async def _publish(self, ctx):
        self._current = []
        self.in_play = False
        await ctx.send("Quiz concluded. Preparing results... (If this message is unexpected or premature, the bot has suffered downtime. Apologies for the inconvenience")
        desc = '\n'.join([f"{self.bot.get_user(user_id).mention}: {score}" for user_id, score in sorted([(user_id, score) for user_id, score in self._lb.items()], key=lambda x: x[1])])
        embed = discord.Embed(title="Final results:", description = desc, colour=discord.Colour.blurple())
        # TODO embellish embeds
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Quiz(bot))
