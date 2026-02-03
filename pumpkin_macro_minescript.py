"""
Pumpkin Farm Macro for Minecraft using Minescript
More precise and reliable than keyboard simulation.

Installation:
1. Install Minescript mod: https://github.com/maxuser0/minescript
2. Place this file in .minecraft/minescript/ folder
3. In-game, run: \pumpkin_macro_minescript

Usage:
- Run the script while standing at farm entrance facing into the farm
- The script will harvest all rows and return to start automatically
"""

import minescript
import random
import time

# Farm Configuration
FARM_CONFIG = {
    "total_rows": 19,           # Number of pumpkin rows (pairs of pumpkin lines)
    "row_length": 91,           # Blocks per row
    "blocks_to_entrance": 2,    # Blocks from spawn to first row
    "row_spacing": 2,           # Blocks between row centers
}

# Randomization Configuration for anti-detection
RANDOM_CONFIG = {
    "timing_variance": 0.15,        # +/- 15% timing variance
    "pause_chance": 0.02,           # 2% chance of random pause
    "pause_duration_min": 0.3,
    "pause_duration_max": 1.5,
    "micro_pause_chance": 0.08,     # 8% chance of micro-pause
    "micro_pause_min": 0.05,
    "micro_pause_max": 0.15,
    "look_jitter_chance": 0.05,     # 5% chance of look jitter
    "look_jitter_amount": 2.0,      # Degrees of jitter
}

# Movement timing (seconds)
TIMING = {
    "block_time": 0.25,             # Time per block while breaking
    "walk_time": 0.20,              # Time per block walking
    "turn_time": 0.1,               # Time for turning
}


def randomize(base_value: float) -> float:
    """Add random variance to a value."""
    variance = base_value * RANDOM_CONFIG["timing_variance"]
    return base_value + random.uniform(-variance, variance)


def maybe_pause():
    """Occasionally pause to seem human-like."""
    if random.random() < RANDOM_CONFIG["pause_chance"]:
        pause_time = random.uniform(
            RANDOM_CONFIG["pause_duration_min"],
            RANDOM_CONFIG["pause_duration_max"]
        )
        minescript.echo(f"[Pause: {pause_time:.2f}s]")
        time.sleep(pause_time)
    elif random.random() < RANDOM_CONFIG["micro_pause_chance"]:
        time.sleep(random.uniform(
            RANDOM_CONFIG["micro_pause_min"],
            RANDOM_CONFIG["micro_pause_max"]
        ))


def maybe_jitter_look():
    """Occasionally add small look direction jitter."""
    if random.random() < RANDOM_CONFIG["look_jitter_chance"]:
        current_yaw, current_pitch = minescript.player_orientation()
        jitter_yaw = random.uniform(
            -RANDOM_CONFIG["look_jitter_amount"],
            RANDOM_CONFIG["look_jitter_amount"]
        )
        jitter_pitch = random.uniform(
            -RANDOM_CONFIG["look_jitter_amount"] / 2,
            RANDOM_CONFIG["look_jitter_amount"] / 2
        )
        minescript.player_set_orientation(
            current_yaw + jitter_yaw,
            current_pitch + jitter_pitch
        )


def get_player_pos():
    """Get player's current position."""
    return minescript.player_position()


def look_direction(yaw: float, pitch: float = 0):
    """Set player look direction with slight randomization."""
    actual_yaw = yaw + random.uniform(-1, 1)
    actual_pitch = pitch + random.uniform(-0.5, 0.5)
    minescript.player_set_orientation(actual_yaw, actual_pitch)
    time.sleep(randomize(TIMING["turn_time"]))


def turn_right_90():
    """Turn 90 degrees right."""
    current_yaw, current_pitch = minescript.player_orientation()
    target_yaw = current_yaw + 90

    # Turn in steps for more natural movement
    steps = random.randint(3, 5)
    step_amount = 90 / steps

    for i in range(steps):
        current_yaw += step_amount + random.uniform(-2, 2)
        minescript.player_set_orientation(current_yaw, current_pitch)
        time.sleep(randomize(TIMING["turn_time"] / steps))

    maybe_jitter_look()


def turn_left_90():
    """Turn 90 degrees left."""
    current_yaw, current_pitch = minescript.player_orientation()
    target_yaw = current_yaw - 90

    steps = random.randint(3, 5)
    step_amount = 90 / steps

    for i in range(steps):
        current_yaw -= step_amount + random.uniform(-2, 2)
        minescript.player_set_orientation(current_yaw, current_pitch)
        time.sleep(randomize(TIMING["turn_time"] / steps))

    maybe_jitter_look()


def turn_around():
    """Turn 180 degrees."""
    current_yaw, current_pitch = minescript.player_orientation()
    direction = random.choice([-1, 1])  # Random direction

    steps = random.randint(5, 8)
    step_amount = 180 / steps

    for i in range(steps):
        current_yaw += direction * (step_amount + random.uniform(-3, 3))
        minescript.player_set_orientation(current_yaw, current_pitch)
        time.sleep(randomize(0.03))

    maybe_jitter_look()


