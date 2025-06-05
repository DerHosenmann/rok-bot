import pyautogui
import time
import traceback
import os
import argparse
import pygetwindow as gw

# --- Configuration ---
GEM_TEMPLATE_DAY = r'images/gem_deposit_template.png' # Adjusted path
GEM_TEMPLATE_NIGHT = r'images/gem_deposit_template_night.png' # Adjusted path
GATHER_TEMPLATE = r'images/gather_template.png' # Adjusted path
NEW_TROOP_TEMPLATE = r'images/new_troop_template.png' # Adjusted path
MARCH_TEMPLATE = r'images/march_template.png' # Adjusted path
ORANGE_MARCH_BUTTON_TEMPLATE = r'images/orange_march_button.png' # New
TROOP_BACK_TEMPLATE = r'images/troop_back.png'

# Gem icons for different zoom levels
GEM_ICON_ZOOM1_TEMPLATES = [rf'images/GemDeposit0{i}.png' for i in range(1, 9)]
GEM_ICON_ZOOM2_TEMPLATES = [rf'images/GemDepositD0{i}.png' for i in range(1, 9)]

# Images to verify a real gem deposit after clicking an icon
GEM_VERIFY_TEMPLATES = [
    r'images/Gem.png',
    r'images/Gem2.png',
    r'images/Gem3.png',
]

# Gathering state templates
GATHERING_SELF_TEMPLATES = [r'images/Gathering.png', r'images/Gathering2.png']
GATHERING_ALLY_TEMPLATES = [r'images/GatheringByAlly.png', r'images/GatheringByAlly2.png']
GATHERING_ENEMY_TEMPLATES = [r'images/GatheringByEnemy.png', r'images/GatheringByEnemy2.png']
GATHERING_MEMBER_TEMPLATES = [r'images/GatheringByMember.png', r'images/GatheringByMember2.png']
# Images that indicated a march in progress to the deposit were previously checked
# via ``MARCHING_TEMPLATES``. These checks caused the bot to skip deposits
# incorrectly, so the list is now empty to disable the behaviour.
MARCHING_TEMPLATES = []


CONFIDENCE_GEM = 0.8
CONFIDENCE_GATHER = 0.80
CONFIDENCE_GENERAL = 0.85

CLICK_DELAY_SHORT = 0.7
CLICK_DELAY_MEDIUM = 2.0
CLICK_DELAY_LONG = 3.0
ORANGE_MARCH_WAIT_SECONDS = 30 * 60 # 30 minutes # New

FARMING_DURATION_SECONDS = 60 * 5
# SEARCH_INTERVAL_SECONDS (not directly used in main loop with continuous nav/scan)

DEFAULT_MOVE_DURATION = 0.4
PRE_CLICK_DELAY = 0.3

MAX_SUBSEQUENT_STEP_RETRIES = 3
RETRY_PAUSE_SECONDS = 2.5

DEBUG_TAKE_SCREENSHOT_AFTER_FIRST_CLICK = True
DEBUG_TAKE_SCREENSHOT_IF_GATHER_FAILS = True
SCREENSHOT_DIR = "debug_screenshots" # Will be relative to where script is run
USE_ALT_CLICK_METHOD = False

# Window management
TARGET_WINDOW_SIZE = (1280, 720)  # Width x Height for the game window

# Track deposits that have already been targeted to prevent sending troops twice
# to the same location within a session.
DISPATCH_IGNORE_RADIUS = 40  # pixels
DISPATCHED_LOCATIONS = []
RIGHT_CLICK_NEXT_GEM = False

# --- Systematic Search Configuration ---
SEARCH_PATTERN_TYPE = "snake" # Defines the active search pattern

# Configuration for "snake" pattern
SNAKE_HORIZONTAL_SCROLL_KEY_RIGHT = 'right' # Key for scrolling right
SNAKE_HORIZONTAL_SCROLL_KEY_LEFT = 'left'   # Key for scrolling left
SNAKE_VERTICAL_SCROLL_KEY = 'down'          # Key for vertical shift

SNAKE_HORIZONTAL_PASS_UNITS = 100 # Arbitrary units for a full horizontal pass (e.g., screen widths, or time units) - CONCEPTUAL, NOT DIRECTLY USED BY DURATION-BASED SCROLLING
SNAKE_VERTICAL_SHIFT_UNITS = 20   # Arbitrary units for vertical shift after a pass (e.g., screen heights, or time units) - CONCEPTUAL, NOT DIRECTLY USED BY DURATION-BASED SCROLLING
SNAKE_SCANS_PER_HORIZONTAL_PASS = 5 # Number of times to scan for gems during one horizontal leg

