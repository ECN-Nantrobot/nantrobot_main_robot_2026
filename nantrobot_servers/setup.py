from setuptools import find_packages, setup
from glob import glob

package_name = 'nantrobot_servers'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jbenoit',
    maintainer_email='jbenoit.grimaldi+github@gmail.com',
    description='TODO: Package description',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'gpio_read_action_server = nantrobot_servers.gpio_read_action_server:main',
            'gpio_write_action_server = nantrobot_servers.gpio_write_action_server:main',
            'gpio_read_action_server_emulator = nantrobot_servers.gpio_read_action_server_emulator:main',
            'gpio_write_action_server_emulator = nantrobot_servers.gpio_write_action_server_emulator:main',
            'gpio_emulator_ui = nantrobot_servers.gpio_emulator_ui:main',
        ],
    },
)
