import random
import time
import keyboard
import threading
import sys
import os
import configparser
from AudioPlayer import AudioManager
from OBS_Websockets import OBSWebsocketsManager
from collections import deque

config = configparser.ConfigParser()
config.read('options.ini')

MINIMUM_SLOT_TIME = int(config['SETTINGS']['minimumDelay']) # The minimum time we'll play a specific save slot
MAXIMUM_SLOT_TIME = int(config['SETTINGS']['maximumDelay']) # The minimum time we'll play a specific save slot
savestate_path = config['SETTINGS']['savestatePath'] # The path where the savestates are located
slot_bank = list(range(1, int(config['SETTINGS']['totalSlots'])+1)) # The amount of slots the user has created
slot_bank = list(map(str,slot_bank))
remaining_slots = random.sample(slot_bank, int(config['SETTINGS']['slotCount'])) # This is what picks the slots to actually play
USE_AUDIO = config['SETTINGS'].getboolean('useAudio')
HARD_MODE = config['SETTINGS'].getboolean('hardMode')
ss_name = config['SETTINGS']['savestateName']
fileExt = config['SETTINGS']['fileExtension']

USING_OBS_WEBSOCKETS = False # Whether or not program should display the # of remaining stars in OBS
OBS_TEXT_SOURCE = "STARS LEFT" # Name this whatever text element you want to update in OBS

REMOVED_SLOTS_STACK = deque()
current_slot = None  # The current game slot
current_emu_slot = config['SETTINGS']['slot1Key'] # This is the slot the emu will actually load
inactive_emu_slot = config['SETTINGS']['slot2Key']
previous_slot = None  # The previous game slot
delayed_previous_slot = None # This lets the file moving see the previous slots before it's overwritten
multiple_slots_remain = True
audio_manager = AudioManager()
if USING_OBS_WEBSOCKETS:
    obswebsockets_manager = OBSWebsocketsManager()
stop_thread = threading.Event()
waiting_thread = threading.Event()
sleep_time = 0.1  # Amount of time to sleep, in seconds
last_swap = 0  # The time when the last game swap happened
last_spacebar = 0  # The time when the last spacebar interrupt occurred
last_undo = 0
SPACEBAR_COOLDOWN = 2  # Cooldown time for the spacebar interrupt, in seconds
GAME_ACTIVE = True

SAVE_SLOT_KEY = config['SETTINGS']['savestateKey']
LOAD_SLOT_KEY = config['SETTINGS']['loadstateKey']

first_run = True

def swap_game():
    global last_swap, current_slot, previous_slot, multiple_slots_remain, first_run, delayed_previous_slot
    
    # Update OBS text
    if USING_OBS_WEBSOCKETS:
        obswebsockets_manager.set_text(OBS_TEXT_SOURCE, f"INSTANCES LEFT: {len(remaining_slots)}")

    # Swap to new slot
    if len(remaining_slots) > 1: # If there's at least 2 unfinished slots, load a new random slot
        while True: # Pick new random slot that isn't the same as previous
            current_slot = random.choice(remaining_slots)
            delayed_previous_slot = previous_slot
            if current_slot != previous_slot:
                previous_slot = current_slot
                break
    elif len(remaining_slots) == 1 and multiple_slots_remain: # If this is the first time we've gotten to the last slot, we swap to it, then set a flag so that we don't swap again
        multiple_slots_remain = False
        current_slot = random.choice(remaining_slots)
        if USE_AUDIO:
            audio_manager.play_audio("Final Level.wav",False,False)
        update_state()
    elif len(remaining_slots) == 0: # Challenge completed!
        if USE_AUDIO:
            audio_manager.play_audio("You Have Completed The Challenge.wav",False,False)
        print("CONGRATULATIONS! YOU MAY NOW POG. Feel free to close this program now and try again :D")
        if USING_OBS_WEBSOCKETS:
            obswebsockets_manager.set_text(OBS_TEXT_SOURCE, f"ANY PRIMERS???")
        waiting_thread.wait(timeout=5)
        waiting_thread.set()
        sys.exit()

    # LOAD THE SLOT2
    if multiple_slots_remain:
        update_state()

