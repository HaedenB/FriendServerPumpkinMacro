"""
Pumpkin Farm Macro for Minecraft using Minescript
Smooth camera movement, diagonal alignment, walk-and-break.

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
    "look_offset_max": 1.5,      # Random offset when looking at blocks
    "smooth_look_steps_min": 8,  # Min steps for smooth camera
    "smooth_look_steps_max": 15, # Max steps for smooth camera
    "smooth_look_time_min": 0.2, # Min time for smooth look
    "smooth_look_time_max": 0.5, # Max time for smooth look
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
        block_str = str(block).lower()
        return "pumpkin" in block_str and "stem" not in block_str
    except:
        return False


def is_solid_block(x: int, y: int, z: int) -> bool:
    """Check if block at position is solid (wall/barrier)."""
    try:
        block = minescript.getblock(x, y, z)
        if block is None:
            return False
        block_str = str(block).lower()
        # Air and plants are not solid
        if "air" in block_str or "stem" in block_str:
            return False
        # Pumpkins are solid but we break them, so don't count as wall
        if "pumpkin" in block_str:
            return False
        # Most other blocks (stone, dirt, etc) are walls
        return True
    except:
        return False


def is_wall_ahead() -> bool:
    """Check if there's a wall directly in front of player."""
    px, py, pz = get_block_pos()
    yaw, _ = get_orientation()

    # Determine forward direction based on yaw
    yaw_norm = yaw % 360
    if yaw_norm < 0:
        yaw_norm += 360

    # Check block ahead based on facing direction
    if 315 <= yaw_norm or yaw_norm < 45:  # Facing south (+Z)
        return is_solid_block(px, py, pz + 1)
    elif 45 <= yaw_norm < 135:  # Facing west (-X)
        return is_solid_block(px - 1, py, pz)
    elif 135 <= yaw_norm < 225:  # Facing north (-Z)
        return is_solid_block(px, py, pz - 1)
    else:  # Facing east (+X)
        return is_solid_block(px + 1, py, pz)


def get_orientation():
    """Get current yaw and pitch."""
    return minescript.player_orientation()


def set_orientation(yaw: float, pitch: float):
    """Set look direction directly."""
    minescript.player_set_orientation(yaw, pitch)


def smooth_look_at(target_yaw: float, target_pitch: float):
    """Smoothly move camera to target with human-like movement.

    Uses easing and randomized timing for natural movement.
    """
    current_yaw, current_pitch = get_orientation()

    # Add small random offset to target (humans don't look at exact center)
    target_yaw += random.uniform(-RANDOM_CONFIG["look_offset_max"], RANDOM_CONFIG["look_offset_max"])
    target_pitch += random.uniform(-RANDOM_CONFIG["look_offset_max"] / 2, RANDOM_CONFIG["look_offset_max"] / 2)

    # Randomize number of steps and total time
    steps = random.randint(RANDOM_CONFIG["smooth_look_steps_min"], RANDOM_CONFIG["smooth_look_steps_max"])
    total_time = random.uniform(RANDOM_CONFIG["smooth_look_time_min"], RANDOM_CONFIG["smooth_look_time_max"])

    # Calculate differences (handle yaw wrap-around)
    dyaw = target_yaw - current_yaw
    # Normalize yaw difference to -180 to 180
    while dyaw > 180:
        dyaw -= 360
    while dyaw < -180:
        dyaw += 360

    dpitch = target_pitch - current_pitch

    for i in range(steps):
        # Use ease-in-out curve for natural movement
        t = (i + 1) / steps
        # Smoothstep easing: 3t^2 - 2t^3
        eased_t = t * t * (3 - 2 * t)

        # Add slight randomness to each step
        jitter = random.uniform(0.95, 1.05)

        new_yaw = current_yaw + dyaw * eased_t * jitter
        new_pitch = current_pitch + dpitch * eased_t * jitter

        set_orientation(new_yaw, new_pitch)

        # Randomize delay between steps
        step_delay = (total_time / steps) * random.uniform(0.7, 1.3)
        time.sleep(step_delay)

    # Final adjustment to exact target (with offset)
    set_orientation(target_yaw, target_pitch)


def calculate_look_angles(target_x: float, target_y: float, target_z: float):
    """Calculate yaw and pitch to look at a world position."""
    px, py, pz = get_pos()
    eye_y = py + 1.62  # Eye height

    dx = target_x - px
    dy = target_y - eye_y
    dz = target_z - pz

    dist_xz = math.sqrt(dx * dx + dz * dz)

    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = math.degrees(math.atan2(-dy, dist_xz))

    return yaw, pitch


def find_nearest_pumpkin(max_range: int = 10):
    """Find the nearest pumpkin within range.

    Returns (x, y, z) of nearest pumpkin or None.
    """
    px, py, pz = get_block_pos()

    nearest = None
    nearest_dist = float('inf')

    # Search in a box around player
    for dx in range(-max_range, max_range + 1):
        for dz in range(-max_range, max_range + 1):
            for dy in range(-1, 2):  # Check at feet level, +1, -1
                x, y, z = px + dx, py + dy, pz + dz
                if is_pumpkin(x, y, z):
                    dist = abs(dx) + abs(dz)  # Manhattan distance
                    if dist < nearest_dist and dist > 0:  # Don't target block we're standing in
                        nearest_dist = dist
                        nearest = (x, y, z)

    return nearest


def get_facing_direction():
    """Get the cardinal direction player is facing.

    Returns: 'north', 'south', 'east', 'west'
    """
    yaw, _ = get_orientation()
    yaw = yaw % 360
    if yaw < 0:
        yaw += 360

    if 45 <= yaw < 135:
        return 'west'
    elif 135 <= yaw < 225:
        return 'north'
    elif 225 <= yaw < 315:
        return 'east'
    else:
        return 'south'


