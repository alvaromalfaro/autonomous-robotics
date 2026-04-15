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
        
        # 7.- SET COLOUR TO RED TO MARK THE ROBOT PATH
        self.set_color('turtle1', 255,0,0,1)        
        
        # 6.- ADD A PUBLISHER / SUBSCRIBER TO INCLUDE THE CONTROLLER FOR TURTLE 1        
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
        

    def listener_callback(self, msg):
        exec_time = time.perf_counter()
        time_since = exec_time - self.last_exec_time
        if time_since < 1:
            return
           
        print(f"New event with time since: {time_since}") 
        
        self.last_exec_time = time.perf_counter()                       
        x = msg.x
        y = msg.y
        theta = msg.theta
        
        new_msg = Twist()
        new_msg.linear.x = 0.2	# We will send 0.2 forward every half second
        
        new_cte = 0.0 # This is the value that should be computed and used
        
        ## INCLUDE YOUR LOGIC HERE --> START ##
        ## ASSUME (5.5,5.5) AS THE CENTER OF THE SCREEN
        # Compute CTE based on geometric regions
        if x <= 3.5:
            # Left curve
            dist = math.sqrt((x - 3.5)**2 + (y - 5.5)**2)
            new_cte = dist - self.radius
        elif x >= 7.5:
            # Right curve
            dist = math.sqrt((x - 7.5)**2 + (y - 5.5)**2)
            new_cte = dist - self.radius
        elif y >= 5.5:
            # Upper straight section
            new_cte = y - (5.5 + self.radius)
        else:
            # Lower straight section
            new_cte = (5.5 - self.radius) - y

        if not hasattr(self, "prev_cte"):
            self.prev_cte = new_cte

        # Compute derivative
        derivative = (new_cte - self.prev_cte) / time_since
        # Apply the PD control law
        tau_p = 0.4
        tau_d = 0.6
        new_msg.angular.z = -tau_p * new_cte - tau_d * derivative
        self.prev_cte = new_cte
        ## INCLUDE YOUR LOGIC HERE --> END ##
        
        self.iteration += 1
        self.agg_error += new_cte
        
        if self.iteration%10 == 0:
            self.get_logger().info(f'Average error {self.agg_error/float(self.iteration)}')
     
        self.publisher_.publish(new_msg)


def main(args=None):
    print("Homework 3 - Starting")
    rclpy.init(args=args)
    minimal_subscriber = Controller()
    rclpy.spin(minimal_subscriber)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
