import random
import time
import keyboard
import threading
import sys
from AudioPlayer import AudioManager
from OBS_Websockets import OBSWebsocketsManager
from collections import deque

MINIMUM_SLOT_TIME = 3 # The minimum time we'll play a specific save slot
MAXIMUM_SLOT_TIME = 10 # The minimum time we'll play a specific save slot

USING_OBS_WEBSOCKETS = False # Whether or not program should display the # of remaining stars in OBS
OBS_TEXT_SOURCE = "STARS LEFT" # Name this whatever text element you want to update in OBS

REMOVED_SLOTS_STACK = deque()
remaining_slots = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
current_slot = None  # The current game slot
previous_slot = None  # The previous game slot
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

SAVE_SLOT_KEY = "F5"
LOAD_SLOT_KEY = "F7"

def swap_game():
    global last_swap, current_slot, previous_slot, multiple_slots_remain
    
    # Update OBS text
    if USING_OBS_WEBSOCKETS:
        obswebsockets_manager.set_text(OBS_TEXT_SOURCE, f"STARS LEFT: {len(remaining_slots)}")

    # Swap to new slot
    if len(remaining_slots) > 1: # If there's at least 2 unfinished slots, load a new random slot
        while True: # Pick new random slot that isn't the same as previous
            current_slot = random.choice(remaining_slots)
            if current_slot != previous_slot:
                previous_slot = current_slot
                break
    elif len(remaining_slots) == 1 and multiple_slots_remain: # If this is the first time we've gotten to the last slot, we swap to it, then set a flag so that we don't swap again
         multiple_slots_remain = False
         current_slot = random.choice(remaining_slots)
         audio_manager.play_audio("Final Level.wav",False,False)
         update_state()
    elif len(remaining_slots) == 0: # Challenge completed!
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
    keyboard.send(current_slot)
    keyboard.press(LOAD_SLOT_KEY)
    waiting_thread.wait(timeout=0.1)
    keyboard.release(LOAD_SLOT_KEY)
    print(f"\nSWAPPING TO SLOT {current_slot}!\n")

    last_swap = time.time()  # Store the current time
    print(f"Remaining Slots: {remaining_slots}\n")

    if multiple_slots_remain:
        # Wait random amount of time
        random_time = random.randint(MINIMUM_SLOT_TIME, MAXIMUM_SLOT_TIME) * (1/sleep_time)  # Multiply by inverse of sleep_time. We do this so that we can run this function every 0.1 seconds instead of every second, to make it feel more responsive
        print(f"Waiting for {int(random_time/10)} seconds\n")
        for i in range(int(random_time)):  # Make sure to cast to an int, as it could be a float
            if stop_thread.is_set() or not GAME_ACTIVE:
                break
            waiting_thread.wait(timeout=sleep_time)

    # Select & save
    keyboard.send(current_slot)
    keyboard.press(SAVE_SLOT_KEY)

    # Wait 0.1 seconds inbetween save->load, so that PJ64 can process it
    waiting_thread.wait(timeout=.1)

    # Release keys
    keyboard.release(SAVE_SLOT_KEY)

    waiting_thread.wait(timeout=0.1)
    
# Runs on separate thread and alerts swap_game() if spacebar is pressed
def spacebar_listener():
    global last_spacebar, current_slot
    while GAME_ACTIVE:
        keyboard.wait('space')  # Wait for space bar
        if time.time() - last_swap >= 1 and time.time() - last_spacebar >= SPACEBAR_COOLDOWN:  # Check if enough time has passed since the last game swap, and if enough time has passed since the last spacebar interrupt
            last_spacebar = time.time()  # Store the current time
            if current_slot and current_slot in remaining_slots:
                remaining_slots.remove(current_slot)
                REMOVED_SLOTS_STACK.append(current_slot)
                print(f"Removed {current_slot} from remaining_slots\n")
            stop_thread.set()  # Signal the other thread to stop
            if len(remaining_slots) > 1:
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
        
######################################################################

try:
    print("\nPRESS SPACEBAR TO BEGIN CHALLENGE!\n")
    audio_manager.play_audio("Press Spacebar To Begin.wav", False)
    keyboard.wait('space')

    audio_manager.play_audio("Starting in 3 2 1.wav", False)
    countdown = 3
    while countdown > 0 and GAME_ACTIVE:
        print(f"\nSTARTING IN {countdown}")
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