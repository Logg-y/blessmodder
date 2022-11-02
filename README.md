# Blessmodder

This is a tool that modifies Dominions 5 executables to change the array of possible bless effects.

Illwinter very kindly set up the new bless effect system using a data table that can easily be edited in a platform-independent way without needing to alter instructions. Not only is it easy to modify, but the vast majority of unit abilities can be made into their own bless effects, simply by finding and altering this table.

This requires a copy of Dominions 5 to use. Please, respect Illwinter and **DO NOT** share original or modified Dominions executables directly. This is set up to allow the passing around of .dbm files, dm-like files which allow this program to modify the main game executable. 

## Running

Copy the blessmodder executable and the .dbm bless mod files into the folder containing the Dominions executable you run.

For 64bit Windows users, this is Steam/SteamApps/common/Dominions5/win64.
For everyone else, this is just Steam/SteamApps/common/Dominions5.

Windows users can use the .exe provided in releases. Otherwise, the blessmodder.py python file can be used directly as it has no external dependencies, and should hopefully work on almost any version of Python 3.

Running this will attempt to apply all found .dbm files to all executables in the folder. This will create a handful of new executables, named after the .dbm file loaded into them. It is then necessary to run the correspondingly named executable to get its effects (**not** running the game through Steam).

Some antivirus vendors seem to incorrectly flag all executables built with PyInstaller as malicious. There is not much I can do about this, the alternatives I am aware of do not support the all-in-one-file approach that keeps your Dominions folder quite clean. If this bothers you, you can install Python 3 on Windows which will allow you to run this from source. I have nothing to hide here, or this would not be open source.

## Caveats

To my knowledge, no automated public Dominions hosting service supports running modified executables. At the time of writing, playing multiplayer with this will require someone to host a game locally.

Most custom bless effects will NOT show in the bless effect list when you click on the lit candelabra icon on a blessed unit's unit card, or the temple button on the strategic map. Fixing this would require modifying actual code/instructions which will be different in all of the builds of Dominions.

There is nothing preventing opening non-blessmodded games with a bless modded executable, but battle reports involving blessed units with go out of sync. So long as the game is hosted on the correct version, the only side effect here are the replay issues.

A pretender created with a bless modded executable will likely produce some form of invalid pretender if submitted to a game with a different bless effect set, much like modded pretenders do in vanilla. This should be correctly flagged as cheating by the usual system.

Multiple scale requirements are supported, but unfortunately the game renders their icons very nearly on top of each other.

It is not possible to make an incarnate bless with a bless point cost lower than 5. 

## Bless Mod File Documentation

It is probably worth being familiar with basic .dm syntax and structures before moving on to writing these.

Bless mod files must be saved with the .dbm extension. This was made up arbitrarily (for **D**ominions **B**less **M**od), but this program will only look for bless mod files with this extension.

This repository contains an example bless mod for reference.

