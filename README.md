# GameShuffler

This is a fork of [griffinbeels' GameShuffler](https://github.com/griffinbeels/GameShuffler), which was based off [DougDoug's](https://twitter.com/DougDougFood) code.

This program loads savestates you've made for your game at random, making for a mind-bending challenge! Test your multitasking skills when the game keeps changing on you!

## Features

- Easy-to-use Shuffler.exe file, no need to mess with python!
- Ability to change the minimum and maximum delays before switching instances
- Option to shut off the tts-style audio
- Unlocked the amount of savestates you can use, making the limit ""infinite""
- Functionality to set the amount of "instances" you want to play and randomly selecting from the savestates you have set up
- Compatible with multiple emulators
- Compatible with custom hotkeys
- ~~Ability to switch between multiple games~~ Coming soon!

## How to Use

- Double click the `Shuffler.exe` file. It'll open up a terminal with the game information.
- Keep the window visible, and then **keep your emulator focused**. You're pretty much set to go!
- The controls are **Spacebar** and **.** 
    - **Spacebar** starts the program, and how you mark instances as complete.
    - **.** is how you undo, if you accidentally mark one as complete, or the wrong one as complete. Note the [error](https://github.com/Artemis6425/GameShuffler/tree/master#known-issues).
    - If you want to end the game early, just close the terminal window the program opens.
- To set it up again after going, simply remove the `savestate#` files, and the savestate slot file the emulator was using. Copy/paste the backup you made into the folder again, and you're ready to go!

## Setup

### Emulator Setup

1. You'll have to find out where your emulator keeps its savestates. For this example, my installation of Project64 keeps savestates at `C:\Users\[username]\AppData\Local\VirtualStore\Program Files (x86)\Project64 1.6\Save`. Open up the folder, and open up your game of choice.
1. If you have savestates you care about, I recommend you back them up now, as this program messes with them a lot.
1. In the game, get to a point where you want the "instance" to start, and create a savestate there. You should see a new file in the folder (For example, `SUPER MARIO 64.pj1.zip`). For this first one, you'll name it `savestate1`, with no file extension. You'll want to continue in your game, creating savestates and renaming them `savestate2`, `savestate3` and so on.
1. Make a backup of all the `savestate#` files you've created, because they're effectively one-time-use
1. Remove the savestate files your emulator has created for the game

### Getting the files

1. [Download the latest release](https://github.com/Artemis6425/GameShuffler/releases/latest)
1. Extract to it's own folder, with all the other files with it. They're necessary for the Shuffler.exe file to run!

### Options.ini

1. There are brief explanations of what each line does, but there are a few that are mandatory to change, which we're doing now.
1. You want to update the `savestatePath` to the folder path of where your emulator keeps the savestates (this is the same one we were just messing with)
1. You also want to update the `totalSlots` depending on how many `savestate#` files you created. If you created 15, you'll want to set it to 15, like this: `totalSlots = 15`.
1. `slotToPlay` is asking how many games/instances you want to play. If you want to play all the ones you created, set it to the same number as `totalSlots`. If you want to play a randomized subset of the ones you made, make it any number under `totalSlots`.
1. `savestateFile` is what the emulator makes the names of the savestate. This usually is the name of the game with some fancy file extension, but we want to make sure we have it down properly. In the above section, mine was `SUPER MARIO 64.pj1.zip`. Replace the number that normally says the savestate slot with `@`!
1. `saveDelay` is the delay between saving the state and loading the next one. I've set this to `0.5` by default, as this works quite well for Project64. However, if you're having issues that say something like `File in use by another process`, then you need to increase this number. On the other hand, if you're noticing your emulator is saving them extremely quickly and you're just waiting around for it to load the next one, you can decrease it. Make sure you account for the savestates that randomly take way longer for no reason!
1. The last important thing you need to make sure is correct are the `savestateKey`, `loadstateKey` and `slotKey` hotkeys are correct. You can verify this by checking inside your emulator hotkey settings. Make sure you set them all to single-key binds!

### OBS Setup

If you want your stream to have an "INSTANCES LEFT" text box, do the few steps below:
1. In the `options.ini` file, change the `obsText` to be whatever you want. By default, it'll say `INSTANCES LEFT: x` but you can change it to whatever you'd like. Some decent suggestions are `RACES LEFT` and `STARS LEFT`.
1. Add a text source to your layout and name it whatever you want.
1. Instead of writing your own text, click "Read from file".
1. Click "Browse" and locate the "OBS Text.txt" file that is in the program folder. It's that easy!

From here, you should be completely set up! Change the settings as you see fit, and hop back up to [How to Use](https://github.com/Artemis6425/GameShuffler/tree/master#how-to-use)

## Known issues

- Undoing causes a `KeyError` in the terminal. As far as I can tell, this is purely visual. Undoing works as intended.
    - When undoing the 2nd to last instance, the script outputs an *even bigger* `KeyError`. This is still purely visual.

## Future ideas

- A version that instead of multiple savestates, uses multiple instances of your emulator. This would allow you to do multi-game Shuffles
- A usable GUI
- The ability to instead look at the emulator window directly to be able to tell the moment it's done saving the savestate. This would allow the program to load the next instance even faster

## Changelog

### v1 "All Initial Features!"

- Initial release! Functioning as long as you don't do anything too complicated.

### v2 "Bugfixed and Better than ever"

- Updated options file, fixed a few bugs

### v3 "The 'Actually Working' Release"

- Re-introduced the bug that causes the `KeyError` to show up when undoing. Purely visual error, it will properly undo.
    - That in mind, the "Final undo" error still exists!
- Changed when the `last_swap` variable is defined, now adds a "blackout period" for hitting space. This fixes an issue where if you hit space at the wrong time, it would remove the wrong instance from the queue.
- Removed unnecessary variabls from code, made it slightly easier to read.

### v3.1 "More Bugs Removed"

- Removed all references to OBS_websocket, and replaced it with the much simpler "OBS Text.txt"
- Removed a bug where sometimes the emulator would not detect the save/load keypresses from the program
- Renamed "Star Collected.wav" to "Instance Completed.wav" to be more generic

### v4 "All Bugs Gone... Hopefully"

- Updated the `options.ini` with the following changes:
    - Updated the wording on some of the help text to clarify things better
    - Combined the `savestateName` and `fileExtension` variables into a new one, `savestateFile`
    - Renamed `slotCount` to `slotsToPlay`, to make it more clear what the variable is changing
    - Changed the default state of `useAudio` to off, because I think it's annoying lol
    - Added a new option, `obsText`, which lets you change what the text before the colon in OBS is
- Added a reminder in the console text to have your emulator focused before starting
- **Fixed the bug that didn't allow you to undo the second to last split**. (This still outputs a large `KeyError`, but works as intended.)
- Fixed the bug that didn't let you finish the final instance
- Fixed the bug where hitting the undo hotkey would immediately switch your instance.