import pygame
import time
import soundfile as sf
import os
from mutagen.mp3 import MP3

class AudioManager:

    def __init__(self):
        pygame.mixer.init()

    def play_audio(self, file_path, sleep_during_playback=True, delete_file=False):
        """
        Parameters:
        file_path (str): path to the audio file
        sleep_during_playback (bool): whether program will wait for audio to finish playing before continuing execution
        delete_file (bool): whether program will delete the provided audio file after execution
        """
        pygame.mixer.init()
        # Use pygame Sound, rather than Music, since sounds can be played simultaneously
        pygame_sound = pygame.mixer.Sound(file_path) 
        pygame_sound.play()
        #pygame.mixer.music.load(file_path)
        #pygame.mixer.music.play()

        if sleep_during_playback:
            # Calculate length of the file, based on the file format
            _, ext = os.path.splitext(file_path) # Get the extension of this file
            if ext.lower() == '.wav':
                wav_file = sf.SoundFile(file_path)
                file_length = wav_file.frames / wav_file.samplerate
                wav_file.close()
            elif ext.lower() == '.mp3':
                mp3_file = MP3(file_path)
                file_length = mp3_file.info.length
            else:
                print("Cannot play audio, unknown file type")
                return

            # Sleep until file is done playing
            time.sleep(file_length + 0.5)

            # Stop pygame so file can be deleted
            pygame.mixer.music.stop()
            pygame.mixer.quit()

            # Delete the file
            if delete_file:
                try:  
                    os.remove(file_path)
                    print(f"Deleted the audio file.")
                except PermissionError:
                    print(f"Couldn't remove {file_path} because it is being used by another process.")

    

    