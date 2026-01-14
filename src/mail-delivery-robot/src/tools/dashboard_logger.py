import os
import time
import re
from datetime import datetime
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import BatteryState
from irobot_create_msgs.msg import DockStatus
import math
from statistics import stdev, mean
from sensor_msgs.msg import LaserScan
from tools.csv_parser import loadConfig

# Base Metric Class
class Metric:
    topic_name = None        # ROS topic to subscribe to
    topic_type = None        # ROS message type
    listen_qos = 10

    def start(self):
        pass

    def update(self, msg):
        pass

    def end(self):
        pass

    def serialize(self):
        return {}

# Battery Metric
class BatteryMetric(Metric):
    topic_name = '/battery_state'
    topic_type = BatteryState

    def __init__(self):
        self.level = None
        self.voltage = None
        self.temperature = None
        self.start_level = None
        self.end_level = None
        self.used = None

    def update(self, msg: BatteryState):
        self.level = msg.percentage * 100
        self.voltage = msg.voltage
        self.temperature = msg.temperature

        if self.start_level is None:
            self.start_level = self.level

    def end(self):
        self.end_level = self.level
        if self.start_level is not None and self.end_level is not None:
            self.used = self.start_level - self.end_level

    def serialize(self):
        return {
            "battery_start": round(self.start_level, 2) if self.start_level else None,
            "battery_end": round(self.end_level, 2) if self.end_level else None,
            "battery_used": round(self.used, 2) if self.used else None,
            "voltage_level": round(self.voltage, 2) if self.voltage else None,
            "temperature_level": round(self.temperature, 2) if self.temperature else None
        }

# Wall Following Metric
class WallFollowMetric(Metric):
    topic_name = None  # Doesn't subscribe to a topic
    topic_type = None

    def __init__(self, log_path):
        self.log_path = log_path
        self.wall_time = "N/A"

    def end(self):
        if not os.path.exists(self.log_path):
            return
        with open(self.log_path, 'r') as f:
            for line in reversed(f.readlines()):
                match = re.search(r"Total wall-following time:\s*([\d.]+)s", line)
                if match:
                    self.wall_time = round(float(match.group(1)), 2)
                    break

    def serialize(self):
        return {"wall_follow_time": self.wall_time}

# Delivery Time Metric
class DeliveryTimeMetric(Metric):
    topic_name = None
    topic_type = None

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    def start(self):
        self.start_time = time.perf_counter()

    def end(self):
        self.end_time = time.perf_counter()
        self.elapsed = round(self.end_time - self.start_time, 2)

    def serialize(self):
        return {"delivery_time": self.elapsed}

# Docking
class Dock(Metric):
    topic_name = '/dock_status'
    topic_type = DockStatus

    def __init__(self):
        self.docked = False

    def update(self, msg: DockStatus):
        self.docked = msg.is_docked

    def serialize(self):
        return {"docked": self.docked}

# Metrics Manager
class MetricsManager:
    def __init__(self):
        self.metrics = []

    def register_metric(self, metric):
        self.metrics.append(metric)
        return metric

    def start_all(self):
        for m in self.metrics:
            m.start()

    def update(self, msg, metric_type):
        for m in self.metrics:
            if isinstance(m, metric_type):
                m.update(msg)

    def end_all(self):
        for m in self.metrics:
            m.end()

    def collect(self):
        data = {}
        for m in self.metrics:
            data.update(m.serialize())
        return data

