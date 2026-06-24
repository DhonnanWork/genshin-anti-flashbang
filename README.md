# Genshin Anti-Flashbang

A lightweight, eye-protecting utility that detects sudden full-screen white flashes (such as game loading screens) and overlays a temporary dark screen that smoothly fades out as the flash passes.

Designed primarily for *Genshin Impact*, it runs silently in the background on extremely low resources and is structured using strict execution safety standards.

---

## Key Features

* **Instant Flash Protection:** Dynamically captures the window's state every 30ms to intercept sudden bright white frames.
* **Smart Border Sensing:** Uses a custom 6-pixel inset overlay allowing the program's border sensors (checking at a 5-pixel offset) to monitor the true game window state even when the black mask is displayed on top of the screen.
* **Low CPU/GPU Impact:** Captures frame coordinates via fast single-pass grabs using the `mss` library and performs rapid average luminance evaluations using NumPy arrays instead of iterating over individual pixels.
* **Rapid False Positive Check:** Re-evaluates frame state every 10ms (100 times per second) when triggered. If a flash is brief (such as a combat animation or UI element), the overlay instantly aborts to avoid disrupting gameplay.
* **Robust Execution Constraints:** Developed adhering to standard mission-critical software patterns:
  * **Bounded Execution Loops:** No infinite `while` loops; all background routines run within hard-bounded iterations to avoid freezing threads.
  * **Explicit Parameter Assertions:** Functions contain explicit parameter and state checks to prevent invalid execution states.
  * **Modular Design:** Deconstructed into small, distinct modules and sub-routines (under 60 lines per function) for high maintainability and static checking.

---

## Project Structure

* **`genshin_window_checker.py`**: A background daemon that searches for the target game window every 3 seconds. It manages a named system mutex to guarantee only one monitor instance runs at a time.
* **`main.py`**: The core logic engine that manages coordinate checks, monitors game state, and coordinates overlay activations.
* **`capture.py`**: Fast frame grabber that checks border and screen arrays via memory slices to compute relative luminance.
* **`overlay.py`**: Handles drawing an always-on-top, click-through (`WS_EX_TRANSPARENT`), black layered window that fades out progressively.
* **`window_utils.py`**: Standard window rect lookup, multi-window enum filters, and configuration handlers.
* **`config.py`**: Holds standard configurable thresholds, check intervals, and timing constraints.

---

## Installation & Setup

### Prerequisites
Make sure you have Python 3 installed on your Windows machine, along with the required dependencies:

```bash
pip install mss numpy pywin32
```

---
## How to Run

### Running Manually (Standard Mode)
If you want to run the utility manually and see the console logs (recommended for testing or selecting your window on the initial run), open your terminal in the project directory and execute:

```bash
python genshin_window_checker.py
```
*Keep this terminal window open while playing. You can stop the program at any time by pressing `Ctrl + C` in the terminal.*

---

### Running Automatically at Startup (Silent Mode)

The project includes a pre-configured `run_silently.vbs` script that runs the window checker in the background without keeping a Command Prompt window visible on your taskbar.

To configure the utility to start automatically on system boot:

1. Press `Win + R` on your keyboard to open the Windows **Run** dialog.
2. Type `shell:startup` and click **OK** to open your Windows **Startup** folder.
3. Right-click an empty space inside the Startup folder and select **New > Shortcut**.
4. Click **Browse...**, navigate to your project directory, and select the existing `run_silently.vbs` file.
5. Click **Next** and then **Finish** to complete the shortcut setup.

The script will now launch silently in the background every time you log into Windows, monitoring for the game window and remaining completely inactive until the game is launched.

### How to Stop the Program
Since the script runs without a visible terminal window, you can stop it via Windows:
1. Open the Windows **Task Manager** (`Ctrl + Shift + Esc`).
2. Search for the process named **Python** under *Background processes*.
3. Right-click it and select **End Task**.
