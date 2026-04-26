import os
import subprocess

class SoundManager:
    def __init__(self, music_dir="assets/music", sfx_dir="assets/sounds"):
        """
        music_dir: Default path for vanilla music
        sfx_dir: Default path for vanilla sound effects
        """
        self.base_music = music_dir
        self.base_sfx = sfx_dir
        self.bgm_process = None
        self.current_track = None

    def get_path(self, file_name, is_music=True):
        """
        Pathing:
        - If Vanilla: Returns vanilla asset path
        - If Mod: Returns mod asset path ONLY
        """
        from __main__ import CURRENT_MOD_NAME
        
        category = "music" if is_music else "sounds"
        
        if CURRENT_MOD_NAME == "vanilla":
            vanilla_dir = self.base_music if is_music else self.base_sfx
            return os.path.abspath(os.path.join(vanilla_dir, file_name))

        mod_path = os.path.abspath(os.path.join("mods", CURRENT_MOD_NAME, "assets", category, file_name))
        
        if os.path.exists(mod_path):
            return mod_path
        return None

    def play_bgm(self, file_name, loop=True):
        if self.current_track == file_name:
            return

        self.stop_bgm()
        path = self.get_path(file_name, is_music=True)

        if path and os.path.exists(path):
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
                print("\033[91mError: 'mpv' not found in system PATH. Audio cannot play.\033[0m")
        else:
            self.current_track = None

    def play_sfx(self, file_name):
        path = self.get_path(file_name, is_music=False)
        
        if path and os.path.exists(path):
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
                self.bgm_process.wait(timeout=0.5)
            except:
                try: 
                    self.bgm_process.kill()
                except: 
                    pass
        
        self.bgm_process = None
        self.current_track = None