def calculate_harvest_angle():
    """Calculate the diagonal look angle for harvesting.

    Based on testing: ~11.7 yaw offset, ~16.7 pitch works well.
    Always strafe left (W+A), walk into pumpkins on the right.

    Returns (yaw_offset, pitch) to add to current forward direction.
    """
    # Yaw: about 11-12 degrees to the left of forward
    # Pitch: about 16-17 degrees down
    yaw_offset = random.uniform(10.5, 13.0)  # Slight left offset
    pitch = random.uniform(15.5, 18.0)       # Looking down at pumpkins

    return yaw_offset, pitch


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


def walk_simple(blocks: int, sprint: bool = False):
    """Walk forward without breaking."""
    for _ in range(blocks):
        press_keys(forward=True, sprint=sprint)
        time.sleep(randomize(0.22))
        release_all()
        time.sleep(randomize(0.03))
        maybe_pause()


def align_to_wall():
    """Walk into the wall briefly to align position before harvesting."""
    minescript.echo("  Aligning to wall...")
    # Walk forward + left to press against the right wall
    press_keys(forward=True, left=True)
    time.sleep(randomize(0.5))
    release_all()
    time.sleep(randomize(0.1))


def harvest_row(row_num: int):
    """Harvest a row with proper diagonal camera alignment.

    1. Align to wall first
    2. Find nearest pumpkin, look at it, and break it
    3. Set diagonal angle (~11.7 yaw, ~16.7 pitch)
    4. Walk W+A + attack until we hit the end wall
    """
    minescript.echo(f"Harvesting row {row_num + 1}/{FARM_CONFIG['total_rows']}")

    # First align to the wall
    align_to_wall()

    # Get current forward direction (should be aligned to row now)
    base_yaw, _ = get_orientation()
    # Snap to nearest cardinal direction for consistency
    base_yaw = round(base_yaw / 90) * 90

    # Find a pumpkin to initially target
    pumpkin = find_nearest_pumpkin(15)

    if pumpkin:
        minescript.echo(f"  Found pumpkin at {pumpkin}")
        # Calculate look angles to that pumpkin
        target_yaw, target_pitch = calculate_look_angles(
            pumpkin[0] + 0.5,
            pumpkin[1] + 0.5,
            pumpkin[2] + 0.5
        )
        # Smoothly look at it
        smooth_look_at(target_yaw, target_pitch)
        time.sleep(randomize(0.1))

        # Break the first pumpkin
        minescript.echo(f"  Breaking first pumpkin...")
        minescript.player_press_attack(True)
        # Wait until pumpkin is broken or timeout
        start_break = time.time()
        while is_pumpkin(pumpkin[0], pumpkin[1], pumpkin[2]) and time.time() - start_break < 2.0:
            time.sleep(0.05)
        minescript.player_press_attack(False)
        time.sleep(randomize(0.1))

    # Now set up the diagonal harvesting angle
    yaw_offset, pitch = calculate_harvest_angle()
    target_yaw = base_yaw + yaw_offset

    minescript.echo(f"  Setting angle: yaw={target_yaw:.1f}, pitch={pitch:.1f}")
    smooth_look_at(target_yaw, pitch)
    time.sleep(randomize(0.15))

    # Now walk the row - always W+A, camera stays fixed
    # Detect end by checking for wall block ahead
    minescript.echo(f"  Walking row...")

    # Start movement: always W+A (forward + strafe left)
    press_keys(forward=True, left=True, attack=True)

    while not is_wall_ahead():
        time.sleep(randomize(0.2))

        # Occasional micro-pause for human-like behavior
        if random.random() < 0.02:
            release_all()
            time.sleep(random.uniform(0.1, 0.3))
            press_keys(forward=True, left=True, attack=True)

    release_all()
    minescript.echo(f"  Row complete (hit wall)")


def turn_smoothly(degrees: float):
    """Turn by specified degrees with smooth movement."""
    yaw, pitch = get_orientation()
    target_yaw = yaw + degrees
    smooth_look_at(target_yaw, pitch)


def move_to_next_row(going_right: bool):
    """Move to the next row."""
    minescript.echo("  Moving to next row...")

    time.sleep(randomize(0.3))

    # Turn 90 degrees
    if going_right:
        turn_smoothly(90)
    else:
        turn_smoothly(-90)

    time.sleep(randomize(0.2))

    # Walk to next row
    walk_simple(FARM_CONFIG["row_spacing"])

    time.sleep(randomize(0.2))

    # Turn another 90 to face down the row
    if going_right:
        turn_smoothly(90)
    else:
        turn_smoothly(-90)

    time.sleep(randomize(0.3))


def return_to_start():
    """Return to starting position."""
    minescript.echo("Returning to start...")

    turn_smoothly(90)
    time.sleep(randomize(0.3))

    total_width = (FARM_CONFIG["total_rows"] - 1) * FARM_CONFIG["row_spacing"]
    walk_simple(total_width, sprint=True)

    time.sleep(randomize(0.3))
    turn_smoothly(90)
    time.sleep(randomize(0.2))

    walk_simple(FARM_CONFIG["row_length"] + FARM_CONFIG["blocks_to_entrance"], sprint=True)

    turn_smoothly(180)
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
            going_right = (row % 2 == 1)  # Left first, then right, alternating
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
    minescript.echo("║  - Smooth camera movement            ║")
    minescript.echo("║  - Diagonal alignment + walk         ║")
    minescript.echo("║  - Smart pumpkin targeting           ║")
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
