"""
Pumpkin Farm Macro for Minecraft using Minescript
Uses proper Minescript API with block detection.

Installation:
1. Install Minescript mod: https://github.com/maxuser0/minescript
2. Place this file in .minecraft/minescript/ folder
3. In-game, run: \pumpkin_macro_minescript
"""

import minescript
import random
import time
import math

# Farm Configuration
FARM_CONFIG = {
    "total_rows": 19,
    "row_length": 91,
    "blocks_to_entrance": 2,
    "row_spacing": 2,
}

# Randomization for anti-detection
RANDOM_CONFIG = {
    "timing_variance": 0.15,
    "pause_chance": 0.02,
    "pause_min": 0.3,
    "pause_max": 1.5,
    "micro_pause_chance": 0.08,
    "micro_pause_min": 0.05,
    "micro_pause_max": 0.15,
}


def randomize(base: float) -> float:
    """Add random variance to timing."""
    variance = base * RANDOM_CONFIG["timing_variance"]
    return base + random.uniform(-variance, variance)


def maybe_pause():
    """Occasionally pause like a human would."""
    if random.random() < RANDOM_CONFIG["pause_chance"]:
        time.sleep(random.uniform(RANDOM_CONFIG["pause_min"], RANDOM_CONFIG["pause_max"]))
    elif random.random() < RANDOM_CONFIG["micro_pause_chance"]:
        time.sleep(random.uniform(RANDOM_CONFIG["micro_pause_min"], RANDOM_CONFIG["micro_pause_max"]))


def get_pos():
    """Get player position as (x, y, z) floats."""
    pos = minescript.player().position
    return pos[0], pos[1], pos[2]


def get_block_pos():
    """Get player block position as integers."""
    x, y, z = get_pos()
    return int(math.floor(x)), int(math.floor(y)), int(math.floor(z))


def is_pumpkin(x: int, y: int, z: int) -> bool:
    """Check if block at position is a pumpkin."""
    try:
        block = minescript.getblock(x, y, z)
        if block is None:
            return False
        # Handle both string and other return types
        block_str = str(block).lower()
        return "pumpkin" in block_str and "stem" not in block_str
    except:
        return False


def get_targeted_block():
    """Get info about block player is looking at."""
    try:
        return minescript.player_get_targeted_block(5)
    except:
        return None


def is_targeting_pumpkin() -> bool:
    """Check if player is looking at a pumpkin."""
    block = get_targeted_block()
    if block is None:
        return False
    try:
        block_type = str(block.type).lower() if hasattr(block, 'type') else str(block).lower()
        return "pumpkin" in block_type and "stem" not in block_type
    except:
        return False


def set_look(yaw: float, pitch: float):
    """Set player look direction."""
    # Add slight randomization
    yaw += random.uniform(-0.5, 0.5)
    pitch += random.uniform(-0.3, 0.3)
    minescript.player_set_orientation(yaw, pitch)


def get_orientation():
    """Get current yaw and pitch."""
    return minescript.player_orientation()


def look_at_block(target_x: int, target_y: int, target_z: int):
    """Look toward a specific block position."""
    px, py, pz = get_pos()
    # Player eye height is roughly y + 1.62
    eye_y = py + 1.62

    dx = target_x + 0.5 - px
    dy = target_y + 0.5 - eye_y
    dz = target_z + 0.5 - pz

    dist_xz = math.sqrt(dx * dx + dz * dz)

    # Calculate yaw (horizontal angle)
    yaw = math.degrees(math.atan2(-dx, dz))

    # Calculate pitch (vertical angle)
    pitch = math.degrees(math.atan2(-dy, dist_xz))

    set_look(yaw, pitch)


def press_keys(forward=False, left=False, right=False, back=False, attack=False, sprint=False):
    """Set movement key states."""
    minescript.player_press_forward(forward)
    minescript.player_press_left(left)
    minescript.player_press_right(right)
    minescript.player_press_backward(back)
    minescript.player_press_attack(attack)
    minescript.player_press_sprint(sprint)