def update_state():
    global first_run
    rename_file(current_emu_slot,current_slot,"toActive")

    keyboard.send(current_emu_slot)
    keyboard.press(LOAD_SLOT_KEY)
    waiting_thread.wait(timeout=0.1)
    keyboard.release(LOAD_SLOT_KEY)
    
    
    print(f"SWAPPING TO INSTANCE {current_slot}!\n")
    

    last_swap = time.time()  # Store the current time
    if not HARD_MODE:
        print(f"Remaining Instance Count: {len(remaining_slots)}\n")

    if not first_run:
        rename_file(inactive_emu_slot, delayed_previous_slot,"toBank")
    first_run = False

    if multiple_slots_remain:
        # Wait random amount of time
        random_time = random.randint(MINIMUM_SLOT_TIME, MAXIMUM_SLOT_TIME) * (1/sleep_time)  # Multiply by inverse of sleep_time. We do this so that we can run this function every 0.1 seconds instead of every second, to make it feel more responsive
        if not HARD_MODE:
            print(f"Waiting for {int(random_time/10)} seconds\n")
        for i in range(int(random_time)):  # Make sure to cast to an int, as it could be a float
            if stop_thread.is_set() or not GAME_ACTIVE:
                break
            waiting_thread.wait(timeout=sleep_time)



    # Select & save
    keyboard.send(current_emu_slot)
    keyboard.press(SAVE_SLOT_KEY)

    # Wait 0.1 seconds inbetween save->load, so that PJ64 can process it
    waiting_thread.wait(timeout=.1)

    # Release keys
    keyboard.release(SAVE_SLOT_KEY)

    # Immediately switches what slot button to press after saving
    flip_slot()

    waiting_thread.wait(timeout=0.1)


# Runs on separate thread and alerts swap_game() if spacebar is pressed
def spacebar_listener():
    global last_spacebar, current_slot, delayed_previous_slot
    while GAME_ACTIVE:
        keyboard.wait('space')  # Wait for space bar
        if time.time() - last_swap >= 1 and time.time() - last_spacebar >= SPACEBAR_COOLDOWN:  # Check if enough time has passed since the last game swap, and if enough time has passed since the last spacebar interrupt
            last_spacebar = time.time()  # Store the current time
            if current_slot and current_slot in remaining_slots:
                delayed_previous_slot = current_slot
                remaining_slots.remove(current_slot)
                REMOVED_SLOTS_STACK.append(current_slot)
                print(f"Removed {current_slot} from remaining_slots\n")
            stop_thread.set()  # Signal the other thread to stop
            if len(remaining_slots) > 1:
                if USE_AUDIO:
                    audio_manager.play_audio("Star Collected.wav",False,False)
            break

# Listener for undo (press .)
def undo_listener():
    global last_undo, current_slot
    while GAME_ACTIVE:
        keyboard.wait('.')  # Wait for undo
        if time.time() - last_swap >= 1 and time.time() - last_undo >= SPACEBAR_COOLDOWN:  # Check if enough time has passed since the last game swap, and if enough time has passed since the last spacebar interrupt
            last_undo = time.time()  # Store the current time
            if len(REMOVED_SLOTS_STACK) >= 1:
                undone_slot = REMOVED_SLOTS_STACK.pop()
                remaining_slots.append(undone_slot)
                print(f"Undid removal of {undone_slot}. Added back to remaining_slots.\n")
            stop_thread.set()  # Signal the other thread to stop
            break

#This removes/places savestats into the "bank"
def rename_file(v1, v2, v3):
    #v1 is _emu_slot, v2 is v2 is _slot, v3 is "toBank" or "toActive"
    global savestate_path, ss_name, fileExt
    tempFileExt = fileExt.replace("@", v1)
    if v3 == "toBank":
        old_file = os.path.join(savestate_path, f"{ss_name}{tempFileExt}")
        new_file = os.path.join(savestate_path, f"savestate{v2}")
    elif v3 == "toActive":
        old_file = os.path.join(savestate_path, f"savestate{v2}")
        new_file = os.path.join(savestate_path, f"{ss_name}{tempFileExt}")
    os.rename(old_file, new_file)

#just flips what slot is available to load
def flip_slot():
    global current_emu_slot, inactive_emu_slot
    current_emu_slot, inactive_emu_slot = inactive_emu_slot,current_emu_slot

######################################################################

try:
    print("\nPRESS SPACEBAR TO BEGIN CHALLENGE!\n")
    if USE_AUDIO:
        audio_manager.play_audio("Press Spacebar To Begin.wav", False)
    keyboard.wait('space')

    if USE_AUDIO:
        audio_manager.play_audio("Starting in 3 2 1.wav", False)
    countdown = 3
    while countdown > 0 and GAME_ACTIVE:
        print(f"STARTING IN {countdown}\n")
        countdown -= 1
        waiting_thread.wait(timeout=1)

    while GAME_ACTIVE:
        stop_thread.clear()
        spacebar_listener_thread = threading.Thread(target=spacebar_listener)
        spacebar_listener_thread.start()

        undo_listener_thread = threading.Thread(target=undo_listener)
        undo_listener_thread.start()

        swap_game()

        while spacebar_listener_thread.is_alive() and GAME_ACTIVE:  
            # the spacebar_listener_thread thread is still waiting for the space bar, so let's start a new game
            stop_thread.clear()
            swap_game()

except KeyboardInterrupt:
    # quit
    print("Thanks for playing! Exiting now.\n")
    waiting_thread.set()
    stop_thread.set()
    GAME_ACTIVE = False
    sys.exit()