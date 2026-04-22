#!/usr/bin/env python3
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional

import rclpy
from rclpy.node import Node
from rclpy.client import Client

from geometry_msgs.msg import Twist, Pose2D
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan

from flatland_msgs.msg import Collisions
from flatland_msgs.srv import MoveModel, SpawnModel

#                         i ≈ 3N/4
#                        angle = +π/2
#                             LEFT
#                              ^
#                              |
#                              |
# i = 0                        |                         i = N/2
# angle = -π                   |                         angle = 0
# BACK         <-------------- R ------------->  FRONT
#                              |
#                              |
#                              v
#                            RIGHT
#                        angle = -π/2
#                         i ≈ N/4
#
#
# i = N-1  → angle ≈ +π  → BACK


@dataclass(frozen=True)
class ObstacleSpec:
    name: str
    x: float
    y: float
    theta: float = 0.0


@dataclass
class RobotPose:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


@dataclass(frozen=True)
class ControllerConfig:
    # Robot motion
    linear_speed: float = 1.0
    min_distance: float = 0.8
    random_rotation_iterations: int = 10

    # Robot initial pose
    robot_initial_x: float = -3.0
    robot_initial_y: float = -1.5
    robot_initial_theta: float = 0.0

    # Obstacle detection
    obstacle_detection_distance: float = 1.0
    obstacle_match_tolerance: float = 0.20
    obstacle_hidden_x: float = -100.0
    obstacle_hidden_y: float = -100.0

    # Laser processing
    mean_window: int = 4

    # Obstacle model
    obstacle_model_path: str = "cylinder_obstacle.model.yaml"


