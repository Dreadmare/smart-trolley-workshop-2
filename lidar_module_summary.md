# Member 4: LiDAR & Obstacle Safety Module — Summary & Tweak Report

This document summarizes the work completed for the **LiDAR & Obstacle Safety Module** of the Smart Trolley project, detailing the adaptations made from the initial checklist to fit the specific hardware chosen for our setup.

---

## 1. Summary of Completed Tasks

### Component Research & Selection (How We Got It)
- **Sensor Model Confirmation:** We consulted with the project supervisor and confirmed our physical sensor is the **YDLIDAR X3 360° Ranging Sensor Module** rather than the initially proposed RPLIDAR A1M8.
- **Connection & Protocol Analysis:** 
  - The YDLIDAR X3 uses a CP2102 USB-to-UART bridge chip to communicate over serial. On Ubuntu 20.04 (Python 3.8.10), plugging it in maps the device to `/dev/ttyUSB0` (or `/dev/ttyACM0`).
  - Standard baud rate for YDLIDAR X3 is typically 115200.
  - User permissions on Linux require the user to be added to the `dialout` group (`sudo usermod -aG dialout $USER`) to read/write serial ports without permission errors.
- **Driver & SDK Choice:** Since direct PyPI packages for older Python versions can be restricted, we adopted the robust Pythonic `lds2d` driver (`pip install lds2d`), which supports self-spinning LiDARs like the YDLIDAR X3 and parses incoming byte streams into structured `(angle_deg, dist_mm, quality)` scan points.

### Front Sector Filtering (How We Got It)
- **Angular Math & Coordinate System:** 
  - The YDLIDAR X3 performs a full $360^\circ$ counter-clockwise scan starting with $0^\circ$ typically aligned straight ahead (or defined by the optical zero marker).
  - To protect the trolley from front collisions while allowing peripheral clearance, we restricted our safety evaluation window to the forward-facing cone:
    - **Front Sector:** $330^\circ$ to $360^\circ$ and $0^\circ$ to $30^\circ$ (a total $60^\circ$ forward window centered at $0^\circ$).
- **Implementation Logic:** 
  ```python
  def is_in_front_sector(angle_deg):
      """Check if the angle falls within the front pathway sector."""
      return (330 <= angle_deg <= 360) or (0 <= angle_deg <= 30)
  ```
  Every incoming scan point is filtered through this condition. If a point falls within these bounds, its distance is evaluated against our safety thresholds.

- **Standalone Python Simulator:** Built a standalone simulator (`ydlidar_obstacle_detector.py --simulate`) that generates mock `(angle, distance_mm)` scan arrays across various test scenarios (`clear`, `caution`, `critical`, `dynamic`).
- **Granular Safety Zone & Speed Capping Logic:** Converted sensor measurements from millimeters to centimeters and implemented a three-tier safety response framework:
  - **Critical Zone ($\le 30\text{ cm}$):** Immediate Stop (`Safety_Clear = False`, `0% PWM`)
  - **Caution Zone ($30\text{--}60\text{ cm}$):** Slow speed (`Safety_Clear = True`, `max 30% PWM`)
  - **Clear Zone ($> 60\text{ cm}$):** Normal speed (`Safety_Clear = True`, `max 60% PWM`)
- **Live Sensor Readiness:** Prepared the `lds2d` integration script for `/dev/ttyUSB0` at standard baud rates, complete with user group permission guidelines (`dialout`).

---

## 2. Tweaks & Adjustments from the Original Task

While our core objective remained identical (obstacle detection, safety thresholding, simulation testing, and stop response integration), we made the following key adjustments to accommodate our specific environment and hardware:

| Original Task Item | Original Specification | Tweak / Adjustment Made | Rationale |
| :--- | :--- | :--- | :--- |
| **LiDAR Model** | RPLIDAR A1M8 | **YDLIDAR X3** | Hardware availability and supervisor confirmation dictated the switch to YDLIDAR X3. |
| **Driver / SDK** | `rplidar-roboticia` / `pyserial` | **`lds2d` Python package** | The `lds2d` library provides clean, modern Pythonic support for both YDLIDAR and other 2D LiDARs with built-in web visualization and robust packet parsing. |
| **Simulator Implementation** | External standalone script (`lidar_safety_sim.py`) | **Integrated CLI Simulator (`--simulate`)** | We built a unified Python module (`ydlidar_obstacle_detector.py`) that acts as both a simulator and a live sensor reader via command-line arguments (`--simulate` and `--scenario`). |
| **Front Sector Angle Mapping** | Broad or default 180° front arc | **Targeted Sector (`330°–360°` & `0°–30°`)** | Refined the forward cone to precisely match the physical mounting orientation on the trolley chassis. |

---

## 3. Deliverables

- **Python Module:** `/home/fitri/Documents/Workshop 2/ydlidar_obstacle_detector.py`
- **Execution Commands:**
  - *Simulation:* `python3 ydlidar_obstacle_detector.py --simulate --scenario dynamic`
  - *Live Hardware:* `python3 ydlidar_obstacle_detector.py`