# Duration settings for scroll actions in snake pattern
# This implies using pyautogui.keyDown, time.sleep, pyautogui.keyUp for each scroll segment.
SNAKE_SCROLL_SEGMENT_DURATION = 2.0 # Seconds to scroll for each segment of a horizontal pass

# General pause after a scan if no gem is found during systematic search
SYSTEMATIC_SCAN_PAUSE_IF_NO_GEM = 0.5

# Zoom configuration
# Up to three zoom-out steps after dispatching a march
# These represent the number of mouse wheel clicks for each step.
ZOOM_OUT_CLICKS_AFTER_MARCH_FIRST = 0
ZOOM_OUT_CLICKS_AFTER_MARCH_SECOND = 0
ZOOM_OUT_CLICKS_AFTER_MARCH_THIRD = 0
ZOOM_OUT_CLICKS_AFTER_MARCH_FOURTH = 0
# Delay between the zoom actions (seconds)
ZOOM_OUT_DELAY_BETWEEN = 0.1

# Create screenshot directory
# Adjusted to be relative to the script's location
script_dir = os.path.dirname(__file__)
screenshot_full_path = os.path.join(script_dir, SCREENSHOT_DIR)

LOG_FILE_NAME = "bot_status.log"
log_file_path = os.path.join(script_dir, LOG_FILE_NAME)
open(log_file_path, 'w').close()  # clear log at start

import builtins
import logging

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_print(*args, **kwargs):
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    message = sep.join(str(a) for a in args)
    timestamped = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    builtins.print(timestamped, end=end, sep=sep)
    logging.info(message)

print = log_print


def parse_args():
    parser = argparse.ArgumentParser(description="Rise of Kingdoms gem farming bot")
    parser.add_argument(
        "--confidence-gem",
        type=float,
        default=CONFIDENCE_GEM,
        help="Confidence for detecting gem deposits",
    )
    parser.add_argument(
        "--scroll-duration",
        type=float,
        default=SNAKE_SCROLL_SEGMENT_DURATION,
        help="Duration in seconds for each horizontal scroll segment",
    )
    parser.add_argument(
        "--scans-per-pass",
        type=int,
        default=SNAKE_SCANS_PER_HORIZONTAL_PASS,
        help="Number of scan segments per horizontal pass",
    )
    parser.add_argument(
        "--pause-no-gem",
        type=float,
        default=SYSTEMATIC_SCAN_PAUSE_IF_NO_GEM,
        help="Pause after a scan if no gem is found",
    )
    parser.add_argument(
        "--zoom-out-clicks-first",
        type=int,
        default=ZOOM_OUT_CLICKS_AFTER_MARCH_FIRST,
        help="Mouse wheel clicks for the first zoom-out after dispatching a march",
    )
    parser.add_argument(
        "--zoom-out-clicks-second",
        type=int,
        default=ZOOM_OUT_CLICKS_AFTER_MARCH_SECOND,
        help="Mouse wheel clicks for the second zoom-out after dispatching a march",
    )
    parser.add_argument(
        "--zoom-out-clicks-third",
        type=int,
        default=ZOOM_OUT_CLICKS_AFTER_MARCH_THIRD,
        help="Mouse wheel clicks for the third zoom-out after dispatching a march",
    )
    parser.add_argument(
        "--zoom-out-clicks-fourth",
        type=int,
        default=ZOOM_OUT_CLICKS_AFTER_MARCH_FOURTH,
        help="Mouse wheel clicks for the fourth zoom-out after dispatching a march",
    )
    parser.add_argument(
        "--farming-duration",
        type=int,
        default=FARMING_DURATION_SECONDS,
        help="Time in seconds to wait after sending a march",
    )
    return parser.parse_args()


def ensure_game_window_size(width=TARGET_WINDOW_SIZE[0], height=TARGET_WINDOW_SIZE[1],
                            title_keywords=("Rise of Kingdoms", "BlueStacks", "LDPlayer")):
    """Ensure the game window is resized to the desired dimensions."""
    try:
        for kw in title_keywords:
            windows = gw.getWindowsWithTitle(kw)
            if windows:
                win = windows[0]
                try:
                    win.resizeTo(width, height)
                    print(f"Set window '{win.title}' size to {width}x{height}")
                except Exception as e:
                    print(f"Failed to resize window '{win.title}': {e}")
                try:
                    win.activate()
                except Exception:
                    pass
                return
        print("Game window not found for resizing. Titles checked: " + ", ".join(title_keywords))
    except Exception as e:
        print(f"Error while adjusting window size: {e}")

if (DEBUG_TAKE_SCREENSHOT_AFTER_FIRST_CLICK or DEBUG_TAKE_SCREENSHOT_IF_GATHER_FAILS) and not os.path.exists(screenshot_full_path):
    try:
        os.makedirs(screenshot_full_path)
        print(f"Created directory for debug screenshots: {screenshot_full_path}")
    except Exception as e:
        print(f"Could not create screenshot directory {screenshot_full_path}: {e}")

