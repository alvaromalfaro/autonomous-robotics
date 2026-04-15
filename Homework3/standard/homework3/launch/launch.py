import os
import launch
from launch_ros.actions import Node
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    package_dir = get_package_share_directory('homework3')
    controller = Node(
        package='homework3',
        executable='controller',
    )

    return LaunchDescription([
        controller,
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='sim'
        ),
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=controller,
                on_exit=[launch.actions.EmitEvent(event=launch.events.Shutdown())],
            )
        )
    ])