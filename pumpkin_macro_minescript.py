"""
Pumpkin Farm Macro for Minecraft using Minescript
Simple: align, look diagonal, hold forward+attack until wall.

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
    "row_spacing": 7,
}


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
        block_str = str(block).lower()
        return "pumpkin" in block_str and "stem" not in block_str
    except:
        return False


def is_solid_block(x: int, y: int, z: int) -> bool:
    """Check if block at position is solid (wall)."""
    try:
        block = minescript.getblock(x, y, z)
        if block is None:
            return False
        block_str = str(block).lower()
        if "air" in block_str or "stem" in block_str:
            return False
        if "pumpkin" in block_str:
            return False
        return True
    except:
        return False


def is_wall_ahead() -> bool:
    """Check if there's a wall directly in front of player."""
    px, py, pz = get_block_pos()
    yaw, _ = get_orientation()

    yaw_norm = yaw % 360
    if yaw_norm < 0:
        yaw_norm += 360

    if 315 <= yaw_norm or yaw_norm < 45:  # South
        return is_solid_block(px, py, pz + 1)
    elif 45 <= yaw_norm < 135:  # West
        return is_solid_block(px - 1, py, pz)
    elif 135 <= yaw_norm < 225:  # North
        return is_solid_block(px, py, pz - 1)
    else:  # East
        return is_solid_block(px + 1, py, pz)


def get_orientation():
    """Get current yaw and pitch."""
    return minescript.player_orientation()


def set_orientation(yaw: float, pitch: float):
    """Set look direction directly."""
    minescript.player_set_orientation(yaw, pitch)


def smooth_look_at(target_yaw: float, target_pitch: float):
    """Smoothly move camera to target."""
    current_yaw, current_pitch = get_orientation()

    # Randomize steps and timing - keep it quick
    steps = random.randint(5, 10)
    total_time = random.uniform(0.1, 0.25)

    # Handle yaw wrap-around
    dyaw = target_yaw - current_yaw
    while dyaw > 180:
        dyaw -= 360
    while dyaw < -180:
        dyaw += 360

    dpitch = target_pitch - current_pitch

    for i in range(steps):
        t = (i + 1) / steps
        # Smoothstep easing
        eased_t = t * t * (3 - 2 * t)

        new_yaw = current_yaw + dyaw * eased_t
        new_pitch = current_pitch + dpitch * eased_t

        set_orientation(new_yaw, new_pitch)
        time.sleep(total_time / steps)

    set_orientation(target_yaw, target_pitch)


def find_nearest_pumpkin(max_range: int = 10):
    """Find the nearest pumpkin within range."""
    px, py, pz = get_block_pos()

    nearest = None
    nearest_dist = float('inf')

    for dx in range(-max_range, max_range + 1):
        for dz in range(-max_range, max_range + 1):
            for dy in range(-1, 2):
                x, y, z = px + dx, py + dy, pz + dz
                if is_pumpkin(x, y, z):
                    dist = abs(dx) + abs(dz)
                    if dist < nearest_dist and dist > 0:
                        nearest_dist = dist
                        nearest = (x, y, z)

    return nearest


def calculate_look_angles(target_x: float, target_y: float, target_z: float):
    """Calculate yaw and pitch to look at a position."""
    px, py, pz = get_pos()
    eye_y = py + 1.62

    dx = target_x - px
    dy = target_y - eye_y
    dz = target_z - pz

    dist_xz = math.sqrt(dx * dx + dz * dz)

    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = math.degrees(math.atan2(-dy, dist_xz))

    return yaw, pitch


def press_keys(forward=False, left=False, right=False, attack=False, sprint=False):
    """Set movement key states."""
    minescript.player_press_forward(forward)
    minescript.player_press_left(left)
    minescript.player_press_right(right)
    minescript.player_press_attack(attack)
    minescript.player_press_sprint(sprint)


def release_all():
    """Release all keys."""
    press_keys()


def walk_simple(blocks: int, sprint: bool = False):
    """Walk forward for a number of blocks."""
    # Hold keys for entire duration instead of pulsing
    press_keys(forward=True, sprint=sprint)
    # ~0.25s per block walking, ~0.18s sprinting
    time_per_block = 0.18 if sprint else 0.25
    time.sleep(blocks * time_per_block)
    release_all()


def harvest_row(row_num: int):
    """Harvest a row - minimal delay version."""
    minescript.echo(f"Row {row_num + 1}")

    # Align with left wall first
    minescript.player_press_forward(True)
    minescript.player_press_left(True)
    time.sleep(0.3)
    minescript.player_press_forward(False)
    minescript.player_press_left(False)

    # Set diagonal angle based on row direction
    if row_num % 2 == 0:
        target_yaw = random.uniform(30, 50)
        target_pitch = random.uniform(25, 60)
    else:
        target_yaw = random.uniform(-150, -130)
        target_pitch = random.uniform(25, 60)

    smooth_look_at(target_yaw, target_pitch)

    # Walk W+A and attack until wall - call each key function directly
    minescript.player_press_forward(True)
    minescript.player_press_left(True)
    minescript.player_press_attack(True)

    while not is_wall_ahead():
        time.sleep(0.05)

    minescript.player_press_forward(False)
    minescript.player_press_left(False)
    minescript.player_press_attack(False)


def turn_smoothly(degrees: float):
    """Turn by degrees with smooth movement."""
    yaw, pitch = get_orientation()
    smooth_look_at(yaw + degrees, pitch)


def move_to_next_row(going_right: bool):
    """Move to next row - uses wall detection to stop at barrier."""
    if going_right:
        turn_smoothly(90)
    else:
        turn_smoothly(-90)

    # Walk until we hit the barrier
    minescript.player_press_forward(True)
    while not is_wall_ahead():
        time.sleep(0.05)
    minescript.player_press_forward(False)

    if going_right:
        turn_smoothly(90)
    else:
        turn_smoothly(-90)


def return_to_start():
    """Return to starting position."""
    minescript.echo("Returning...")

    turn_smoothly(90)
    total_width = (FARM_CONFIG["total_rows"] - 1) * FARM_CONFIG["row_spacing"]
    walk_simple(total_width, sprint=True)

    turn_smoothly(90)
    walk_simple(FARM_CONFIG["row_length"] + FARM_CONFIG["blocks_to_entrance"], sprint=True)

    turn_smoothly(180)


def run_cycle(cycle_num: int):
    """Run one harvest cycle."""
    minescript.echo(f"\n{'='*40}")
    minescript.echo(f"Harvest cycle #{cycle_num}")
    minescript.echo(f"{'='*40}")

    minescript.echo("Walking to first row...")
    walk_simple(FARM_CONFIG["blocks_to_entrance"])

    for row in range(FARM_CONFIG["total_rows"]):
        harvest_row(row)

        if row < FARM_CONFIG["total_rows"] - 1:
            going_right = (row % 2 == 1)  # Left first, then right
            move_to_next_row(going_right)

    return_to_start()


def main():
    minescript.echo("Pumpkin Macro - Starting...")

    cycle = 0
    try:
        while True:
            cycle += 1
            run_cycle(cycle)

            delay = random.uniform(0.5, 1.5)
            minescript.echo(f"Next cycle in {delay:.1f}s...")
            time.sleep(delay)
    except KeyboardInterrupt:
        release_all()
        minescript.echo("Stopped!")
    finally:
        release_all()


if __name__ == "__main__":
    main()
