# Rise of Kingdoms - Gem Farming Bot

This Python script uses `pyautogui` to automate the process of finding and farming gem deposits in the game Rise of Kingdoms. It includes features for screen scanning, mouse control, and a systematic 'snake' (boustrophedon) navigation pattern to search for gems.

## Features

*   Scans for gem deposits using template images (day and night versions).
*   Automates the click sequence: Gem -> Gather -> (Optional) New Troop -> March.
*   Detects a specific orange march button after attempting to gather, indicating a potential full queue or other condition, and waits for 30 minutes before resuming search.
*   Navigates the map using a systematic 'snake' (boustrophedon) pattern to cover a large area, replacing the previous spiral search.
*   Configurable settings for confidence levels, delays, and navigation parameters.
*   Debug options, including taking screenshots on certain events (e.g., after initial click, if gather fails).
*   Simple GUI to start and stop the bot.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install dependencies:**
    Ensure you have Python 3 installed. Then, install the required packages using pip:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `pyautogui` and `Pillow`. Depending on your operating system, `pyautogui` might have other dependencies. Please refer to the [PyAutoGUI installation instructions](https://pyautogui.readthedocs.io/en/latest/install.html) for more details (e.g., `python3-tk`, `python3-dev`, ` scrot` and `libxtst-dev` on Linux, or `pyobjc-framework-Quartz`, `pyobjc-core`, and `pyobjc` on macOS).

3.  **Prepare Image Templates:**
    *   You need to provide your own template images for the bot to work correctly. These are the images the bot will search for on the screen.
    *   Place your images in the `rok_bot/images/` directory.
    *   The script is configured to look for the following image files by default:
        *   `gem_deposit_template.png` (Daytime gem deposit)
        *   `gem_deposit_template_night.png` (Nighttime gem deposit)
        *   `gather_template.png` (The "Gather" button)
        *   `new_troop_template.png` (The "New Troop" button, if applicable)
        *   `march_template.png` (The "March" button)
        *   `orange_march_button.png` (A specific orange-colored march button that indicates a full queue or special condition)
    *   Ensure these filenames match exactly, or update the paths at the top of the `rok_bot/gem_farmer.py` script.
    *   Good quality template images are crucial for the bot's accuracy. Crop them tightly around the object you want to detect.

## How to Run

1.  **Open Rise of Kingdoms:** Make sure the game is running and is the active window on your primary screen. The bot interacts with whatever is visible on the screen.
2.  **Run the script:**
    Navigate to the root directory of the project in your terminal and run:
    ```bash
    python rok_bot/gem_farmer.py
    ```
Alternatively, launch the GUI:
    ```bash
    python rok_bot/gui.py
    ```
3.  **Initial Countdown:** The script has a 5-second countdown before it starts interacting. Use this time to switch to the game window and ensure it's in focus.
4.  **Stopping the Bot:**
    *   **Failsafe:** Quickly move your mouse cursor to one of the corners of your primary screen. This will trigger `pyautogui`'s failsafe mechanism and stop the script.
    *   **Ctrl+C:** You can also try pressing `Ctrl+C` in the terminal window where the script is running.

## Configuration

The main configuration variables are located at the top of the `rok_bot/gem_farmer.py` script. You can adjust:
*   `CONFIDENCE_GEM`, `CONFIDENCE_GATHER`, `CONFIDENCE_GENERAL`: Confidence levels for image detection (0.0 to 1.0). Lower values may find more matches but can lead to false positives. Higher values require a closer match.
*   `CLICK_DELAY_SHORT`, `CLICK_DELAY_MEDIUM`, `CLICK_DELAY_LONG`: Pauses after certain actions.
*   `FARMING_DURATION_SECONDS`: How long to wait after successfully dispatching troops (default: 5 minutes).
*   `ORANGE_MARCH_BUTTON_TEMPLATE`: Path to the image for the special orange march button that might indicate a full farming queue (default: `images/orange_march_button.png`).
*   `ORANGE_MARCH_WAIT_SECONDS`: Duration (in seconds) to wait if the orange march button is detected (default: `1800`, i.e., 30 minutes).
*   `DEBUG_TAKE_SCREENSHOT_AFTER_FIRST_CLICK`, `DEBUG_TAKE_SCREENSHOT_IF_GATHER_FAILS`: Set to `True` or `False` to enable/disable debug screenshots. Screenshots are saved in the `rok_bot/debug_screenshots` directory.

### Systematic Search (Snake Pattern) Configuration:
The bot now uses a 'snake' or boustrophedon pattern for map exploration.
*   `SEARCH_PATTERN_TYPE`: Defines the active search pattern (currently hardcoded to `"snake"` in the script, this variable is for future flexibility).
*   `SNAKE_HORIZONTAL_SCROLL_KEY_RIGHT`: Key used to scroll the map to the right (default: `'right'`).
*   `SNAKE_HORIZONTAL_SCROLL_KEY_LEFT`: Key used to scroll the map to the left (default: `'left'`).
*   `SNAKE_VERTICAL_SCROLL_KEY`: Key used to scroll the map downwards for a vertical shift (default: `'down'`).
*   `SNAKE_HORIZONTAL_PASS_UNITS`: Conceptual. Represents the intended number of horizontal segments or decision points in one full sweep. The actual distance of a pass is determined by `SNAKE_SCANS_PER_HORIZONTAL_PASS` multiplied by the scroll distance of each `SNAKE_SCROLL_SEGMENT_DURATION`.
*   `SNAKE_VERTICAL_SHIFT_UNITS`: Conceptual. Represents the intended vertical shift. The actual distance is determined by how long `SNAKE_VERTICAL_SCROLL_KEY` is pressed, which in the current implementation is tied to `SNAKE_SCROLL_SEGMENT_DURATION`.
*   `SNAKE_SCANS_PER_HORIZONTAL_PASS`: The number of times the bot will scan for gems during one horizontal pass (i.e., before making a vertical shift). Each scan is preceded by a scroll segment.
*   `SNAKE_SCROLL_SEGMENT_DURATION`: The duration (in seconds) for which the script will press a horizontal scroll key for each segment of a pass (default: `2.0` seconds).
*   `SYSTEMATIC_SCAN_PAUSE_IF_NO_GEM`: The duration (in seconds) the bot will pause after a scan if no gem is found, before continuing the search pattern (default: `0.5` seconds).

## Disclaimer

This bot interacts with the game by simulating mouse clicks and keyboard inputs based on screen image recognition. Using bots can be against the terms of service of many games, including Rise of Kingdoms. Use this script responsibly and at your own risk. The developers of this script are not responsible for any consequences that may arise from its use.

Ensure the game window is unobstructed and on your primary monitor for the bot to function correctly. The bot's performance can be affected by screen resolution and in-game visual settings.
```
