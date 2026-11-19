import math
import time
import argparse

# --- Configuration ---
# Serial port for YDLIDAR X3 on Linux (confirm via dmesg / ls /dev/tty*)
LIDAR_PORT = '/dev/ttyUSB0'

# Safety Zones and Speed Caps (in cm and PWM percentage)
CRITICAL_THRESHOLD_CM = 30  # <= 30 cm: Immediate Stop (0% PWM)
CAUTION_THRESHOLD_CM = 60   # 30-60 cm: Slow speed (max 30% PWM)
# > 60 cm: Normal speed (max 60% PWM)

# Front Pathway Sector for YDLIDAR X3 (in degrees, 0 to 360)
# Front sector: 330° to 360° and 0° to 30°
FRONT_MIN_1 = 330
FRONT_MAX_1 = 360
FRONT_MIN_2 = 0
FRONT_MAX_2 = 30

# --- Mock Classes for Standalone Simulation ---
class MockScanPoint:
    def __init__(self, angle_deg, dist_mm, quality=10):
        self.angle_deg = angle_deg
        self.dist_mm = dist_mm
        self.quality = quality

class MockScan:
    def __init__(self, valid_points):
        self.valid_points = valid_points

class MockLidarSimulator:
    """Standalone Python simulator that generates mock scan arrays for YDLIDAR X3."""
    def __init__(self, scenario="clear"):
        self.scenario = scenario
        self._step = 0

    def open(self, model, port):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def close(self):
        print("MockLidarSimulator closed.")

    def scans(self):
        while True:
            self._step += 1
            points = []
            
            # Generate 360 points (one per degree)
            for deg in range(360):
                dist_mm = 2000  # Default 2 meters away (Clear Zone)
                
                # Simulate scenarios
                if self.scenario == "critical" and (deg <= 30 or deg >= 330):
                    dist_mm = 200  # 20 cm (Critical Zone <= 30 cm)
                elif self.scenario == "caution" and (deg <= 30 or deg >= 330):
                    dist_mm = 450  # 45 cm (Caution Zone 30-60 cm)
                elif self.scenario == "dynamic":
                    phase = (self._step // 10) % 3
                    if phase == 1 and (deg <= 30 or deg >= 330):
                        dist_mm = 450
                    elif phase == 2 and (deg <= 30 or deg >= 330):
                        dist_mm = 200
                
                points.append(MockScanPoint(angle_deg=float(deg), dist_mm=dist_mm))
            
            yield MockScan(valid_points=points)
            time.sleep(0.1)

# --- Safety Evaluation Logic ---
def is_in_front_sector(angle_deg):
    """Check if the angle falls within the front pathway sector."""
    return (FRONT_MIN_1 <= angle_deg <= FRONT_MAX_1) or (FRONT_MIN_2 <= angle_deg <= FRONT_MAX_2)

def evaluate_safety(scan_points):
    """
    Evaluates scan points in the front sector and returns:
    - safety_clear (bool)
    - pwm_percent (int)
    - closest_dist_cm (float)
    - zone (str)
    """
    closest_dist_mm = float('inf')

    for p in scan_points:
        if is_in_front_sector(p.angle_deg):
            if p.dist_mm > 0:
                if p.dist_mm < closest_dist_mm:
                    closest_dist_mm = p.dist_mm

    if closest_dist_mm == float('inf'):
        closest_dist_cm = 999.0
    else:
        closest_dist_cm = closest_dist_mm / 10.0  # Convert mm to cm

    # Zone mapping
    if closest_dist_cm <= CRITICAL_THRESHOLD_CM:
        return False, 0, closest_dist_cm, "CRITICAL (Stop)"
    elif closest_dist_cm <= CAUTION_THRESHOLD_CM:
        return True, 30, closest_dist_cm, "CAUTION (Slow)"
    else:
        return True, 60, closest_dist_cm, "CLEAR (Normal)"

# --- Main Program ---
def main():
    parser = argparse.ArgumentParser(description="YDLIDAR X3 Obstacle Detection & Safety Module.")
    parser.add_argument('--simulate', action='store_true',
                        help='Run standalone simulator instead of real hardware.')
    parser.add_argument('--scenario', type=str, default='dynamic',
                        choices=['clear', 'caution', 'critical', 'dynamic'],
                        help='Simulation scenario when --simulate is active.')
    args = parser.parse_args()

    if args.simulate:
        print(f"\n[INFO] Running Standalone Simulator with scenario: '{args.scenario}'")
        lidar = MockLidarSimulator(scenario=args.scenario)
    else:
        try:
            from lds2d import Lidar
            print(f"\n[INFO] Connecting to real YDLIDAR X3 on port {LIDAR_PORT}...")
            lidar = Lidar.open("YDLIDAR-X3", LIDAR_PORT)
        except ImportError:
            print("[ERROR] 'lds2d' library not found. Run 'pip install lds2d' or use '--simulate'.")
            return
        except Exception as e:
            print(f"[ERROR] Failed to open LiDAR: {e}")
            print("[HINT] Make sure your user is in the 'dialout' group: sudo usermod -aG dialout $USER")
            return

    try:
        with lidar as dev:
            print("[INFO] LiDAR active. Monitoring front sector for obstacles...")
            for scan in dev.scans():
                if not scan or not scan.valid_points:
                    continue

                safety_clear, pwm, dist_cm, zone = evaluate_safety(scan.valid_points)

                print(f"Closest Front Obstacle: {dist_cm:.1f} cm | Zone: {zone} | Safety_Clear: {safety_clear} | Motor PWM: {pwm}%")

                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")
    finally:
        print("[INFO] Exiting obstacle detection module.")

if __name__ == "__main__":
    main()