# Logger Class
class FileLogger:
    def __init__(self, log_dir):
        self.log_dir = os.path.abspath(log_dir)
        self.declare_parameter('log_dir', './tools/logs')
        self.log_dir = os.path.abspath(self.get_parameter('log_dir').value)
        os.makedirs(self.log_dir, exist_ok=True)
        self.runs_dir = os.path.join(self.log_dir, "runs")
        os.makedirs(self.runs_dir, exist_ok=True)
        self.wall_log_path = os.path.join(self.log_dir, "robot_log_wallFollowing.txt")
        self.wall_log_file = open(self.wall_log_path, "a")

    def write_log(self, tag, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.wall_log_file.write(f"[{timestamp}] [{tag}] {message}\n")
        self.wall_log_file.flush()

    def write_run_file(self, metrics_data):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join(self.runs_dir, f"run_{timestamp}.txt")
        with open(filepath, "w") as f:
            for k, v in metrics_data.items():
                f.write(f"{k}={v}\n")

    def close(self):
        self.wall_log_file.close()
        open(self.wall_log_path, 'w').close()

# Lidar distance class
class LidarDistanceMetric(Metric):
    topic_name = "/scan"
    topic_type = LaserScan
    listen_qos = 10

    def __init__(self):
        self.config = loadConfig()

        self.left_distances = []
        self.right_distances = []
        self.front_distances = []

        self.wall_distances = []
        self.wall_angles = []

    def update(self, scan: LaserScan):
        result = self.calculate(scan)
        if result is None:
            return

        wall_dist, wall_angle, right, left, front = result

        if right != -1:
            self.right_distances.append(right)
        if left != -1:
            self.left_distances.append(left)
        if front != -1:
            self.front_distances.append(front)
        if wall_dist != -1:
            self.wall_distances.append(wall_dist)
            self.wall_angles.append(wall_angle)

    def calculate(self, scan):
        count = len(scan.ranges)
        angle = 0

        min_left = self.config["LARGE_DEFAULT_DISTANCE"]
        min_right = self.config["LARGE_DEFAULT_DISTANCE"]
        min_front = self.config["LARGE_DEFAULT_DISTANCE"]
        min_distance = self.config["LARGE_DEFAULT_DISTANCE"]

        for i in range(count):
            degree = math.degrees(scan.angle_min + scan.angle_increment * i)
            cur = scan.ranges[i]

            if cur == math.inf or cur <= 0.0:
                continue

            if (self.config["WALL_FOLLOW_MIN_ANGLE"] <= degree <= self.config["WALL_FOLLOW_MAX_ANGLE"]
                    and cur < min_distance):
                min_distance = cur
                angle = degree

            if (degree <= self.config["FRONT_MIN_ANGLE"] or degree >= self.config["FRONT_MAX_ANGLE"]) and cur < min_front:
                min_front = cur
            elif self.config["RIGHT_MIN_ANGLE"] <= degree < self.config["RIGHT_MAX_ANGLE"] and cur < min_right:
                min_right = cur
            elif self.config["LEFT_MIN_ANGLE"] < degree <= self.config["LEFT_MAX_ANGLE"] and cur < min_left:
                min_left = cur

        return min_distance, angle - 90, min_right, min_left, min_front

    def end(self):
        pass

    def serialize(self):
        def safe_avg(data):
            return round(mean(data), 2) if data else None

        def safe_min(data):
            return round(min(data), 2) if data else None

        return {
            "lidar_front_avg": safe_avg(self.front_distances),
            "lidar_front_min": safe_min(self.front_distances),

            "lidar_left_avg": safe_avg(self.left_distances),
            "lidar_left_min": safe_min(self.left_distances),

            "lidar_right_avg": safe_avg(self.right_distances),
            "lidar_right_min": safe_min(self.right_distances),

            "wall_distance_avg": safe_avg(self.wall_distances),
            "wall_angle_avg": safe_avg(self.wall_angles),
        }

# Main Node
class RobotGeneralLogger(Node):
    def __init__(self):
        super().__init__('general_logger')
        self.declare_parameter('log_dir', './tools/logs')
        log_dir = self.get_parameter('log_dir').value

        # Initialize logger
        self.logger = FileLogger(log_dir)
        self.logger.write_log("SYSTEM", f"Logging all data to {self.logger.wall_log_path}")

        # Initialize metrics
        self.metrics_manager = MetricsManager()
        self.battery_metric = self.metrics_manager.register_metric(BatteryMetric())
        self.wall_metric = self.metrics_manager.register_metric(WallFollowMetric(self.logger.wall_log_path))
        self.delivery_metric = self.metrics_manager.register_metric(DeliveryTimeMetric())
        self.lidar_metric = self.metrics_manager.register_metric(LidarDistanceMetric())
        self.dock_metric = self.metrics_manager.register_metric(Dock())

        self.metrics_manager.start_all()
        self.should_shutdown = False

        # Automatically subscribe to metrics with a topic
        for metric in self.metrics_manager.metrics:
            if getattr(metric, "topic_name", None) and getattr(metric, "topic_type", None):
                self.create_subscription(
                    metric.topic_type,
                    metric.topic_name,
                    lambda msg, mtype=type(metric): self.metrics_manager.update(msg, mtype),
                    getattr(metric, "listen_qos", 10)
                )

        self.get_logger().info("RobotGeneralLogger started.")

    def end_trip(self):
        self.metrics_manager.end_all()
        data = self.metrics_manager.collect()
        # Add trip start/end timestamps
        data["trip_start_time"] = self.delivery_metric.start_time
        data["trip_end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.write_run_file(data)
        self.logger.close()
        self.get_logger().info("Trip logging complete.")

def main(args=None):
    rclpy.init(args=args)
    node = RobotGeneralLogger()
    try:
        while rclpy.ok() and not node.should_shutdown:
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.dock_metric.docked:
                node.get_logger().info("Docking detected, ending trip...")
                node.should_shutdown = True
                node.end_trip()
    except KeyboardInterrupt:
        node.get_logger().info("KeyboardInterrupt detected, ending trip...")
        node.end_trip()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
