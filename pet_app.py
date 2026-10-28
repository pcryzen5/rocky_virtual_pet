"""
Rocky Desktop Pet - Project Hail Mary
A desktop companion featuring Rocky the Eridian engineer.

Features:
- Startup greeting wave (rocky_waving.png)
- Default idle state with gentle bobbing (rocky_idle(1).png)
- Auto-dances when music/songs play in any browser or YouTube Music app (rocky_dancing(1&2).png)
- Auto-watches movie when video/movie plays in any browser or YouTube app (rocky_watching_movie.png)
- Sleep transitions (rocky_goingtosleep(1&2).png -> rocky_sleeping.png)
- Fistbump interaction ("Fist my bump!" 👊) (rocky_fistbumping.png)
- Mouse dragging and positioning (rocky_being_dragged.png)
- Left and right roaming walk cycles (rocky_left(1..3).png, rocky_right(1..3).png)
- High-visibility floating speech bubbles with Eridian chords
- Musical notes (♪ ♫ ♬) and sleeping particles (z Z 💤)
"""

import os
import sys
import time
import math
import random
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

try:
    import win32gui
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_ASSET_DIRS = [
    os.path.join(BASE_DIR, "rocky (1)", "frames_gemini"),
    os.path.join(BASE_DIR, "frames_gemini"),
    os.path.join(BASE_DIR, "assets"),
]

# Size Presets: (Rocky Width, Rocky Height, Canvas Width, Canvas Height)
SIZE_PRESETS = {
    "small": (145, 153, 220, 245),
    "normal": (194, 204, 280, 295),
    "large": (260, 273, 350, 370),
}

# State constants
STATE_WAVING = "waving"
STATE_IDLE = "idle"
STATE_WALK_LEFT = "walk_left"
STATE_WALK_RIGHT = "walk_right"
STATE_DRAGGED = "dragged"
STATE_FISTBUMP = "fistbump"
STATE_DANCING = "dancing"
STATE_WATCHING_MOVIE = "watching_movie"
STATE_GOING_TO_SLEEP = "going_to_sleep"
STATE_SLEEPING = "sleeping"


class SpriteManager:
    """Loads, cleans backgrounds, resizes, and caches Rocky sprite frames."""
    
    def __init__(self, size_preset="normal"):
        self.size_preset = size_preset
        self.asset_dir = self._find_asset_dir()
        self.rw, self.rh, self.cw, self.ch = SIZE_PRESETS[size_preset]
        self.cache_dir = os.path.join(BASE_DIR, "assets", f"cache_{size_preset}")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.frames = {}
        self.load_all_frames()

    def _find_asset_dir(self):
        for path in POSSIBLE_ASSET_DIRS:
            if os.path.exists(path) and any(f.endswith('.png') for f in os.listdir(path)):
                return path
        return os.path.join(BASE_DIR, "assets")

    def set_size_preset(self, size_preset):
        if size_preset in SIZE_PRESETS and size_preset != self.size_preset:
            self.size_preset = size_preset
            self.rw, self.rh, self.cw, self.ch = SIZE_PRESETS[size_preset]
            self.cache_dir = os.path.join(BASE_DIR, "assets", f"cache_{size_preset}")
            os.makedirs(self.cache_dir, exist_ok=True)
            self.load_all_frames()

    def _process_frame(self, src_path, target_size):
        with Image.open(src_path) as raw_img:
            if raw_img.mode == 'RGBA':
                extrema = raw_img.getextrema()
                if len(extrema) == 4 and extrema[3][0] < 250:
                    # Clean RGBA transparency: resize RGBA first with LANCZOS, then composite on pure white
                    resized_rgba = raw_img.resize(target_size, Image.Resampling.LANCZOS)
                    bg = Image.new('RGB', target_size, (255, 255, 255))
                    bg.paste(resized_rgba, mask=resized_rgba.split()[3])
                    return bg
                else:
                    img = raw_img.convert('RGB')
            else:
                img = raw_img.convert('RGB')

            resized = img.resize(target_size, Image.Resampling.LANCZOS)
            arr = np.array(resized)

            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            bg_seed_mask = (gray >= 238).astype(np.uint8) * 255
            h, w = gray.shape
            cv_mask = np.zeros((h + 2, w + 2), np.uint8)

            for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
                if bg_seed_mask[pt[1], pt[0]] == 255:
                    cv2.floodFill(bg_seed_mask, cv_mask, pt, 128)

            outer_bg = (bg_seed_mask == 128)
            arr[outer_bg] = [255, 255, 255]
            return Image.fromarray(arr)

    def load_all_frames(self):
        target_size = (self.rw, self.rh)
        required_frames = [
            'rocky_idle(1).png',
            'rocky_dancing(1).png',
            'rocky_dancing(2).png',
            'rocky_being_dragged.png',
            'rocky_fistbumping.png',
            'rocky_left(1).png',
            'rocky_left(2).png',
            'rocky_left(3).png',
            'rocky_right(1).png',
            'rocky_right(2).png',
            'rocky_right(3).png',
            'rocky_goingtosleep(1).png',
            'rocky_goingtosleep(2).png',
            'rocky_sleeping.png',
            'rocky_watching_movie.png',
            'rocky_waving.png',
        ]

        for fname in required_frames:
            cache_file = os.path.join(self.cache_dir, fname)
            src_file = os.path.join(self.asset_dir, fname)

            pil_img = None
            if os.path.exists(cache_file) and os.path.exists(src_file):
                try:
                    if os.path.getmtime(cache_file) >= os.path.getmtime(src_file):
                        pil_img = Image.open(cache_file)
                except Exception:
                    pil_img = None

            if pil_img is None:
                if os.path.exists(src_file):
                    pil_img = self._process_frame(src_file, target_size)
                    try:
                        pil_img.save(cache_file)
                    except Exception:
                        pass
                else:
                    pil_img = Image.new('RGB', target_size, (255, 255, 255))

            self.frames[fname] = ImageTk.PhotoImage(pil_img)

    def get_frame(self, fname):
        return self.frames.get(fname)


