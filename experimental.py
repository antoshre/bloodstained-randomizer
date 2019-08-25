import json
import binascii
import struct
import random
import itertools
from io import BytesIO
import sys

class DropEntry():
	def __init__(self, name_, shard_, rareitem_, commonitem_, rareing_, commoning_, coin_, areachange_):
		self.Name = name_
		self.Shard = shard_
		self.RareItem = rareitem_
		self.CommonItem = commonitem_
		self.RareIngredient = rareing_
		self.CommonIngredient = commoning_
		self.Coin = coin_
		self.AreaChange = areachange_
	def __repr__(self):
		return "DropEntry({}, {}, {}, {}, {}, {}, {})" \
				.format(self.Name, self.Shard, self.RareItem, self.CommonItem, self.RareIngredient, self.CommonIngredient, self.Coin)

		
class Shard():
	def __init__(self, id, rate, names):
		self.Id = id['Index']
		self.Rate = rate
		self.Name = names[str(self.Id['Value'])]['Name'][:-1]
	def __repr__(self):
		if 'None' in self.Name:
			return "Shard(None)"
		return "Shard({}, Id={}, Rate={})".format(self.Name, self.Id['Value'], self.Rate['Value'])
		
class Item():
	def __init__(self, id, quantity, rate, names):
		self.Id = id['Index']
		self.Quantity = quantity
		self.Rate = rate
		self.Name = names[str(self.Id['Value'])]['Name'][:-1]
	def __repr__(self):
		if self.Quantity['Value'] == 0:
			return "Item(None)"
		return "Item({}, Id={}, Quantity={}, Rate={})".format(self.Name, self.Id['Value'], self.Quantity['Value'], self.Rate['Value'])
		
class Coin():
	def __init__(self, type, override, rate, names):
		self.Type = type['Index']
		self.Override = override
		self.Rate = rate
		self.Name = names[ str(self.Type['Value'])]['Name'][:-1]
	def __repr__(self):
		if 'None' in self.Name:
			return "Coin(None)"
		return "Coin({}, Type={}, Override={}, Rate={})".format(self.Name, self.Type, self.Override, self.Rate)

class Patch():
	def __init__(self, offset, value):
		self.Offset = offset
		self.Value = value
	def __repr__(self):
		return "Patch(offset={}, value={})".format(self.Offset, self.Value)		
		
def filterHPMPBulletUP(entries):
	#Return True if keep, False if drop entry
	def f(entry):
		bad = ['MaxHPUP', 'MaxMPUP', 'MaxBulletUP']
		for name in bad:
			if name in entry.RareItem.Name:
				return False
			if name in entry.CommonItem.Name:
				return False
		return True
	return list(filter(f, entries))
	
def filterProgressionShards(entries):
	#True if keep, False if drop
	def f(entry):
		bad = [	'ReflectionRay',
				'Dimensionshift',
				'Invert',
				'Doublejump',
				'Demoniccapture',
				'Aquastream',
				'Bloodsteel', 
				'SwingTentacle',
				'Ceruleansplash',
				'FireCannon', #Needed on Galleon Minerva
		]
		for name in bad:
			if name in entry.Shard.Name:
				return False
		return True
	return list(filter(f, entries))

def clearAllDrops(entries, blank_shard_id, blank_item_id, blank_coin_id):
	patchset = []
	for entry in entries:
		patchset.append( Patch(entry.Shard.Id['offset'], blank_shard_id))
		patchset.append( Patch(entry.Shard.Rate['offset'], 0.0))
		patchset.append( Patch(entry.RareItem.Id['offset'], blank_item_id))
		patchset.append( Patch(entry.RareItem.Rate['offset'], 0.0))
		patchset.append( Patch(entry.CommonItem.Id['offset'], blank_item_id))
		patchset.append( Patch(entry.CommonItem.Rate['offset'], 0.0))
		patchset.append( Patch(entry.RareIngredient.Id['offset'], blank_item_id))
		patchset.append( Patch(entry.RareIngredient.Rate['offset'], 0.0))
		patchset.append( Patch(entry.CommonIngredient.Id['offset'], blank_item_id))
		patchset.append( Patch(entry.CommonIngredient.Rate['offset'], 0.0))
		patchset.append( Patch(entry.Coin.Type['offset'], blank_coin_id))
		patchset.append( Patch(entry.Coin.Override['offset'], 0))
		patchset.append( Patch(entry.Coin.Rate['offset'], 0.0))
	return patchset