class Controller(Node):

    def __init__(self) -> None:
        super().__init__("controller")

        # ---------------------------
        # Centralized configuration
        # ---------------------------
        self.config: ControllerConfig = ControllerConfig()

        self.obstacles: List[ObstacleSpec] = [
            ObstacleSpec("obstacle1", -2.0, -1.5, 0.0),
            ObstacleSpec("obstacle2", -2.0,  1.5, 0.0),
            ObstacleSpec("obstacle3",  2.0, -1.5, 0.0),
            ObstacleSpec("obstacle4",  2.0,  1.5, 0.0),
        ]

        # ---------------------------
        # Runtime state
        # ---------------------------
        self.pose: RobotPose = RobotPose(
            x=self.config.robot_initial_x,
            y=self.config.robot_initial_y,
            theta=self.config.robot_initial_theta,
        )
        self.rotation_iterations_left: int = 0
        self.angular_speed: float = 0.0
        self.active_obstacles: Dict[str, ObstacleSpec] = {
            obstacle.name: obstacle for obstacle in self.obstacles
        }

        # ---------------------------
        # ROS interfaces
        # ---------------------------
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 1)

        self.create_subscription(
            LaserScan, "/static_laser", self.lidar_callback, 1)
        self.create_subscription(
            Collisions, "/collisions", self.collision_callback, 1)
        self.create_subscription(Odometry, "/odom", self.odom_callback, 10)

        self.move_client: Client = self.create_client(MoveModel, "/move_model")
        self.spawn_client: Client = self.create_client(
            SpawnModel, "/spawn_model")

        self.wait_for_services()
        self.spawn_all_obstacles()

    # ---------------------------
    # Initialization helpers
    # ---------------------------
    def wait_for_services(self) -> None:
        self.move_client.wait_for_service()
        self.spawn_client.wait_for_service()

    def spawn_all_obstacles(self) -> None:
        for obstacle in self.obstacles:
            self.spawn_obstacle(obstacle)

    # ---------------------------
    # ROS service helpers
    # ---------------------------
    def spawn_obstacle(self, obstacle: ObstacleSpec) -> None:
        request = SpawnModel.Request()
        request.name = obstacle.name
        request.yaml_path = self.config.obstacle_model_path
        request.pose = Pose2D(x=obstacle.x, y=obstacle.y, theta=obstacle.theta)
        self.spawn_client.call_async(request)

        self.get_logger().info(
            f"Spawned obstacle {obstacle.name} at ({obstacle.x:.2f}, {obstacle.y:.2f})"
        )

    def move_model(self, name: str, x: float, y: float, theta: float) -> None:
        request = MoveModel.Request()
        request.name = name
        request.pose = Pose2D(x=x, y=y, theta=theta)
        self.move_client.call_async(request)

    def remove_obstacle(self, name: str) -> None:
        if name not in self.active_obstacles:
            return

        self.move_model(
            name,
            self.config.obstacle_hidden_x,
            self.config.obstacle_hidden_y,
            0.0,
        )
        del self.active_obstacles[name]
        self.get_logger().info(f"Removed obstacle {name}")

    # ---------------------------
    # Motion helpers
    # ---------------------------
    def publish_speed(self, linear: float, angular: float) -> None:
        message = Twist()
        message.linear.x = linear
        message.angular.z = angular
        self.cmd_pub.publish(message)

    def start_random_rotation(self) -> None:
        self.angular_speed = random.uniform(-math.pi, math.pi)
        self.rotation_iterations_left = self.config.random_rotation_iterations

    # ---------------------------
    # Geometry helpers
    # ---------------------------
    def normalize_angle(self, angle: float) -> float:
        return math.atan2(math.sin(angle), math.cos(angle))

    def quaternion_to_yaw(self, q) -> float:
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    # TODO: add as many methods as needed

    # ---------------------------
    # Laser helpers
    # ---------------------------
    def get_mean_range(
        self,
        ranges: List[float],
        center_idx: int,
        window: Optional[int] = None,
    ) -> float:
        effective_window: int = self.config.mean_window if window is None else window
        n: int = len(ranges)
        values: List[float] = []

        for i in range(center_idx - effective_window, center_idx + effective_window + 1):
            idx = i % n
            value = ranges[idx]
            if math.isfinite(value):
                values.append(value)

        if not values:
            return math.inf

        return sum(values) / len(values)

    def angle_to_scan_index(self, scan: LaserScan, angle: float) -> Optional[int]:
        if angle < scan.angle_min or angle > scan.angle_max:
            return None

        index = int(round((angle - scan.angle_min) / scan.angle_increment))
        index = max(0, min(index, len(scan.ranges) - 1))
        return index

    # ---------------------------
    # Detection logic
    # ---------------------------
    def should_remove_obstacle(self, obstacle: ObstacleSpec, scan: LaserScan) -> bool:
        dx = obstacle.x - self.pose.x
        dy = obstacle.y - self.pose.y
        distance = math.hypot(dx, dy)

        if distance > 1.0:
            # not close enough
            return False

        # calculate local angle to the goal
        global_angle = math.atan2(dy, dx)
        local_angle = self.normalize_angle(global_angle - self.pose.theta)

        # find LiDAR array index
        scan_idx = self.angle_to_scan_index(scan, local_angle)
        if scan_idx is None:
            return False

        # check LiDAR measurement
        lidar_distance = self.get_mean_range(
            list(scan.ranges), scan_idx, window=self.config.mean_window)

        # verify if the reading matches the expected distance
        distance_error = abs(lidar_distance - distance)
        if distance_error <= self.config.obstacle_match_tolerance:
            return True

        return False

    def process_obstacle_detection(self, scan: LaserScan) -> None:
        obstacle_names: List[str] = list(self.active_obstacles.keys())

        for obstacle_name in obstacle_names:
            obstacle = self.active_obstacles[obstacle_name]
            if self.should_remove_obstacle(obstacle, scan):
                self.remove_obstacle(obstacle_name)

    # ---------------------------
    # Callbacks
    # ---------------------------
    def collision_callback(self, msg: Collisions) -> None:
        if msg.collisions:
            self.get_logger().warn("Collision detected -> reset robot")
            self.move_model(
                "serp",
                self.config.robot_initial_x,
                self.config.robot_initial_y,
                self.config.robot_initial_theta,
            )

    def odom_callback(self, msg: Odometry) -> None:
        self.pose.x = msg.pose.pose.position.x
        self.pose.y = msg.pose.pose.position.y
        self.pose.theta = self.quaternion_to_yaw(msg.pose.pose.orientation)

        self.get_logger().info(
            f"Pose -> x: {self.pose.x:.2f}, y: {self.pose.y:.2f}, theta: {self.pose.theta:.2f}"
        )

    def lidar_callback(self, scan: LaserScan) -> None:
        self.process_obstacle_detection(scan)

        if self.rotation_iterations_left == 0:
            front_index: int = len(scan.ranges) // 2
            front_distance: float = self.get_mean_range(
                list(scan.ranges), front_index)

            if front_distance < self.config.min_distance:
                self.start_random_rotation()
                self.get_logger().info(
                    f"Front obstacle at {front_distance:.2f} m -> rotating with "
                    f"angular speed {self.angular_speed:.2f}"
                )
            else:
                self.publish_speed(self.config.linear_speed, 0.0)
                return

        self.rotation_iterations_left -= 1
        self.publish_speed(0.0, self.angular_speed)

    # ---------------------------
    # Shutdown helpers
    # ---------------------------
    def stop_robot(self) -> None:
        self.publish_speed(0.0, 0.0)


def main(args: Optional[List[str]] = None) -> None:
    rclpy.init(args=args)
    node = Controller()

    try:
        rclpy.spin(node)
    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()
