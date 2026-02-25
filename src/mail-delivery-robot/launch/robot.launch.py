from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node


def generate_launch_description():
    enable_metrics = LaunchConfiguration('enable_metrics')
    use_ai_lidar = LaunchConfiguration('use_ai_lidar')
    use_ai_navigation = LaunchConfiguration('use_ai_navigation')
    use_ai_avoidance = LaunchConfiguration('use_ai_avoidance')
    use_ai_intersection = LaunchConfiguration('use_ai_intersection')

    nodes = [
        Node(package='mail-delivery-robot', executable='captain', name='captain'),
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            parameters=[{
                'channel_type': 'serial',
                'serial_port': '/dev/ttyUSB0',
                'serial_baudrate': 115200,
                'frame_id': 'laser',
                'inverted': False,
                'angle_compensate': True
            }],
            output='screen'
        ),
        # Lidar nodes - standard vs AI
        Node(
            package='mail-delivery-robot',
            executable='lidar_sensor',
            name='lidar_sensor',
            condition=UnlessCondition(use_ai_lidar)
        ),
        Node(
            package='mail-delivery-robot',
            executable='lidar_sensor_AI',
            name='lidar_sensor_AI',
            condition=IfCondition(use_ai_lidar)
        ),

        # Navigation nodes - standard vs AI
        Node(
            package='mail-delivery-robot',
            executable='navigation_unit',
            name='navigation_unit',
            condition=UnlessCondition(use_ai_navigation)
        ),
        Node(
            package='mail-delivery-robot',
            executable='navigation_unit_AI',
            name='navigation_unit_AI',
            condition=IfCondition(use_ai_navigation)
        ),

        # Avoidance nodes - standard vs AI
        Node(
            package='mail-delivery-robot',
            executable='avoidance_layer',
            name='avoidance_layer',
            condition=UnlessCondition(use_ai_avoidance)
        ),
        Node(
            package='mail-delivery-robot',
            executable='avoidance_layer_AI',
            name='avoidance_layer_AI',
            condition=IfCondition(use_ai_avoidance)
        ),

        # Common nodes (always run)
        Node(package='mail-delivery-robot', executable='bumper_sensor', name='bumper_sensor'),
        Node(package='mail-delivery-robot', executable='beacon_sensor', name='beacon_sensor'),
        Node(
            package='mail-delivery-robot',
            executable='intersection_detection_unit',
            name='intersection_detection_unit',
            condition=UnlessCondition(use_ai_intersection)
        ),
        Node(
            package='mail-delivery-robot',
            executable='intersection_detection_unit_AI',
            name='intersection_detection_unit_AI',
            condition=IfCondition(use_ai_intersection)
        ),
        Node(package='mail-delivery-robot', executable='docking_layer', name='docking_layer'),
        Node(package='mail-delivery-robot', executable='turning_layer', name='turning_layer'),
        Node(package='mail-delivery-robot', executable='travel_layer', name='travel_layer'),
        Node(package='mail-delivery-robot', executable='logger', name='general_logger'),
        Node(package='mail-delivery-robot', executable='dashboard_logger', name='dashboard_logger'),

        # Optional: Metric Analyzer Node
        Node(
            package='mail-delivery-robot',
            executable='metric_analyzer',
            name='metric_analyzer',
            condition=IfCondition(enable_metrics)
        )
    ]

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_ai_lidar',
            default_value='false',
            description='Use AI version of lidar_sensor'
        ),
        DeclareLaunchArgument(
            'use_ai_navigation',
            default_value='false',
            description='Use AI version of navigation_unit'
        ),
        DeclareLaunchArgument(
            'enable_metrics',
            default_value='false',
            description='Enable the metric analyzer node'
        ),
        DeclareLaunchArgument(
            'use_ai_avoidance',
            default_value='false',
            description='Use AI version of avoidance_layer'
        ),
        DeclareLaunchArgument(
            'use_ai_intersection',
            default_value='false',
            description='Use AI version of intersection_detection_unit'
        ),
        *nodes
    ])
