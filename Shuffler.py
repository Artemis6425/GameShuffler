import random
import time
import keyboard
import threading
import sys
import os
import configparser
from AudioPlayer import AudioManager
from collections import deque

config = configparser.ConfigParser()
config.read('options.ini')

MINIMUM_SLOT_TIME = int(config['SETTINGS']['minimumDelay']) # The minimum time we'll play a specific save slot
MAXIMUM_SLOT_TIME = int(config['SETTINGS']['maximumDelay']) # The minimum time we'll play a specific save slot
savestate_path = config['SETTINGS']['savestatePath'] # The path where the savestates are located
slot_bank = list(range(1, int(config['SETTINGS']['totalSlots'])+1)) # The amount of slots the user has created
slot_bank = list(map(str,slot_bank))
remaining_slots = random.sample(slot_bank, int(config['SETTINGS']['slotsToPlay'])) # This is what picks the slots to actually play
USE_AUDIO = config['SETTINGS'].getboolean('useAudio')
HARD_MODE = config['SETTINGS'].getboolean('hardMode')
ss_name = config['SETTINGS']['savestateFile']
save_delay = float(config['SETTINGS']['saveDelay']) - 0.1

REMOVED_SLOTS_STACK = deque()
current_slot = None  # The current game slot
emu_slot = config['SETTINGS']['slotKey'] # This is the slot the emu will actually load
previous_slot = None  # The previous game slot
delayed_previous_slot = None # This lets the file moving see the previous slots before it's overwritten
multiple_slots_remain = True
audio_manager = AudioManager()
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

    # After it goes down to 1 instance, swap_game runs constantly. This is why I added the below if statement
    if multiple_slots_remain:
        last_swap = time.time()  # Store the current time
        obstxt_update(f"INSTANCES LEFT: {len(remaining_slots)}") # Update OBS text

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
        delayed_previous_slot = previous_slot
        if USE_AUDIO:
            audio_manager.play_audio("Final Level.wav",False,False)
        update_state()
    elif len(remaining_slots) == 0: # Challenge completed!
        if USE_AUDIO:
            audio_manager.play_audio("You Have Completed The Challenge.wav",False,False)
        print("CONGRATULATIONS! YOU MAY NOW POG. Feel free to close this program now and try again :D")
        obstxt_update(f"CHALLENGE COMPLETE")
        waiting_thread.wait(timeout=5)
        waiting_thread.set()
        sys.exit()

    # LOAD THE SLOT2
    if multiple_slots_remain:
        update_state()

def update_state():
    global first_run, last_swap

    keyboard.send(emu_slot) # Select the slot we want to save & load from
    if not first_run:
        keyboard.press(SAVE_SLOT_KEY)
        waiting_thread.wait(timeout=0.1)
        keyboard.release(SAVE_SLOT_KEY)
        # This is the delay to give the emulator time to save before swapping files to load to
        waiting_thread.wait(timeout=save_delay)

    print(f"\nSWAPPING TO INSTANCE {current_slot}!\n")
    switch_file()
    first_run = False
    keyboard.press(LOAD_SLOT_KEY)
    waiting_thread.wait(timeout=0.1)
    keyboard.release(LOAD_SLOT_KEY)
    
    if not HARD_MODE:
        print(f"Remaining Instance Count: {len(remaining_slots)}\n")

    if multiple_slots_remain:
        # Wait random amount of time
        random_time = random.randint(MINIMUM_SLOT_TIME, MAXIMUM_SLOT_TIME) * (1/sleep_time)  # Multiply by inverse of sleep_time. We do this so that we can run this function every 0.1 seconds instead of every second, to make it feel more responsive
        if not HARD_MODE:
            print(f"Waiting for {int(random_time/10)} seconds\n")
        for i in range(int(random_time)):  # Make sure to cast to an int, as it could be a float
            if stop_thread.is_set() or not GAME_ACTIVE:
                break
            waiting_thread.wait(timeout=sleep_time)


# Runs on separate thread and alerts swap_game() if spacebar is pressed
def spacebar_listener():
    global last_spacebar, current_slot, delayed_previous_slot, previous_slot
    while GAME_ACTIVE:
        keyboard.wait('space')  # Wait for space bar
        if time.time() - last_swap >= 1 and time.time() - last_spacebar >= SPACEBAR_COOLDOWN:  # Check if enough time has passed since the last game swap, and if enough time has passed since the last spacebar interrupt
            last_spacebar = time.time()  # Store the current time
            if current_slot and current_slot in remaining_slots:
                remaining_slots.remove(current_slot)
                REMOVED_SLOTS_STACK.append(current_slot)
                print(f"Removed {current_slot} from remaining_slots\n")
            stop_thread.set()  # Signal the other thread to stop2
            if len(remaining_slots) > 1:
                if USE_AUDIO:
                    audio_manager.play_audio("Instance Completed.wav",False,False)
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
def switch_file():
    global savestate_path, ss_name, first_run, emu_slot, delayed_previous_slot, current_slot
    tempFileName = ss_name.replace("@", emu_slot)

    if not first_run:
        if current_slot != previous_slot:
            new_banked_file = os.path.join(savestate_path, f"savestate{previous_slot}")
        else:
            new_banked_file = os.path.join(savestate_path, f"savestate{delayed_previous_slot}")
        old_active_file = os.path.join(savestate_path, f"{tempFileName}")
        
        os.rename(old_active_file, new_banked_file)

    old_banked_file = os.path.join(savestate_path, f"savestate{current_slot}")
    new_active_file = os.path.join(savestate_path, f"{tempFileName}")
    os.rename(old_banked_file, new_active_file)

#this just opens and closes the OBS Text.txt file, and passes in the text we want it to say
def obstxt_update(text):
    obstxt = open("OBS Text.txt", "w")
    obstxt.write(text)
    obstxt.close()

######################################################################

try:
    print("\nPRESS SPACEBAR TO BEGIN CHALLENGE!\n(make sure to have your emulator focused!)\n\n")
    obstxt_update(f"INSTANCES LEFT: {len(remaining_slots)}")
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