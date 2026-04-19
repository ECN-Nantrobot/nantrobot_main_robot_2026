from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'motor_control_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*')))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='chiara',
    maintainer_email='s7687956@studenti.unige.it',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'motor_node = motor_control_pkg.motor_node:main',
            'interface_node = motor_control_pkg.interface_node:main',
            'move = motor_control_pkg.move:main',
            'odom_node_sim = motor_control_pkg.odom_node_sim:main'
        ],
    },
)
