#!/usr/bin/env python3
"""
Pumpkin Farm Macro for Minecraft
Automates harvesting pumpkins with randomized timing to avoid anticheat detection.
"""

import time
import random
import threading
from pynput import keyboard, mouse
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

# Controllers
kb = KeyboardController()
ms = MouseController()

# Global state
running = False
paused = False
stop_flag = False

# Farm Configuration
FARM_CONFIG = {
    "total_rows": 19,           # Number of pumpkin rows
    "row_length": 91,           # Pumpkins per row
    "blocks_to_entrance": 2,    # Blocks from spawn to first row
    "row_spacing": 2,           # Blocks between row starts (path + pumpkin row)
}

# Timing Configuration (in seconds) - base values before randomization
TIMING_CONFIG = {
    "block_break_time": 0.25,       # Time to break one pumpkin
    "walk_speed": 0.22,             # Time to walk one block (not sprinting)
    "turn_time": 0.15,              # Time for 90-degree turn
    "row_transition_time": 0.5,     # Time to move between rows
    "return_walk_speed": 0.18,      # Faster return (sprinting)
}

# Randomization Configuration
RANDOM_CONFIG = {
    "timing_variance": 0.15,        # +/- 15% timing variance
    "pause_chance": 0.02,           # 2% chance of random pause per action
    "pause_duration_min": 0.3,      # Minimum pause duration
    "pause_duration_max": 1.5,      # Maximum pause duration
    "micro_pause_chance": 0.08,     # 8% chance of micro-pause
    "micro_pause_min": 0.05,        # Minimum micro-pause
    "micro_pause_max": 0.15,        # Maximum micro-pause
    "look_jitter_chance": 0.05,     # 5% chance of slight look adjustment
    "look_jitter_amount": 3,        # Pixels of mouse jitter
    "sprint_toggle_chance": 0.03,   # 3% chance to briefly toggle sprint
}


def randomize_time(base_time: float) -> float:
    """Add random variance to a time value."""
    variance = base_time * RANDOM_CONFIG["timing_variance"]
    return base_time + random.uniform(-variance, variance)


def maybe_pause():
    """Occasionally pause to seem more human-like."""
    if random.random() < RANDOM_CONFIG["pause_chance"]:
        pause_time = random.uniform(
            RANDOM_CONFIG["pause_duration_min"],
            RANDOM_CONFIG["pause_duration_max"]
        )
        print(f"  [Human pause: {pause_time:.2f}s]")
        time.sleep(pause_time)
    elif random.random() < RANDOM_CONFIG["micro_pause_chance"]:
        micro_time = random.uniform(
            RANDOM_CONFIG["micro_pause_min"],
            RANDOM_CONFIG["micro_pause_max"]
        )
        time.sleep(micro_time)


def maybe_jitter_look():
    """Occasionally add small mouse movement jitter."""
    if random.random() < RANDOM_CONFIG["look_jitter_chance"]:
        jitter_x = random.randint(
            -RANDOM_CONFIG["look_jitter_amount"],
            RANDOM_CONFIG["look_jitter_amount"]
        )
        jitter_y = random.randint(
            -RANDOM_CONFIG["look_jitter_amount"] // 2,
            RANDOM_CONFIG["look_jitter_amount"] // 2
        )
        ms.move(jitter_x, jitter_y)


def maybe_toggle_sprint():
    """Occasionally toggle sprint briefly."""
    if random.random() < RANDOM_CONFIG["sprint_toggle_chance"]:
        kb.press(Key.ctrl)
        time.sleep(random.uniform(0.05, 0.1))
        kb.release(Key.ctrl)


def safe_sleep(duration: float):
    """Sleep that checks for stop flag."""
    global stop_flag, paused
    end_time = time.time() + duration
    while time.time() < end_time:
        if stop_flag:
            return False
        while paused and not stop_flag:
            time.sleep(0.1)
        time.sleep(min(0.05, end_time - time.time()))
    return True


def press_key(key):
    """Press a key."""
    kb.press(key)


def release_key(key):
    """Release a key."""
    kb.release(key)


def hold_key_for(key, duration: float):
    """Hold a key for a duration with randomization."""
    actual_duration = randomize_time(duration)
    press_key(key)
    if not safe_sleep(actual_duration):
        release_key(key)
        return False
    release_key(key)
    return True


def click_mouse(button=Button.left):
    """Click mouse button."""
    ms.click(button)


def hold_mouse(button=Button.left):
    """Hold mouse button."""
    ms.press(button)


def release_mouse(button=Button.left):
    """Release mouse button."""
    ms.release(button)


def turn_right_90():
    """Turn 90 degrees to the right."""
    # Minecraft default sensitivity: ~400-500 pixels for 90 degrees
    # This may need calibration based on your sensitivity settings
    turn_pixels = 470 + random.randint(-20, 20)

    # Move in small increments for more natural movement
    steps = random.randint(3, 6)
    pixels_per_step = turn_pixels // steps

    for _ in range(steps):
        if stop_flag:
            return False
        ms.move(pixels_per_step + random.randint(-5, 5), random.randint(-2, 2))
        time.sleep(randomize_time(TIMING_CONFIG["turn_time"] / steps))

    maybe_jitter_look()
    return True


