#!/usr/bin/env python3
"""
Noeud d'inference: charge le modele BC entraine et pilote le robot en autonome.
Sert de base pour le DAgger (l'humain peut reprendre le clavier a tout moment
via teleop_twist_keyboard, qui a priorite car lance en dernier / topic remape).
"""

import math
import os
import numpy as np
import torch
import torch.nn as nn

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, qos_profile_sensor_data

from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan

NUM_SCAN_SAMPLES = 36
LIDAR_DISTANCE_CAP = 10.0
MAX_LINEAR_SPEED = 0.5
MAX_ANGULAR_SPEED = 2.0
MAX_GOAL_DISTANCE = 12.0
MODEL_PATH = os.path.expanduser('~/stage_imitation_learning/models/bc_model.pt')

GOAL_X = 6.5
GOAL_Y = -2.0


def euler_from_quaternion(q):
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class BCPolicy(nn.Module):
    def __init__(self, input_dim=40, output_dim=2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, output_dim),
        )

    def forward(self, x):
        return self.net(x)


class BCInferenceNode(Node):
    def __init__(self):
        super().__init__('bc_inference_node')

        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_heading = 0.0
        self.goal_distance = 0.0
        self.goal_angle = 0.0
        self.odom_received = False
        self.scan_ranges = [1.0] * NUM_SCAN_SAMPLES
        self.prev_linear = 0.0
        self.prev_angular = 0.0

        self.device = torch.device('cpu')
        self.model = BCPolicy().to(self.device)
        self.model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
        self.model.eval()
        self.get_logger().info(f"Modele charge depuis {MODEL_PATH}")

        qos = QoSProfile(depth=10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, qos)
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, qos_profile=qos_profile_sensor_data)
        self.goal_sub = self.create_subscription(
            PoseStamped, '/goal_pose', self.goal_pose_callback, qos)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', qos)

        self.timer = self.create_timer(0.1, self.control_step)
        self.get_logger().info("Inference demarree: le robot est pilote par le modele BC.")

    def odom_callback(self, msg):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        self.robot_heading = euler_from_quaternion(msg.pose.pose.orientation)

        diff_x = GOAL_X - self.robot_x
        diff_y = GOAL_Y - self.robot_y
        self.goal_distance = math.sqrt(diff_x ** 2 + diff_y ** 2)

        heading_to_goal = math.atan2(diff_y, diff_x)
        angle = heading_to_goal - self.robot_heading
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        self.goal_angle = angle
        self.odom_received = True

    def goal_pose_callback(self, msg):
        global GOAL_X, GOAL_Y
        GOAL_X = msg.pose.position.x
        GOAL_Y = msg.pose.position.y
        self.get_logger().info(f"Nouveau goal recu: x={GOAL_X:.2f} y={GOAL_Y:.2f}")

    def scan_callback(self, msg):
        n = min(len(msg.ranges), NUM_SCAN_SAMPLES)
        for i in range(n):
            r = msg.ranges[i]
            if math.isinf(r) or math.isnan(r):
                r = LIDAR_DISTANCE_CAP
            self.scan_ranges[i] = float(np.clip(r / LIDAR_DISTANCE_CAP, 0.0, 1.0))

    def build_observation(self):
        obs = list(self.scan_ranges)
        obs.append(float(np.clip(self.goal_distance / MAX_GOAL_DISTANCE, 0, 1)))
        obs.append(float(self.goal_angle) / math.pi)
        obs.append(float(np.clip(self.prev_linear / MAX_LINEAR_SPEED, -1, 1)))
        obs.append(float(np.clip(self.prev_angular / MAX_ANGULAR_SPEED, -1, 1)))
        return np.array(obs, dtype=np.float32)

    def control_step(self):
        if not self.odom_received:
            return
        if self.goal_distance < 0.3:
            self.publish_cmd(0.0, 0.0)
            self.get_logger().info("Objectif atteint, arret.", throttle_duration_sec=2.0)
            return

        obs = self.build_observation()
        with torch.no_grad():
            x = torch.tensor(obs, dtype=torch.float32).unsqueeze(0)
            action = self.model(x).squeeze(0).numpy()

        linear = float(np.clip(action[0], -MAX_LINEAR_SPEED, MAX_LINEAR_SPEED))
        angular = float(np.clip(action[1], -MAX_ANGULAR_SPEED, MAX_ANGULAR_SPEED))

        self.publish_cmd(linear, angular)
        self.prev_linear = linear
        self.prev_angular = angular

    def publish_cmd(self, linear, angular):
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.cmd_vel_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = BCInferenceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_cmd(0.0, 0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
