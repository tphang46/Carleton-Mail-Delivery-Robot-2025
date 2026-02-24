import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
import time
import ollama
from tools.csv_parser import loadConfig


class IntersectionDetectionUnit(Node):
    '''
    The Node in charge of intersection detection.

    @Subscribers:
    - Subscribes to /lidar_data for information about nearby walls

    @Publishers:
    - Publishes intersection detection data to /intersection_detection
    '''

    def __init__(self):
        '''
        The constructor for the node.
        Defines the necessary publishers and subscribers.
        '''
        super().__init__('intersection_detection_unit')

        self.config = loadConfig()

        self.lidar_data_sub = self.create_subscription(String, 'lidar_data', self.lidar_data_callback, 10)
        self.odometry_sub = self.create_subscription(Odometry, 'odom', self.odometry_callback, qos_profile=QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            depth=10
        ))

        self.intersection_detection_publisher = self.create_publisher(String, 'intersection_detection', 10)
        self.intersection_detection_timer = self.create_timer(0.5, self.update_intersection_detection)

        self.true_msg = String()
        self.true_msg.data = 'TRUE'
        self.false_msg = String()
        self.false_msg.data = 'FALSE'

        self.lidar_indicates_intersection = False
        self.odom_x_snapshot = None
        self.odom_y_snapshot = None
        self.odom_x = None
        self.odom_y = None
        self.can_send_intersection_update = False
        self.ai_intersection_decision = None
        self.last_lidar_snapshot = None
        self.llm_response_latencies = []

    def lidar_data_callback(self, data):
        '''
        The callback for /lidar_data.
        Reads information from the lidar sensor.
        '''
        lidar_data = str(data.data)

        split_data = lidar_data.split(":")

        # waiting for the lidar to calibrate
        if split_data[0] == "-1" and split_data[1] == "-1":
            return

        if ((split_data[2] == "-1" and split_data[3] == "-1")
                or (split_data[2] == "-1" and split_data[4] == "-1")
                or (split_data[3] == "-1" and split_data[4] == "-1")):
            self.lidar_indicates_intersection = True
        else:
            self.lidar_indicates_intersection = False

        self.last_lidar_snapshot = lidar_data
        self.can_send_intersection_update = True

    def odometry_callback(self, data):
        self.odom_x = data.pose.pose.position.x
        self.odom_y = data.pose.pose.position.y

    def update_intersection_detection(self):
        '''
        The timer callback. Updates the internal state of this node and sends
        updates to /navigation when necessary
        '''
        if self.odom_x_snapshot is not None and self.odom_y_snapshot is not None:
            starting_location = [self.odom_x_snapshot, self.odom_y_snapshot]
            current_location = [self.odom_x, self.odom_y]
            # self.get_logger().info(str(math.dist(starting_location, current_location)))

        if not self.can_send_intersection_update:
            return

        self.can_send_intersection_update = False
        fallback_decision = 'TRUE' if self.lidar_indicates_intersection else 'FALSE'
        final_decision = fallback_decision

        try:
            ai_decision = self.query_ollama(self.last_lidar_snapshot, fallback_decision)
            self.get_logger().info(f"AI Decision: {ai_decision}")

            if ai_decision in ['TRUE', 'FALSE']:
                final_decision = ai_decision
            else:
                self.get_logger().info(
                    "Ollama returned invalid intersection decision, falling back to lidar rule."
                )
        except Exception as e:
            self.get_logger().warn(
                f"Ollama query failed: {e}. Falling back to lidar rule."
            )

        self.ai_intersection_decision = final_decision
        if final_decision == 'TRUE':
            self.intersection_detection_publisher.publish(self.true_msg)
        else:
            self.intersection_detection_publisher.publish(self.false_msg)

    def _token_to_path_state(self, token: str) -> str:
        return "OPEN" if token == "-1" else "BLOCKED"

    def _build_lidar_semantics(self, lidar_data: str):
        split_data = lidar_data.split(":")
        if len(split_data) < 5:
            return None

        # lidar_sensor format: feedback:angle:right:left:front
        right = self._token_to_path_state(split_data[2])
        left = self._token_to_path_state(split_data[3])
        front = self._token_to_path_state(split_data[4])
        open_paths = sum(
            value == "OPEN" for value in [left, front, right]
        )

        return {
            "left": left,
            "front": front,
            "right": right,
            "open_paths": open_paths
        }

    def query_ollama(self, lidar_data: str, fallback_decision: str):
        start = time.perf_counter()
        semantics = self._build_lidar_semantics(lidar_data)
        odom_x = "unknown" if self.odom_x is None else f"{self.odom_x:.3f}"
        odom_y = "unknown" if self.odom_y is None else f"{self.odom_y:.3f}"

        if semantics is None:
            semantic_block = "Lidar semantics unavailable (malformed payload)."
        else:
            semantic_block = (
                f"Left: {semantics['left']}\n"
                f"Front: {semantics['front']}\n"
                f"Right: {semantics['right']}\n"
                f"Open paths among left/front/right: {semantics['open_paths']}"
            )

        prompt = f"""
        You are deciding whether the robot is currently at an intersection.
        Current position: x={odom_x}, y={odom_y}
        Interpreted lidar:
        {semantic_block}
        Raw lidar payload: {lidar_data}
        Deterministic fallback decision: {fallback_decision}
        Output must be exactly one token:
        - TRUE
        - FALSE
        """

        response = ollama.generate(
            model="gemma2:2b-instruct-q4_0",
            prompt=prompt
        )

        elapsed = time.perf_counter() - start
        self.llm_response_latencies.append(elapsed)
        decision = response["response"].strip().split()[0].upper()
        self.get_logger().info(f"Ollama decision: {decision} (latency={elapsed:.3f}s)")
        return decision

    def get_llm_response_latencies(self):
        return list(self.llm_response_latencies)


def main():
    rclpy.init()
    intersection_detection_unit = IntersectionDetectionUnit()
    rclpy.spin(intersection_detection_unit)


if __name__ == '__main__':
    main()