def turn_left_90():
    """Turn 90 degrees to the left."""
    turn_pixels = 470 + random.randint(-20, 20)
    steps = random.randint(3, 6)
    pixels_per_step = turn_pixels // steps

    for _ in range(steps):
        if stop_flag:
            return False
        ms.move(-(pixels_per_step + random.randint(-5, 5)), random.randint(-2, 2))
        time.sleep(randomize_time(TIMING_CONFIG["turn_time"] / steps))

    maybe_jitter_look()
    return True


def turn_around():
    """Turn 180 degrees."""
    turn_pixels = 940 + random.randint(-30, 30)
    steps = random.randint(5, 10)
    pixels_per_step = turn_pixels // steps

    # Randomly choose left or right
    direction = random.choice([-1, 1])

    for _ in range(steps):
        if stop_flag:
            return False
        ms.move(direction * (pixels_per_step + random.randint(-8, 8)), random.randint(-3, 3))
        time.sleep(randomize_time(0.03))

    maybe_jitter_look()
    return True


def walk_forward_blocks(num_blocks: int, break_blocks: bool = False):
    """Walk forward a number of blocks, optionally breaking blocks."""
    global stop_flag, paused

    if break_blocks:
        hold_mouse(Button.left)

    press_key('w')

    for i in range(num_blocks):
        if stop_flag:
            release_key('w')
            if break_blocks:
                release_mouse(Button.left)
            return False

        while paused and not stop_flag:
            release_key('w')
            if break_blocks:
                release_mouse(Button.left)
            time.sleep(0.1)
            if not paused:
                press_key('w')
                if break_blocks:
                    hold_mouse(Button.left)

        # Time to walk one block
        walk_time = randomize_time(TIMING_CONFIG["walk_speed"])
        if break_blocks:
            # Add extra time for breaking
            walk_time += randomize_time(TIMING_CONFIG["block_break_time"])

        time.sleep(walk_time)

        # Human-like behaviors
        maybe_pause()
        maybe_jitter_look()
        maybe_toggle_sprint()

        # Occasional progress indicator
        if (i + 1) % 20 == 0:
            print(f"    Progress: {i + 1}/{num_blocks} blocks")

    release_key('w')
    if break_blocks:
        release_mouse(Button.left)

    return True


def walk_backward_blocks(num_blocks: int):
    """Walk backward a number of blocks."""
    global stop_flag

    press_key('s')

    for i in range(num_blocks):
        if stop_flag:
            release_key('s')
            return False

        walk_time = randomize_time(TIMING_CONFIG["walk_speed"])
        time.sleep(walk_time)
        maybe_pause()

    release_key('s')
    return True


def strafe_right_blocks(num_blocks: int):
    """Strafe right a number of blocks."""
    global stop_flag

    press_key('d')

    for _ in range(num_blocks):
        if stop_flag:
            release_key('d')
            return False
        time.sleep(randomize_time(TIMING_CONFIG["walk_speed"]))
        maybe_pause()

    release_key('d')
    return True


def strafe_left_blocks(num_blocks: int):
    """Strafe left a number of blocks."""
    global stop_flag

    press_key('a')

    for _ in range(num_blocks):
        if stop_flag:
            release_key('a')
            return False
        time.sleep(randomize_time(TIMING_CONFIG["walk_speed"]))
        maybe_pause()

    release_key('a')
    return True


def harvest_row(row_number: int, going_forward: bool = True):
    """Harvest a single row of pumpkins."""
    global stop_flag

    direction = "forward" if going_forward else "backward"
    print(f"  Harvesting row {row_number + 1}/{FARM_CONFIG['total_rows']} ({direction})")

    if going_forward:
        return walk_forward_blocks(FARM_CONFIG["row_length"], break_blocks=True)
    else:
        # Turn around, walk forward (breaking), turn around again
        if not turn_around():
            return False
        time.sleep(randomize_time(0.2))

        if not walk_forward_blocks(FARM_CONFIG["row_length"], break_blocks=True):
            return False

        time.sleep(randomize_time(0.2))
        return turn_around()


def move_to_next_row(current_row: int, going_right: bool = True):
    """Move from current row to the next row."""
    global stop_flag

    print(f"  Moving to next row...")

    time.sleep(randomize_time(0.3))

    # Turn to face the direction of the next row
    if going_right:
        if not turn_right_90():
            return False
    else:
        if not turn_left_90():
            return False

    time.sleep(randomize_time(0.2))

    # Walk to the next row (row_spacing blocks)
    if not walk_forward_blocks(FARM_CONFIG["row_spacing"], break_blocks=False):
        return False

    time.sleep(randomize_time(0.2))

    # Turn to face down the new row
    if going_right:
        if not turn_right_90():
            return False
    else:
        if not turn_left_90():
            return False

    time.sleep(randomize_time(0.3))
    maybe_pause()

    return True


