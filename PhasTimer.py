"""
Phasmophobia Overlay Timer  v3
────────────────────────────────────────────────────────
• Milestone text is the BIG focus — ghost phase labels dominate
• Countdown number is compact / secondary
• 3-second flashing alert before each checkpoint
• Keyboard 1/2/3/4 = start / pause / resume
Requires: Python 3.x (tkinter built-in)
"""

import tkinter as tk
import time as _time
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

# ─── Palette ──────────────────────────────────────────────────────────────────
BG      = "#090b0f"
BG2     = "#0f1219"
BG3     = "#141820"
BORDER  = "#1c2130"
ACCENT  = "#4fc3f7"
HUNT_C  = "#ff4757"
COOL_C  = "#ffa502"
PARA_C  = "#a29bfe"
GREEN   = "#2ed573"
WARN    = "#ff6348"
MUTED   = "#3d4a60"
DIM     = "#5a6a85"
WHITE   = "#e8eef8"
FLASH1  = "#ffffff"
FLASH2  = "#ff4757"

# milestones: (remaining_threshold, triggered_label, upcoming_label)
TIMERS = [
    {
        "key": "1", "title": "SMUDGE", "icon": "🔥", "color": ACCENT,
        "total": 180,
        "milestones": [
            (120, "Demon CAN HUNT",   "Demon hunts at 2:00"),
            ( 90, "Normal CAN HUNT",  "Normal hunts at 1:30"),
            (  0, "Spirit CAN HUNT",  "Spirit hunts at 0:00"),
        ],
        "stuns": [
            ("Normal 5s", 5,  ACCENT),
            ("Moroi 7s",  7,  "#e84393"),
        ],
    },
    {
        "key": "2", "title": "HUNT DURATION", "icon": "🔴", "color": HUNT_C,
        "total": 50,
        "map_sizes": {
            "Small":  {"total": 50,  "milestones": [(25, "Obambo Short ends", "Obambo Short → 25s"), (20, "Normal hunt ends", "Normal → 20s"), (7, "Obambo Long ends", "Obambo Long → 7s"),  (0, "Cursed hunt ends", "Cursed → 0s")]},
            "Medium": {"total": 70,  "milestones": [(30, "Obambo Short ends", "Obambo Short → 30s"), (20, "Normal hunt ends", "Normal → 20s"), (10, "Obambo Long ends", "Obambo Long → 10s"), (0, "Cursed hunt ends", "Cursed → 0s")]},
            "Large":  {"total": 80,  "milestones": [(30, "Obambo Short ends", "Obambo Short → 30s"), (20, "Normal hunt ends", "Normal → 20s"), (10, "Obambo Long ends", "Obambo Long → 10s"), (0, "Cursed hunt ends", "Cursed → 0s")]},
        },
        "milestones": [
            (25, "Obambo Short ends", "Obambo Short → 25s"),
            (20, "Normal hunt ends",  "Normal → 20s"),
            ( 7, "Obambo Long ends",  "Obambo Long → 7s"),
            ( 0, "Cursed hunt ends",  "Cursed → 0s"),
        ],
    },
    {
        "key": "3", "title": "HUNT COOLDOWN", "icon": "🟡", "color": COOL_C,
        "total": 30,
        "milestones": [
            (5, "Demon CD ends",  "Demon ends at 5s"),
            (0, "Normal CD ends", "Normal ends at 0s"),
        ],
    },
    {
        "key": "4", "title": "PARANORMAL SOUND CD", "icon": "🔊", "color": PARA_C,
        "total": 80,
        "milestones": [
            (15, "Myling CD ends",       "Myling ends at 15s"),
            ( 0, "Normal ghost CD ends", "Normal ends at 0s"),
        ],
    },
]

BAR_W   = 310
BAR_H   = 7
PANEL_W = 340


