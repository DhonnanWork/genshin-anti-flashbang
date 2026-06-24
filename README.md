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

## Running Automatically at Startup (Silent Mode)

You can run this program silently in the background without a persistent Command Prompt window by utilizing the `run_silently.vbs` script.

### 1. Create the VBScript File
Ensure you have a file named `run_silently.vbs` in your project folder with the following content:

```vbscript
Set ObjShell = CreateObject("Wscript.Shell")
StrPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(Wscript.ScriptFullName)
ObjShell.CurrentDirectory = StrPath
ObjShell.Run "python genshin_window_checker.py", 0, False
```

### 2. Place it in the Windows Startup Folder
To configure the utility to start automatically whenever you turn on your computer:

1. Press `Win + R` on your keyboard to open the Windows **Run** dialog.
2. Type `shell:startup` and click **OK**. This opens your Windows Startup folder.
3. Right-click inside the Startup folder and select **New > Shortcut**.
4. Click **Browse** and select your `run_silently.vbs` file, then finish creating the shortcut.

Now, whenever you log into Windows, the script will run silently in the background, consuming minimal system memory. It will remain completely inactive until you launch *Genshin Impact*.

### How to Stop the Program
Since the script runs without a visible terminal window, you can stop it via Windows:
1. Open the Windows **Task Manager** (`Ctrl + Shift + Esc`).
2. Search for the process named **Python** under *Background processes*.
3. Right-click it and select **End Task**.
