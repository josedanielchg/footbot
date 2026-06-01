from glob import glob
from setuptools import find_packages, setup

package_name = 'footbot_soccer_vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/models', ['models/README.md']),
        ('share/' + package_name + '/models/weights', glob('models/weights/.gitkeep')),
        ('share/' + package_name + '/datasets', ['datasets/README.md']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='josedanielchg',
    maintainer_email='j.daniel.chg@gmail.com',
    description='YOLO-based soccer vision package for the FootBot simulation.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'opponent_detector = footbot_soccer_vision.nodes.opponent_detector_node:main',
            'goal_detector = footbot_soccer_vision.nodes.goal_detector_node:main',
            'image_capture = footbot_soccer_vision.nodes.image_capture_node:main',
        ],
    },
)
