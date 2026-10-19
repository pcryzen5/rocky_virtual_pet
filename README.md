# Rocky Desktop Pet - Project Hail Mary 🪨🚀

An ambient, animated desktop companion featuring **Rocky the Eridian engineer** from Andy Weir's *Project Hail Mary*! Rocky lives floating borderless on top of your desktop windows, reacts to music and movies, loves fistbumps, roams your screen, and sleeps peacefully when requested.

![Rocky Features](https://img.shields.io/badge/Companion-Rocky_Eridian-brightgreen)
![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)

---

## 🌟 Key Behaviors & Animations

| Action / State | Trigger | Animation / Visual |
| :--- | :--- | :--- |
| **Startup Wave** 👋 | On pet launch | `rocky_waving.png` + *"♪ ♫ Hello human friend! Amaze!"* |
| **Idle** 🪨 | Default resting state | `rocky_idle(1).png` with gentle vertical breathing |
| **Dance Mode** 🎵 | Playing music in browser (YT Music, Spotify, SoundCloud, etc.) | Alternates `rocky_dancing(1&2).png` with floating musical notes `♪ ♫ ♬` |
| **Movie Mode** 🍿 | Watching movie/video in browser (YouTube, Netflix, Prime, Disney+, VLC) | `rocky_watching_movie.png` (eating popcorn) |
| **Dragging / Shifting** 🖱️ | Left-click and drag anywhere on screen | `rocky_being_dragged.png` tracking the cursor |
| **Fistbump** 👊 | Double-click or menu selection | `rocky_fistbumping.png` + *"Fist my bump! 👊"* |
| **Going to Sleep** 🥱 | Select "Sleep" from context menu | Sequence: `rocky_goingtosleep(1&2).png` |
| **Sleeping** 💤 | Asleep loop | `rocky_sleeping.png` with floating `z Z 💤` |
| **Roam & Explore** 🐾 | Autonomous or menu | 3-frame left and right walking cycles (`rocky_left(1..3)`, `rocky_right(1..3)`) |

---

## 🛠️ Installation

Make sure Python 3.7+ is installed, then install the dependencies:

```powershell
pip install -r requirements.txt
```

*(Includes Pillow, OpenCV, NumPy, and pywin32)*

---

## 🚀 How to Run

```powershell
python pet_app.py
```

---

## 🖱️ How to Interact

- **Left-Click + Drag**: Move Rocky anywhere across your screens (shows dragged animation).
- **Double Click**: Fistbump with Rocky (*"Fist my bump!" 👊*).
- **Right-Click**: Opens Rocky's context menu:
  - 👊 **Fist my bump!**
  - ♨️ **Feed Astrophage** (replenishes fuel energy)
  - 😴 **Sleep** (Rocky yawns and goes to sleep)
  - ⏰ **Wake Up** (wakes Rocky from his nap)
  - 🎵 **Dance Mode (Toggle)** (force or enjoy dancing anytime)
  - 🍿 **Watch Movie (Toggle)** (force or enjoy movie watching anytime)
  - 🐾 **Roam & Explore** (walks across the screen)
  - 📏 **Pet Size**:
    - Small ($145 \times 153\text{ px}$)
    - Normal ($194 \times 204\text{ px}$) [Default sweet spot]
    - Large ($260 \times 273\text{ px}$)
  - 📊 **Ship Log & Stats** (view Astrophage fuel, Xenonite shell integrity, Camaraderie)
  - ❌ **Exit**

---

## 🎧 Automatic Media Detection

Rocky actively listens to open windows using the Windows API:
1. **Music Detection**: When a tab or application like **YouTube Music**, **Spotify**, **Apple Music**, **SoundCloud**, **Tidal**, etc. is open, Rocky automatically transitions into **Dance Mode** with floating musical chords.
2. **Movie & Video Detection**: When you watch videos on **YouTube**, **Netflix**, **Prime Video**, **Disney+ / Hotstar**, or open a video in **VLC / MPC**, Rocky grabs his popcorn and transitions into **Watch Movie Mode**.
3. When playback ends or tabs close, Rocky smoothly returns to **Idle**.
"# rocky_virtual_pet" 