# Utility to fetch the active game window
def get_game_window(title_keywords=("Rise of Kingdoms", "BlueStacks", "LDPlayer")):
    """Return the first window matching known game titles."""
    try:
        for kw in title_keywords:
            windows = gw.getWindowsWithTitle(kw)
            if windows:
                return windows[0]
    except Exception as e:
        print(f"Error while retrieving game window: {e}")
    return None

# Helper to calculate the center box of the game window
def get_game_center_box():
    """Return a small box centred on the game window for reliable clicking."""
    win = get_game_window()
    if win:
        return (
            win.left + win.width // 2 - 1,
            win.top + win.height // 2 - 1,
            2,
            2,
        )
    # Fallback to assuming the window starts at (0,0)
    return (
        TARGET_WINDOW_SIZE[0] // 2 - 1,
        TARGET_WINDOW_SIZE[1] // 2 - 1,
        2,
        2,
    )

# --- Helper Functions ---
def find_template(template_image_path, confidence_level, description="template", use_grayscale=False,
                  debug_screenshot_on_fail=False, screenshot_filename_prefix="fail_", region=None):
    # Ensure template path is relative to script directory
    full_template_path = os.path.join(script_dir, template_image_path)
    print(f"Searching for '{description}' (file: {full_template_path}) with confidence {confidence_level:.2f}, grayscale: {use_grayscale}...")
    try:
        location = pyautogui.locateOnScreen(full_template_path, confidence=confidence_level,
                                            grayscale=use_grayscale, region=region)
        if location:
            if (location.left == 0 and location.top == 0 and
                    location.width <= 5 and location.height <= 5):
                # Extremely small match in the top-left corner is often a false positive
                print(f"Suspicious detection for '{description}' at {location}. Ignoring as false positive.")
                location = None
            else:
                print(f"Found '{description}' at: {location}")
                return location
        else:
            if debug_screenshot_on_fail:
                try:
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    # Use screenshot_full_path for saving screenshots
                    filename = os.path.join(screenshot_full_path, f"{screenshot_filename_prefix}{description.replace(' ', '_')}_{timestamp}.png")
                    pyautogui.screenshot(filename)
                    print(f"DEBUG: '{description}' not found, screenshot saved to {filename} for analysis.")
                except Exception as e:
                    print(f"DEBUG: Failed to take screenshot for '{description}' on fail: {e}")
            return None
    except pyautogui.ImageNotFoundException:
        if debug_screenshot_on_fail:
             try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = os.path.join(screenshot_full_path, f"{screenshot_filename_prefix}{description.replace(' ', '_')}_{timestamp}_exception.png")
                pyautogui.screenshot(filename)
                print(f"DEBUG: '{description}' ImageNotFoundException, screenshot saved to {filename} for analysis.")
             except Exception as e:
                print(f"DEBUG: Failed to take screenshot for '{description}' on exception: {e}")
        return None
    except Exception as e:
        print(f"Error during PyAutoGUI search for '{description}' ({full_template_path}): {type(e).__name__} - {e}")
        if "Failed to read" in str(e) or "could not be found" in str(e) or "No such file or directory" in str(e):
             print(f"CRITICAL FILE ERROR: Ensure '{full_template_path}' exists, path is correct, and it's a valid image.")
        return None

def verify_deposit_available():
    """Verify the clicked object is a gem deposit.

    All checks for whether another player is gathering have been removed. The
    availability of a deposit should be determined **before** clicking using
    :func:`is_deposit_gathered_on_map`.
    """

    found_confirm = False
    for tmpl in GEM_VERIFY_TEMPLATES:
        if find_template(
            tmpl,
            CONFIDENCE_GENERAL,
            f"Verify Gem {os.path.basename(tmpl)}",
            use_grayscale=True,
        ):
            found_confirm = True
            break

    if not found_confirm:
        print("Gem confirmation images not found - skipping this icon.")
        return False

    return True

def find_any_gem_deposit(confidence_level, use_grayscale):
    # Search through all provided gem icon templates
    for path in GEM_ICON_ZOOM1_TEMPLATES + GEM_ICON_ZOOM2_TEMPLATES:
        location = find_template(path, confidence_level, f"Gem Icon {os.path.basename(path)}", use_grayscale=use_grayscale)
        if location:
            return location

    # Fallback to legacy day/night templates if provided
    location = find_template(GEM_TEMPLATE_DAY, confidence_level, "Gem Deposit (Day)", use_grayscale=use_grayscale)
    if location:
        return location
    location = find_template(GEM_TEMPLATE_NIGHT, confidence_level, "Gem Deposit (Night)", use_grayscale=use_grayscale)
    if location:
        return location
    return None

