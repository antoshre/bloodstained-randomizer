import json
import binascii
import struct
import random
from io import BytesIO
import sys

from operator import itemgetter

class Item():
	def __init__(self, name, index, quantity, rate):
		self.name = name
		self.index = index
		self.quantity = quantity
		self.rate = rate
	def __repr__(self):
		return self.__class__.__name__ + "({}, index={}, quantity={}, rate={})".format(self.name, self.index, self.quantity, self.rate)
class CommonItem(Item):
	def __init__(self, *args):
		super().__init__(*args)
class RareItem(Item):
	def __init__(self, *args):
		super().__init__(*args)
		
class CommonIngredient(Item):
	def __init__(self, *args):
		super().__init__(*args)
class RareIngredient(Item):
	def __init__(self, *args):
		super().__init__(*args)
class Shard(Item):
	def __init__(self, *args):
		super().__init__(*args)		
class Coin():
	def __init__(self, name, index, rate, override):
		self.name = name
		self.index = index
		self.rate = rate
		self.override = override
	def __repr__(self):
		return "Coin({}, index={}, rate={}, override={})".format(self.name, self.index, self.rate, self.override)

def getNameFromEntry(entry):
	return entry["Key"]["Value"]["Value"]
def getRareItemFromEntry(entry):
	name = entry["Properties"]["RareItemId\x00"][1]["Value"]
	index = entry["Properties"]["RareItemId\x00"][1]["Index"]
	quantity = entry["Properties"]["RareItemQuantity\x00"][1]
	rate = entry["Properties"]["RareItemRate\x00"][1]
	return RareItem(name, index, quantity, rate)
def getCommonItemFromEntry(entry):
	name = entry["Properties"]["CommonItemId\x00"][1]["Value"]
	index = entry["Properties"]["CommonItemId\x00"][1]["Index"]
	quantity = entry["Properties"]["CommonItemQuantity\x00"][1]
	rate = entry["Properties"]["CommonRate\x00"][1]
	return CommonItem(name, index, quantity, rate)
def getRareIngredientFromEntry(entry):
	name = entry["Properties"]["RareIngredientId\x00"][1]["Value"]
	index = entry["Properties"]["RareIngredientId\x00"][1]["Index"]
	quantity = entry["Properties"]["RareIngredientQuantity\x00"][1]
	rate = entry["Properties"]["RareIngredientRate\x00"][1]
	return RareIngredient(name, index, quantity, rate)
def getCommonIngredientFromEntry(entry):
	name = entry["Properties"]["CommonIngredientId\x00"][1]["Value"]
	index = entry["Properties"]["CommonIngredientId\x00"][1]["Index"]
	quantity = entry["Properties"]["CommonIngredientQuantity\x00"][1]
	rate = entry["Properties"]["CommonIngredientRate\x00"][1]
	return CommonIngredient(name, index, quantity, rate)
def getShardFromEntry(entry):
	name = entry["Properties"]["ShardId\x00"][1]["Value"]
	index = entry["Properties"]["ShardId\x00"][1]["Index"]
	rate = entry["Properties"]["ShardRate\x00"][1]
	return Shard(name, index, 1, rate)
def getCoinFromEntry(entry):
	name = entry["Properties"]["CoinType\x00"][1]["Value"]
	index = entry["Properties"]["CoinType\x00"][1]["Index"]
	override = entry["Properties"]["CoinOverride\x00"][1]
	rate = entry["Properties"]["CoinRate\x00"][1]
	return Coin(name, index, rate, override)
def getAllFromEntry(entry):
	name = getNameFromEntry(entry)
	shard = getShardFromEntry(entry)
	ritem = getRareItemFromEntry(entry)
	citem = getCommonItemFromEntry(entry)
	ring = getRareIngredientFromEntry(entry)
	cing = getCommonIngredientFromEntry(entry)
	coin = getCoinFromEntry(entry)
	return (name, shard, ritem, citem, ring, cing, coin)
	
class DropLocation():
	def __init__(self, name, shard, rare_item, common_item, rare_ingredient, common_ingredient, coin):
		self.name = name
		self.shard = shard
		self.rare_item = rare_item
		self.common_item = common_item
		self.rare_ingredient = rare_ingredient
		self.common_ingredient = common_ingredient
		self.coin = coin
	def __repr__(self):
		return "DropLocation(\n\t{},\n\t{},\n\t{},\n\t{},\n\t{},\n\t{},\n\t{}\n)".format( \
			self.name, \
			self.shard, \
			self.rare_item, \
			self.common_item, \
			self.rare_ingredient, \
			self.common_ingredient, \
			self.coin)

#Yield all chests
def allChests(locs):
	for loc in locs:
		if "Treasurebox" in loc.name:
			yield loc