def filterProgressionItems(entries):
	#True if keep, False if drop
	def f(entry):
		bad = [
			'ChangeHP', #wtf is this
			'Silverbromide',
			'SpikeBreast', #Spike Aegis
			'VillageKey', #Key to get out of Ardantville house
		]
		for name in bad:
			if name in entry.RareItem.Name:
				return False
			if name in entry.CommonItem.Name:
				return False
		return True
	return list(filter(f, entries))
	
def filterSingleEncounterMobs(entries):
	#True if keep, False if drop
	def f(entry):
		bad = [	'N1001', 'N1011', 'N1003', 'N2004', 'N1005',
				'N2001', 'N1006', 'N1012', 'N1002', 'N2014',
				'N2007', 'N2006', 'N1004', 'N1008', 'N1009',
				'N1013', 'N2012'
		]
		for name in bad:
			if name in entry.Name:
				return False
		return True
	return list(filter(f, entries))
	
def filterUnknowns(entries):
	def f(entry):
		bad = [	'HPRecover',
				'SPEED',
				'Peanut',
				'Lantern',
				'AAAA',
				'TestIngredients',
				'VillageKeyBox',
				'PotionMaterial',
				'PhotoEvent',
				'CertificationboardEvent',
				'Qu07_Last',
				'Swordsman',
				'N3006_OpeningDemo'
		]
		for name in bad:
			if name in entry.Name:
				return False
		return True
	return list( filter(f, entries))
	
def assignShards(entries, shards):
	assert( len(entries) == len(shards))
	patchset = []
	for e, shard in zip(entries, shards):
		patchset.append( Patch(e.Shard.Id['offset'], shard.Id['Value']) )
		if e.AreaChange['Value'] == 0 and 'Treasurebox' in e.Name and not 'None' in shard.Name:
			patchset.append( Patch(e.Shard.Rate['offset'], 100.0) )
		else:
			patchset.append( Patch(e.Shard.Rate['offset'], shard.Rate['Value']) )
	return patchset
def assignRareItems(entries, ritems):
	assert( len(entries) == len(ritems))
	patchset = []
	for e, ritem in zip(entries, ritems):
		patchset.append( Patch(e.RareItem.Id['offset'], ritem.Id['Value']) )
		if e.AreaChange['Value'] == 0 and 'Treasurebox' in e.Name and not 'None' in ritem.Name:
			patchset.append( Patch(e.RareItem.Rate['offset'], 100.0) )
		else:
			patchset.append( Patch(e.RareItem.Rate['offset'], ritem.Rate['Value']) )
		patchset.append( Patch(e.RareItem.Quantity['offset'], ritem.Quantity['Value']) )
	return patchset
def assignCommonItems(entries, citems):
	assert( len(entries) == len(citems))
	patchset = []
	for e, citem in zip(entries, citems):
		patchset.append( Patch(e.CommonItem.Id['offset'], citem.Id['Value']) )
		if e.AreaChange['Value'] == 0 and 'Treasurebox' in e.Name and not 'None' in citem.Name:
			patchset.append( Patch(e.CommonItem.Rate['offset'], 100.0) )
		else:
			patchset.append( Patch(e.CommonItem.Rate['offset'], citem.Rate['Value']) )
		patchset.append( Patch(e.CommonItem.Quantity['offset'], citem.Quantity['Value']) )
	return patchset

def assignRareIngredients(entries, rings):
	assert( len(entries) == len(rings))
	patchset = []
	for e, ring in zip(entries, rings):
		patchset.append( Patch(e.RareIngredient.Id['offset'], ring.Id['Value']) )
		if e.AreaChange['Value'] == 0 and 'Treasurebox' in e.Name and not 'None' in ring.Name:
			patchset.append( Patch(e.RareIngredient.Rate['offset'], 100.0) )
		else:
			patchset.append( Patch(e.RareIngredient.Rate['offset'], ring.Rate['Value']) )
		patchset.append( Patch(e.RareIngredient.Quantity['offset'], ring.Quantity['Value']) )
	return patchset
	