def click_at_location(location_box, description="location", move_duration=DEFAULT_MOVE_DURATION, pre_click_pause=PRE_CLICK_DELAY):
    if not location_box:
        print(f"No location_box provided for '{description}', cannot click.")
        return False
    try:
        center_x, center_y = pyautogui.center(location_box)
        print(f"Calculated center for '{description}': ({int(center_x)}, {int(center_y)})")
        current_mouse_x, current_mouse_y = pyautogui.position()
        print(f"Current mouse position BEFORE move: ({current_mouse_x}, {current_mouse_y})")
        pyautogui.moveTo(center_x, center_y, duration=move_duration)
        print(f"Mouse moved to ({int(center_x)}, {int(center_y)}) for '{description}' over {move_duration}s.")
        if pre_click_pause > 0:
            print(f"Waiting {pre_click_pause:.2f}s before clicking '{description}'...")
            time.sleep(pre_click_pause)
        if USE_ALT_CLICK_METHOD:
            print(f"Using alternative click method for '{description}' (mouseDown/mouseUp).")
            pyautogui.mouseDown(); time.sleep(0.05); pyautogui.mouseUp()
        else:
            print(f"Using standard click method for '{description}'.")
            pyautogui.click()
        print(f"Action resembling click performed for '{description}' at ({int(center_x)}, {int(center_y)})")
        return True
    except Exception as e:
        print(f"Error during move or click operation for '{description}': {e}")
        traceback.print_exc(); return False

def right_click_at_location(location_box, description="location", move_duration=DEFAULT_MOVE_DURATION, pre_click_pause=PRE_CLICK_DELAY):
    """Perform a right-click at the specified location."""
    if not location_box:
        print(f"No location_box provided for '{description}', cannot right-click.")
        return False
    try:
        center_x, center_y = pyautogui.center(location_box)
        pyautogui.moveTo(center_x, center_y, duration=move_duration)
        if pre_click_pause > 0:
            time.sleep(pre_click_pause)
        pyautogui.click(button='right')
        print(f"Right-clicked '{description}' at ({int(center_x)}, {int(center_y)})")
        return True
    except Exception as e:
        print(f"Error during right-click operation for '{description}': {e}")
        traceback.print_exc(); return False

def find_and_click(template_image_path, confidence_level, description,
                   click_delay_after=CLICK_DELAY_SHORT, optional=False,
                   move_duration=DEFAULT_MOVE_DURATION, pre_click_pause=PRE_CLICK_DELAY,
                   use_grayscale=False,
                   debug_screenshot_on_fail_find=False,
                   screenshot_filename_prefix="fail_find_"):
    location = find_template(template_image_path, confidence_level, description, use_grayscale=use_grayscale,
                             debug_screenshot_on_fail=debug_screenshot_on_fail_find,
                             screenshot_filename_prefix=screenshot_filename_prefix)
    if location:
        if click_at_location(location, description, move_duration=move_duration, pre_click_pause=pre_click_pause):
            print(f"Action resembling click successful for '{description}'.")
            print(f"Waiting {click_delay_after:.2f}s...")
            time.sleep(click_delay_after)
            return location # Return location if successful
        else:
            print(f"Found '{description}' but action resembling click failed.")
            return None # Indicate click failure
    else:
        if optional:
            print(f"'{description}' is optional and not found, continuing sequence.")
            return True # Indicate optional item was handled (by not being found)
        return None # Indicate mandatory item not found


def is_near_dispatched(location_box):
    """Return True if the location is close to a previously dispatched deposit."""
    center_x, center_y = pyautogui.center(location_box)
    for dx, dy in DISPATCHED_LOCATIONS:
        if abs(center_x - dx) <= DISPATCH_IGNORE_RADIUS and abs(center_y - dy) <= DISPATCH_IGNORE_RADIUS:
            return True
    return False


def record_dispatched(location_box):
    """Record the center of a successfully dispatched gem deposit."""
    center_x, center_y = pyautogui.center(location_box)
    DISPATCHED_LOCATIONS.append((center_x, center_y))


