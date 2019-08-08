# bloodstained-randomizer
Bloodstained drop randomizer

## Description
Modifies the `PB_DT_DropRateMaster.uasset` file from Bloodstained to randomize drops.
Most definitely **alpha quality**!  Not ready for general usage, still requires significant knowledge to use correctly.

~~TODO: Merge in the json dumper and `.pak` packer to produce a final output.~~

## Usage

```
usage: randomizer.py --input [infile]

Bloodstained drop randomizer

optional arguments:
  -h, --help       show this help message and exit
  --input INPUT    Original 'PB_DT_DropRateMaster.uasset' file
  --seed SEED      Seed for randomizer
```

Normal usage:

`python randomizer.py --input PB_DT_DropRateMaster.uasset --seed "omg so random lol"`

`PB_DT_DropRateMaster.uasset` : Original uasset from the Bloodstained install

If all goes well a file named `Randomizer.pak` should be created in the top directory.  This is the mod.