def assignCommonIngredients(entries, cings):
	assert( len(entries) == len(cings))
	patchset = []
	for e, cing in zip(entries, cings):
		patchset.append( Patch(e.CommonIngredient.Id['offset'], cing.Id['Value']) )
		if e.AreaChange['Value'] == 0 and 'TreasureBox' in e.Name and not 'None' in cing.Name:
			patchset.append( Patch(e.CommonIngredient.Rate['offset'], 100.0) )
		else:
			patchset.append( Patch(e.CommonIngredient.Rate['offset'], cing.Rate['Value']) )
		patchset.append( Patch(e.CommonIngredient.Quantity['offset'], cing.Quantity['Value']) )
	return patchset
	
def assignCoins(entries, coins):
	assert (len(entries) == len(coins))
	patchset = []
	for e, coin in zip(entries, coins):
		patchset.append( Patch( e.Coin.Type['offset'], coin.Type['Value']) )
		patchset.append( Patch( e.Coin.Override['offset'], coin.Override['Value']) )
		patchset.append( Patch( e.Coin.Rate['offset'], coin.Rate['Value']) )
	return patchset
	
def handleEmptyChests(entries, blank_coin_id, d10_coin_id):
	patchset = []
	for entry in entries:
		if 'TreasureBox' in entry.Name:
			if entry.RareItem.Rate['Value'] == 0:
				if entry.CommonItem.Rate['Value'] == 0:
					patchset.append( Patch( entry.Coin.Type['offset'], d10_coin_id) )
					patchset.append( Patch( entry.Coin.Override['offset'], 10) ) #Override appears to be the denomination
					patchset.append( Patch( entry.Coin.Rate['offset'], 0.0) ) #Rate isn't used
	return patchset

def applyPatches(patchset):
	with open("PB_DT_DropRateMaster-v1.03.uasset", "rb") as original:
		raw = original.read()
	stream = BytesIO(raw)
	for patch in patchset:
		stream.seek(patch.Offset)
		if isinstance(patch.Value, int):
			stream.write( struct.pack("i", patch.Value))
		elif isinstance(patch.Value, float):
			stream.write( struct.pack("f", patch.Value))
		else:
			raise NotImplementedError(type(patch.Value))
	with open("mod.uasset", 'wb') as modified:
		modified.write(stream.getbuffer())