def zoom_out_after_dispatch():
    """Zoom out the map in up to four steps after a successful dispatch."""
    if ZOOM_OUT_CLICKS_AFTER_MARCH_FIRST > 0:
        print(
            f"Zooming out {ZOOM_OUT_CLICKS_AFTER_MARCH_FIRST} wheel clicks (step 1) after dispatch..."
        )
        pyautogui.scroll(-ZOOM_OUT_CLICKS_AFTER_MARCH_FIRST)
        time.sleep(ZOOM_OUT_DELAY_BETWEEN)
    if ZOOM_OUT_CLICKS_AFTER_MARCH_SECOND > 0:
        print(
            f"Zooming out {ZOOM_OUT_CLICKS_AFTER_MARCH_SECOND} wheel clicks (step 2) after dispatch..."
        )
        pyautogui.scroll(-ZOOM_OUT_CLICKS_AFTER_MARCH_SECOND)
        time.sleep(ZOOM_OUT_DELAY_BETWEEN)
    if ZOOM_OUT_CLICKS_AFTER_MARCH_THIRD > 0:
        print(
            f"Zooming out {ZOOM_OUT_CLICKS_AFTER_MARCH_THIRD} wheel clicks (step 3) after dispatch..."
        )
        pyautogui.scroll(-ZOOM_OUT_CLICKS_AFTER_MARCH_THIRD)
        time.sleep(ZOOM_OUT_DELAY_BETWEEN)
    if ZOOM_OUT_CLICKS_AFTER_MARCH_FOURTH > 0:
        print(
            f"Zooming out {ZOOM_OUT_CLICKS_AFTER_MARCH_FOURTH} wheel clicks (step 4) after dispatch..."
        )
        pyautogui.scroll(-ZOOM_OUT_CLICKS_AFTER_MARCH_FOURTH)


def perform_quick_gem_farming_cycle(initial_gem_location_box):
    """Farm a gem deposit using a single right-click."""
    print("\n--- Quick right-click gem farming ---")
    if not right_click_at_location(initial_gem_location_box, "Quick Right-Click Gem", move_duration=0.5, pre_click_pause=0.4):
        print("Failed to right-click on the located gem.")
        return False
    zoom_out_after_dispatch()
    return True

def is_deposit_gathered_on_map(location_box, margin=30):
    """Return True if the provided location appears to be already gathered on the map."""
    left = max(location_box.left - margin, 0)
    top = max(location_box.top - margin, 0)
    region = (left, top, location_box.width + margin * 2, location_box.height + margin * 2)

    for check_list, desc in [
        (GATHERING_SELF_TEMPLATES, "Already Gathering (self)"),
        (GATHERING_ALLY_TEMPLATES, "Gathered by Ally"),
        (GATHERING_ENEMY_TEMPLATES, "Gathered by Enemy"),
        (GATHERING_MEMBER_TEMPLATES, "Gathered by Member"),
    ]:
        for tmpl in check_list:
            if find_template(tmpl, CONFIDENCE_GENERAL, desc, use_grayscale=True, region=region):
                print(f"{desc} detected near deposit on map. Skipping deposit before interaction.")
                return True
    return False