# ─── Progress bar ─────────────────────────────────────────────────────────────
class ProgressBar:
    def __init__(self, parent, color, total, milestones):
        self.total      = total
        self.milestones = milestones
        canvas_h        = BAR_H + 13
        self.cv = tk.Canvas(parent, width=BAR_W, height=canvas_h,
                            bg=BG2, bd=0, highlightthickness=0)
        self.cv.pack(padx=16, pady=(0, 1))
        self.cv.create_rectangle(0, 0, BAR_W, BAR_H, fill=BORDER, outline="")
        self.fill_id = self.cv.create_rectangle(0, 0, BAR_W, BAR_H,
                                                fill=color, outline="")
        for thresh, _, _ in milestones:
            ratio = thresh / total if total else 0
            x = max(1, min(BAR_W - 1, int(BAR_W * ratio)))
            self.cv.create_line(x, 0, x, BAR_H, fill=WHITE, width=1, dash=(2, 2))
            lbl = f"{thresh}s" if thresh < 60 else f"{thresh//60}:{thresh%60:02d}"
            self.cv.create_text(x, BAR_H + 6, text=lbl,
                                fill=DIM, font=("Courier", 6), anchor="center")

    def update(self, remaining):
        ratio = max(0.0, min(1.0, remaining / self.total)) if self.total else 0
        self.cv.coords(self.fill_id, 0, 0, max(0, int(BAR_W * ratio)), BAR_H)
        if ratio > 0.5:
            col = GREEN
        elif ratio > 0.2:
            t = (ratio - 0.2) / 0.3
            r = int(0x2e + (0xff - 0x2e) * (1 - t))
            g = int(0xd5 + (0x63 - 0xd5) * (1 - t))
            b = int(0x73 + (0x48 - 0x73) * (1 - t))
            col = f"#{r:02x}{g:02x}{b:02x}"
        else:
            col = HUNT_C
        self.cv.itemconfig(self.fill_id, fill=col)