class MediaDetector:
    """Monitors running window titles to detect active music or movies/videos."""

    MUSIC_KEYWORDS = [
        'youtube music', 'spotify', 'soundcloud', 'apple music',
        'tidal', 'deezer', 'musicbee', 'foobar2000', 'aimp',
        'itunes', 'amazon music', 'pandora', 'gaana', 'jiosaavn'
    ]

    MOVIE_KEYWORDS = [
        'netflix', 'prime video', 'disney+', 'hotstar', 'hulu',
        'crunchyroll', 'vlc media player', 'potplayer', 'movies & tv',
        'films & tv', 'twitch', 'hbomax', 'max.com', 'plex', 'kodi'
    ]

    def __init__(self, callback):
        self.callback = callback
        self.running = True
        self.thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _scan_loop(self):
        while self.running:
            try:
                music, movie = self._check_media()
                if self.callback:
                    self.callback(music, movie)
            except Exception:
                pass
            time.sleep(1.8)

    def _check_media(self):
        if not HAS_WIN32:
            return False, False

        found_music = False
        found_movie = False

        def enum_cb(hwnd, _):
            nonlocal found_music, found_movie
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                title = win32gui.GetWindowText(hwnd).strip().lower()
                if not title:
                    return True

                # Check music first
                for k in self.MUSIC_KEYWORDS:
                    if k in title:
                        found_music = True
                        return True

                # Check video: YouTube (excluding YouTube Music)
                if 'youtube' in title and 'youtube music' not in title:
                    found_movie = True
                    return True

                # Check movie services / players
                for k in self.MOVIE_KEYWORDS:
                    if k in title:
                        found_movie = True
                        return True
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(enum_cb, None)
        except Exception:
            pass

        return found_music, found_movie


class Particle:
    """Floating particle for musical notes (dance) or zZz (sleep)."""
    def __init__(self, char, x, y, color, vy=-1.5, life=35):
        self.char = char
        self.x = x
        self.y = y
        self.color = color
        self.vy = vy
        self.life = life
        self.max_life = life