# --- Main Farming Logic (Called after a gem is SPOTTED) ---
def perform_full_gem_farming_cycle(initial_gem_location_box):
    print("\n--- Attempting to farm located gem ---")

    if not click_at_location(initial_gem_location_box, "Click Located Initial Gem", move_duration=0.5, pre_click_pause=0.4):
        print("Failed to perform initial click on the located gem. Aborting this gem.")
        return False

    if DEBUG_TAKE_SCREENSHOT_AFTER_FIRST_CLICK:
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            # Use screenshot_full_path for saving screenshots
            filename = os.path.join(screenshot_full_path, f"after_initial_click_on_located_gem_{timestamp}.png")
            pyautogui.screenshot(filename)
            print("DEBUG: Screenshot after initial click on located gem saved to"
                  f" {filename}. EXAMINE THIS.")
            print("       Verify if the game menu opened and if the 'Gather Button' is visible.")
        except Exception as e:
            print(f"DEBUG: Failed to take screenshot: {e}")

    time.sleep(CLICK_DELAY_MEDIUM)

    # After the initial click the game typically centers the gem within the game
    # window. Calculate the window centre dynamically so re-clicks remain
    # accurate even if the window has been moved.
    initial_gem_location_box = get_game_center_box()

    if not verify_deposit_available():
        print("Deposit not available after verification. Skipping.")
        zoom_out_after_dispatch()
        return False

    for attempt in range(MAX_SUBSEQUENT_STEP_RETRIES):
        print(f"\nAttempt {attempt + 1} of {MAX_SUBSEQUENT_STEP_RETRIES} for subsequent steps (Gather, New Troop, March)...")

        # Ensure the gem menu is open by clicking the deposit at the start of each attempt
        initial_gem_location_box = get_game_center_box()
        click_at_location(
            initial_gem_location_box,
            "Re-Click Initial Gem at Attempt Start",
            move_duration=0.3,
            pre_click_pause=0.1,
        )
        time.sleep(RETRY_PAUSE_SECONDS / 2)

        gather_button_location_result = find_and_click( # Renamed to avoid conflict
            GATHER_TEMPLATE, CONFIDENCE_GATHER, "Gather Button",
            click_delay_after=CLICK_DELAY_MEDIUM, use_grayscale=True,
            debug_screenshot_on_fail_find=DEBUG_TAKE_SCREENSHOT_IF_GATHER_FAILS,
            screenshot_filename_prefix="fail_gather_"
        )
        # Check if gather_button_location_result is None (failure) or True (optional and not found, but this isn't optional)
        # For a mandatory step like Gather, we need a location box, not True.
        if not gather_button_location_result or gather_button_location_result is True:
            if attempt < MAX_SUBSEQUENT_STEP_RETRIES - 1:
                print(f"Gather Button not found or click failed on attempt {attempt + 1}. Re-clicking initial gem and retrying...")
                initial_gem_location_box = get_game_center_box()
                click_at_location(initial_gem_location_box, "Re-Click Initial Gem", move_duration=0.3, pre_click_pause=0.1)
                time.sleep(RETRY_PAUSE_SECONDS)
                continue
            else:
                print("Failed to find or action Gather Button after all retries.")
                return False


        new_troop_action_result = find_and_click(
            NEW_TROOP_TEMPLATE, CONFIDENCE_GENERAL, "New Troop Button",
            click_delay_after=CLICK_DELAY_MEDIUM, optional=True, use_grayscale=True
        )
        # new_troop_action_result will be:
        # - location box if found and clicked
        # - True if optional and not found
        # - None if mandatory and not found, or if click failed
        if new_troop_action_result is None: # This means it was mandatory (not optional) OR click failed
             if attempt < MAX_SUBSEQUENT_STEP_RETRIES - 1:
                print("New Troop Button (optional but failed interaction or mandatory and failed). Re-clicking initial gem...")
                initial_gem_location_box = get_game_center_box()
                click_at_location(initial_gem_location_box, "Re-Click Initial Gem (due to New Troop interaction fail)", move_duration=0.3, pre_click_pause=0.1)
                time.sleep(RETRY_PAUSE_SECONDS)
                continue
             else:
                print("Failed to handle New Troop Button interaction after all retries.")
                return False

        march_button_location_result = find_and_click( # Renamed
            MARCH_TEMPLATE, CONFIDENCE_GENERAL, "March Button",
            click_delay_after=CLICK_DELAY_SHORT, use_grayscale=True
        )
        if not march_button_location_result or march_button_location_result is True:
            if attempt < MAX_SUBSEQUENT_STEP_RETRIES - 1:
                print("March Button not found or click failed. Re-clicking initial gem...")
                initial_gem_location_box = get_game_center_box()
                click_at_location(initial_gem_location_box, "Re-Click Initial Gem (due to March fail)", move_duration=0.3, pre_click_pause=0.1)
                time.sleep(RETRY_PAUSE_SECONDS)
                continue
            else:
                print("Failed to find or action March Button after all retries.")
                return False

        # Check for Orange March Button AFTER attempting to March
        print("Checking for orange march button...")
        orange_march_location = find_template(
            ORANGE_MARCH_BUTTON_TEMPLATE,
            CONFIDENCE_GENERAL,
            "Orange March Button",
            use_grayscale=True,
            # Not taking a screenshot on fail for this one by default, can be added if needed
            # debug_screenshot_on_fail=DEBUG_TAKE_SCREENSHOT_IF_GATHER_FAILS,
            # screenshot_filename_prefix="fail_orange_march_",
        )
        if orange_march_location:
            print(f"Orange march button found at {orange_march_location}. Waiting for {ORANGE_MARCH_WAIT_SECONDS // 60} minutes.")
            time.sleep(ORANGE_MARCH_WAIT_SECONDS)
            print("Finished waiting after orange march button detection.")
            return "orange_march_detected" # Signal to main loop

        print(f"--- Successfully dispatched troops to gem deposit on attempt {attempt + 1}! ---")
        zoom_out_after_dispatch()
        return True

    print("All retry attempts for subsequent steps failed for this gem.")
    return False

