import random
import time
import keyboard
import threading
import sys
from AudioPlayer import AudioManager
from OBS_Websockets import OBSWebsocketsManager

MINIMUM_SLOT_TIME = 2 # The minimum time we'll play a specific save slot
MAXIMUM_SLOT_TIME = 25 # The minimum time we'll play a specific save slot

USING_OBS_WEBSOCKETS = True # Whether or not program should display the # of remaining races in OBS
OBS_TEXT_SOURCE = "RACES LEFT" # Name this whatever text element you want to update in OBS

remaining_slots = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
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
SPACEBAR_COOLDOWN = 2  # Cooldown time for the spacebar interrupt, in seconds
GAME_ACTIVE = True

def swap_game():
    global last_swap, current_slot, previous_slot, multiple_slots_remain
    
    # Update OBS text
    if USING_OBS_WEBSOCKETS:
        obswebsockets_manager.set_text(OBS_TEXT_SOURCE, f"RACES LEFT: {len(remaining_slots)}")

    # Swap to new slot
    if len(remaining_slots) > 1: # If there's at least 2 unfinished slots, load a new random slot
        while True: # Pick new random slot that isn't the same as previous
            current_slot = random.choice(remaining_slots)
            if current_slot != previous_slot:
                previous_slot = current_slot
                break
        keyboard.press(f'F{current_slot}')
        waiting_thread.wait(timeout=0.1)
        keyboard.release(f'F{current_slot}')
        print(f"\nSWAPPING TO SLOT {current_slot}!")
    elif len(remaining_slots) == 1 and multiple_slots_remain: # If this is the first time we've gotten to the last slot, we swap to it, then set a flag so that we don't swap again
         multiple_slots_remain = False
         current_slot = random.choice(remaining_slots)
         audio_manager.play_audio("Final Race.mp3",False,False)
         keyboard.press(f'F{current_slot}')
         waiting_thread.wait(timeout=0.1)
         keyboard.release(f'F{current_slot}')
         print(f"\nSWAPPING TO SLOT {current_slot}!")
    elif len(remaining_slots) == 0: # Challenge completed!
        audio_manager.play_audio("You Have Completed The Challenge.mp3",False,False)
        if USING_OBS_WEBSOCKETS:
            obswebsockets_manager.set_text(OBS_TEXT_SOURCE, f"ANY PRIMERS???")
        waiting_thread.wait(timeout=15)
        waiting_thread.set()
        sys.exit()

    last_swap = time.time()  # Store the current time
    print(f"Remaining Slots: {remaining_slots}\n")

    # Wait random amount of time
    random_time = random.randint(MINIMUM_SLOT_TIME, MAXIMUM_SLOT_TIME) * (1/sleep_time)  # Multiply by inverse of sleep_time. We do this so that we can run this function every 0.1 seconds instead of every second, to make it feel more responsive
    print(f"Waiting for {int(random_time/10)} seconds")
    for i in range(int(random_time)):  # Make sure to cast to an int, as it could be a float
        if stop_thread.is_set() or not GAME_ACTIVE:
            break
        waiting_thread.wait(timeout=sleep_time)

    # Save the slot
    keyboard.press('shift')
    if current_slot == '10':
        keyboard.press('0')
    else:
        keyboard.press(current_slot)
    waiting_thread.wait(timeout=0.1)
    keyboard.release('shift')
    if current_slot == '10':
        keyboard.release('0')
    else:
        keyboard.release(current_slot)

    waiting_thread.wait(timeout=0.1) # Wait 0.1 seconds inbetween save->load, so that Dolphin can process it

# Runs on separate thread and alerts swap_game() if spacebar is pressed
def keyboard_listener():
    global last_spacebar, current_slot
    while GAME_ACTIVE:
        keyboard.wait('space')  # Wait for space bar
        if time.time() - last_swap >= 1 and time.time() - last_spacebar >= SPACEBAR_COOLDOWN:  # Check if enough time has passed since the last game swap, and if enough time has passed since the last spacebar interrupt
            last_spacebar = time.time()  # Store the current time
            if current_slot and current_slot in remaining_slots:
                remaining_slots.remove(current_slot)  # Remove current_slot from unfinished_slots
                print(f"Removed {current_slot} from unfinished_slots")
            stop_thread.set()  # Signal the other thread to stop
            if len(remaining_slots) > 1:
                audio_manager.play_audio("Race Completed.mp3",False,False)
            break

######################################################################

try:
    print("\nPRESS SPACEBAR TO BEGIN!")
    audio_manager.play_audio("Press Spacebar To Begin.mp3", False)
    keyboard.wait('space')

    audio_manager.play_audio("Starting in 3 2 1.mp3", False)
    countdown = 3
    while countdown > 0 and GAME_ACTIVE:
        print(f"\nSTARTING IN {countdown}")
        countdown -= 1
        waiting_thread.wait(timeout=1)

    while GAME_ACTIVE:
        stop_thread.clear()
        listener = threading.Thread(target=keyboard_listener)
        listener.start()

        swap_game()

        while listener.is_alive() and GAME_ACTIVE:  
            # the listener thread is still waiting for the space bar, so let's start a new game
            stop_thread.clear()
            swap_game()
except KeyboardInterrupt:
    # quit
    print("Thanks for playing! Exiting now.")
    waiting_thread.set()
    stop_thread.set()
    GAME_ACTIVE = False
    sys.exit()