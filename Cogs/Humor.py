import asyncio
import discord
import random
import urllib
import requests
import json
import time
import os
from   discord.ext import commands
from Cogs import Message
from Cogs import FuzzySearch
from Cogs import GetImage
from Cogs import Nullify

# This module is for random funny things I guess...

class Humor:

	def __init__(self, bot, settings, listName = "Adjectives.txt"):
		self.bot = bot
		self.settings = settings
		# Setup our adjective list
		self.adj = []
		marks = map(chr, range(768, 879))
		self.marks = list(marks)
		if os.path.exists(listName):
			with open(listName) as f:
				for line in f:
					self.adj.append(line)
					
					
	@commands.command(pass_context=True)
	async def zalgo(self, ctx, *, message = None):
		"""Ỉ s̰hͨo̹u̳lͪd͆ r͈͍e͓̬a͓͜lͨ̈l̘̇y̡͟ h͚͆a̵͢v͐͑eͦ̓ i͋̍̕n̵̰ͤs͖̟̟t͔ͤ̉ǎ͓͐ḻ̪ͨl̦͒̂ḙ͕͉d͏̖̏ ṡ̢ͬö̹͗m̬͔̌e̵̤͕ a̸̫͓͗n̹ͥ̓͋t̴͍͊̍i̝̿̾̕v̪̈̈͜i̷̞̋̄r̦̅́͡u͓̎̀̿s̖̜̉͌..."""
		if message == None:
			await ctx.send("Usage: `{}zalgo [message]`".format(ctx.prefix))
			return
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		words = message.split()
		try:
			iterations = int(words[len(words)-1])
			words = words[:-1]
		except Exception:
			iterations = 1
			
		if iterations > 100:
			iterations = 100
		if iterations < 1:
			iterations = 1
			
		zalgo = " ".join(words)
		for i in range(iterations):
			if len(zalgo) > 2000:
				break
			zalgo = self._zalgo(zalgo)
		
		zalgo = zalgo[:2000]

		# Check for suppress
		if suppress:
			zalgo = Nullify.clean(zalgo)
		await Message.say(self.bot, zalgo, ctx.message.channel, ctx.message.author, 1, 2000, 5)
		#await ctx.send(zalgo)
		
	def _zalgo(self, text):
		words = text.split()
		zalgo = ' '.join(''.join(c + ''.join(random.choice(self.marks)
				for _ in range(i // 2 + 1)) * c.isalnum()
				for c in word)
				for i, word in enumerate(words))
		return zalgo

	@commands.command(pass_context=True)
	async def holy(self, ctx, *, subject : str = None):
		"""Time to backup the Batman!"""
		
		if subject == None:
			await ctx.channel.send("Usage: `{}holy [subject]`".format(ctx.prefix))
			return
		
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		matchList = []
		for a in self.adj:
			if a[:1].lower() == subject[:1].lower():
				matchList.append(a)
		
		if not len(matchList):
			# Nothing in there - get random entry
			# msg = "*Whoah there!* That was *too* holy for Robin!"
			word = random.choice(self.adj)
			word = word.strip().capitalize()
			subject = subject.strip().capitalize()
			msg = "*Holy {} {}, Batman!*".format(word, subject)
		else:
			# Get a random one
			word = random.choice(matchList)
			word = word.strip().capitalize()
			subject = subject.strip().capitalize()
			msg = "*Holy {} {}, Batman!*".format(word, subject)
		
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		
		await ctx.channel.send(msg)
			
		
	@commands.command(pass_context=True)
	async def fart(self, ctx):
		"""PrincessZoey :P"""
		fartList = ["Poot", "Prrrrt", "Thhbbthbbbthhh", "Plllleerrrrffff", "Toot", "Blaaaaahnk", "Squerk"]
		randnum = random.randint(0, len(fartList)-1)
		msg = '{}'.format(fartList[randnum])
		await ctx.channel.send(msg)

	def canDisplay(self, server):
		# Check if we can display images
		lastTime = int(self.settings.getServerStat(server, "LastPicture"))
		threshold = int(self.settings.getServerStat(server, "PictureThreshold"))
		if not GetImage.canDisplay( lastTime, threshold ):
			# await self.bot.send_message(channel, 'Too many images at once - please wait a few seconds.')
			return False
		
		# If we made it here - set the LastPicture method
		self.settings.setServerStat(server, "LastPicture", int(time.time()))
		return True

	@commands.command(pass_context=True)
	async def memetemps(self, ctx):
		"""Get Meme Templates"""
		url = "https://api.imgflip.com/get_memes"
		r = requests.get(url)
		result_json = json.loads(r.text)
		templates = result_json["data"]["memes"]

		templates_string_list = []

		templates_string = "**Meme Templates**\n"
		for template in templates:
			length_test = templates_string + "* [`{}` - `{}`]\n".format(template["id"], template["name"])
			if len(length_test) > 2000:
				# We're past our character limit - add it to the list and reset the
				# templates_string
				templates_string_list.append(templates_string)
				templates_string = ''
				continue
			# Not over the limit - add it to the string
			templates_string += "* [`{}` - `{}`]\n".format(template["id"], template["name"])
		# Add the templates_string to the list here if it contains anything
		if len(templates_string):
			templates_string_list.append(templates_string)
		# Iterate over all the template strings and display them
		for string in templates_string_list:
			await ctx.message.author.send(string)

		# await Message.say(self.bot, templates_string, ctx.message.author)

	@commands.command(pass_context=True)
	async def meme(self, ctx, template_id = None, text_zero = None, text_one = None):
		"""Generate Meme"""

		if not self.canDisplay(ctx.message.guild):
			return

		if text_one == None:
			# Set as space if not included
			text_one = " "

		if template_id == None or text_zero == None or text_one == None:
			msg = "Usage: `{}meme [template_id] [text#1] [text#2]`\n\n Meme Templates can be found using `$memetemps`".format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		templates = self.getTemps()

		chosenTemp = None
		msg = ''

		idMatch = FuzzySearch.search(template_id, templates, 'id', 1)
		if idMatch[0]['Ratio'] < 1:
			# Not a perfect match - try name
			nameMatch = FuzzySearch.search(template_id, templates, 'name', 1)
			if nameMatch[0]['Ratio'] > idMatch[0]['Ratio']:
				# Better match on name than id
				chosenTemp = nameMatch[0]['Item']['id']
				if not nameMatch[0]['Ratio'] == 1:
					# Still not a perfect match...
					msg = 'I\'ll assume you meant *{}*.'.format(nameMatch[0]['Item']['name'])
		else:
			# ID is a perfect match
			chosenTemp = idMatch[0]['Item']['id']


		url = "https://api.imgflip.com/caption_image"
		payload = {'template_id': chosenTemp, 'username':'CorpBot', 'password': 'pooter123', 'text0': text_zero, 'text1': text_one }
		r = requests.post(url, data=payload)
		result_json = json.loads(r.text)
		result = result_json["data"]["url"]
		if msg:
			# result = '{}\n{}'.format(msg, result)
			await ctx.channel.send(msg)
		# Download Image - set title as a space so it disappears on upload
		await GetImage.get(result, self.bot, ctx.message.channel, " ")


	def getTemps(self):
		url = "https://api.imgflip.com/get_memes"
		r = requests.get(url)
		result_json = json.loads(r.text)
		templates = result_json["data"]["memes"]
		if templates:
			return templates
		return None
