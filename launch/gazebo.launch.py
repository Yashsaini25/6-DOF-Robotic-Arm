from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    TimerAction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
import os


def generate_launch_description():
    pkg_share = FindPackageShare('six_dof_robot_description')

    robot_file = PathJoinSubstitution([
        pkg_share, 'urdf', 'robot_2.urdf'
    ])

    robot_description = ParameterValue(
        Command(['xacro ', robot_file]),
        value_type=str,
    )

    controller_file = PathJoinSubstitution([
        pkg_share, 'config', 'controllers.yaml'
    ])

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
        }],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            '/opt/ros/lyrical/share/ros_gz_sim/launch/gz_sim.launch.py'
        ),
        launch_arguments={
            'gz_args': '-r empty.sdf',
        }.items(),
    )
    
    clock_bridge = Node(
	package = 'ros_gz_bridge',
	executable = 'parameter_bridge',
	arguments = [
		'/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
	],
	output = 'screen',
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-world', 'empty',
            '-file', os.path.expanduser(
                '~/robot_ws/install/six_dof_robot_description/share/'
                'six_dof_robot_description/urdf/robot_2.urdf'
            ),
            '-name', 'robotic_arm',
            '-z', '0.05',
        ],
        output='screen',
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
        ],
        output='screen',
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'arm_controller',
            '--controller-manager', '/controller_manager',
	    '--param-file',
	    controller_file,
        ],
        output='screen',
    )

    return LaunchDescription([
        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=os.path.expanduser(
                '~/robot_ws/install/six_dof_robot_description/share'
            ),
        ),
        robot_state_publisher,
        gazebo,
	clock_bridge,
        TimerAction(period=5.0, actions=[spawn_robot]),
        TimerAction(
            period=10.0,
            actions=[joint_state_broadcaster_spawner],
        ),
        TimerAction(
            period=12.0,
            actions=[arm_controller_spawner],
        ),
    ])
