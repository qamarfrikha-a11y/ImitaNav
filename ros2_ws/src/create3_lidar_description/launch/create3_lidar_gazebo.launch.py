import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command

def generate_launch_description():
    pkg_share = get_package_share_directory('create3_lidar_description')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')
    xacro_file = os.path.join(pkg_share, 'urdf', 'create3_with_lidar.urdf.xacro')

    robot_description = Command(['xacro ', xacro_file])

    # Lance gzserver + gzclient via les launch files officiels (gère mieux le timing)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gazebo.launch.py')
        )
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'create3_lidar'],
        output='screen'
    )

    # Attend 5 secondes que Gazebo soit complètement chargé avant de spawn le robot
    delayed_spawn = TimerAction(period=5.0, actions=[spawn_entity])

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        delayed_spawn
    ])
