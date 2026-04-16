# Docker Android TikTok Automation Setup

## Overview
Run 3 Android containers with TikTok for automated viewing/following

**Disk Space Required:** ~15 GB
**Setup Time:** 1-2 hours
**Difficulty:** Hard (requires Docker knowledge)

---

## Installation

### Step 1: Install Docker Desktop

```bash
# Download Docker Desktop for Mac
# Go to: https://www.docker.com/products/docker-desktop

# Or install via Homebrew
brew install --cask docker
```

After install:
1. Open Docker Desktop
2. Accept terms
3. Wait for Docker to start (whale icon in menu bar)

### Step 2: Verify Docker

```bash
docker --version
# Should show: Docker version 24.x.x or higher

docker ps
# Should show empty list (no containers running yet)
```

---

## Create Android Container

### Dockerfile

Create file: `Dockerfile.tiktok`

```dockerfile
FROM budtmo/docker-android:emulator_11.0

# Set environment variables
ENV DEVICE="Samsung Galaxy S10"
ENV ANDROID_VERSION=11.0
ENV EMULATOR_TIMEOUT=300

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    adb

# Install Python automation libraries
RUN pip3 install uiautomator2

# Expose ports
EXPOSE 5555 5554

# Keep container running
CMD ["/bin/bash"]
```

### Build Image

```bash
# Build the image (takes 20-30 minutes first time)
docker build -f Dockerfile.tiktok -t tiktok-android .

# Image size: ~4 GB
```

---

## Run 3 Containers (3 TikTok Accounts)

### Container 1
```bash
docker run -d \
  --name tiktok-account-1 \
  --privileged \
  -p 5555:5555 \
  -p 6080:6080 \
  -e DEVICE="Samsung Galaxy S10" \
  tiktok-android
```

### Container 2
```bash
docker run -d \
  --name tiktok-account-2 \
  --privileged \
  -p 5556:5555 \
  -p 6081:6080 \
  -e DEVICE="Samsung Galaxy S10" \
  tiktok-android
```

### Container 3
```bash
docker run -d \
  --name tiktok-account-3 \
  --privileged \
  -p 5557:5555 \
  -p 6082:6080 \
  -e DEVICE="Samsung Galaxy S10" \
  tiktok-android
```

---

## Install TikTok on Each Container

### Method 1: Web Interface

1. Open browser:
   - Container 1: http://localhost:6080
   - Container 2: http://localhost:6081
   - Container 3: http://localhost:6082

2. Wait for Android to boot (~2 minutes)

3. Open Play Store

4. Search "TikTok"

5. Install

6. Sign in with your account

### Method 2: ADB Command

```bash
# Download TikTok APK
wget https://apkpure.com/tiktok/com.zhiliaoapp.musically/download -O tiktok.apk

# Install on container 1
docker exec tiktok-account-1 adb install /path/to/tiktok.apk

# Install on container 2
docker exec tiktok-account-2 adb install /path/to/tiktok.apk

# Install on container 3
docker exec tiktok-account-3 adb install /path/to/tiktok.apk
```

---

## Automation Script

```python
#!/usr/bin/env python3
"""
Docker TikTok Automation - 3 Containers
"""
import subprocess
import time

CONTAINERS = [
    {'name': 'tiktok-account-1', 'port': 5555},
    {'name': 'tiktok-account-2', 'port': 5556},
    {'name': 'tiktok-account-3', 'port': 5557},
]

TARGET_ACCOUNTS = ['charlidamelio', 'addisonre', 'bellapoarch']
VIDEOS_PER_ACCOUNT = 30

def adb_command(container_name, command):
    """Execute ADB command in container"""
    full_cmd = f"docker exec {container_name} adb shell {command}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def tap(container_name, x, y):
    """Tap at coordinates"""
    adb_command(container_name, f"input tap {x} {y}")
    time.sleep(1)

def swipe(container_name, x1, y1, x2, y2, duration=500):
    """Swipe gesture"""
    adb_command(container_name, f"input swipe {x1} {y1} {x2} {y2} {duration}")
    time.sleep(1)

def type_text(container_name, text):
    """Type text"""
    adb_command(container_name, f"input text '{text}'")
    time.sleep(1)

def view_videos(container_name, target_username, num_videos):
    """View videos from target account"""
    print(f"\n{container_name}: Viewing @{target_username}")

    # Open TikTok
    adb_command(container_name, "am start -n com.zhiliaoapp.musically/.MainActivity")
    time.sleep(3)

    # Tap search
    tap(container_name, 540, 1800)  # Search button
    time.sleep(2)

    # Type username
    tap(container_name, 540, 300)  # Search field
    type_text(container_name, target_username)
    time.sleep(2)

    # Tap first result
    tap(container_name, 540, 500)
    time.sleep(2)

    # Tap first video
    tap(container_name, 540, 800)
    time.sleep(2)

    # Watch videos
    for i in range(num_videos):
        print(f"  Video {i+1}/{num_videos}...")
        time.sleep(15)  # Watch 15 seconds

        # Swipe up for next video
        swipe(container_name, 540, 1500, 540, 500)
        time.sleep(2)

    print(f"  ✓ Watched {num_videos} videos")

def main():
    print("=" * 80)
    print("  DOCKER TIKTOK AUTOMATION - 3 Containers")
    print("=" * 80)

    for container in CONTAINERS:
        for target in TARGET_ACCOUNTS:
            view_videos(container['name'], target, VIDEOS_PER_ACCOUNT)
            time.sleep(30)  # Break between targets

    print("\n✓ All containers finished!")

if __name__ == '__main__':
    main()
```

---

## Resource Usage

```
Per Container:
- CPU: ~20-30%
- RAM: ~2-3 GB
- Disk: ~4 GB

3 Containers Total:
- CPU: ~60-90% (can slow down Mac)
- RAM: ~6-9 GB
- Disk: ~12 GB
```

---

## Pros & Cons

### Pros
- ✓ Can scale to many containers
- ✓ Runs headless (no UI needed)
- ✓ Fully automated (no manual switching)
- ✓ Can run on server 24/7

### Cons
- ✗ Uses lots of resources (15GB disk, 9GB RAM)
- ✗ Complex setup
- ✗ Slower than real devices
- ✗ May be detected by TikTok (emulator detection)

---

## Recommendation

For just 3 accounts, Docker is **overkill**.

Better options:
1. **iPhone USB** - 0 GB, easiest, most trusted
2. **NoxPlayer** - 10 GB, easier than Docker, has GUI

Use Docker only if:
- You want to scale to 10+ accounts
- You have a dedicated server
- You're comfortable with Docker

