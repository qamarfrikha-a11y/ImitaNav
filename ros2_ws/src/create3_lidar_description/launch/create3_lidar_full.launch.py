from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution

def generate_launch_description():
    pkg_gazebo_bringup = get_package_share_directory('irobot_create_gazebo_bringup')
    pkg_lidar_description = get_package_share_directory('create3_lidar_description')

    gazebo_launch_file = PathJoinSubstitution([pkg_gazebo_bringup, 'launch', 'gazebo.launch.py'])
    spawn_launch_file = PathJoinSubstitution([pkg_lidar_description, 'launch', 'create3_lidar_spawn.launch.py'])
    world_file = PathJoinSubstitution([pkg_lidar_description, 'worlds', 'obstacles.world'])

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([gazebo_launch_file]),
        launch_arguments={'world_path': world_file}.items()
    )
    spawn = IncludeLaunchDescription(PythonLaunchDescriptionSource([spawn_launch_file]))

    return LaunchDescription([gazebo, spawn])