class RockyPet:
    def __init__(self, root):
        self.root = root
        self.root.title("Rocky - Project Hail Mary")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-transparentcolor', 'white')

        # Size & Sprites
        self.size_preset = "normal"
        self.sprite_mgr = SpriteManager(self.size_preset)
        self.cw = self.sprite_mgr.cw
        self.ch = self.sprite_mgr.ch
        self.rw = self.sprite_mgr.rw
        self.rh = self.sprite_mgr.rh

        # State management
        self.state = STATE_WAVING
        self.prev_state = STATE_IDLE
        self.animation_step = 0
        self.walk_steps_left = 0
        self.walk_dir = 1
        self.is_dragging = False
        self.force_dance = False
        self.force_movie = False
        self.music_active = False
        self.movie_active = False

        # Rocky stats (Project Hail Mary lore)
        self.astrophage_fuel = 100.0
        self.xenonite_integrity = 100.0
        self.camaraderie = 100.0
        self.days_on_ship = 1

        # Dragging coordinates
        self.drag_x = 0
        self.drag_y = 0

        # Speech bubble text and timer (~4 seconds duration)
        self.speech_text = "♪ ♫ Hello human friend! Amaze!"
        self.speech_timer = 55

        # Particles
        self.particles = []

        # Canvas with transparent background
        self.canvas = tk.Canvas(root, width=self.cw, height=self.ch, bg='white', highlightthickness=0)
        self.canvas.pack()

        # Canvas Rocky image item
        self.pet_img_tag = self.canvas.create_image(self.cw // 2, self.ch - 10, anchor='s')
        
        # Idle bobbing offset
        self.bob_offset = 0

        # Build Context Menu
        self._build_context_menu()

        # Bindings & Protocols
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.canvas.bind('<Button-3>', self.show_context_menu)
        self.canvas.bind('<Double-Button-1>', self.on_double_click)

        # Center on screen
        self.center_window()

        # Start Media Detection
        self.detector = MediaDetector(self.on_media_detected)

        # Start Loops
        self.update_tick()
        self.stat_decay_loop()
        self.roam_scheduler_loop()

    def center_window(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - self.cw) // 2
        y = (sh - self.ch) // 2
        self.root.geometry(f"{self.cw}x{self.ch}+{x}+{y}")

    def _build_context_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0, bg='#11111b', fg='#cdd6f4', activebackground='#313244', activeforeground='#f9e2af')
        self.menu.add_command(label="👊 Fist my bump!", command=self.trigger_fistbump)
        self.menu.add_command(label="♨️ Feed Astrophage", command=self.feed_astrophage)
        self.menu.add_command(label="😴 Sleep", command=self.start_sleeping)
        self.menu.add_command(label="⏰ Wake Up", command=self.wake_up)
        self.menu.add_separator()
        self.menu.add_command(label="🎵 Dance Mode (Toggle)", command=self.toggle_dance)
        self.menu.add_command(label="🍿 Watch Movie (Toggle)", command=self.toggle_movie)
        self.menu.add_command(label="🐾 Roam & Explore", command=self.trigger_walk)
        
        # Submenu for Size
        self.size_menu = tk.Menu(self.menu, tearoff=0, bg='#11111b', fg='#cdd6f4', activebackground='#313244', activeforeground='#f9e2af')
        self.size_menu.add_command(label="Small (145x153)", command=lambda: self.change_size("small"))
        self.size_menu.add_command(label="Normal (194x204)", command=lambda: self.change_size("normal"))
        self.size_menu.add_command(label="Large (260x273)", command=lambda: self.change_size("large"))
        self.menu.add_cascade(label="📏 Pet Size", menu=self.size_menu)

        self.menu.add_separator()
        self.menu.add_command(label="📊 Ship Log & Stats", command=self.show_stats)
        self.menu.add_command(label="❌ Exit", command=self.exit_app)

    def change_size(self, size_key):
        if size_key in SIZE_PRESETS:
            self.size_preset = size_key
            self.sprite_mgr.set_size_preset(size_key)
            self.cw = self.sprite_mgr.cw
            self.ch = self.sprite_mgr.ch
            self.rw = self.sprite_mgr.rw
            self.rh = self.sprite_mgr.rh

            curr_x = self.root.winfo_x()
            curr_y = self.root.winfo_y()
            self.canvas.config(width=self.cw, height=self.ch)
            self.canvas.coords(self.pet_img_tag, self.cw // 2, self.ch - 10)
            self.root.geometry(f"{self.cw}x{self.ch}+{curr_x}+{curr_y}")
            self.show_speech(f"Scale adjusted! Amaze!", 35)

    def show_context_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def on_mouse_down(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
        self.is_dragging = True
        if self.state not in (STATE_SLEEPING, STATE_GOING_TO_SLEEP):
            self.state = STATE_DRAGGED
            self.show_speech("Whoa! Shifting position!", 30)

    def on_mouse_drag(self, event):
        new_x = self.root.winfo_x() + (event.x - self.drag_x)
        new_y = self.root.winfo_y() + (event.y - self.drag_y)
        
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        new_x = max(-50, min(sw - self.cw + 50, new_x))
        new_y = max(-50, min(sh - self.ch + 50, new_y))

        self.root.geometry(f"+{new_x}+{new_y}")

    def on_mouse_up(self, event):
        self.is_dragging = False
        if self.state == STATE_DRAGGED:
            self.state = STATE_IDLE
            self.clear_speech()

    def on_double_click(self, event):
        if self.state == STATE_SLEEPING:
            self.wake_up()
        else:
            self.trigger_fistbump()

    def trigger_fistbump(self):
        if self.state == STATE_SLEEPING:
            self.wake_up()
        self.state = STATE_FISTBUMP
        self.camaraderie = min(100.0, self.camaraderie + 20.0)
        self.animation_step = 0
        self.show_speech("Fist my bump! 👊", 45)

    def feed_astrophage(self):
        if self.state == STATE_SLEEPING:
            self.wake_up()
        if self.astrophage_fuel < 100:
            self.astrophage_fuel = min(100.0, self.astrophage_fuel + 35.0)
            self.camaraderie = min(100.0, self.camaraderie + 10.0)
            self.show_speech("Amaze! Astrophage energy replenished! ♨️", 45)
        else:
            self.show_speech("Astrophage fuel cell full! Amaze! ♨️", 35)

    def start_sleeping(self):
        if self.state != STATE_SLEEPING:
            self.state = STATE_GOING_TO_SLEEP
            self.animation_step = 0
            self.show_speech("Yawn... time to sleep... Watch me.", 35)

    def wake_up(self):
        if self.state in (STATE_SLEEPING, STATE_GOING_TO_SLEEP):
            self.state = STATE_IDLE
            self.show_speech("Good! Proud! Woke up!", 40)

    def toggle_dance(self):
        self.force_dance = not self.force_dance
        if self.force_dance:
            self.force_movie = False
            self.state = STATE_DANCING
            self.show_speech("♪ ♫ ♬ Amaze rhythm! ♬ ♫ ♪", 50)
        else:
            if self.state == STATE_DANCING:
                self.state = STATE_IDLE
                self.clear_speech()

    def toggle_movie(self):
        self.force_movie = not self.force_movie
        if self.force_movie:
            self.force_dance = False
            self.state = STATE_WATCHING_MOVIE
            self.show_speech("Watching human movie! Amaze! 🍿", 50)
        else:
            if self.state == STATE_WATCHING_MOVIE:
                self.state = STATE_IDLE
                self.clear_speech()

    def trigger_walk(self):
        if self.state in (STATE_IDLE, STATE_WAVING):
            sw = self.root.winfo_screenwidth()
            cur_x = self.root.winfo_x()
            if cur_x < 200:
                self.walk_dir = 1
            elif cur_x > sw - self.cw - 200:
                self.walk_dir = -1
            else:
                self.walk_dir = random.choice([-1, 1])

            self.walk_steps_left = random.randint(12, 24)
            self.state = STATE_WALK_RIGHT if self.walk_dir == 1 else STATE_WALK_LEFT
            self.animation_step = 0
            self.show_speech("Exploring ship deck...", 35)

    def show_speech(self, text, duration_ticks=45):
        self.speech_text = text
        self.speech_timer = duration_ticks

    def clear_speech(self):
        self.speech_text = ""
        self.speech_timer = 0
        self.canvas.delete('speech')

    def on_media_detected(self, music, movie):
        # Safely marshal callback from background thread to main Tkinter thread
        try:
            self.root.after(0, lambda: self._apply_media_detection(music, movie))
        except Exception:
            pass

    def _apply_media_detection(self, music, movie):
        self.music_active = music
        self.movie_active = movie

        if self.state not in (STATE_SLEEPING, STATE_GOING_TO_SLEEP, STATE_DRAGGED, STATE_FISTBUMP):
            if not self.force_dance and not self.force_movie:
                if music and self.state != STATE_DANCING:
                    self.state = STATE_DANCING
                    self.show_speech("♪ ♫ Music playing! Amaze dance! ♫ ♪", 45)
                elif not music and movie and self.state != STATE_WATCHING_MOVIE:
                    self.state = STATE_WATCHING_MOVIE
                    self.show_speech("Human video detected! Popcorn time! 🍿", 45)
                elif not music and not movie and self.state in (STATE_DANCING, STATE_WATCHING_MOVIE):
                    self.state = STATE_IDLE
                    self.clear_speech()

    def spawn_particle(self, char, color):
        px = self.cw // 2 + random.randint(-40, 40)
        py = self.ch // 2 + random.randint(-40, -10)
        p = Particle(char, px, py, color, vy=random.uniform(-2.2, -1.2), life=30)
        self.particles.append(p)

    def _draw_speech_bubble(self):
        self.canvas.delete('speech')
        if not self.speech_text:
            return

        pad_x = 12
        pad_y = 6
        font = ("Segoe UI", 10, "bold")
        
        # Calculate target position in top headroom
        target_center_y = 36
        max_width = self.cw - 28

        # 1. Create text with high-contrast amber/gold text (never white!)
        text_id = self.canvas.create_text(
            self.cw // 2,
            target_center_y,
            text=self.speech_text,
            font=font,
            fill='#f9e2af',
            justify='center',
            width=max_width,
            tags='speech'
        )
        
        bbox = self.canvas.bbox(text_id)
        if bbox:
            bx1, by1, bx2, by2 = bbox
            x1 = max(6, bx1 - pad_x)
            x2 = min(self.cw - 6, bx2 + pad_x)
            y1 = max(4, by1 - pad_y)
            y2 = by2 + pad_y

            # Draw outer glow / contrast border
            glow_rect = self.canvas.create_rectangle(
                x1 - 1, y1 - 1, x2 + 1, y2 + 1,
                fill='', outline='#313244', width=2, tags='speech'
            )

            # Draw sleek solid dark capsule background
            bubble_rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill='#11111b', outline='#89b4fa', width=2, tags='speech'
            )
            
            # Pointer triangle pointing directly down to Rocky
            mid_x = (x1 + x2) // 2
            tri_tail = self.canvas.create_polygon(
                mid_x - 6, y2,
                mid_x + 6, y2,
                mid_x, y2 + 7,
                fill='#11111b', outline='#89b4fa', tags='speech'
            )

            # Bring all bubble elements and text forward
            self.canvas.tag_raise(glow_rect)
            self.canvas.tag_raise(bubble_rect)
            self.canvas.tag_raise(tri_tail)
            self.canvas.tag_raise(text_id)

    def _update_particles(self):
        self.canvas.delete('particle')
        remaining = []
        for p in self.particles:
            p.y += p.vy
            p.life -= 1
            if p.life > 0:
                self.canvas.create_text(
                    p.x, p.y,
                    text=p.char,
                    fill=p.color,
                    font=("Segoe UI", 13, "bold"),
                    tags='particle'
                )
                remaining.append(p)
        self.particles = remaining

    def update_tick(self):
        """Main animation & state tick (~70ms interval)"""
        self.animation_step += 1

        frame_name = 'rocky_idle(1).png'
        self.bob_offset = 0

        if self.state == STATE_WAVING:
            frame_name = 'rocky_waving.png'
            if self.animation_step > 50:  # ~3.5 seconds
                self.state = STATE_IDLE
                self.clear_speech()

        elif self.state == STATE_IDLE:
            frame_name = 'rocky_idle(1).png'
            # Gentle vertical breathing bobbing
            self.bob_offset = int(math.sin(self.animation_step * 0.15) * 3)

        elif self.state == STATE_DRAGGED:
            frame_name = 'rocky_being_dragged.png'

        elif self.state == STATE_FISTBUMP:
            frame_name = 'rocky_fistbumping.png'
            if self.animation_step > 35:  # ~2.5 seconds
                self.state = STATE_IDLE
                self.clear_speech()

        elif self.state == STATE_DANCING:
            # Alternates between dancing(1) and dancing(2) every ~300ms
            frame_idx = (self.animation_step // 4) % 2 + 1
            frame_name = f'rocky_dancing({frame_idx}).png'
            self.bob_offset = int(math.sin(self.animation_step * 0.4) * 4)

            # Spawn floating musical notes
            if random.random() < 0.28:
                note = random.choice(['♪', '♫', '♬', '🎶'])
                color = random.choice(['#fab387', '#a6e3a1', '#89b4fa', '#f38ba8', '#f9e2af'])
                self.spawn_particle(note, color)

        elif self.state == STATE_WATCHING_MOVIE:
            frame_name = 'rocky_watching_movie.png'
            self.bob_offset = int(math.sin(self.animation_step * 0.08) * 1)

        elif self.state == STATE_GOING_TO_SLEEP:
            if self.animation_step < 18:
                frame_name = 'rocky_goingtosleep(1).png'
            elif self.animation_step < 36:
                frame_name = 'rocky_goingtosleep(2).png'
            else:
                self.state = STATE_SLEEPING
                self.animation_step = 0
                self.show_speech("Zzz... Watching sleep.", 45)

        elif self.state == STATE_SLEEPING:
            frame_name = 'rocky_sleeping.png'
            if random.random() < 0.16:
                z = random.choice(['z', 'Z', '💤'])
                self.spawn_particle(z, '#b4befe')

        elif self.state in (STATE_WALK_LEFT, STATE_WALK_RIGHT):
            frame_idx = (self.animation_step // 3) % 3 + 1
            if self.state == STATE_WALK_LEFT:
                frame_name = f'rocky_left({frame_idx}).png'
                dx = -4
            else:
                frame_name = f'rocky_right({frame_idx}).png'
                dx = 4

            cur_x = self.root.winfo_x()
            cur_y = self.root.winfo_y()
            self.root.geometry(f"+{cur_x + dx}+{cur_y}")

            self.walk_steps_left -= 1
            if self.walk_steps_left <= 0:
                self.state = STATE_IDLE
                self.clear_speech()

        # Update sprite frame
        photo = self.sprite_mgr.get_frame(frame_name)
        if photo:
            self.canvas.itemconfig(self.pet_img_tag, image=photo)
            self.canvas.coords(self.pet_img_tag, self.cw // 2, self.ch - 10 + self.bob_offset)

        # Update floating particles
        self._update_particles()

        # Update Speech Bubble
        if self.speech_timer > 0:
            self.speech_timer -= 1
            self._draw_speech_bubble()
        else:
            self.canvas.delete('speech')

        # Schedule next tick (~70ms)
        self.root.after(70, self.update_tick)

    def stat_decay_loop(self):
        """Gradual stats update every 5 seconds"""
        if self.state == STATE_SLEEPING:
            self.astrophage_fuel = min(100.0, self.astrophage_fuel + 0.5)
            self.camaraderie = min(100.0, self.camaraderie + 0.2)
        else:
            self.astrophage_fuel = max(0.0, self.astrophage_fuel - 0.25)
            self.camaraderie = max(0.0, self.camaraderie - 0.15)

        self.root.after(5000, self.stat_decay_loop)

    def roam_scheduler_loop(self):
        """Occasional random actions when idle (every 12-20s)"""
        if self.state == STATE_IDLE and not self.is_dragging:
            roll = random.random()
            if roll < 0.35:
                self.trigger_walk()
            elif roll < 0.65:
                quotes = [
                    "♪ ♫ Question?",
                    "Good. Proud. Happy.",
                    "You have five fingers. I have five legs! Amaze!",
                    "Astrophage energy levels optimal.",
                    "Xenonite is strongest material in universe.",
                    "Eat Astrophage, make fuel! Amaze!",
                    "♪ ♫ ♬ Eridian harmony ♬ ♫ ♪",
                ]
                self.show_speech(random.choice(quotes), 45)

        self.root.after(random.randint(12000, 20000), self.roam_scheduler_loop)

    def show_stats(self):
        msg = f"""🚀 Project Hail Mary - Rocky Ship Log 🚀

♨️ Astrophage Fuel: {self.astrophage_fuel:.1f}%
🛡️ Xenonite Integrity: {self.xenonite_integrity:.1f}%
🤝 Camaraderie: {self.camaraderie:.1f}%
🗓️ Days on Blip-A: {self.days_on_ship} days
🎭 Current State: {self.state}
🎵 Music Detected: {'Yes' if self.music_active else 'No'}
🍿 Video Detected: {'Yes' if self.movie_active else 'No'}
"""
        messagebox.showinfo("Rocky's Ship Log", msg)

    def exit_app(self):
        self.detector.stop()
        self.root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    root = tk.Tk()
    app = RockyPet(root)
    root.mainloop()
