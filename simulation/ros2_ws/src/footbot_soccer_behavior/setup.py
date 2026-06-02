from setuptools import find_packages, setup

package_name = 'footbot_soccer_behavior'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/ball_control.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='josedanielchg',
    maintainer_email='j.daniel.chg@gmail.com',
    description='Deterministic soccer behavior nodes for the FootBot simulation.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'ball_state_estimator = footbot_soccer_behavior.state_estimation.ball_state_estimator_node:main',
            'ball_control_fsm = footbot_soccer_behavior.fsm.ball_control_fsm_node:main',
        ],
    },
)