def release_all():
    """Release all movement keys."""
    press_keys()


def break_block_at(x: int, y: int, z: int, timeout: float = 2.0):
    """Look at and break a specific block."""
    look_at_block(x, y, z)
    time.sleep(randomize(0.1))

    # Start attacking
    minescript.player_press_attack(True)

    start = time.time()
    while time.time() - start < timeout:
        # Check if block is gone
        if not is_pumpkin(x, y, z):
            break
        time.sleep(0.05)

    minescript.player_press_attack(False)
    time.sleep(randomize(0.05))


def check_and_break_adjacent_pumpkins():
    """Check for pumpkins to left and right, break if found."""
    px, py, pz = get_block_pos()
    yaw, pitch = get_orientation()

    # Determine which direction we're facing (N/S/E/W)
    # Yaw: 0 = south, 90 = west, 180/-180 = north, -90 = east
    yaw_normalized = yaw % 360
    if yaw_normalized > 180:
        yaw_normalized -= 360

    # Calculate left and right offsets based on facing direction
    if -45 <= yaw_normalized < 45:  # Facing south (+Z)
        left_offset = (1, 0)   # East
        right_offset = (-1, 0) # West
    elif 45 <= yaw_normalized < 135:  # Facing west (-X)
        left_offset = (0, 1)   # South
        right_offset = (0, -1) # North
    elif yaw_normalized >= 135 or yaw_normalized < -135:  # Facing north (-Z)
        left_offset = (-1, 0)  # West
        right_offset = (1, 0)  # East
    else:  # Facing east (+X)
        left_offset = (0, -1)  # North
        right_offset = (0, 1)  # South

    # Check and break left pumpkin
    left_x = px + left_offset[0]
    left_z = pz + left_offset[1]
    if is_pumpkin(left_x, py, left_z):
        break_block_at(left_x, py, left_z)
        # Restore forward look
        set_look(yaw, 0)

    # Check and break right pumpkin
    right_x = px + right_offset[0]
    right_z = pz + right_offset[1]
    if is_pumpkin(right_x, py, right_z):
        break_block_at(right_x, py, right_z)
        # Restore forward look
        set_look(yaw, 0)


def walk_row_smart(length: int, strafe_left: bool = True):
    """Walk a row, checking for and breaking pumpkins."""
    minescript.echo(f"  Walking row ({length} blocks)...")

    start_x, start_y, start_z = get_block_pos()
    yaw, _ = get_orientation()

    # Look slightly down to see pumpkins better
    set_look(yaw, 10)

    blocks_walked = 0

    while blocks_walked < length:
        # Check for pumpkins on sides
        check_and_break_adjacent_pumpkins()

        # Move forward with diagonal strafe
        if strafe_left:
            press_keys(forward=True, left=True, attack=True)
        else:
            press_keys(forward=True, right=True, attack=True)

        time.sleep(randomize(0.25))
        release_all()

        # Count distance traveled
        curr_x, curr_y, curr_z = get_block_pos()
        dx = abs(curr_x - start_x)
        dz = abs(curr_z - start_z)
        blocks_walked = max(dx, dz)

        maybe_pause()

        if blocks_walked % 20 == 0 and blocks_walked > 0:
            minescript.echo(f"    Progress: {blocks_walked}/{length}")

    release_all()


def walk_simple(blocks: int, sprint: bool = False):
    """Walk forward without breaking."""
    for _ in range(blocks):
        press_keys(forward=True, sprint=sprint)
        time.sleep(randomize(0.22))
        release_all()
        maybe_pause()


def turn_right():
    """Turn 90 degrees right."""
    yaw, pitch = get_orientation()
    target = yaw + 90

    steps = random.randint(3, 5)
    for i in range(steps):
        current = yaw + (90 * (i + 1) / steps)
        set_look(current, pitch)
        time.sleep(randomize(0.05))