# --- Main Program Loop ---
def main_bot_loop():
    global RIGHT_CLICK_NEXT_GEM
    print("Rise of Kingdoms Gem Farming Bot with EXPANDING SPIRAL Navigation (Day/Night Scan) - Starting...")
    print(f"Farming duration per cycle: {FARMING_DURATION_SECONDS} seconds.")
    print(f"Max retries for steps after initial click: {MAX_SUBSEQUENT_STEP_RETRIES}")
    print("IMPORTANT: Ensure the Rise of Kingdoms game window is ACTIVE and in the FOREGROUND.")
    print("           The bot will start actions after the initial countdown.")
    print("           To STOP the bot, move your mouse to a screen corner quickly (FAILSAFE).")
    print("           You can also try Ctrl+C in the console window.")
    print(f"DEBUG_TAKE_SCREENSHOT_AFTER_FIRST_CLICK is set to: {DEBUG_TAKE_SCREENSHOT_AFTER_FIRST_CLICK}")
    print(f"DEBUG_TAKE_SCREENSHOT_IF_GATHER_FAILS is set to: {DEBUG_TAKE_SCREENSHOT_IF_GATHER_FAILS}")
    print(f"USE_ALT_CLICK_METHOD is set to: {USE_ALT_CLICK_METHOD}")
    print(f"CONFIDENCE_GATHER is set to: {CONFIDENCE_GATHER}")
    print(f"CONFIDENCE_GEM (for Day/Night) is set to: {CONFIDENCE_GEM}")
    print(f"Screenshot directory: {screenshot_full_path}") # Display full path


    pyautogui.FAILSAFE = True

    ensure_game_window_size()

    # nav_actions_taken_since_scan = 0 # Will be replaced by new search logic's scan counter/timer

    for i in range(5, 0, -1):
        print(f"\rStarting in {i} seconds... Switch to game, ensure it's ACTIVE & ADMIN rights!", end="")
        time.sleep(1)
    # Updated print statements for snake configuration
    print("\nBot active! Systematic 'snake' navigation will begin.")
    print(f"Search pattern: {SEARCH_PATTERN_TYPE}")
    print(f"Horizontal pass scroll units (config name: SNAKE_HORIZONTAL_PASS_UNITS): {SNAKE_HORIZONTAL_PASS_UNITS}")
    print(f"Vertical shift units (config name: SNAKE_VERTICAL_SHIFT_UNITS): {SNAKE_VERTICAL_SHIFT_UNITS}")
    print(f"Scans per horizontal pass: {SNAKE_SCANS_PER_HORIZONTAL_PASS}")
    print(f"Scroll segment duration: {SNAKE_SCROLL_SEGMENT_DURATION}s")
    print(f"Pause if no gem found: {SYSTEMATIC_SCAN_PAUSE_IF_NO_GEM}s")
    
    # Define local pause and vertical shift scroll duration
    snake_post_scroll_pause = 0.3 
    print(f"Post-scroll pause (local setting): {snake_post_scroll_pause}s")
    snake_vertical_shift_scroll_duration = SNAKE_SCROLL_SEGMENT_DURATION 
    print(f"Vertical shift scroll duration (local setting, based on segment duration): {snake_vertical_shift_scroll_duration}s")

    # Snake search state
    current_horizontal_direction_key = SNAKE_HORIZONTAL_SCROLL_KEY_RIGHT
    passes_completed = 0

    try:
        while True:
            # This is the main bot operating loop, inside try:
            print(f"\n--- Starting new horizontal pass (Pass #{passes_completed + 1}) ---")
            print(f"Current horizontal direction: {current_horizontal_direction_key}")

            # This flag helps manage scrolling behavior after a farming attempt within a pass
            action_taken_in_current_segment = False 

            for segment_num in range(SNAKE_SCANS_PER_HORIZONTAL_PASS):
                print(f"\nSegment {segment_num + 1}/{SNAKE_SCANS_PER_HORIZONTAL_PASS} of horizontal pass.")

                # 1. Scroll for one segment, only if no action (like farming) was just taken
                if not action_taken_in_current_segment:
                    print(f"Scrolling {current_horizontal_direction_key} for {SNAKE_SCROLL_SEGMENT_DURATION}s...")
                    pyautogui.keyDown(current_horizontal_direction_key)
                    time.sleep(SNAKE_SCROLL_SEGMENT_DURATION)
                    pyautogui.keyUp(current_horizontal_direction_key)
                    print("Scroll segment complete.")
                    time.sleep(snake_post_scroll_pause) 
                else:
                    # Reset flag if an action was taken in the previous iteration of this loop
                    action_taken_in_current_segment = False 

                # Check for returning troops indicator
                troop_back_location = find_template(
                    TROOP_BACK_TEMPLATE,
                    CONFIDENCE_GENERAL,
                    "Troop Back",
                    use_grayscale=True,
                )
                if troop_back_location:
                    click_at_location(troop_back_location, "Troop Back", move_duration=0.3, pre_click_pause=0.1)
                    RIGHT_CLICK_NEXT_GEM = True
                    print("Troop back detected. Next gem will be farmed with right click.")
                    time.sleep(CLICK_DELAY_SHORT)
                    continue

                # 2. Scan for gems
                print("Scanning for gem deposits (Day or Night)...")
                initial_gem_location_box = find_any_gem_deposit(CONFIDENCE_GEM, use_grayscale=True)

                if initial_gem_location_box:
                    if is_near_dispatched(initial_gem_location_box):
                        print("Gem deposit already dispatched recently. Skipping.")
                        action_taken_in_current_segment = False
                        continue

                    if is_deposit_gathered_on_map(initial_gem_location_box):
                        action_taken_in_current_segment = False
                        continue

                    print(f"GEM SPOTTED at {initial_gem_location_box}! Pausing navigation to attempt farming.")
                    if RIGHT_CLICK_NEXT_GEM:
                        farming_outcome = perform_quick_gem_farming_cycle(initial_gem_location_box)
                        RIGHT_CLICK_NEXT_GEM = False
                    else:
                        farming_outcome = perform_full_gem_farming_cycle(initial_gem_location_box)
                    action_taken_in_current_segment = True # Mark that an action occurred

                    if farming_outcome is True:
                        record_dispatched(initial_gem_location_box)
                        print(f"Farming successful. Standard {FARMING_DURATION_SECONDS // 60} min wait starts.")
                        for i_waitCounter in range(FARMING_DURATION_SECONDS, 0, -1):
                            print(f"\rTime remaining: {i_waitCounter:03d}s ", end="")
                            time.sleep(1)
                        print("\nFarming duration complete. Resuming search.")
                    elif farming_outcome == "orange_march_detected":
                        print("Orange march button was detected and handled (30-min wait occurred). Resuming search.")
                    else: # farming_outcome is False
                        print("Farming attempt failed for the spotted gem. Resuming search.")
                    
                    print("Short pause before resuming map interaction...")
                    time.sleep(2.0) # General pause after any farming attempt
                    
                    print("Continuing with the current search pass after farming attempt...")

                else: # No gem found in this scan
                    print(f"No gem deposit found in current view. Pausing for {SYSTEMATIC_SCAN_PAUSE_IF_NO_GEM}s.")
                    time.sleep(SYSTEMATIC_SCAN_PAUSE_IF_NO_GEM)
                    action_taken_in_current_segment = False # No action taken if no gem found
                
            # --- Horizontal pass completed ---
            print(f"--- Horizontal pass #{passes_completed + 1} completed ---")

            # 3. Perform vertical shift
            print(f"Performing vertical shift: Scrolling {SNAKE_VERTICAL_SCROLL_KEY} for {snake_vertical_shift_scroll_duration}s.")
            pyautogui.keyDown(SNAKE_VERTICAL_SCROLL_KEY)
            time.sleep(snake_vertical_shift_scroll_duration)
            pyautogui.keyUp(SNAKE_VERTICAL_SCROLL_KEY)
            print("Vertical shift complete.")
            time.sleep(snake_post_scroll_pause)

            # 4. Reverse horizontal direction
            if current_horizontal_direction_key == SNAKE_HORIZONTAL_SCROLL_KEY_RIGHT:
                current_horizontal_direction_key = SNAKE_HORIZONTAL_SCROLL_KEY_LEFT
            else:
                current_horizontal_direction_key = SNAKE_HORIZONTAL_SCROLL_KEY_RIGHT
            
            passes_completed += 1
            action_taken_in_current_segment = False # Reset for the new pass
            print(f"Ready for next pass. New direction: {current_horizontal_direction_key}")

    except pyautogui.FailSafeException:
        print("\nFAILSAFE TRIGGERED (mouse moved to screen corner). Exiting bot.")
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting bot gracefully.")
    except Exception as e:
        print(f"\nAN UNEXPECTED ERROR OCCURRED: {e}")
        traceback.print_exc()
    finally:
        print("Rise of Kingdoms Gem Farming Bot - Stopped.")

