import rclpy
import time
import random
import math
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Empty
from turtlesim.msg import Pose
from turtlesim.srv import SetPen
from turtlesim.srv import Spawn
from turtlesim.srv import TeleportAbsolute, Kill
from geometry_msgs.msg import Twist
from turtlesim.action import RotateAbsolute
from rclpy.action import ActionClient


class Controller(Node):

    def __init__(self):
        super().__init__('controller')
        
        self.radius = 2.0 
        self.speed = math.pi
        
        # 0.- LAUNCH WILL AUTOMATICALLY EXECUTE A NEW SIMULATOR (nothing is needed)
        
        # 1.- RESET, CLEAR SIMULATOR AND REMOVE INITIAL TURTLE
        
        self.reset()        
        self.clear()
        self.kill_turtle('turtle1')
        
        # 2.- ADD A NEW TURTLE NAMED 'GUIDANCE', LOCATED AT INITIAL POSICION WITH EAST ORIENTATION (0 DEGREES)
        self.add_turtle("GUIDANCE", 5.5 - self.radius, 5.5 + self.radius, 0.0)
        
        # 3.- SET COLOUR TO GREEN TO MARK THE GUIDANCE PATH
        self.set_color('GUIDANCE', 0,255,0,10)        

        # 4.- DRAW THE GUIDANCE PATH
        self.draw_path()
            
        # 5.- REMOVE GUIDANCE        
        self.kill_turtle('GUIDANCE')
        
        # 6.- REMOVE TURTLE1 (FOR MULTIPLE TESTING) AND ADD IT INTO AN INITIAL RANDOM POSE
        
        self.add_turtle("turtle1", 5.5 - self.radius, 5.5 + self.radius + random.uniform(-0.5, 0.5), random.uniform(-0.2, 0.2))
        
        # 7.- SET INITIAL COLOUR TO RED
        self.set_color('turtle1', 255,0,0,2)        
        
        # PD and Twiddle initialization
        self.p = [171.2719, 38.5078] # tau_p, tau_d
        self.dp = [0.05, 0.05] # initial tuning steps 
        self.best_err = math.inf
        self.tune_idx = 0 # 0: tau_p, 1: tau_d
        self.tune_state = 0 # states for Twiddle

        self.last_lap_time = 0.0
        self.lap_count = -1
        self.lap_err_sum = 0.0
        self.lap_steps = 0
        self.prev_x = 5.5
        self.prev_cte = None
        
        self.iteration = 0
        self.agg_error = 0
        self.last_exec_time = time.perf_counter()
        
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.listener_callback,
            10)
        self.subscription      
        
    ## METHODS TO BE USED ##
        
    def kill_turtle(self, name):
        cli = self.create_client(Kill, '/kill')
        while not cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('...')
        req = Kill.Request()
        req.name = name
        future = cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        
    def reset(self):
        reset_cli = self.create_client(Empty, '/reset')
        while not reset_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('...')
        reset_req = Empty.Request()        
        future = reset_cli.call_async(reset_req)
        rclpy.spin_until_future_complete(self, future)
        
    def clear(self):
        clear_cli = self.create_client(Empty, '/clear')
        while not clear_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('...')
        clear_req = Empty.Request()        
        future = clear_cli.call_async(clear_req)
        rclpy.spin_until_future_complete(self, future)
        
    def set_color(self, turtlename, r, g, b, width):
        setpen_cli = self.create_client(SetPen, f'/{turtlename}/set_pen')
        while not setpen_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('...turtle1 ready to go...')
        setpen_req = SetPen.Request()
        setpen_req.r = r
        setpen_req.g = g
        setpen_req.b = b        
        setpen_req.width = width
        future = setpen_cli.call_async(setpen_req)
        rclpy.spin_until_future_complete(self, future)
        
    def add_turtle(self, name, posX, posY, theta):
        spawn_cli = self.create_client(Spawn, '/spawn')
        while not spawn_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('...')
        spawn_req = Spawn.Request()        
        spawn_req.x = posX
        spawn_req.y = posY
        spawn_req.theta = theta
        spawn_req.name = name
        future = spawn_cli.call_async(spawn_req)        
        rclpy.spin_until_future_complete(self, future)
        
    def draw_path(self):
        self.publisher_ref = self.create_publisher(Twist, '/GUIDANCE/cmd_vel', 10)
        self.go_straight()
        self.go_curve(True)
        self.go_straight()
        self.go_curve()    
        
    def go_straight(self):
        msg = Twist()
        msg.linear.x = 2.0 * self.radius
        msg.linear.y = 0.0
        self.publisher_ref.publish(msg)   
        time.sleep(2)
        
    def go_curve(self, final_rotate=False):
        msg = Twist()
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        msg.angular.x = 0.0        
        msg.angular.y = 0.0        
        
        msg.linear.x = self.speed
        msg.angular.z = -self.speed/self.radius

        for _ in range(0,2):
            self.publisher_ref.publish(msg)
            time.sleep(1.5)
            
        if final_rotate:
            self._action_client = ActionClient(self, RotateAbsolute, '/GUIDANCE/rotate_absolute')
            goal_msg = RotateAbsolute.Goal()
            goal_msg.theta = math.pi
            self._action_client.wait_for_server()
            future = self._action_client.send_goal_async(goal_msg)
            time.sleep(0.5)

    def change_pen_color_async(self):
        setpen_cli = self.create_client(SetPen, '/turtle1/set_pen')
        if setpen_cli.wait_for_service(timeout_sec=0.1):
            req = SetPen.Request()
            req.r = random.randint(50, 255)
            req.g = random.randint(50, 255)
            req.b = random.randint(50, 255)
            req.width = 2
            setpen_cli.call_async(req)

    def listener_callback(self, msg):
        exec_time = time.perf_counter()
        time_since = exec_time - self.last_exec_time
        if time_since < 0.1:
            return
    
        self.last_exec_time = exec_time
        x, y, theta = msg.x, msg.y, msg.theta
    
        new_msg = Twist()
        new_msg.linear.x = 0.2
    
        # CTE computation
        if 3.5 <= x <= 7.5 and y > 5.5:
            new_cte = y - (5.5 + self.radius)
        elif 3.5 <= x <= 7.5 and y <= 5.5:
            new_cte = (5.5 - self.radius) - y
        elif x > 7.5:
            dist = math.sqrt((x - 7.5)**2 + (y - 5.5)**2)
            new_cte = dist - self.radius
        else:
            dist = math.sqrt((x - 3.5)**2 + (y - 5.5)**2)
            new_cte = dist - self.radius
    
        if self.prev_cte is None:
            self.prev_cte = new_cte
    
        # PD control law
        derivative = (new_cte - self.prev_cte) / time_since
        tau_p, tau_d = self.p[0], self.p[1]
        new_msg.angular.z = -tau_p * new_cte - tau_d * derivative
    
        # Require 2 seconds between triggers and that we're in the upper half
        lap_gate_crossed = (
            y > 5.5
            and self.prev_x < 5.5 <= x
            and (exec_time - self.last_lap_time) > 2.0
        )
        if lap_gate_crossed:
            self.last_lap_time = exec_time
            self.lap_count += 1
    
            if self.lap_count == 1:
                self.best_err = self.lap_err_sum / max(1, self.lap_steps)
                self.get_logger().info(
                    f"- LAP 1 FINISHED - Base Error: {self.best_err:.4f}"
                )
                self.change_pen_color_async()
                # First Twiddle perturbation
                self.p[self.tune_idx] += self.dp[self.tune_idx]
    
            elif self.lap_count > 1:
                avg_err = self.lap_err_sum / max(1, self.lap_steps)
                self.get_logger().info(
                    f"- LAP {self.lap_count} FINISHED - Error: {avg_err:.4f}"
                )
                self._twiddle_step(avg_err)
                self.get_logger().info(
                    f"New params: tau_p = {self.p[0]:.4f}, tau_d = {self.p[1]:.4f}"
                )
                self.change_pen_color_async()
    
            self.lap_err_sum = 0.0
            self.lap_steps = 0
    
        if self.lap_count >= 0:
            self.lap_err_sum += abs(new_cte)
            self.lap_steps += 1
    
        self.prev_x = x
        self.prev_cte = new_cte
    
        # Accumulation
        self.iteration += 1
        self.agg_error += new_cte
    
        if self.iteration % 10 == 0:
            self.get_logger().info(
                f"Average error {self.agg_error / float(self.iteration):.4f}"
            )
    
        self.publisher_.publish(new_msg)
    
    
    def _twiddle_step(self, avg_err):
        """Twiddle state machine"""
        i = self.tune_idx
        if self.tune_state == 0:
            if avg_err < self.best_err:
                self.best_err = avg_err
                self.dp[i] *= 1.1
                self.tune_idx = (i + 1) % 2
                self.p[self.tune_idx] += self.dp[self.tune_idx]
                # stay in state 0
            else:
                self.p[i] -= 2 * self.dp[i]
                self.tune_state = 1
        else:  # state 1
            if avg_err < self.best_err:
                self.best_err = avg_err
                self.dp[i] *= 1.1
            else:
                self.p[i] += self.dp[i]   # revert to original
                self.dp[i] *= 0.9
            self.tune_idx = (i + 1) % 2
            self.p[self.tune_idx] += self.dp[self.tune_idx]
            self.tune_state = 0


def main(args=None):
    print("Homework 3 - Starting")
    rclpy.init(args=args)
    minimal_subscriber = Controller()
    rclpy.spin(minimal_subscriber)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
