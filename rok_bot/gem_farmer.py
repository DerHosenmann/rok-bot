import pyautogui
import time
import traceback
import os

# --- Configuration ---
GEM_TEMPLATE_DAY = r'images/gem_deposit_template.png' # Adjusted path
GEM_TEMPLATE_NIGHT = r'images/gem_deposit_template_night.png' # Adjusted path
GATHER_TEMPLATE = r'images/gather_template.png' # Adjusted path
NEW_TROOP_TEMPLATE = r'images/new_troop_template.png' # Adjusted path
MARCH_TEMPLATE = r'images/march_template.png' # Adjusted path

CONFIDENCE_GEM = 0.8
CONFIDENCE_GATHER = 0.80
CONFIDENCE_GENERAL = 0.85

CLICK_DELAY_SHORT = 0.7
CLICK_DELAY_MEDIUM = 2.0
CLICK_DELAY_LONG = 3.0

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

# --- Navigation Configuration (Expanding Square Spiral) ---
CARDINAL_DIRECTIONS = ['right', 'down', 'left', 'up']

SCROLL_UNITS_PER_LEG_INITIAL = 5
SCROLL_UNITS_INCREMENT_PER_LEVEL = 5

NAVIGATION_SCROLL_DURATION = 0.3
NAVIGATION_STEPS_BEFORE_SCAN = 1 # Scan after every scroll
NAVIGATION_POST_SCROLL_PAUSE = 0.3
SCAN_FOR_GEMS_INTERVAL = 0.5 # Pause after a scan if no gem found

# Create screenshot directory
# Adjusted to be relative to the script's location
script_dir = os.path.dirname(__file__)
screenshot_full_path = os.path.join(script_dir, SCREENSHOT_DIR)

if (DEBUG_TAKE_SCREENSHOT_AFTER_FIRST_CLICK or DEBUG_TAKE_SCREENSHOT_IF_GATHER_FAILS) and not os.path.exists(screenshot_full_path):
    try:
        os.makedirs(screenshot_full_path)
        print(f"Created directory for debug screenshots: {screenshot_full_path}")
    except Exception as e:
        print(f"Could not create screenshot directory {screenshot_full_path}: {e}")

# --- Helper Functions ---
def find_template(template_image_path, confidence_level, description="template", use_grayscale=False,
                  debug_screenshot_on_fail=False, screenshot_filename_prefix="fail_"):
    # Ensure template path is relative to script directory
    full_template_path = os.path.join(script_dir, template_image_path)
    print(f"Searching for '{description}' (file: {full_template_path}) with confidence {confidence_level:.2f}, grayscale: {use_grayscale}...")
    try:
        location = pyautogui.locateOnScreen(full_template_path, confidence=confidence_level, grayscale=use_grayscale)
        if location:
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

def find_any_gem_deposit(confidence_level, use_grayscale):
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
            print(f"DEBUG: Screenshot after initial click on located gem saved to {filename}. EXAMINE THIS.")
            print(f"       Verify if the game menu opened and if the 'Gather Button' is visible.")
        except Exception as e:
            print(f"DEBUG: Failed to take screenshot: {e}")
    
    time.sleep(CLICK_DELAY_MEDIUM)

    for attempt in range(MAX_SUBSEQUENT_STEP_RETRIES):
        print(f"\nAttempt {attempt + 1} of {MAX_SUBSEQUENT_STEP_RETRIES} for subsequent steps (Gather, New Troop, March)...")

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
                print(f"New Troop Button (optional but failed interaction or mandatory and failed). Re-clicking initial gem...")
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
                print(f"March Button not found or click failed. Re-clicking initial gem...")
                click_at_location(initial_gem_location_box, "Re-Click Initial Gem (due to March fail)", move_duration=0.3, pre_click_pause=0.1)
                time.sleep(RETRY_PAUSE_SECONDS)
                continue
            else:
                print("Failed to find or action March Button after all retries.")
                return False

        print(f"--- Successfully dispatched troops to gem deposit on attempt {attempt + 1}! ---")
        return True

    print("All retry attempts for subsequent steps failed for this gem.")
    return False