Unlike .dm files, there are no top-level name files. Two dashes (--) can (and should) be used to denote comments, either on the end of lines or on lines of their own. Only the following commands are valid:

  * **\#selectbless** (id)
    * Selects the given bless ID. The valid ID range is 0 through 99 inclusive. 
    * Bless effect 0 contains the inherent Morale +1 effect that all player blesses get for free. This may be edited. Giving it a cost is unwise as its cost will be deducted from *every* pretender creation. 
    * The game stops reading bless effects after finding the first empty bless effect, which means that any actual effects after a "gap" or empty bless effect will be ignored. A clumsy dump of vanilla bless effects and IDs can be found in this repository.
  * **\#clear**
    * Clears all data for the selected bless effect, much like the #clear command in normal .dm files.
  * **\#cleareffects**
    * Clears all effect data for the selected bless effect. This includes #multipick and #alwaysactive, but not scales or path requirements.
  * **\#clearscales**
    * Clears all scale requirements for the selected bless effect.
  * **\#addeffect** (effect id) (effect magnitude)
    * Adds an effect to the selected bless effect slot. A single bless effect may have up to 7 total effects, use this command multiple times to add several.
    * Effect ID refers to the internal effect IDs, which some modders may recognise from using effect numbers 500-699. A hopefully mostly-complete and correct list of these can be found [here](https://docs.google.com/spreadsheets/d/1G2pZXwdo_c_QxLmIBZhl1E-UNGma__I9yuZTmJiuMhE). Note that some effects do NOT work when added this way.
    * For the sake of readability, it is good practice to comment what effect IDs are when adding them this way.
    * Effect magnitude is the amount of this effect to add when the bless is active. Some effects do not matter, so long as their value is nonzero. Negative values may also be used, which may also disable the use of certain abilities. For instance, assassins can only assassinate if their final assassin ability value is greater than zero, therefore subtracting a large value from the assassin ability value in the bless would cause the bless to make sacred assassins unable to assassinate.
  * **\#reqscale** (scale id) (scale amount)
    * Makes this bless effect require scales. Up to four different scale requirements can be used together on a single effect, but their icons will overlap quite a lot on the bless selection screen. Use this command multiple times to add several.
    * Negative values can be used to make a bless require positive scale effects.
    * The scales are as follows:
      * 0: Turmoil
      * 1: Sloth
      * 2: Cold
      * 3: Death
      * 4: Misfortune
      * 5: Drain
  * **\#effect10buffs** (buff mask)
    * Makes the bless apply effects from the "type 1 buffs" spell effect (effect 10). The buff mask should be the damage value used for a corresponding spell. A full list of available values can be found [here](https://github.com/larzm42/dom5inspector/blob/gh-pages/gamedata/buffs_1_types.csv).
    * As with the vanilla Quickness bless, buffs added this way count as the same effect as their normal spell counterparts, and as such do not stack with them.
    * This command should not be used multiple time to combine multiple buff effects: add together the buff masks and use a single command to achieve this.
    * This command does *not* use up one of the seven allowed effect slots.
  * **\#multipick**
    * Makes this bless effect able to be picked multiple times (with the effect stacking for each pick), like vanilla's Undying. This takes up one of the seven allowed effect slots.
  * **\#alwaysactive**
    * Makes this bless effect always active on all sacred units, even on the strategic map, like vanilla's Larger and Wind Walkers. This takes up one of the seven allowed effect slots.
  * **\#name** "Bless Effect Name"
    * This sets the name of the bless effect on the pretender creation screen. The maximum allowed length is 31 characters.
  * **\#path1** (primary path ID)
    * Sets the primary path requirement for this bless effect. Path IDs are the same as for spells, that is to say:
      * 0: Fire
      * 1: Air
      * 2: Water
      * 3: Earth
      * 4: Astral
      * 5: Death
      * 6: Nature
      * 7: Blood
  * **\#path2** (secondary path ID)
    * Sets the secondary path requirement for this bless effect. In addition to the above values, -1 may be used to represent no secondary path.
  * **\#path1level** (primary path bless point cost)
    * Sets the bless point cost for the primary path. This must be a value between 0 and 20 inclusive.
  * **\#path2level** (secondary path bless point cost)
    * Sets the bless point cost for the secondary path. This must be a value between 0 and 20 inclusive.
  * **\#end**
    * Use to stop editing the selected bless effect slot.
  
    
An effect is incarnate if it has a path 1 level of 5 or higher. Non-incarnate higher level effects can be made by setting path2 to the same as path1, which will cause the split costs to be added together. The example bless mod contains an example of a non-incarnate N7 bless using this trick.

## Technical stuff

I wrote a bit about the bless table format [here](https://docs.google.com/spreadsheets/d/1kK1nb0Sse2DZg-cyjPappypgIE_lpnPmLIKCqpdYRJ8/edit#gid=0). It's not terribly formal, but it might help somebody.

## Thanks

Illwinter, for making Dominions, and for making bless data in such a nice table that permits so many new options.