if __name__ == "__main__":
	import argparse
	import os
	
	from uasset_dt_to_json import dumper as udump
	
	parser = argparse.ArgumentParser( \
		description="Bloodstained drop randomizer",
		usage="%(prog)s --input [infile]"
	)
	#parser.add_argument("--debug", help="Enable debug output", action='store_true', default=False)
	parser.add_argument("--input", help="Original 'PB_DT_DropRateMaster.uasset' file", \
						action='store', required=True)
	parser.add_argument("--seed", help="Seed for randomizer", action='store', default=random.random())
	
	args = parser.parse_args()
	
	drop_entries = []
	with open(args.input, 'rb') as original_file:
		ctx = dumper.ParserCtx(file, debug=False)
		uasset = dumper.UAsset(ctx)
		#Load names array
		with open("PB_DT_DropRateMaster-v1.03-names.json", 'r') as namedump:
			names = json.loads(namedump.read())
		#Load main drop table
		drm = json.loads(jdump.read())
		outer = drm['Extra']['Data']
		
		all_drop_entries = []
		#Parse all drop entries
		for entry in outer:
			#Name of the drop location
			name = entry['Name'][:-1]
			#drop data
			tags = entry['Obj']['Tags']
			#Convert {'Name', 'Value'} tuple to dict
			d = {}
			for e in tags:
				#strip last character off name, it's a null
				d[e['Name'][:-1]] = e['Value']
			
			#extract shard
			shard = Shard(d['ShardId'], d['ShardRate'], names)
			#extract Rare Item
			rareitem = Item(d['RareItemId'], d['RareItemQuantity'], d['RareItemRate'], names)
			#extract Common Item
			commonitem = Item(d['CommonItemId'], d['CommonItemQuantity'], d['CommonRate'], names)
			#extract Rare Ingredient
			rareingredient = Item(d['RareIngredientId'], d['RareIngredientQuantity'], d['RareIngredientRate'], names)
			#extract Common Ingredient
			commoningredient = Item(d['CommonIngredientId'], d['CommonIngredientQuantity'], d['CommonIngredientRate'], names)
			#extract coin
			coin = Coin(d['CoinType'], d['CoinOverride'], d['CoinRate'], names)
			#Construct full entry
			drop = DropEntry(name, shard, rareitem, commonitem, rareingredient, commoningredient, coin, d['AreaChangeTreasureFlag'])
			print(drop)
			all_drop_entries.append(drop)
		
		print("Loaded {} drop entries".format(len(all_drop_entries)))
		
		
		
		print("Filtering out MaxHPUP, MaxMPUP, MaxBulletUP...")
		valid_drop_entries = filterHPMPBulletUP(all_drop_entries)
		#print("{} remain".format( len(valid_drop_entries)))
		
		print("Filtering out unknown drop entries...")
		valid_drop_entries = filterUnknowns(valid_drop_entries)
		
		print("Filtering out progression-critical shards...")
		valid_drop_entries = filterProgressionShards(valid_drop_entries)
		#print("{} remain".format( len(valid_drop_entries)))
		
		print("Filtering out progression-critical items...")
		valid_drop_entries = filterProgressionItems(valid_drop_entries)
		#print("{} remain".format( len(valid_drop_entries)))
		
		print("Filtering out single-encounter mobs...")
		valid_drop_entries = filterSingleEncounterMobs(valid_drop_entries)
		#print("{} remain".format( len(valid_drop_entries)))
		
		#Start randomization!
		print("Starting randomization with {} entries".format( len(valid_drop_entries)))
		
		#Collect remaining shards
		shards = [e.Shard for e in valid_drop_entries if not 'None' in e.Shard.Name]
		rare_items = [e.RareItem for e in valid_drop_entries if not 'None' in e.RareItem.Name]
		common_items = [e.CommonItem for e in valid_drop_entries if not 'None' in e.CommonItem.Name]
		rare_ingredients = [e.RareIngredient for e in valid_drop_entries if not 'None' in e.RareIngredient.Name]
		common_ingredients = [e.CommonIngredient for e in valid_drop_entries if not 'None' in e.CommonIngredient.Name]
		coins = [e.Coin for e in valid_drop_entries if not 'None' in e.Coin.Name]
		
		print("{} shards in play".format(len(shards)))
		print("{} rare items in play".format(len(rare_items)))
		print("{} common items in play".format(len(common_items)))
		print("{} rare ingredients in play".format(len(rare_ingredients)))
		print("{} common ingredients in play".format(len(common_ingredients)))
		print("{} coins in play".format(len(coins)))
		
		#find 'None' shard ID
		blank_shard_id = [e.Shard for e in valid_drop_entries if 'None' in e.Shard.Name][0].Id['Value']
		#find 'None' item ID
		blank_item_id = [e.RareItem for e in valid_drop_entries if 'None' in e.RareItem.Name][0].Id['Value']
		#Find 'None' coin Type
		blank_coin_id = [e.Coin for e in valid_drop_entries if 'None' in e.Coin.Name][0].Type['Value']
		#Find 'D10' coin Type
		#needed for otherwise empty chests
		d10_coin = [e.Coin for e in valid_drop_entries if 'D10' in e.Coin.Name][0]
		print("d10 coin: ", d10_coin)
		d10_coin_id = d10_coin.Type['Value']
		
		
		random.seed("lolwut")
		
		blank_drop_entries = valid_drop_entries.copy()
		patches = clearAllDrops(blank_drop_entries, blank_shard_id, blank_item_id, blank_coin_id)
		
		#Assign shards
		entries = random.sample(blank_drop_entries, len(shards))
		patches += assignShards(entries, shards)
		
		#Assign rare items
		entries = random.sample(blank_drop_entries, len(rare_items))
		patches += assignRareItems(entries, rare_items)
		
		#Assign common items
		entries = random.sample(blank_drop_entries, len(common_items))
		patches += assignCommonItems(entries, common_items)
		
		#Assign rare ingredients
		entries = random.sample(blank_drop_entries, len(rare_ingredients))
		patches += assignRareIngredients(entries, rare_ingredients)
		
		#Assign common ingredients
		entries = random.sample(blank_drop_entries, len(common_ingredients))
		patches += assignCommonIngredients(entries, common_ingredients)
		
		#Assign coins
		entries = random.sample(blank_drop_entries, len(coins))
		patches += assignCoins(entries, coins)
		
		#Check that chests have something
		patches += handleEmptyChests(entries, blank_coin_id, d10_coin_id)
		
		print("{} patches to apply".format(len(patches)))
		
		applyPatches(patches)