# --- Main Program Loop ---
def main_bot_loop():
    print("Rise of Kingdoms Gem Farming Bot with EXPANDING SPIRAL Navigation (Day/Night Scan) - Starting...")
    print(f"Farming duration per cycle: {FARMING_DURATION_SECONDS} seconds.")
    print(f"Max retries for steps after initial click: {MAX_SUBSEQUENT_STEP_RETRIES}")
    print(f"Initial leg scroll units: {SCROLL_UNITS_PER_LEG_INITIAL}")
    print(f"Leg increment per level: {SCROLL_UNITS_INCREMENT_PER_LEVEL}")
    print(f"Scroll duration per action: {NAVIGATION_SCROLL_DURATION}s")
    print(f"Scroll actions before scan: {NAVIGATION_STEPS_BEFORE_SCAN} (should be 1 for scan after each scroll)")
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

    direction_index = 0
    current_leg_target_scrolls = SCROLL_UNITS_PER_LEG_INITIAL
    scrolls_taken_in_current_leg = 0
    legs_completed_at_current_length = 0
    nav_actions_taken_since_scan = 0

    for i in range(5, 0, -1):
        print(f"\rStarting in {i} seconds... Switch to game, ensure it's ACTIVE & ADMIN rights!", end="")
        time.sleep(1)
    print("\nBot active! Expanding spiral navigation will begin.")

    try:
        while True:
            if nav_actions_taken_since_scan >= NAVIGATION_STEPS_BEFORE_SCAN:
                print("\nScanning for gem deposits (Day or Night)...")
                initial_gem_location_box = find_any_gem_deposit(CONFIDENCE_GEM, use_grayscale=True)
                nav_actions_taken_since_scan = 0

                if initial_gem_location_box:
                    print(f"GEM SPOTTED at {initial_gem_location_box}! Pausing navigation to attempt farming.")
                    farmed_successfully = perform_full_gem_farming_cycle(initial_gem_location_box)

                    if farmed_successfully:
                        print(f"Farming successful. Waiting for {FARMING_DURATION_SECONDS} seconds...")
                        for i in range(FARMING_DURATION_SECONDS, 0, -1): # Corrected loop variable
                            print(f"\rTime remaining: {i:03d}s ", end="")
                            time.sleep(1)
                        print("\nFarming duration complete. Resuming navigation.")
                    else:
                        print("Farming attempt failed for the spotted gem. Resuming navigation.")
                    
                    time.sleep(2.0) # Pause before resuming navigation regardless of farming outcome
                else:
                    print("No gem deposit found in current view.")
                    time.sleep(SCAN_FOR_GEMS_INTERVAL) # Pause briefly if no gem found

            # Navigation logic continues
            if scrolls_taken_in_current_leg >= current_leg_target_scrolls:
                print(f"--- Leg complete (Target: {current_leg_target_scrolls} scrolls in {CARDINAL_DIRECTIONS[direction_index]}) ---")
                direction_index = (direction_index + 1) % len(CARDINAL_DIRECTIONS)
                scrolls_taken_in_current_leg = 0
                legs_completed_at_current_length += 1

                if legs_completed_at_current_length >= 2: # After two legs (e.g., right, down), increase length
                    current_leg_target_scrolls += SCROLL_UNITS_INCREMENT_PER_LEVEL
                    legs_completed_at_current_length = 0
                    print(f"--- Increasing leg length. New target: {current_leg_target_scrolls} scrolls per leg. ---")

            current_key = CARDINAL_DIRECTIONS[direction_index]
            # More descriptive log for navigation action
            print(f"\nNavigating (Leg {scrolls_taken_in_current_leg + 1}/{current_leg_target_scrolls} of current length {current_leg_target_scrolls}, Direction: {current_key}):")
            
            if NAVIGATION_SCROLL_DURATION > 0: # Use keyDown/keyUp for a sustained press
                pyautogui.keyDown(current_key)
                time.sleep(NAVIGATION_SCROLL_DURATION)
                pyautogui.keyUp(current_key)
            else: # Use press for a quick tap if duration is zero
                pyautogui.press(current_key)
            print(f"Action: Scrolled {current_key} (simulated duration: {NAVIGATION_SCROLL_DURATION if NAVIGATION_SCROLL_DURATION > 0 else 'instant press'}).")

            scrolls_taken_in_current_leg += 1
            nav_actions_taken_since_scan += 1
            time.sleep(NAVIGATION_POST_SCROLL_PAUSE) # Pause after each scroll

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
    screenshot_full_path = os.path.join(script_dir, SCREENSHOT_DIR) # Define for global scope if helper functions are called standalone
    main_bot_loop()
