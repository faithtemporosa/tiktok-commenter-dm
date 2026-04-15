#!/usr/bin/env python3
"""
Stealth browsing utilities to hide automation and add natural behavior
Fixes CDP detection and adds human-like patterns
"""

import random
import time

def inject_stealth(page):
    """Inject stealth scripts to hide automation fingerprints"""

    # Hide webdriver
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    # Hide CDP runtime
    page.add_init_script("""
        window.chrome = {
            runtime: {}
        };
    """)

    # Fake plugins
    page.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
    """)

    # Fake languages
    page.add_init_script("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """)

    # Remove automation indicators
    page.add_init_script("""
        delete navigator.__proto__.webdriver;
    """)

def natural_scroll(page, direction='down', distance=None):
    """Scroll naturally like a human"""
    if distance is None:
        distance = random.randint(300, 800)

    # Scroll in chunks with pauses (human-like)
    chunks = random.randint(3, 6)
    chunk_size = distance // chunks

    for i in range(chunks):
        if direction == 'down':
            page.mouse.wheel(0, chunk_size)
        else:
            page.mouse.wheel(0, -chunk_size)

        time.sleep(random.uniform(0.1, 0.3))

    # Random pause after scrolling
    time.sleep(random.uniform(0.5, 2.0))

def natural_mouse_movement(page):
    """Move mouse naturally on the page"""
    # Get viewport size
    viewport = page.viewport_size
    if not viewport:
        viewport = {'width': 1920, 'height': 1080}

    # Random position
    x = random.randint(100, viewport['width'] - 100)
    y = random.randint(100, viewport['height'] - 100)

    # Move in steps (human-like)
    current_pos = {'x': viewport['width'] // 2, 'y': viewport['height'] // 2}
    steps = random.randint(5, 10)

    for i in range(steps):
        step_x = current_pos['x'] + (x - current_pos['x']) * (i + 1) / steps
        step_y = current_pos['y'] + (y - current_pos['y']) * (i + 1) / steps

        page.mouse.move(step_x, step_y)
        time.sleep(random.uniform(0.02, 0.05))

def watch_video_naturally(page, video_duration_seconds=None):
    """Watch a video with natural human behavior"""

    # If duration not provided, estimate 10-60 seconds
    if video_duration_seconds is None:
        video_duration_seconds = random.randint(10, 60)

    # Watch 40-90% of the video
    watch_percentage = random.uniform(0.4, 0.9)
    watch_time = video_duration_seconds * watch_percentage

    # Break watching into natural chunks
    chunks = random.randint(2, 4)
    chunk_time = watch_time / chunks

    for i in range(chunks):
        # Watch chunk
        time.sleep(chunk_time)

        # Random actions while watching
        action = random.choice(['move_mouse', 'small_scroll', 'nothing', 'nothing'])

        if action == 'move_mouse':
            natural_mouse_movement(page)
        elif action == 'small_scroll':
            # Small scroll down/up
            direction = random.choice(['down', 'up'])
            natural_scroll(page, direction, distance=random.randint(50, 150))

def browse_for_you_page(page, num_videos=5):
    """Browse For You page naturally"""

    print(f"  Browsing For You page ({num_videos} videos)...")

    # Go to For You
    page.goto("https://www.tiktok.com/foryou", wait_until="networkidle", timeout=30000)
    time.sleep(random.uniform(2, 4))

    for i in range(num_videos):
        print(f"    Video {i+1}/{num_videos}")

        # Watch current video
        watch_video_naturally(page, video_duration_seconds=random.randint(8, 45))

        # Scroll to next video (swipe down)
        natural_scroll(page, 'down', distance=random.randint(600, 900))

        # Pause before next video
        time.sleep(random.uniform(0.5, 2.0))

    print(f"  Finished browsing {num_videos} videos")

def random_pause(min_seconds=1, max_seconds=3):
    """Random human-like pause"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def click_naturally(page, selector, timeout=5000):
    """Click an element with natural mouse movement"""
    try:
        element = page.locator(selector).first

        # Wait for element
        element.wait_for(state="visible", timeout=timeout)

        # Get element position
        box = element.bounding_box()
        if box:
            # Click at random point within element
            x = box['x'] + random.uniform(5, box['width'] - 5)
            y = box['y'] + random.uniform(5, box['height'] - 5)

            # Move mouse to position
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.1, 0.3))

            # Click
            page.mouse.click(x, y)
            return True
        else:
            # Fallback to regular click
            element.click()
            return True

    except Exception as e:
        return False

def type_naturally(page, selector, text, timeout=5000):
    """Type text with natural human timing"""
    try:
        element = page.locator(selector).first
        element.wait_for(state="visible", timeout=timeout)

        # Click to focus
        click_naturally(page, selector)
        time.sleep(random.uniform(0.2, 0.5))

        # Type with delays between characters
        for char in text:
            page.keyboard.type(char)
            # Random typing speed (50-150ms per character)
            time.sleep(random.uniform(0.05, 0.15))

        return True

    except Exception as e:
        return False