# ─── Timer panel ──────────────────────────────────────────────────────────────
class TimerPanel:
    def __init__(self, parent, cfg, key_num):
        self.cfg      = cfg
        self.total    = float(cfg["total"])
        self.color    = cfg["color"]
        self.key_num  = key_num

        self.running   = False
        self.remaining = self.total

        self.stun_running   = False
        self.stun_remaining = 0.0

        # Flash state
        self._flash_countdown = 0   # counts down 3→2→1 (integer seconds left until checkpoint)
        self._flash_prev_int  = -1  # last integer we showed
        self._flash_on        = False
        self._flash_tick      = 0.0
        self._last_triggered  = set()  # milestones we've already triggered

        # Map size selector (hunt duration panel only)
        self._map_size = "Small"

        self._build(parent)
        self._update_display(self.total)

    # ── Build UI ──────────────────────────────────────────────────────────
    def _build(self, parent):
        self.frame = tk.Frame(parent, bg=BG2,
                              highlightbackground=BORDER, highlightthickness=1)
        self.frame.pack(fill="x", padx=4, pady=2)

        # ── Header row ────────────────────────────────────────────────────
        hdr = tk.Frame(self.frame, bg=BG2)
        hdr.pack(fill="x", padx=8, pady=(5, 0))

        # Key badge
        badge = tk.Frame(hdr, bg=self.color, width=14, height=14)
        badge.pack(side="left", padx=(0, 5))
        badge.pack_propagate(False)
        tk.Label(badge, text=str(self.key_num), bg=self.color, fg=BG,
                 font=("Courier", 6, "bold")).pack(expand=True)

        tk.Label(hdr, text=f"{self.cfg['icon']}  {self.cfg['title']}",
                 bg=BG2, fg=self.color,
                 font=("Courier", 8, "bold")).pack(side="left")

        # Reset button right next to the title
        self.reset_btn = tk.Button(hdr, text="⟳", bg=BG2, fg=MUTED,
                                   relief="flat", bd=0,
                                   font=("Courier", 9, "bold"), padx=4, pady=0,
                                   cursor="hand2",
                                   activebackground=self.color, activeforeground=BG,
                                   command=self.reset)
        self.reset_btn.pack(side="left", padx=(5, 0))

        self.status_var = tk.StringVar(value="READY")
        self.status_lbl = tk.Label(hdr, textvariable=self.status_var,
                                   bg=MUTED, fg=DIM,
                                   font=("Courier", 6, "bold"), padx=4, pady=1)
        self.status_lbl.pack(side="right")

        # ── Centre block: small time | big milestone ───────────────────────
        centre = tk.Frame(self.frame, bg=BG2)
        centre.pack(fill="x", padx=8, pady=(2, 0))

        # LEFT: small countdown
        left = tk.Frame(centre, bg=BG2, width=58)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        self.time_var = tk.StringVar(value=self._fmt(self.total))
        self.time_lbl = tk.Label(left, textvariable=self.time_var,
                                 bg=BG2, fg=WHITE,
                                 font=("Courier", 13, "bold"), anchor="center")
        self.time_lbl.pack(expand=True)

        # Divider
        tk.Frame(centre, bg=BORDER, width=1).pack(side="left", fill="y", padx=(0, 7))

        # RIGHT: big milestone text + flash alert
        right = tk.Frame(centre, bg=BG2)
        right.pack(side="left", fill="both", expand=True)

        self.ms_var = tk.StringVar(value="—")
        self.ms_lbl = tk.Label(right, textvariable=self.ms_var,
                               bg=BG2, fg=DIM,
                               font=("Courier", 12, "bold"),
                               anchor="w", wraplength=220, justify="left")
        self.ms_lbl.pack(anchor="w")

        self.flash_var = tk.StringVar(value="")
        self.flash_lbl = tk.Label(right, textvariable=self.flash_var,
                                  bg=BG2, fg=FLASH2,
                                  font=("Courier", 10, "bold"), anchor="w")
        self.flash_lbl.pack(anchor="w")

        # ── Stun inline (smudge only) ─────────────────────────────────────
        if "stuns" in self.cfg:
            stun_row = tk.Frame(right, bg=BG2)
            stun_row.pack(anchor="w", pady=(3, 0))

            tk.Label(stun_row, text="STUN", bg=BG2, fg=DIM,
                     font=("Courier", 6, "bold")).pack(side="left", padx=(0, 3))

            self.stun_disp = tk.StringVar(value="")
            tk.Label(stun_row, textvariable=self.stun_disp,
                     bg=BG2, fg="#e84393",
                     font=("Courier", 10, "bold"), width=4).pack(side="left", padx=(0, 5))

            for name, secs, col in self.cfg["stuns"]:
                tk.Button(stun_row, text=name, bg=BG3, fg=col, relief="flat", bd=0,
                          font=("Courier", 6, "bold"), padx=4, pady=1,
                          cursor="hand2", activebackground=col, activeforeground=BG,
                          command=lambda s=secs: self._stun_start(s)
                          ).pack(side="left", padx=2)

        # ── Progress bar ──────────────────────────────────────────────────
        self.pbar = ProgressBar(self.frame, self.color, self.total,
                                self.cfg.get("milestones", []))

        # ── Map size selector (hunt duration only) ────────────────────────
        if "map_sizes" in self.cfg:
            map_row = tk.Frame(self.frame, bg=BG2)
            map_row.pack(fill="x", padx=8, pady=(2, 4))
            tk.Label(map_row, text="MAP:", bg=BG2, fg=DIM,
                     font=("Courier", 6, "bold")).pack(side="left", padx=(0, 4))
            self._map_btns = {}
            for size in self.cfg["map_sizes"]:
                col = self.color if size == "Small" else MUTED
                btn = tk.Button(map_row, text=size, bg=BG3, fg=col,
                                relief="flat", bd=0,
                                font=("Courier", 7, "bold"), padx=6, pady=1,
                                cursor="hand2",
                                highlightbackground=col, highlightthickness=1,
                                activebackground=self.color, activeforeground=BG,
                                command=lambda s=size: self._set_map_size(s))
                btn.pack(side="left", padx=2)
                self._map_btns[size] = btn

    # ── Formatting ────────────────────────────────────────────────────────
    def _fmt(self, secs):
        secs = max(0.0, secs)
        m = int(secs) // 60
        s = int(secs) % 60
        return f"{m}:{s:02d}"

    def _set_map_size(self, size):
        self._map_size = size
        data = self.cfg["map_sizes"][size]
        self.total = float(data["total"])
        self.cfg["milestones"] = data["milestones"]
        # Rebuild progress bar ticks
        self.pbar.total      = self.total
        self.pbar.milestones = data["milestones"]
        self.pbar.cv.delete("all")
        self.pbar.cv.create_rectangle(0, 0, BAR_W, BAR_H, fill=BORDER, outline="")
        self.pbar.fill_id = self.pbar.cv.create_rectangle(0, 0, BAR_W, BAR_H,
                                                          fill=self.color, outline="")
        for thresh, _, _ in data["milestones"]:
            ratio = thresh / self.total if self.total else 0
            x = max(1, min(BAR_W - 1, int(BAR_W * ratio)))
            self.pbar.cv.create_line(x, 0, x, BAR_H, fill=WHITE, width=1, dash=(2, 2))
            lbl = f"{thresh}s" if thresh < 60 else f"{thresh//60}:{thresh%60:02d}"
            self.pbar.cv.create_text(x, BAR_H + 6, text=lbl,
                                     fill=DIM, font=("Courier", 6), anchor="center")
        # Update button highlights
        for s, btn in self._map_btns.items():
            active = s == size
            btn.config(fg=self.color if active else MUTED,
                       highlightbackground=self.color if active else MUTED)
        # Reset timer to new total
        self.reset()

    def _stun_start(self, secs):
        self.stun_remaining = float(secs)
        self.stun_running   = True
        self.stun_disp.set(self._fmt(secs))

    # ── Controls ──────────────────────────────────────────────────────────
    def toggle(self):
        self.start()

    def start(self):
        self.remaining = self.total
        self._last_triggered.clear()
        self._flash_countdown  = 0
        self._flash_prev_int   = -1
        self.flash_var.set("")
        self.running = True
        self._set_status("RUNNING", self.color)
        # Auto-start Normal stun (5s) whenever smudge is triggered
        if hasattr(self, "stun_disp"):
            self._stun_start(5)

    def reset(self):
        self.running            = False
        self.remaining          = self.total
        self._last_triggered    = set()
        self._flash_countdown   = 0
        self._flash_prev_int    = -1
        self.flash_var.set("")
        self.time_var.set(self._fmt(self.total))
        self.time_lbl.config(fg=WHITE)
        self.pbar.update(self.total)
        self._set_status("READY", MUTED)
        self.flash_var.set("")
        self._update_display(self.total)
        if hasattr(self, "stun_disp"):
            self.stun_running   = False
            self.stun_remaining = 0
            self.stun_disp.set("")

    def _set_status(self, text, color):
        self.status_var.set(text)
        if color == MUTED:
            self.status_lbl.config(bg=MUTED, fg=DIM)
            self.reset_btn.config(fg=MUTED)
        else:
            self.status_lbl.config(bg=color, fg=BG)
            self.reset_btn.config(fg=self.color)

    # ── Tick (called every ~100 ms) ───────────────────────────────────────
    def tick(self, dt):
        if self.running:
            self.remaining -= dt
            if self.remaining <= 0:
                self.remaining = 0.0
                self.running   = False
                self._set_status("DONE", GREEN)
                self.flash_var.set("")
                self._last_triggered.clear()

            r = self.remaining
            self.time_var.set(self._fmt(r))
            self.pbar.update(r)
            self._update_display(r)
            self._update_flash(r, dt)

        if self.stun_running:
            self.stun_remaining -= dt
            if self.stun_remaining <= 0:
                self.stun_remaining = 0.0
                self.stun_running   = False
                self.stun_disp.set("✓")
            else:
                self.stun_disp.set(self._fmt(self.stun_remaining))

    # ── Milestone display ─────────────────────────────────────────────────
    def _update_display(self, r):
        milestones = self.cfg.get("milestones", [])
        if not milestones:
            return

        triggered = [(t, after, bef) for t, after, bef in milestones if r <= t]
        upcoming  = [(t, after, bef) for t, after, bef in milestones if r  > t]

        if triggered:
            t, after, _ = triggered[-1]
            self.ms_var.set(after)
            col = HUNT_C if t == 0 else GREEN
            self.ms_lbl.config(fg=col)
        elif upcoming:
            _, _, bef = upcoming[0]
            self.ms_var.set(bef)
            self.ms_lbl.config(fg=DIM)
        else:
            self.ms_var.set("—")
            self.ms_lbl.config(fg=DIM)

        # Small timer urgency tint (subtle — it's secondary now)
        ratio = r / self.total if self.total else 0
        if ratio > 0.4:
            self.time_lbl.config(fg=WHITE)
        elif ratio > 0.15:
            self.time_lbl.config(fg=WARN)
        else:
            self.time_lbl.config(fg=HUNT_C)

    # ── 3-second flash countdown ──────────────────────────────────────────
    def _update_flash(self, r, dt):
        milestones = self.cfg.get("milestones", [])
        self._flash_tick += dt

        # Find the nearest upcoming milestone within 3 seconds
        nearest = None
        for thresh, after, _ in milestones:
            dist = r - thresh          # how many seconds away
            if 0 < dist <= 3.05:
                if nearest is None or dist < r - nearest[0]:
                    nearest = (thresh, after)

        if nearest is None:
            # No checkpoint imminent — clear flash
            if self.flash_var.get():
                self.flash_var.set("")
            return

        thresh, label = nearest
        dist    = r - thresh
        cnt_int = max(1, min(3, int(dist) + 1))  # 3, 2, 1

        # Blink every 0.35 s
        if self._flash_tick >= 0.35:
            self._flash_on  = not self._flash_on
            self._flash_tick = 0.0

        if self._flash_on:
            self.flash_lbl.config(fg=FLASH1)
        else:
            self.flash_lbl.config(fg=FLASH2)

        self.flash_var.set(f"⚠ {cnt_int}s  →  {label}")


