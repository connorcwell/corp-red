import asyncio
import discord
import time
import parsedatetime
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import CheckRoles

# This is the admin module.  It holds the admin-only commands
# Everything here *requires* that you're an admin

class Admin:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions").lower() == "yes":
			return Nullify.clean(msg)
		else:
			return msg

	async def message_edit(self, before_message, message):
		# Pipe the edit into our message func to respond if needed
		return await self.message(message)
		
	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		ignore = False
		delete = False
		res    = None
		# Check if user is muted
		isMute = self.settings.getUserStat(message.author, message.guild, "Muted")

		# Check for admin status
		isAdmin = message.author.permissions_in(message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(message.guild, "AdminArray")
			for role in message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True

		if isMute.lower() == "yes":
			ignore = True
			delete = True
			checkTime = self.settings.getUserStat(message.author, message.guild, "Cooldown")
			if checkTime:
				checkTime = int(checkTime)
			currentTime = int(time.time())
			
			# Build our PM
			if checkTime:
				# We have a cooldown
				checkRead = ReadableTime.getReadableTimeBetween(currentTime, checkTime)
				res = 'You are currently **Muted**.  You need to wait *{}* before sending messages in *{}*.'.format(checkRead, self.suppressed(message.guild, message.guild.name))
			else:
				# No cooldown - muted indefinitely
				res = 'You are still **Muted** in *{}* and cannot send messages until you are **Unmuted**.'.format(self.suppressed(message.guild, message.guild.name))

			if checkTime and currentTime >= checkTime:
				# We have passed the check time
				ignore = False
				delete = False
				res    = None
				self.settings.setUserStat(message.author, message.guild, "Cooldown", None)
				self.settings.setUserStat(message.author, message.guild, "Muted", "No")
			
		
		ignoreList = self.settings.getServerStat(message.guild, "IgnoredUsers")
		if ignoreList:
			for user in ignoreList:
				if not isAdmin and str(message.author.id) == str(user["ID"]):
					# Found our user - ignored
					ignore = True

		adminLock = self.settings.getServerStat(message.guild, "AdminLock")
		if not isAdmin and adminLock.lower() == "yes":
			ignore = True

		if isAdmin:
			ignore = False
			delete = False

		# Get Owner and OwnerLock
		try:
			ownerLock = self.settings.serverDict['OwnerLock']
		except KeyError:
			ownerLock = "No"
		owner = self.settings.isOwner(message.author)
		# Check if owner exists - and we're in OwnerLock
		if (not owner) and ownerLock.lower() == "yes":
			# Not the owner - ignore
			ignore = True
				
		if not isAdmin and res:
			# We have a response - PM it
			await message.author.send(res)
		
		return { 'Ignore' : ignore, 'Delete' : delete}

	
	@commands.command(pass_context=True)
	async def defaultchannel(self, ctx):
		"""Lists the server's default channel, whether custom or not."""
		# Returns the default channel for the server
		targetChan = ctx.guild.default_channel
		targetChanID = self.settings.getServerStat(ctx.guild, "DefaultChannel")
		if len(str(targetChanID)):
			# We *should* have a channel
			tChan = self.bot.get_channel(int(targetChanID))
			if tChan:
				# We *do* have one
				targetChan = tChan
		if targetChan.id == ctx.guild.default_channel.id:
			# We're using the server default
			msg = "The default channel is the server's original default: **{}**".format(targetChan.name)
		else:
			# We have a custom channel
			msg = "The default channel is set to **{}**.".format(targetChan.name)
		await ctx.channel.send(msg)
		
	
	@commands.command(pass_context=True)
	async def setdefaultchannel(self, ctx, *, channel: discord.TextChannel = None):
		"""Sets a replacement default channel for bot messages (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		if channel == None:
			self.settings.setServerStat(ctx.message.guild, "DefaultChannel", "")
			msg = 'Default channel has been returned to **{}**.'.format(ctx.guild.default_channel.name)
			await ctx.message.channel.send(msg)
			return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "DefaultChannel", channel.id)

		msg = 'Default channel set to **{}**.'.format(channel.name)
		await ctx.message.channel.send(msg)
		
	
	@setdefaultchannel.error
	async def setdefaultchannel_error(self, error, ctx):
		# do stuff
		msg = 'setdefaultchannel Error: {}'.format(error)
		await ctx.channel.send(msg)
	

	@commands.command(pass_context=True)
	async def setmadlibschannel(self, ctx, *, channel: discord.TextChannel = None):
		"""Sets the channel for MadLibs (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		if channel == None:
			self.settings.setServerStat(ctx.message.guild, "MadLibsChannel", "")
			msg = 'MadLibs works in *any channel* now.'
			await ctx.message.channel.send(msg)
			return

		if type(channel) is str:
			try:
				role = discord.utils.get(message.guild.channels, name=role)
			except:
				print("That channel does not exist")
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "MadLibsChannel", channel.id)

		msg = 'MadLibs channel set to **{}**.'.format(channel.name)
		await ctx.message.channel.send(msg)
		
	
	@setmadlibschannel.error
	async def setmadlibschannel_error(self, error, ctx):
		# do stuff
		msg = 'setmadlibschannel Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def setxp(self, ctx, *, member = None, xpAmount : int = None):
		"""Sets an absolute value for the member's xp (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		usage = 'Usage: `{}setxp [member] [amount]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		if member == None:
			await ctx.message.channel.send(usage)
			return

		if xpAmount == None:
			# Check if we have trailing xp
			nameCheck = DisplayName.checkNameForInt(member, server)
			if not nameCheck:
				await ctx.message.channel.send(usage)
				return
			if not nameCheck["Member"]:
				msg = 'I couldn\'t find *{}* on the server.'.format(member)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return
			member   = nameCheck["Member"]
			xpAmount = nameCheck["Int"]
			
		# Check for formatting issues
		if xpAmount == None:
			# Still no xp...
			await channel.send(usage)
			return

		self.settings.setUserStat(member, server, "XP", xpAmount)
		msg = '*{}\'s* xp was set to *{}!*'.format(DisplayName.name(member), xpAmount)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)
		await CheckRoles.checkroles(member, channel, self.settings, self.bot)


	@setxp.error
	async def setxp_error(self, error, ctx):
		# do stuff
		msg = 'setxp Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def setxpreserve(self, ctx, *, member = None, xpAmount : int = None):
		"""Set's an absolute value for the member's xp reserve (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		usage = 'Usage: `{}setxpreserve [member] [amount]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		if member == None:
			await ctx.message.channel.send(usage)
			return
		
		if xpAmount == None:
			# Check if we have trailing xp
			nameCheck = DisplayName.checkNameForInt(member, server)
			if not nameCheck:
				await ctx.message.channel.send(usage)
				return
			if not nameCheck["Member"]:
				msg = 'I couldn\'t find *{}* on the server.'.format(member)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return
			member   = nameCheck["Member"]
			xpAmount = nameCheck["Int"]
			
		# Check for formatting issues
		if xpAmount == None:
			# Still no xp
			await channel.send(usage)
			return

		self.settings.setUserStat(member, server, "XPReserve", xpAmount)
		msg = '*{}\'s* XPReserve was set to *{}*!'.format(DisplayName.name(member), xpAmount)
		await channel.send(msg)


	@setxpreserve.error
	async def setxpreserve_error(self, error, ctx):
		# do stuff
		msg = 'setxpreserve Error: {}'.format(error)
		await ctx.channel.send(msg)
	
	@commands.command(pass_context=True)
	async def setdefaultrole(self, ctx, *, role : str = None):
		"""Sets the default role or position for auto-role assignment."""
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		if role is None:
			# Disable auto-role and set default to none
			self.settings.setServerStat(server, "DefaultRole", "")
			msg = 'Auto-role management now **disabled**.'
			await channel.send(msg)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			roleName = role
			role = DisplayName.roleForName(roleName, server)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		self.settings.setServerStat(server, "DefaultRole", role.id)
		rolename = role.name
		# Check for suppress
		if suppress:
			rolename = Nullify.clean(rolename)
		await channel.send('Default role set to **{}**!'.format(rolename))


	@setdefaultrole.error
	async def setdefaultrole_error(self, error, ctx):
		# do stuff
		msg = 'setdefaultrole Error: {}'.format(error)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def addxprole(self, ctx, *, role = None, xp : int = None):
		"""Adds a new role to the xp promotion/demotion system (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		usage = 'Usage: `{}addxprole [role] [required xp]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return
		if xp == None:
			# Either xp wasn't set - or it's the last section
			if type(role) is str:
				if role == "everyone":
					role = "@everyone"
				# It' a string - the hope continues
				roleCheck = DisplayName.checkRoleForInt(role, server)
				if not roleCheck:
					await ctx.message.channel.send(usage)
					return
				if not roleCheck["Role"]:
					msg = 'I couldn\'t find *{}* on the server.'.format(role)
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
					await ctx.message.channel.send(msg)
					return
				role = roleCheck["Role"]
				xp   = roleCheck["Int"]

		if xp == None:
			await channel.send(usage)
			return
		if not type(xp) is int:
			await channel.send(usage)
			return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(server, "PromotionArray")
		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(aRole['ID']) == str(role.id):
				# We found it - throw an error message and return
				msg = '**{}** is already in the list.  Required xp: *{}*'.format(role.name, aRole['XP'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name, 'XP' : xp })
		self.settings.setServerStat(server, "PromotionArray", promoArray)

		msg = '**{}** added to list.  Required xp: *{}*'.format(role.name, xp)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)
		return

	@addxprole.error
	async def addxprole_error(self, error, ctx):
		# do stuff
		msg = 'addxprole Error: {}'.format(error)
		await ctx.channel.send(msg)
		
	@commands.command(pass_context=True)
	async def removexprole(self, ctx, *, role = None):
		"""Removes a role from the xp promotion/demotion system (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		usage = 'Usage: `{}removexprole [role]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			await channel.send(usage)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			# It' a string - the hope continues
			# Let's clear out by name first - then by role id
			promoArray = self.settings.getServerStat(server, "PromotionArray")

			for aRole in promoArray:
				# Get the role that corresponds to the name
				if aRole['Name'].lower() == role.lower():
					# We found it - let's remove it
					promoArray.remove(aRole)
					self.settings.setServerStat(server, "PromotionArray", promoArray)
					msg = '**{}** removed successfully.'.format(aRole['Name'])
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
					await channel.send(msg)
					return
			# At this point - no name
			# Let's see if it's a role that's had a name change


			roleCheck = DisplayName.roleForName(role, server)
			if roleCheck:
				# We got a role
				# If we're here - then the role is an actual role
				promoArray = self.settings.getServerStat(server, "PromotionArray")

				for aRole in promoArray:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(roleCheck.id):
						# We found it - let's remove it
						promoArray.remove(aRole)
						self.settings.setServerStat(server, "PromotionArray", promoArray)
						msg = '**{}** removed successfully.'.format(aRole['Name'])
						# Check for suppress
						if suppress:
							msg = Nullify.clean(msg)
						await channel.send(msg)
						return
				
			# If we made it this far - then we didn't find it
			msg = '{} not found in list.'.format(roleCheck.name)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return

		# If we're here - then the role is an actual role - I think?
		promoArray = self.settings.getServerStat(server, "PromotionArray")

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(aRole['ID']) == str(role.id):
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(server, "PromotionArray", promoArray)
				msg = '**{}** removed successfully.'.format(aRole['Name'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return

		# If we made it this far - then we didn't find it
		msg = '{} not found in list.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)

	@removexprole.error
	async def removexprole_error(self, error, ctx):
		# do stuff
		msg = 'removexprole Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def prunexproles(self, ctx):
		"""Removes any roles from the xp promotion/demotion system that are no longer on the server (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		# Get the array
		promoArray = self.settings.getServerStat(server, "PromotionArray")
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
		
		removed = 0
		for arole in promoSorted:
			# Get current role name based on id
			foundRole = False
			for role in server.roles:
				if str(role.id) == str(arole['ID']):
					# We found it
					foundRole = True
			if not foundRole:
				promoArray.remove(arole)
				removed += 1

		msg = 'Removed *{}* orphaned roles.'.format(removed)
		await ctx.message.channel.send(msg)
		

	@commands.command(pass_context=True)
	async def setxprole(self, ctx, *, role : str = None):
		"""Sets the required role ID to give xp, gamble, or feed the bot (admin only)."""
		
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
			self.settings.setServerStat(ctx.message.guild, "RequiredXPRole", "")
			msg = 'Giving xp, gambling, and feeding the bot now available to *everyone*.'
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
		self.settings.setServerStat(ctx.message.guild, "RequiredXPRole", role.id)

		msg = 'Role required to give xp, gamble, or feed the bot set to **{}**.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)
		
	
	@setxprole.error
	async def xprole_error(self, error, ctx):
		# do stuff
		msg = 'xprole Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def xprole(self, ctx):
		"""Lists the required role to give xp, gamble, or feed the bot."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		role = self.settings.getServerStat(ctx.message.guild, "RequiredXPRole")
		if role == None or role == "":
			msg = '**Everyone** can give xp, gamble, and feed the bot.'
			await ctx.message.channel.send(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.guild.roles:
				if str(arole.id) == str(role):
					found = True
					vowels = "aeiou"
					if arole.name[:1].lower() in vowels:
						msg = 'You need to be an **{}** to *give xp*, *gamble*, or *feed* the bot.'.format(arole.name)
					else:
						msg = 'You need to be a **{}** to *give xp*, *gamble*, or *feed* the bot.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.message.channel.send(msg)
		
	@commands.command(pass_context=True)
	async def setstoprole(self, ctx, *, role : str = None):
		"""Sets the required role ID to stop the music player (admin only)."""
		
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
			self.settings.setServerStat(ctx.message.guild, "RequiredStopRole", "")
			msg = 'Stopping the music now *admin-only*.'
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
		self.settings.setServerStat(ctx.message.guild, "RequiredStopRole", role.id)

		msg = 'Role required to stop the music player set to **{}**.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)
		
	
	@setstoprole.error
	async def stoprole_error(self, error, ctx):
		# do stuff
		msg = 'setstoprole Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def stoprole(self, ctx):
		"""Lists the required role to stop the bot from playing music."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		role = self.settings.getServerStat(ctx.message.guild, "RequiredStopRole")
		if role == None or role == "":
			msg = '**Only Admins** can use stop.'
			await ctx.message.channel.send(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.guild.roles:
				if str(arole.id) == str(role):
					found = True
					vowels = "aeiou"
					if arole.name[:1].lower() in vowels:
						msg = 'You need to be an **{}** to use `$stop`.'.format(arole.name)
					else:
						msg = 'You need to be a **{}** to use `$stop`.'.format(arole.name)
					
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.message.channel.send(msg)

		
	@commands.command(pass_context=True)
	async def setlinkrole(self, ctx, *, role : str = None):
		"""Sets the required role ID to add/remove links (admin only)."""
		
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
			self.settings.setServerStat(ctx.message.guild, "RequiredLinkRole", "")
			msg = 'Add/remove links now *admin-only*.'
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
		self.settings.setServerStat(ctx.message.guild, "RequiredLinkRole", role.id)

		msg = 'Role required for add/remove links set to **{}**.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)
		
	
	@setlinkrole.error
	async def setlinkrole_error(self, error, ctx):
		# do stuff
		msg = 'setlinkrole Error: {}'.format(error)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def sethackrole(self, ctx, *, role : str = None):
		"""Sets the required role ID to add/remove hacks (admin only)."""
		
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
			self.settings.setServerStat(ctx.message.guild, "RequiredHackRole", "")
			msg = 'Add/remove hacks now *admin-only*.'
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
		self.settings.setServerStat(ctx.message.guild, "RequiredHackRole", role.id)

		msg = 'Role required for add/remove hacks set to **{}**.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)


	@sethackrole.error
	async def hackrole_error(self, error, ctx):
		# do stuff
		msg = 'sethackrole Error: {}'.format(error)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def setrules(self, ctx, *, rules : str = None):
		"""Set the server's rules (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return
		
		if rules == None:
			rules = ""
			
		self.settings.setServerStat(ctx.message.guild, "Rules", rules)
		msg = 'Rules now set to:\n{}'.format(rules)
		
		await ctx.message.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def lock(self, ctx):
		"""Toggles whether the bot only responds to admins (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return
		
		isLocked = self.settings.getServerStat(ctx.message.guild, "AdminLock")
		if isLocked.lower() == "yes":
			msg = 'Admin lock now *Off*.'
			self.settings.setServerStat(ctx.message.guild, "AdminLock", "No")
		else:
			msg = 'Admin lock now *On*.'
			self.settings.setServerStat(ctx.message.guild, "AdminLock", "Yes")
		await ctx.message.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def addadmin(self, ctx, *, role : str = None):
		"""Adds a new role to the admin list (admin only)."""

		usage = 'Usage: `{}addadmin [role]`'.format(ctx.prefix)

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
			await ctx.message.channel.send(usage)
			return

		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(roleName, ctx.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.message.guild, "AdminArray")

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(aRole['ID']) == str(role.id):
				# We found it - throw an error message and return
				msg = '**{}** is already in the list.'.format(role.name)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(ctx.message.guild, "AdminArray", promoArray)

		msg = '**{}** added to list.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)
		return

	@addadmin.error
	async def addadmin_error(self, error, ctx):
		# do stuff
		msg = 'addadmin Error: {}'.format(error)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def removeadmin(self, ctx, *, role : str = None):
		"""Removes a role from the admin list (admin only)."""

		usage = 'Usage: `{}removeadmin [role]`'.format(ctx.prefix)

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
			await ctx.message.channel.send(usage)
			return

		# Name placeholder
		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(role, ctx.guild)

		# If we're here - then the role is a real one
		promoArray = self.settings.getServerStat(ctx.message.guild, "AdminArray")

		for aRole in promoArray:
			# Check for Name
			if aRole['Name'].lower() == roleName.lower():
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(ctx.message.guild, "AdminArray", promoArray)
				msg = '**{}** removed successfully.'.format(aRole['Name'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

			# Get the role that corresponds to the id
			if role and (str(aRole['ID']) == str(role.id)):
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(ctx.message.guild, "AdminArray", promoArray)
				msg = '**{}** removed successfully.'.format(role.name)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we didn't find it
		msg = '**{}** not found in list.'.format(aRole['Name'])
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)

	@removeadmin.error
	async def removeadmin_error(self, error, ctx):
		# do stuff
		msg = 'removeadmin Error: {}'.format(error)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def removemotd(self, ctx, *, chan = None):
		"""Removes the message of the day from the selected channel."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		usage = 'Usage: `{}broadcast [message]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return
		if chan == None:
			chan = channel
		if type(chan) is str:
			try:
				chan = discord.utils.get(server.channels, name=chan)
			except:
				print("That channel does not exist")
				return
		# At this point - we should have the necessary stuff
		motdArray = self.settings.getServerStat(server, "ChannelMOTD")
		for a in motdArray:
			# Get the channel that corresponds to the id
			if str(a['ID']) == str(chan.id):
				# We found it - throw an error message and return
				motdArray.remove(a)
				self.settings.setServerStat(server, "ChannelMOTD", motdArray)
				
				msg = 'MOTD for *{}* removed.'.format(channel.name)
				await channel.send(msg)
				await channel.edit(topic=None)
				await self.updateMOTD()
				return		
		msg = 'MOTD for *{}* not found.'.format(chan.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)	
		
	@removemotd.error
	async def removemotd_error(self, error, ctx):
		# do stuff
		msg = 'removemotd Error: {}'.format(error)
		await ctx.channel.send(msg)
				

	@commands.command(pass_context=True)
	async def broadcast(self, ctx, *, message : str = None):
		"""Broadcasts a message to all connected servers.  Can only be done by the owner."""

		channel = ctx.message.channel
		author  = ctx.message.author

		if message == None:
			await channel.send(usage)
			return

		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return
		
		for server in self.bot.guilds:
			# Get the default channel
			targetChan = server.default_channel
			targetChanID = self.settings.getServerStat(server, "DefaultChannel")
			if len(str(targetChanID)):
				# We *should* have a channel
				tChan = self.bot.get_channel(int(targetChanID))
				if tChan:
					# We *do* have one
					targetChan = tChan
			try:
				await targetChan.send(message)
			except Exception:
				pass

		
	@commands.command(pass_context=True)
	async def setmotd(self, ctx, message : str = None, users : str = "No", chan : discord.TextChannel = None):
		"""Adds a message of the day to the selected channel."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		usage = 'Usage: `{}setmotd "[message]" [usercount Yes/No (default is No)] [channel]`'.format(ctx.prefix)
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return
		if not message:
			await channel.send(usage)
			return	
		if not chan:
			chan = channel
		if type(chan) is str:
			try:
				chan = discord.utils.get(server.channels, name=chan)
			except:
				print("That channel does not exist")
				return
		
		# At this point - we should have the necessary stuff
		motdArray = self.settings.getServerStat(server, "ChannelMOTD")
		for a in motdArray:
			# Get the channel that corresponds to the id
			if str(a['ID']) == str(chan.id):
				# We found it - throw an error message and return
				a['MOTD'] = message
				a['ListOnline'] = users
				self.settings.setServerStat(server, "ChannelMOTD", motdArray)
				
				msg = 'MOTD for *{}* changed.'.format(chan.name)
				await channel.send(msg)
				await self.updateMOTD()
				return

		# If we made it this far - then we can add it
		motdArray.append({ 'ID' : chan.id, 'MOTD' : message, 'ListOnline' : users })
		self.settings.setServerStat(server, "ChannelMOTD", motdArray)

		msg = 'MOTD for *{}* added.'.format(chan.name)
		await channel.send(msg)
		await self.updateMOTD()

		
	@setmotd.error
	async def setmotd_error(self, error, ctx):
		# do stuff
		msg = 'setmotd Error: {}'.format(error)
		await ctx.channel.send(msg)
		
		
	async def updateMOTD(self):
		for server in self.bot.guilds:
			try:
				channelMOTDList = self.settings.getServerStat(server, "ChannelMOTD")
			except KeyError:
				channelMOTDList = []
			
			if len(channelMOTDList) > 0:
				members = 0
				membersOnline = 0
				for member in server.members:
					members += 1
					if str(member.status).lower() == "online":
						membersOnline += 1
				
			for id in channelMOTDList:
				channel = self.bot.get_channel(id['ID'])
				if channel:
					# Got our channel - let's update
					motd = id['MOTD'] # A markdown message of the day
					listOnline = id['ListOnline'] # Yes/No - do we list all online members or not?
						
					if listOnline.lower() == "yes":
						msg = '{} - ({}/{} users online)'.format(motd, int(membersOnline), int(members))
					else:
						msg = motd
							
					# print(msg)
					try:		
						await channel.edit(topic=msg)
					except Exception:
						# If someone has the wrong perms - we just move on
						continue