def return_to_start():
    """Return to the starting position after harvesting all rows."""
    global stop_flag

    print("Returning to start position...")

    # We're at the end of the last row
    # Need to navigate back to the entrance

    # Turn to face back toward entrance side
    if not turn_right_90():
        return False

    time.sleep(randomize_time(0.3))

    # Walk back across all rows
    total_width = (FARM_CONFIG["total_rows"] - 1) * FARM_CONFIG["row_spacing"]

    # Sprint back for speed
    press_key(Key.ctrl)
    time.sleep(0.1)

    if not walk_forward_blocks(total_width, break_blocks=False):
        release_key(Key.ctrl)
        return False

    release_key(Key.ctrl)
    time.sleep(randomize_time(0.3))

    # Turn to face the entrance
    if not turn_right_90():
        return False

    time.sleep(randomize_time(0.2))

    # Walk back to entrance
    if not walk_forward_blocks(FARM_CONFIG["row_length"] + FARM_CONFIG["blocks_to_entrance"], break_blocks=False):
        return False

    # Turn around to face into the farm
    if not turn_around():
        return False

    print("Returned to start!")
    return True


def run_harvest_cycle():
    """Run a complete harvest cycle of the farm."""
    global stop_flag, running

    cycle_count = 0

    while running and not stop_flag:
        cycle_count += 1
        print(f"\n{'='*50}")
        print(f"Starting harvest cycle #{cycle_count}")
        print(f"{'='*50}")

        # Initial walk to first row
        print("Walking to first row...")
        time.sleep(randomize_time(0.5))

        if not walk_forward_blocks(FARM_CONFIG["blocks_to_entrance"], break_blocks=False):
            break

        # Harvest all rows in a serpentine pattern
        for row in range(FARM_CONFIG["total_rows"]):
            if stop_flag:
                break

            # Harvest current row
            going_forward = (row % 2 == 0)
            if not harvest_row(row, going_forward=True):
                break

            # Move to next row if not the last one
            if row < FARM_CONFIG["total_rows"] - 1:
                # Alternate direction for serpentine pattern
                going_right = (row % 2 == 0)
                if not move_to_next_row(row, going_right=going_right):
                    break

        if stop_flag:
            break

        # Return to start for next cycle
        if not return_to_start():
            break

        # Random delay between cycles
        delay = random.uniform(1.0, 3.0)
        print(f"Waiting {delay:.1f}s before next cycle...")
        if not safe_sleep(delay):
            break

    print("\nHarvest stopped.")
    running = False


def on_press(key):
    """Handle key press events."""
    global running, paused, stop_flag

    try:
        if key == Key.f6:
            if not running:
                print("\n[F6] Starting macro...")
                running = True
                stop_flag = False
                paused = False
                # Start harvest in a separate thread
                harvest_thread = threading.Thread(target=run_harvest_cycle)
                harvest_thread.daemon = True
                harvest_thread.start()
            else:
                print("\n[F6] Macro already running!")

        elif key == Key.f7:
            if running:
                paused = not paused
                status = "PAUSED" if paused else "RESUMED"
                print(f"\n[F7] Macro {status}")

        elif key == Key.f8:
            if running:
                print("\n[F8] Stopping macro...")
                stop_flag = True
                running = False
                # Release any held keys
                release_key('w')
                release_key('a')
                release_key('s')
                release_key('d')
                release_key(Key.ctrl)
                release_mouse(Button.left)

        elif key == Key.f9:
            print("\n[F9] Exiting program...")
            stop_flag = True
            running = False
            return False  # Stop listener

    except AttributeError:
        pass


def print_banner():
    """Print the startup banner."""
    print("""
╔════════════════════════════════════════════════════════════╗
║           Pumpkin Farm Macro for Minecraft                 ║
╠════════════════════════════════════════════════════════════╣
║  Controls:                                                 ║
║    F6 - Start/Begin harvesting                            ║
║    F7 - Pause/Resume                                       ║
║    F8 - Stop current cycle                                 ║
║    F9 - Exit program                                       ║
╠════════════════════════════════════════════════════════════╣
║  Farm Configuration:                                       ║
║    - Rows: {rows:3d}                                            ║
║    - Pumpkins per row: {length:3d}                              ║
║    - Total pumpkins: {total:5d}                                ║
╠════════════════════════════════════════════════════════════╣
║  Anti-Detection Features:                                  ║
║    - Randomized timing (±{variance:.0%})                          ║
║    - Random pauses and micro-pauses                        ║
║    - Mouse movement jitter                                 ║
║    - Variable sprint toggling                              ║
╚════════════════════════════════════════════════════════════╝
""".format(
        rows=FARM_CONFIG["total_rows"],
        length=FARM_CONFIG["row_length"],
        total=FARM_CONFIG["total_rows"] * FARM_CONFIG["row_length"],
        variance=RANDOM_CONFIG["timing_variance"]
    ))


def main():
    """Main entry point."""
    print_banner()

    print("Position your character at the farm entrance facing into the farm.")
    print("Make sure Minecraft is focused when you press F6 to start.")
    print("\nWaiting for input...")

    # Start keyboard listener
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    print("Goodbye!")


if __name__ == "__main__":
    main()
