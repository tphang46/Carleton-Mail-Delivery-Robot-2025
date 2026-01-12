import os
import time
import re
from datetime import datetime, timedelta

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

from sensor_msgs.msg import BatteryState
from irobot_create_msgs.msg import DockStatus


class RobotGeneralLogger(Node):
    def __init__(self):
        super().__init__('general_logger')

        self.declare_parameter('log_dir', './tools/logs')
        self.log_dir = os.path.abspath(self.get_parameter('log_dir').value)
        os.makedirs(self.log_dir, exist_ok=True)
        self.runs_dir = os.path.join(self.log_dir, "runs")
        os.makedirs(self.runs_dir, exist_ok=True)
        self.wall_log_path = os.path.join(self.log_dir, "robot_log_wallFollowing.txt")
        self.wall_log_file = open(self.wall_log_path, "a")
        self.write_log("SYSTEM", f"Logging all data to {self.wall_log_path}")

        # --- Trip timing ---
        self.trip_start_time = time.perf_counter()
        self.trip_start_timestamp = datetime.now()

        # --- Battery info ---
        self.battery = {
            'level': None,
            'voltage': None,
            'temperature': None
        }
        self.battery_start = None
        self.battery_end = None
        self.battery_used = None

        self.should_shutdown = False

        # --- Subscriptions ---
        qos = QoSProfile(depth=10)
        self.create_subscription(
            BatteryState, '/battery_state', self.battery_callback, qos
        )
        self.create_subscription(
            DockStatus, '/dock_status', self.dock_status_callback, 10
        )
        self.get_logger().info("RobotGeneralLogger started.")

    def write_log(self, tag, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.wall_log_file.write(f"[{timestamp}] [{tag}] {message}\n")
        self.wall_log_file.flush()

    def battery_callback(self, msg):
        self.battery['level'] = msg.percentage * 100
        self.battery['voltage'] = msg.voltage
        self.battery['temperature'] = msg.temperature

        if self.battery_start is None:
            self.battery_start = self.battery['level']
            self.get_logger().info(
                f"Battery at trip start: {self.battery_start:.2f}%"
            )

    def dock_status_callback(self, msg: DockStatus):
        if msg.is_docked and not self.should_shutdown:
            self.get_logger().info("Docking detected, ending trip...")
            self.end_trip()
            self.should_shutdown = True

    def get_wall_follow_time(self):
        if not os.path.exists(self.wall_log_path):
            return "N/A"
        with open(self.wall_log_path, 'r') as f:
            for line in reversed(f.readlines()):
                match = re.search(r"Total wall-following time:\s*([\d.]+)s", line)
                if match:
                    return f"{match.group(1)} s"
        return "N/A"

    def end_trip(self):
        self.trip_end_timestamp = datetime.now()
        delivery_time_sec = time.perf_counter() - self.trip_start_time

        self.battery_end = self.battery['level']
        self.battery_used = (
            self.battery_start - self.battery_end
            if self.battery_start is not None and self.battery_end is not None
            else None
        )

        wall_time = self.get_wall_follow_time()
        self.write_run_file(wall_time, delivery_time_sec)
        self.wall_log_file.close()
        open(self.wall_log_path, 'w').close()
        self.get_logger().info("Trip logging complete.")

    def write_run_file(self, wall_time, delivery_time):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join(self.runs_dir, f"run_{timestamp}.txt")
        with open(filepath, "w") as f:
            f.write(f"battery_start={self.battery_start}\n")
            f.write(f"battery_end={self.battery_end}\n")
            f.write(f"battery_used={self.battery_used}\n")
            f.write(f"delivery_time={delivery_time:.2f}\n")
            f.write(f"wall_follow_time={wall_time}\n")
            f.write(f"voltage_level={self.battery['voltage']}\n")
            f.write(f"temperature_level={self.battery['temperature']}\n")
            f.write(f"trip_start_time={self.trip_start_timestamp}\n")
            f.write(f"trip_end_time={self.trip_end_timestamp}\n")

def main(args=None):
    rclpy.init(args=args)
    node = RobotGeneralLogger()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.should_shutdown:
                break
    except KeyboardInterrupt:
        node.get_logger().info("KeyboardInterrupt detected, ending trip...")
        node.end_trip()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