def turn_left():
    """Turn 90 degrees left."""
    yaw, pitch = get_orientation()
    target = yaw - 90

    steps = random.randint(3, 5)
    for i in range(steps):
        current = yaw - (90 * (i + 1) / steps)
        set_look(current, pitch)
        time.sleep(randomize(0.05))


def turn_around():
    """Turn 180 degrees."""
    yaw, pitch = get_orientation()
    direction = random.choice([-1, 1])

    steps = random.randint(5, 8)
    for i in range(steps):
        current = yaw + direction * (180 * (i + 1) / steps)
        set_look(current, pitch)
        time.sleep(randomize(0.03))


def harvest_row(row_num: int):
    """Harvest one row."""
    minescript.echo(f"Harvesting row {row_num + 1}/{FARM_CONFIG['total_rows']}")

    # Alternate strafe direction
    strafe_left = (row_num % 2 == 0)
    walk_row_smart(FARM_CONFIG["row_length"], strafe_left)


def move_to_next_row(going_right: bool):
    """Move to the next row."""
    minescript.echo("  Moving to next row...")

    time.sleep(randomize(0.3))

    if going_right:
        turn_right()
    else:
        turn_left()

    time.sleep(randomize(0.2))
    walk_simple(FARM_CONFIG["row_spacing"])
    time.sleep(randomize(0.2))

    if going_right:
        turn_right()
    else:
        turn_left()

    time.sleep(randomize(0.3))


def return_to_start():
    """Return to starting position."""
    minescript.echo("Returning to start...")

    turn_right()
    time.sleep(randomize(0.3))

    total_width = (FARM_CONFIG["total_rows"] - 1) * FARM_CONFIG["row_spacing"]
    walk_simple(total_width, sprint=True)

    time.sleep(randomize(0.3))
    turn_right()
    time.sleep(randomize(0.2))

    walk_simple(FARM_CONFIG["row_length"] + FARM_CONFIG["blocks_to_entrance"], sprint=True)

    turn_around()
    minescript.echo("Returned to start!")


def run_cycle(cycle_num: int):
    """Run one harvest cycle."""
    minescript.echo(f"\n{'='*40}")
    minescript.echo(f"Harvest cycle #{cycle_num}")
    minescript.echo(f"{'='*40}")

    # Walk to first row
    minescript.echo("Walking to first row...")
    walk_simple(FARM_CONFIG["blocks_to_entrance"])

    # Harvest all rows
    for row in range(FARM_CONFIG["total_rows"]):
        harvest_row(row)

        if row < FARM_CONFIG["total_rows"] - 1:
            going_right = (row % 2 == 0)
            move_to_next_row(going_right)

    return_to_start()


def main():
    minescript.echo("")
    minescript.echo("╔══════════════════════════════════════╗")
    minescript.echo("║   Pumpkin Farm Macro (Minescript)    ║")
    minescript.echo("╠══════════════════════════════════════╣")
    minescript.echo(f"║  Rows: {FARM_CONFIG['total_rows']:3d}                            ║")
    minescript.echo(f"║  Length: {FARM_CONFIG['row_length']:3d}                          ║")
    minescript.echo(f"║  Total: {FARM_CONFIG['total_rows'] * FARM_CONFIG['row_length']:5d}                        ║")
    minescript.echo("╠══════════════════════════════════════╣")
    minescript.echo("║  - Smart pumpkin detection           ║")
    minescript.echo("║  - Diagonal movement                 ║")
    minescript.echo("║  - Anti-detection randomization      ║")
    minescript.echo("╚══════════════════════════════════════╝")
    minescript.echo("")
    minescript.echo("Starting in 3 seconds...")
    minescript.echo("Stand at entrance facing into farm!")

    time.sleep(3)

    cycle = 0
    try:
        while True:
            cycle += 1
            run_cycle(cycle)

            delay = random.uniform(1.0, 3.0)
            minescript.echo(f"Next cycle in {delay:.1f}s...")
            time.sleep(delay)
    except KeyboardInterrupt:
        release_all()
        minescript.echo("Stopped!")
    finally:
        release_all()


if __name__ == "__main__":
    main()
