import os
import subprocess
from helpers import game_utils

class SoundManager:
    def __init__(self, music_dir="assets/music", sfx_dir="assets/sounds"):
        self.base_music = music_dir
        self.base_sfx = sfx_dir
        self.bgm_process = None
        self.current_track = None

    def get_path(self, file_name, mod_name="vanilla", is_music=True):
        category = "music" if is_music else "sounds"
        
        if mod_name != "vanilla":
            mod_path = os.path.abspath(os.path.join("mods", mod_name, "assets", category, file_name))
            if os.path.exists(mod_path):
                return mod_path
        
        vanilla_dir = self.base_music if is_music else self.base_sfx
        vanilla_path = os.path.abspath(os.path.join(vanilla_dir, file_name))
        
        if os.path.exists(vanilla_path):
            return vanilla_path
            
        return None

    def play_bgm(self, file_name, mod_name="vanilla", loop=True):
        if self.current_track == file_name:
            return

        self.stop_bgm()
        path = self.get_path(file_name, mod_name, is_music=True)

        if path:
            args = ["mpv", "--no-video", "--really-quiet"]
            if loop:
                args.append("--loop")
            args.append(path)

            try:
                self.bgm_process = subprocess.Popen(
                    args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.current_track = file_name
            except FileNotFoundError:
                print(f"\033[91m[Audio Error] mpv not found. Music disabled.\033[0m")
        else:
            self.current_track = None

    def play_sfx(self, file_name, mod_name="vanilla"):
        path = self.get_path(file_name, mod_name, is_music=False)
        if path:
            try:
                subprocess.Popen(
                    ["mpv", "--no-video", "--really-quiet", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except FileNotFoundError:
                pass

    def stop_bgm(self):
        if self.bgm_process:
            try:
                self.bgm_process.terminate()
                self.bgm_process.wait(timeout=0.2)
            except:
                try: 
                    self.bgm_process.kill()
                except: 
                    pass
        
        self.bgm_process = None
        self.current_track = None