# ─── Main overlay ─────────────────────────────────────────────────────────────
class PhasmoOverlay:
    def __init__(self, root):
        self.root = root
        self.root.title("Phasmo Overlay")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.95)
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self._dx = self._dy = 0
        self._last = None
        self.panels = []

        self._build()
        self._bind_keys()
        self._tick()

    def _build(self):
        tbar = tk.Frame(self.root, bg=BG3)
        tbar.pack(fill="x")
        tbar.bind("<ButtonPress-1>", lambda e: self._drag_start(e))
        tbar.bind("<B1-Motion>",     lambda e: self._drag_move(e))

        tk.Label(tbar, text="💀  PHASMO OVERLAY", bg=BG3, fg=ACCENT,
                 font=("Courier", 9, "bold")).pack(side="left", padx=10, pady=5)
        tk.Label(tbar, text="[1] [2] [3] [4]", bg=BG3, fg=MUTED,
                 font=("Courier", 7)).pack(side="left", padx=4)
        tk.Button(tbar, text="✕", bg=BG3, fg=MUTED, relief="flat", bd=0,
                  font=("Courier", 11, "bold"), cursor="hand2",
                  activebackground=HUNT_C, activeforeground=WHITE,
                  command=self.root.destroy).pack(side="right", padx=8, pady=4)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, pady=4)

        for i, cfg in enumerate(TIMERS):
            p = TimerPanel(body, cfg, i + 1)
            self.panels.append(p)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")
        tk.Label(self.root, text="drag title to move   •   ✕ to close",
                 bg=BG, fg=MUTED, font=("Courier", 7)).pack(pady=3)

        self.root.update_idletasks()
        self.root.geometry("+0+0")

    def _bind_keys(self):
        if HAS_KEYBOARD:
            # Use on_press so keys fire even while W/A/S/D are held down.
            # add_hotkey blocks combos; on_press does not.
            key_map = {str(i + 1): p for i, p in enumerate(self.panels)}
            # numpad names in the keyboard library
            numpad_map = {f"num {i + 1}": p for i, p in enumerate(self.panels)}

            def _on_press(event):
                panel = key_map.get(event.name) or numpad_map.get(event.name)
                if panel:
                    self.root.after(0, panel.toggle)

            keyboard.on_press(_on_press, suppress=False)
        else:
            # Fallback: only works when overlay is focused
            for i, p in enumerate(self.panels):
                n = str(i + 1)
                self.root.bind_all(f"<Key-{n}>", lambda e, panel=p: panel.toggle())
                self.root.bind_all(f"<KP_{n}>",  lambda e, panel=p: panel.toggle())
            self.root.after(500, lambda: print("Install 'keyboard' package for global hotkeys: pip install keyboard"))

    def _drag_start(self, e):
        self._dx = e.x_root - self.root.winfo_x()
        self._dy = e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def _tick(self):
        now = _time.monotonic()
        dt  = (now - self._last) if self._last else 0.1
        self._last = now
        for p in self.panels:
            p.tick(dt)
        self.root.after(100, self._tick)


if __name__ == "__main__":
    root = tk.Tk()
    PhasmoOverlay(root)
    root.mainloop()