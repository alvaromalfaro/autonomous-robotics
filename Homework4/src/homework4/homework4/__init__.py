#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import os
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


@dataclass(frozen=True)
class ExperimentConfig:
    nav_mode: str       # "basic" or "improved"
    linear_speed: float
    mean_window: int


EXPERIMENT_CONFIGS: List[ExperimentConfig] = [
    ExperimentConfig(nav, speed, window)
    for nav in ("basic", "improved")
    for speed in (1.0, 0.5, 2.0)
    for window in (4, 2)
]  # 12 configurations x 10 runs each = 120 total runs
RUNS_PER_CONFIG = 10


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

        # Stuck detection & escape
        self._stuck_ref_time: float = 0.0
        self._stuck_ref_pos: tuple = (0.0, 0.0)
        self._stuck_timeout: float = 5.0   # s without moving -> escape
        self._stuck_dist: float = 0.4      # m minimum displacement
        self._escape_reverse_iters: int = 0  # phase 1: reverse
        self._escape_spin_speed: float = 0.0  # phase 2: random spin
        self._escape_spin_iters: int = 35     # phase 2 duration

        # ---------------------------
        # Experiment tracking
        # ---------------------------
        self.map_name: str = self.declare_parameter(
            "map_name", "default").value
        self.output_csv: str = self.declare_parameter(
            "output_csv",
            os.path.expanduser(f"~/homework4_results_{self.map_name}.csv")
        ).value
        self.config_idx: int = 0
        self.run_idx: int = 0
        self.all_results: List[dict] = []
        self.detection_times: Dict[str, float] = {}
        self.run_start_time: float = 0.0
        self.resetting: bool = True  # blocks lidar_callback until world is ready

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

        # Give the simulator time to settle before starting the first run.
        self._initial_start_timer = self.create_timer(3.0, self._initial_start)

    # ---------------------------
    # Initialization helpers
    # ---------------------------
    def wait_for_services(self) -> None:
        self.move_client.wait_for_service()
        self.spawn_client.wait_for_service()

    def spawn_all_obstacles(self) -> None:
        for obstacle in self.obstacles:
            self.spawn_obstacle(obstacle)

    def _initial_start(self) -> None:
        """One-shot timer callback that fires 3 s after startup."""
        self.destroy_timer(self._initial_start_timer)
        self._start_run()

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

        # record detection time
        elapsed = self.get_clock().now().nanoseconds / 1e9 - self.run_start_time
        self.detection_times[name] = round(elapsed, 3)

        # check if all obstacles have been detected and finish the run if so
        if not self.active_obstacles:
            self._finish_run()

    # ---------------------------
    # Experiment helpers
    # ---------------------------
    def _current_exp(self) -> ExperimentConfig:
        """Returns the ExperimentConfig for the current config_idx."""
        return EXPERIMENT_CONFIGS[self.config_idx]

    def _start_run(self) -> None:
        """Starts a new run using the current config_idx and run_idx."""
        exp = self._current_exp()
        self.detection_times = {}
        self.active_obstacles = {o.name: o for o in self.obstacles}
        self.rotation_iterations_left = 0
        self.run_start_time = self.get_clock().now().nanoseconds / 1e9
        self._stuck_ref_time = self.run_start_time
        self._stuck_ref_pos = (self.pose.x, self.pose.y)
        self._escape_reverse_iters = 0
        self.resetting = False
        self.get_logger().info(
            f"[Config {self.config_idx + 1}/{len(EXPERIMENT_CONFIGS)}, "
            f"Run {self.run_idx + 1}/{RUNS_PER_CONFIG}] "
            f"nav={exp.nav_mode} speed={exp.linear_speed} window={exp.mean_window}"
        )

    def _finish_run(self) -> None:
        """Finishes the current run, records results, and triggers world reset."""
        exp = self._current_exp()
        total_time = round(max(self.detection_times.values()), 3)
        row = {
            "map_name": self.map_name,
            "nav_mode": exp.nav_mode,
            "linear_speed": exp.linear_speed,
            "mean_window": exp.mean_window,
            "run": self.run_idx + 1,
            "obstacle1_time": self.detection_times.get("obstacle1", ""),
            "obstacle2_time": self.detection_times.get("obstacle2", ""),
            "obstacle3_time": self.detection_times.get("obstacle3", ""),
            "obstacle4_time": self.detection_times.get("obstacle4", ""),
            "total_time": total_time,
        }
        self.all_results.append(row)
        self.get_logger().info(
            f"Run finished — total_time={total_time:.2f}s detections={self.detection_times}"
        )
        self._reset_world()

    def _reset_world(self) -> None:
        """Resets the world to the initial state for the next run."""
        self.resetting = True
        self.publish_speed(0.0, 0.0)
        self.rotation_iterations_left = 0

        self.move_model(
            "robot",
            self.config.robot_initial_x,
            self.config.robot_initial_y,
            self.config.robot_initial_theta,
        )
        for obstacle in self.obstacles:
            self.move_model(obstacle.name, obstacle.x,
                            obstacle.y, obstacle.theta)

        self._reset_timer = self.create_timer(2.0, self._advance_and_start)

    def _advance_and_start(self) -> None:
        self.destroy_timer(self._reset_timer)

        self.run_idx += 1
        if self.run_idx >= RUNS_PER_CONFIG:
            self.run_idx = 0
            self.config_idx += 1

        if self.config_idx >= len(EXPERIMENT_CONFIGS):
            self._save_csv()
            self.get_logger().info("All experiments done. Shutting down.")
            rclpy.shutdown()
            return

        self._start_run()

    def _save_csv(self) -> None:
        fieldnames = [
            "map_name", "nav_mode", "linear_speed", "mean_window", "run",
            "obstacle1_time", "obstacle2_time", "obstacle3_time", "obstacle4_time",
            "total_time",
        ]
        path = os.path.expanduser(self.output_csv)
        file_exists = os.path.isfile(path)
        with open(path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerows(self.all_results)
        self.get_logger().info(
            f"Results saved to {path} ({len(self.all_results)} rows)")

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

    def start_heuristic_rotation(self, scan: LaserScan) -> None:
        """
        Rotate toward the direction with the most free space across all 360 degrees.
        """
        ranges = list(scan.ranges)
        window = self._current_exp().mean_window

        best_idx = max(range(len(ranges)),
                       key=lambda i: self.get_mean_range(ranges, i, window=window))

        best_angle = scan.angle_min + best_idx * scan.angle_increment
        turn_speed = 1.5
        self.angular_speed = turn_speed if best_angle >= 0 else -turn_speed

        self.get_logger().info(
            f"Turning {'LEFT' if self.angular_speed > 0 else 'RIGHT'} "
            f"toward best angle {math.degrees(best_angle):.1f}° "
            f"(space={self.get_mean_range(ranges, best_idx, window=window):.2f} m)"
        )
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

        if distance > self.config.obstacle_detection_distance:
            # not close enough
            return False

        # calculate local angle to the goal
        global_angle = math.atan2(dy, dx)
        local_angle = self.normalize_angle(global_angle - self.pose.theta)

        # find LiDAR array index
        scan_idx = self.angle_to_scan_index(scan, local_angle)
        if scan_idx is None:
            return False

        # check LiDAR measurement using the current experiment's mean_window
        exp_window = self._current_exp().mean_window
        lidar_distance = self.get_mean_range(
            list(scan.ranges), scan_idx, window=exp_window)

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

    def _check_stuck(self) -> bool:
        """Returns True and triggers reverse+spin escape if the robot hasn't moved enough."""
        now = self.get_clock().now().nanoseconds / 1e9
        if now - self._stuck_ref_time < self._stuck_timeout:
            return False

        moved = math.hypot(
            self.pose.x - self._stuck_ref_pos[0],
            self.pose.y - self._stuck_ref_pos[1],
        )
        self._stuck_ref_time = now
        self._stuck_ref_pos = (self.pose.x, self.pose.y)

        if moved < self._stuck_dist:
            self._escape_reverse_iters = 20
            self._escape_spin_speed = random.uniform(-math.pi, math.pi)
            self.get_logger().warn(
                f"Stuck (moved {moved:.2f} m in {self._stuck_timeout:.0f}s) "
                f"→ reversing then spinning"
            )
            return True
        return False

    def lidar_callback(self, scan: LaserScan) -> None:
        if self.resetting:
            return

        self.process_obstacle_detection(scan)

        if self.resetting:  # _reset_world may have been triggered inside detection
            return

        exp = self._current_exp()

        # Phase 1: reverse to physically leave the stuck spot
        if self._escape_reverse_iters > 0:
            self._escape_reverse_iters -= 1
            self.publish_speed(-exp.linear_speed, 0.0)
            if self._escape_reverse_iters == 0:
                # switch to phase 2: random spin
                self.angular_speed = self._escape_spin_speed
                self.rotation_iterations_left = self._escape_spin_iters
            return

        if self.rotation_iterations_left == 0:
            self._check_stuck()
            if self._escape_reverse_iters > 0:
                return  # escape just triggered, handle next callback

            front_index: int = len(scan.ranges) // 2
            front_distance: float = self.get_mean_range(
                list(scan.ranges), front_index, window=exp.mean_window)

            if front_distance < self.config.min_distance:
                if exp.nav_mode == "basic":
                    self.start_random_rotation()
                else:
                    self.start_heuristic_rotation(scan)
                self.get_logger().info(
                    f"Front obstacle at {front_distance:.2f} m -> rotating with "
                    f"angular speed {self.angular_speed:.2f}"
                )
            else:
                self.publish_speed(exp.linear_speed, 0.0)
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