#True: accept item into randomizer logic
#False: reject item from randomizer logic
def filterChests(loc):
	#Names to filter out
	bad_item_names = [
		"MaxHPUP", "MaxMPUP", "MaxBulletUP", #Max HP/MP/Bullet upgrades
		"ChangeHP", #Dunno what this is
		"Silverbromide", #Progression item
		"SpikeBreast" #Spike Aegis needed for progression, lock for now
	]
	
	for name in bad_item_names:
		if name in loc.rare_item.name["Value"]:
			print("Rejecting chest item: {}".format(name))
			return False
		if name in loc.common_item.name["Value"]:
			print("Rejecting chest item: {}".format(name))
			return False
			
	return True
#Yield all shard entries
def allMobs(locs):
	for loc in locs:
		if "_Shard" in loc.name:
			yield loc
		other_good_names = [
			"_1ST_Treasure", #Carpenter
			"_2ND_Treasure" #Also Carpenter
		]
		for other in other_good_names:
			if other in loc.name:
				yield loc
				
#True/False whether to include this specific shard in random pool
def filterMobs(loc):
	progression_shard_names = [
		"Reflectionray", #Reflect Ray
		"Dimensionshift", #Dimension Shift
		"Invert", #Invert
		"Doublejump", #Double Jump
		"Demoniccapture", #Craftwork
		"Aquastream", #Only to make sure water access is available
		"Bloodsteel" #Blood Steal
	]
	for shard_name in progression_shard_names:
		if shard_name in loc.shard.name["Value"]:
			print("Rejecting shard: {}".format(loc.shard.name))
			return False
	return True

def allWalls(locs):
	for loc in locs:
		if "Wall_" in loc.name:
			yield loc
def filterWalls(loc):
	bad_item_names = [
		"MaxHPUP", "MaxMPUp", "MaxBulletUP", #Max HP/MP/Bullet upgrades
		"ChangeHP", #Dunno what this is
	]
	for name in bad_item_names:
		if name in loc.rare_item.name["Value"]:
			print("Rejecting item: {}".format(name))
			return False
		if name in loc.common_item.name["Value"]:
			print("Rejecting item: {}".format(name))
			return False
	return True
	
class Patch():
	def __init__(self, offset, value):
		self.offset = offset
		self.value = value
	def __repr__(self):
		return "Patch(offset={}, value={})".format(self.offset, self.value)

def clearAllDrops(locs):
	patches = []
	for loc in locs:
		patches.append(Patch(loc.shard.index["offset"], empty_drop.index["Value"]))
		patches.append(Patch(loc.shard.rate["offset"], 0.0))
		patches.append(Patch(loc.rare_item.index["offset"], empty_drop.index["Value"]))
		patches.append(Patch(loc.rare_item.quantity["offset"], 0))
		patches.append(Patch(loc.rare_item.rate["offset"], 0.0))
		patches.append(Patch(loc.common_item.index["offset"], empty_drop.index["Value"]))
		patches.append(Patch(loc.common_item.quantity["offset"], 0))
		patches.append(Patch(loc.common_item.rate["offset"], 0.0))
		patches.append(Patch(loc.rare_ingredient.index["offset"], empty_drop.index["Value"]))
		patches.append(Patch(loc.rare_ingredient.quantity["offset"], 0))
		patches.append(Patch(loc.rare_ingredient.rate["offset"], 0.0))
		patches.append(Patch(loc.common_ingredient.index["offset"], empty_drop.index["Value"]))
		patches.append(Patch(loc.common_ingredient.quantity["offset"], 0))
		patches.append(Patch(loc.common_ingredient.rate["offset"], 0.0))
		patches.append(Patch(loc.coin.index["offset"], empty_coin.index["Value"]))
		patches.append(Patch(loc.coin.override["offset"], empty_coin.override["Value"]))
		patches.append(Patch(loc.coin.rate["offset"], 100.0))
	return patches
	
def assignShards(orig, new):
	patchset = []
	for orig, new in zip(orig,new):
		patchset.append( Patch(orig.shard.index["offset"], new.index["Value"]) )
		patchset.append( Patch(orig.shard.rate["offset"], new.rate["Value"]))
	return patchset
def assignRareItems(origs, news):
	patchset = []
	for orig, new in zip(origs, news):
		patchset.append( Patch(orig.rare_item.index["offset"], new.index["Value"]))
		patchset.append( Patch(orig.rare_item.quantity["offset"], new.quantity["Value"]))
		patchset.append( Patch(orig.rare_item.rate["offset"], new.rate["Value"]))
	return patchset
def assignCommonItems(origs, news):
	patchset = []
	for orig, new in zip(origs, news):
		patchset.append( Patch(orig.common_item.index["offset"], new.index["Value"]))
		patchset.append( Patch(orig.common_item.quantity["offset"], new.quantity["Value"]))
		patchset.append( Patch(orig.common_item.rate["offset"], new.rate["Value"]))
	return patchset
def assignRareIngredients(origs, news):
	patchset = []
	for orig, new in zip(origs, news):
		patchset.append( Patch(orig.rare_ingredient.index["offset"], new.index["Value"]))
		patchset.append( Patch(orig.rare_ingredient.quantity["offset"], new.quantity["Value"]))
		patchset.append( Patch(orig.rare_ingredient.rate["offset"], new.rate["Value"]))
	return patchset
