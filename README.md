# Phasmophobia_Ingame_Timer

A floating overlay timer for Phasmophobia gameplay using Python.

## 🖼 UI Overview

<table>
  <tr>
    <td>
      
    </td>
    <td>
      
    </td>
  </tr>
</table>

## Features

- Floating overlay window with progress bars for different timers.
- Keyboard shortcuts: 1/2/3/4 to start/reset timers.
- Timers include Smudge, Hunt Cooldown, Hunt Duration, and Paranormal Sounds.
- Each timer cycles through different ghost types/options when started.

## Installation

1. Ensure Python 3.12 or later is installed.
2. Install dependencies: `pip install pynput`
3. Run the script: `python PhasTimer.py`

## Usage

- Press 1: Smudge Timer (3 minutes, shows when ghosts can hunt)
- Press 2: Hunt Cooldown (cycles between Normal 30s and Demon 25s)
- Press 3: Hunt Duration (cycles between Obambo Short 25s, Normal 30s, Obambo Long 45s, Cursed 50s)
- Press 4: Paranormal Sounds (cycles between Normal 80s and Myling 80s)

The overlay is semi-transparent, topmost, and movable by dragging.

## Requirements

- Python 3.12+
- pynput
- tkinter (built-in)
