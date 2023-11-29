# GameShuffler

This is a fork of [griffinbeels' GameShuffler](https://github.com/griffinbeels/GameShuffler), which was based off [DougDoug's](https://twitter.com/DougDougFood) code.

This program loads savestates you've made for your game at random, making for a mind-bending challenge! Test your multitasking skills when the game keeps changing on you!

## Features

- Ability to change the minimum and maximum delays before switching instances
- Option to shut off the tts-style audio
- Unlocked the amount of savestates you can use, making the limit ""infinite""
- Functionality to set the amount of "instances" you want to play and randomly selecting from the savestates you have set up
- ~~Compatible with multiple emulators~~ Coming soon!
- ~~Compatible with custom hotkeys~~ Coming soon!

## How to Use

-run the program by typing `python Shuffler.py`
-The controls are **Spacebar** and **.**. 
    -**Spacebar** starts the program, and how you mark instances as complete.
    -**.** is how you undo, if you accidentally mark one as complete, or the wrong one as complete.

## Setup

### Emulator Setup

1. You'll have to find out where your emulator keeps its savestates. For this example, my installation of Project64 keeps savestates at `C:\Users\[username]\AppData\Local\VirtualStore\Program Files (x86)\Project64 1.6\Save`. Open up the folder, and open up your game of choice.
1. If you have savestates you care about, I recommend you back them up now, as this program messes with them a lot.
1. In the game, get to a point where you want the "instance" to start, and create a savestate there. You should see a new file in the folder (For example, `SUPER MARIO 64.pj1.zip`). For this first one, you'll name it `savestate1`, with no file extension. You'll want to continue in your game, creating savestates and renaming them `savestate2`, `savestate3` and so on.
1. Make a backup of all the `savestate#` files you've created, because they're effectively one-time-use
1. Remove the savestate files your emulator has created for the game

### Options.ini

1. There are brief explanations of what each line does, but there are a few that are mandatory to change, which we're doing now.
1. You want to update the `savestatePath` to the folder path of where your emulator keeps the savestates (this is the same one we were just messing with)
1. You also want to update the `totalSlots` depending on how many `savestate#` files you created. If you created 15, you'll want to set it to 15, like this: `totalSlots = 15`.
1. `slotCount` is asking how many games/instances you want to play. If you want to play all the ones you created, set it to the same number as `totalSlots`. If you want to play a randomized subset of the ones you made, make it any number under `totalSlots`.
1. `savestateName` is what the emulator makes the names of the savestate. This usually is the name of the game, but we want to make sure we have it down properly. In the above section, mine was `SUPER MARIO 64`. Make sure this doesn't include the file extension.

### The Code Itself

it's not super user friendly yet since I don't want to release without all the features, but this is how to get it to work for now:

1. Install Python 3.10.6 (should work on similar versions, untested though)
1. Clone/download the repository.
1. Open a terminal in the directory the files in, and type `pip install -r requirements.txt`. This will install all the dependencies for the program.

From here, you should be completely set up! Change the settings as you see fit, and hop back up to How to Use