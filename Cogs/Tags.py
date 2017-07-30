import asyncio
import discord
import time
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import FuzzySearch
from   Cogs import Message

class Tags:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(pass_context=True)
	async def settagrole(self, ctx, *, role : str = None):
		"""Sets the required role ID to add/remove tags (admin only)."""
		
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			self.settings.setServerStat(ctx.message.guild, "RequiredTagRole", "")
			msg = 'Add/remove tags now *admin-only*.'
			await ctx.message.channel.send(msg)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.message.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "RequiredTagRole", role.id)

		msg = 'Role required for add/remove tags set to **{}**.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)
		
	
	@settagrole.error
	async def settagrole_error(self, error, ctx):
		# do stuff
		msg = 'settagrole Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def addtag(self, ctx, name : str = None, *, tag : str = None):
		"""Add a tag to the tag list."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredTagRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if str(role.id) == str(requiredRole):
					hasPerms = True
			if not hasPerms:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
				
		# Passed role requirements!
		if not (name or tag):
			msg = 'Usage: `{}addtag "[tag name]" [tag]`'.format(ctx.prefix)
			await channel.send(msg)
			return

		tagList = self.settings.getServerStat(server, "Tags")
		if not tagList:
			tagList = []
		
		found = False
		currentTime = int(time.time())	
		for atag in tagList:
			if atag['Name'].lower() == name.lower():
				# The tag exists!
				msg = '*{}* updated!'.format(name)
				atag['URL'] = tag
				atag['UpdatedBy'] = DisplayName.name(author)
				atag['UpdatedID'] = author.id
				atag['Updated'] = currentTime
				found = True
		if not found:	
			tagList.append({"Name" : name, "URL" : tag, "CreatedBy" : DisplayName.name(author), "CreatedID": author.id, "Created" : currentTime})
			msg = '*{}* added to tag list!'.format(name)
		
		self.settings.setServerStat(server, "Tags", tagList)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def removetag(self, ctx, *, name : str = None):
		"""Remove a tag from the tag list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredTagRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if str(role.id) == str(requiredRole):
					hasPerms = True
			if not hasPerms:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		
		if name == None:
			msg = 'Usage: `{}removetag "[tag name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		tagList = self.settings.getServerStat(server, "Tags")
		if not tagList or tagList == []:
			msg = 'No tags in list!  You can add some with the `{}addtag "[tag name]" [tag]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return

		for atag in tagList:
			if atag['Name'].lower() == name.lower():
				tagList.remove(atag)
				self.settings.setServerStat(server, "Tags", tagList)
				msg = '*{}* removed from tag list!'.format(name)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return

		msg = '*{}* not found in tag list!'.format(name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)


	@commands.command(pass_context=True)
	async def tag(self, ctx, *, name : str = None):
		"""Retrieve a tag from the tag list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		if not name:
			msg = 'Usage: `{}tag "[tag name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		tagList = self.settings.getServerStat(server, "Tags")
		if not tagList or tagList == []:
			msg = 'No tags in list!  You can add some with the `{}addtag "[tag name]" [tag]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return

		for atag in tagList:
			if atag['Name'].lower() == name.lower():
				msg = '**{}:**\n{}'.format(atag['Name'], atag['URL'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return
				
		msg = 'Tag "*{}*" not found!'.format(name)
		
		# No tag - let's fuzzy search
		potentialList = FuzzySearch.search(name, tagList, 'Name')
		if len(potentialList):
			msg+='\n\nDid you maybe mean one of the following?\n```\n'
			for pot in potentialList:
				msg+='{}\n'.format(pot['Item']['Name'])
			msg+='```'
		
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)		

	@commands.command(pass_context=True)
	async def taginfo(self, ctx, *, name : str = None):
		"""Displays info about a tag from the tag list."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		if not name:
			msg = 'Usage: `{}taginfo "[tag name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		tagList = self.settings.getServerStat(server, "Tags")
		if not tagList or tagList == []:
			msg = 'No tags in list!  You can add some with the `{}addtag "[tag name]" [tag]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return

		for atag in tagList:
			if atag['Name'].lower() == name.lower():
				currentTime = int(time.time())
				msg = '**{}:**'.format(atag['Name'])
				try:
					memID = DisplayName.memberForID(atag['CreatedID'], server)
				except KeyError as e:
					memID = None
				if memID:
					msg = '{}\nCreated By: *{}*'.format(msg, DisplayName.name(memID))
				else:
					try:	
						msg = '{}\nCreated By: *{}*'.format(msg, atag['CreatedBy'])
					except KeyError as e:
						msg = '{}\nCreated By: `UNKNOWN`'.format(msg)
				try:
					createdTime = int(atag['Created'])
					timeString  = ReadableTime.getReadableTimeBetween(createdTime, currentTime)
					msg = '{}\nCreated : *{}* ago'.format(msg, timeString)
				except KeyError as e:
					pass
				try:
					msg = '{}\nUpdated By: *{}*'.format(msg, atag['UpdatedBy'])
				except KeyError as e:
					pass
				try:
					createdTime = atag['Updated']
					createdTime = int(createdTime)
					timeString  = ReadableTime.getReadableTimeBetween(createdTime, currentTime)
					msg = '{}\nUpdated : *{}* ago'.format(msg, timeString)
				except:
					pass
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return
				
		msg = 'Tag "*{}*" not found!'.format(name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)

	@commands.command(pass_context=True)
	async def tags(self, ctx):
		"""List all tags in the tags list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		argList = ctx.message.content.split()

		if len(argList) > 1:
			extraArgs = ' '.join(argList[1:len(argList)])
			# We have a random attempt at a passed variable - Thanks Sydney!
			msg = 'You passed *{}* to this command - are you sure you didn\'t mean `{}tag {}`?'.format(extraArgs, ctx.prefix, extraArgs)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return
		
		tagList = self.settings.getServerStat(server, "Tags")
		if tagList == None or tagList == []:
			msg = 'No tags in list!  You can add some with the `{}addtag "[tag name]" [tag]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return
			
		# Sort by tag name
		tagList = sorted(tagList, key=itemgetter('Name'))
		tagText = "Current Tags:\n\n"
		for atag in tagList:
			tagText = '{}*{}*, '.format(tagText, atag['Name'])

		# Speak the tag list while cutting off the end ", "
		# Check for suppress
		if suppress:
			tagText = Nullify.clean(tagText)
		#await channel.send(tagText[:-2])
		await Message.say(self.bot, tagText[:-2], ctx.channel, ctx.author, 1)


	@commands.command(pass_context=True)
	async def tagrole(self, ctx):
		"""Lists the required role to add tags."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		role = self.settings.getServerStat(ctx.message.guild, "RequiredTagRole")
		if role == None or role == "":
			msg = '**Only Admins** can add tags.'.format(ctx)
			await ctx.channel.send(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.guild.roles:
				if str(arole.id) == str(role):
					found = True
					vowels = "aeiou"
					if arole.name[:1].lower() in vowels:
						msg = 'You need to be an **{}** to add tags.'.format(arole.name)
					else:
						msg = 'You need to be a **{}** to add tags.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
