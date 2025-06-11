# mediapipe-numpy2

A patching tool to remove the `numpy<2` constraint from
official [mediapipe](https://github.com/google-ai-edge/mediapipe) wheels.

### Why does this repository exist?

The official mediapipe Python wheels published on PyPI include a strict dependency:

```
Requires-Dist: numpy<2
```

This prevents installation or use of mediapipe with `numpy` version 2 or higher.

This constraint is problematic for users and downstream projects who want to use the latest `numpy` (
see [mediapipe issue #5612](https://github.com/google-ai-edge/mediapipe/issues/5612)).  
As of now, mediapipe works with `numpy` 2.x, but the PyPI wheels block installation.

### What does this repository do?

This repository provides a script (`patch_wheels.sh`) that:

- Downloads all official mediapipe wheels for a given version from PyPI.
- Removes the `numpy<2` requirement from the wheel metadata.
- Renames the package to `mediapipe-numpy2` to avoid conflicts with the official package.
- Updates the wheel metadata to reference this repository.
- Rebuilds and outputs patched wheels that can be installed alongside `numpy>=2`.


### Usage

1. **Clone this repository:**
   ```sh
   git clone https://github.com/cansik/mediapipe-numpy2.git
   cd mediapipe-numpy2
   ```

2. **Run the patching script:**
   ```sh
   ./patch_wheels.sh
   ```
   By default, this will:
    - Download the latest mediapipe wheels into `./downloaded_wheels`
    - Output patched wheels into `./patched_wheels`

   You can override the mediapipe version and directories using environment variables:
   ```sh
   VERSION=0.10.21 DOWNLOAD_DIR=./my_dl OUTPUT_DIR=./my_patched ./patch_wheels.sh
   ```

3. **Install a patched wheel:**
   ```sh
   pip install ./patched_wheels/mediapipe_numpy2-*.whl
   ```

### Notes

- The patched wheels are named `mediapipe-numpy2` to avoid clashing with the official package.
- This repository is not affiliated with the official mediapipe project.
- Use at your own risk; always test compatibility with your workflow.