if __name__ == "__main__":
    # Initialize script_dir here as well if functions using it might be called
    # before main_bot_loop (though in this script, they are not directly)
    # However, for robustness, especially if you refactor later:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    screenshot_full_path = os.path.join(script_dir, SCREENSHOT_DIR)  # Define for global scope if helper functions are called standalone

    args = parse_args()

    # Override key configuration variables with CLI values
    CONFIDENCE_GEM = args.confidence_gem
    SNAKE_SCROLL_SEGMENT_DURATION = args.scroll_duration
    SNAKE_SCANS_PER_HORIZONTAL_PASS = args.scans_per_pass
    SYSTEMATIC_SCAN_PAUSE_IF_NO_GEM = args.pause_no_gem
    ZOOM_OUT_CLICKS_AFTER_MARCH_FIRST = args.zoom_out_clicks_first
    ZOOM_OUT_CLICKS_AFTER_MARCH_SECOND = args.zoom_out_clicks_second
    ZOOM_OUT_CLICKS_AFTER_MARCH_THIRD = args.zoom_out_clicks_third
    ZOOM_OUT_CLICKS_AFTER_MARCH_FOURTH = args.zoom_out_clicks_fourth
    FARMING_DURATION_SECONDS = args.farming_duration

    main_bot_loop()
