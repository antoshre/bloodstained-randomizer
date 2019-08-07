# bloodstained-randomizer
Bloodstained drop randomizer

## Description
Modifies the `PB_DT_DropRateMaster.uasset` file from Bloodstained to randomize drops.
Most definitely **alpha quality**!  Not ready for general usage, still requires significant knowledge to use correctly.

TODO: Merge in the json dumper and `.pak` packer to produce a final output.

## Usage

```
usage: randomizer.py --json [jsonfile] --input [infile] --output [outfile]

Bloodstained drop randomizer

optional arguments:
  -h, --help       show this help message and exit
  --json JSON      JSON dump of PB_DT_DropRateMaster.uasset
  --input INPUT    Original 'PB_DT_DropRateMaster.uasset' file
  --output OUTPUT  Filename for modified output
  --seed SEED      Seed for randomizer
```

Normal usage:

`python randomizer.py --json PB_DT_DropRateMaster.json --input PB_DT_DropRateMaster.uasset --output modified.uasset --seed "omg so random lol"`

`PB_DT_DropRateMaster.json` : JSON dump of the original uasset using [the uasset-dt-to-json dumper](https://github.com/thegreatunclean/uasset-dt-to-json)
`PB_DT_DropRateMaster.uasset` : Original uasset from the Bloodstained install
`modified.uasset` : Modified uasset file, needs to be put into `.pak` to be used.