def walk_and_break(num_blocks: int, strafe: str = None):
    """Walk forward while breaking blocks, optionally strafing.

    Args:
        num_blocks: Number of blocks to traverse
        strafe: 'left' or 'right' to walk diagonally into wall
    """
    minescript.echo(f"  Walking {num_blocks} blocks...")

    # Start holding attack (left click) - True means pressed
    minescript.player_press_attack(True)

    # Start movement
    minescript.player_press_forward(True)
    if strafe == 'left':
        minescript.player_press_left(True)
    elif strafe == 'right':
        minescript.player_press_right(True)

    try:
        for i in range(num_blocks):
            # Wait for one block of movement
            block_time = randomize(TIMING["block_time"])
            time.sleep(block_time)

            # Human-like behaviors
            maybe_pause()
            maybe_jitter_look()

            # Progress indicator
            if (i + 1) % 20 == 0:
                minescript.echo(f"    Progress: {i + 1}/{num_blocks}")
    finally:
        # Release all keys - False means released
        minescript.player_press_forward(False)
        minescript.player_press_attack(False)
        if strafe == 'left':
            minescript.player_press_left(False)
        elif strafe == 'right':
            minescript.player_press_right(False)


def walk_forward(num_blocks: int, sprint: bool = False):
    """Walk forward without breaking."""
    if sprint:
        minescript.player_press_sprint(True)

    minescript.player_press_forward(True)

    try:
        for i in range(num_blocks):
            time.sleep(randomize(TIMING["walk_time"]))
            maybe_pause()
    finally:
        minescript.player_press_forward(False)
        if sprint:
            minescript.player_press_sprint(False)


def harvest_row(row_num: int):
    """Harvest a single row using diagonal movement.

    Alternates strafe direction between rows for variety.
    """
    minescript.echo(f"Harvesting row {row_num + 1}/{FARM_CONFIG['total_rows']}")

    # Alternate strafe direction for anti-detection variety
    strafe = 'left' if (row_num % 2 == 0) else 'right'

    walk_and_break(FARM_CONFIG["row_length"], strafe=strafe)


def move_to_next_row(going_right: bool = True):
    """Move to the adjacent row."""
    minescript.echo("  Moving to next row...")

    time.sleep(randomize(0.3))

    # Turn toward next row
    if going_right:
        turn_right_90()
    else:
        turn_left_90()

    time.sleep(randomize(0.2))

    # Walk to next row
    walk_forward(FARM_CONFIG["row_spacing"])

    time.sleep(randomize(0.2))

    # Turn to face down the row
    if going_right:
        turn_right_90()
    else:
        turn_left_90()

    time.sleep(randomize(0.3))
    maybe_pause()


def return_to_start():
    """Return to starting position after harvesting."""
    minescript.echo("Returning to start...")

    # Turn toward entrance side
    turn_right_90()
    time.sleep(randomize(0.3))

    # Walk back across all rows (sprinting)
    total_width = (FARM_CONFIG["total_rows"] - 1) * FARM_CONFIG["row_spacing"]
    walk_forward(total_width, sprint=True)

    time.sleep(randomize(0.3))

    # Turn toward entrance
    turn_right_90()
    time.sleep(randomize(0.2))

    # Walk back to entrance
    walk_forward(FARM_CONFIG["row_length"] + FARM_CONFIG["blocks_to_entrance"], sprint=True)

    # Face into farm again
    turn_around()

    minescript.echo("Returned to start!")


def run_harvest_cycle(cycle_num: int):
    """Run one complete harvest cycle."""
    minescript.echo(f"\n{'='*40}")
    minescript.echo(f"Starting harvest cycle #{cycle_num}")
    minescript.echo(f"{'='*40}")

    # Walk to first row
    minescript.echo("Walking to first row...")
    time.sleep(randomize(0.5))
    walk_forward(FARM_CONFIG["blocks_to_entrance"])

    # Harvest all rows in serpentine pattern
    for row in range(FARM_CONFIG["total_rows"]):
        harvest_row(row)

        # Move to next row if not last
        if row < FARM_CONFIG["total_rows"] - 1:
            going_right = (row % 2 == 0)
            move_to_next_row(going_right)

    # Return to start
    return_to_start()


def main():
    """Main entry point."""
    minescript.echo("")
    minescript.echo("╔════════════════════════════════════════╗")
    minescript.echo("║     Pumpkin Farm Macro (Minescript)    ║")
    minescript.echo("╠════════════════════════════════════════╣")
    minescript.echo(f"║  Rows: {FARM_CONFIG['total_rows']:3d}                              ║")
    minescript.echo(f"║  Pumpkins/row: {FARM_CONFIG['row_length']:3d}                      ║")
    minescript.echo(f"║  Total: {FARM_CONFIG['total_rows'] * FARM_CONFIG['row_length']:5d}                          ║")
    minescript.echo("╠════════════════════════════════════════╣")
    minescript.echo("║  Features:                             ║")
    minescript.echo("║  - Diagonal movement (both rows)       ║")
    minescript.echo("║  - Randomized timing                   ║")
    minescript.echo("║  - Human-like pauses                   ║")
    minescript.echo("╚════════════════════════════════════════╝")
    minescript.echo("")
    minescript.echo("Starting in 3 seconds...")
    minescript.echo("Face into the farm from the entrance!")

    time.sleep(3)

    cycle = 0
    while True:
        cycle += 1
        run_harvest_cycle(cycle)

        # Random delay between cycles
        delay = random.uniform(1.0, 3.0)
        minescript.echo(f"Next cycle in {delay:.1f}s...")
        time.sleep(delay)


if __name__ == "__main__":
    main()