def assignCommonIngredients(origs, news):
	patchset = []
	for orig, new in zip(origs, news):
		patchset.append( Patch(orig.common_ingredient.index["offset"], new.index["Value"]))
		patchset.append( Patch(orig.common_ingredient.quantity["offset"], new.quantity["Value"]))
		patchset.append( Patch(orig.common_ingredient.rate["offset"], new.rate["Value"]))
	return patchset
def assignCoins(origs, news):
	patchset = []
	for orig, new in zip(origs, news):
		if new.rate["Value"] == 0.0:
			continue
		patchset.append( Patch(orig.coin.index["offset"], new.index["Value"]))
		patchset.append( Patch(orig.coin.override["offset"], new.override["Value"]))
		patchset.append( Patch(orig.coin.rate["offset"], new.rate["Value"]))
	return patchset
	
def applyPatches(raw, patches):
	stream = BytesIO(raw)
	for patch in patches:
		stream.seek(patch.offset)
		if isinstance(patch.value, int):
			stream.write(struct.pack("i", patch.value))
		elif isinstance(patch.value, float):
			stream.write(struct.pack("f", patch.value))
		else:
			raise NotImplementedError(type(patch.offset))
	return stream.getbuffer()
	
	
if __name__ == "__main__":
	import argparse
	
	parser = argparse.ArgumentParser( \
		description="Bloodstained drop randomizer",
		usage="%(prog)s --json [jsonfile] --input [infile] --output [outfile]"
		)
	parser.add_argument("--json", help="JSON dump of PB_DT_DropRateMaster.uasset", \
						action='store', required=True)
	parser.add_argument("--input", help="Original 'PB_DT_DropRateMaster.uasset' file", \
						action='store', required=True)
	parser.add_argument("--output", help="Filename for modified output", \
						action='store', required=True)
	parser.add_argument("--seed", help="Seed for randomizer", action='store', default=random.random())
	
	#Parse arguments
	args = parser.parse_args()

	#Set random seed
	random.seed(args.seed)
	
	#Open json dump
	#TODO: use the datatable-to-json.py file to generate from the original
	with open(args.json, "r") as file:
		raw = file.read()
	drop_rate_master = json.loads(raw)
	
	#get all possible locations with associated drops
	all_locations = [DropLocation(*getAllFromEntry(entry)) for entry in drop_rate_master]

	#get just chests
	all_chests = [loc for loc in allChests(all_locations) if filterChests(loc)]
	#get just mobs
	all_mobs = [loc for loc in allMobs(all_locations) if filterMobs(loc)]
	#get just walls
	all_walls = [loc for loc in allWalls(all_locations) if filterWalls(loc)]
	
	
	#Find empty/low drops to use if needed.
	#Since they can be copied endlessly without breaking anything it's a safe default drop.  Usually.
	#find empty coin to copy into all chests without a valid drop
	#FIXME: empty coin still screws up, using low-value coin instead
	empty_coin = [c.coin for c in all_chests if "D10\u0000" in c.coin.name["Value"]][0]
	#find empty drop
	empty_drop = [e.common_item for e in all_chests if "None" in e.common_item.name["Value"]][0]
	
	#Get list of all locations to be entered into the randomization pool
	combined = all_chests + all_mobs + all_walls 
	
	#list of patches to apply to the final file
	patches = []
	#Clear all drop slots
	patches += clearAllDrops(combined)
	
	#Get all items 
	shards = [loc.shard for loc in combined]
	rare_items = [loc.rare_item for loc in combined]
	common_items = [loc.common_item for loc in combined]
	rare_ingredients = [loc.rare_ingredient for loc in combined]
	common_ingredients = [loc.common_ingredient for loc in combined]
	coins = [loc.coin for loc in combined]
	
	#shuffle them all around
	random.shuffle(shards)
	random.shuffle(rare_items)
	random.shuffle(common_items)
	random.shuffle(rare_ingredients)
	random.shuffle(common_ingredients)
	random.shuffle(coins)
	
	#shuffle locations
	random.shuffle(combined)
	
	#TODO: N3006_OpeningDemo MUST HAVE VALID SHARD!
	
	#re-assign random shards to first len(shards) locations
	patches += assignShards(combined[: len(shards)], shards)
	#'' '' '' first len(rare_items) locations
	patches += assignRareItems(combined[: len(rare_items)], rare_items)
	#etc etc
	patches += assignCommonItems(combined[: len(common_items)], common_items)
	patches += assignRareIngredients(combined[: len(rare_ingredients)], rare_ingredients)
	patches += assignCommonIngredients(combined[: len(common_ingredients)], common_ingredients)
	patches += assignCoins(combined[: len(coins)], coins)
	
	#Should result in all shards/items/coins being re-assigned to somewhere.
	#Does nothing to guarantee things intended to be re-aquired like ingredients are infinitely available.
	
	
	#with open("PB_DT_DropRateMaster.uasset", "rb") as file:
	with open(args.input, "rb") as file:
		raw = file.read()
	
	mod = applyPatches(raw, patches)
	
	with open(args.output, "wb") as file:
		file.write(mod)
	
	sys.exit()