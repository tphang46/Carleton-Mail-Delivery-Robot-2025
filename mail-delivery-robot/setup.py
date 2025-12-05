from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'mail-delivery-robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(where='src'),  
    package_dir={'': 'src'},             
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='create3',
    maintainer_email='deniscengu@cmail.carleton.ca',
    description='Mail delivery robot package',
    license='Apache-2.0',
    tests_require=['pytest'],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('lib', package_name, 'config'), glob('src/config/*.csv')),
    ],
    entry_points={
        'console_scripts': [
            # Sensor nodes
            'beacon_sensor = sensors.beacon_sensor:main',
            'bumper_sensor = sensors.bumper_sensor:main',
            'lidar_sensor = sensors.lidar_sensor:main',
            'navigation_unit = sensors.navigation_unit:main',
            'navigation_unit_AI = sensors.navigation_unit_AI:main',
            'intersection_detection_unit = sensors.intersection_detection_unit:main',
            'battery_monitor = sensors.battery_monitor:main',

            # Layer nodes
            'avoidance_layer = layers.avoidance_layer:main',
            'docking_layer = layers.docking_layer:main',
            'travel_layer = layers.travel_layer:main',
            'turning_layer = layers.turning_layer:main',

            # Communication nodes
            'client = communication.client:main',
            'music_player = communication.music_player:main',

            # Control nodes
            'captain = control.captain:main',
            'action_translator = control.action_translator:main',

            # Tools / Utilities
            'logger = tools.logger:main',
            'csv_parser = tools.csv_parser:main',
            'nav_parser = tools.nav_parser:main',
            'map = tools.map:main',

            # Tests
            'travel_analyzer = tests.travel_analyzer:main',
        ],
    },
)
