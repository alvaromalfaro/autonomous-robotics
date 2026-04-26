- `Homework1.ipynb`: implementation of **Monte Carlo Localization**, analysis of simulation results, proposed improvement for the Kidnapped Robot problem,
  and evaluation of how the number of particles affects pose estimation. Run the notebook to reproduce the simulations.
  
- `Homework2.ipynb`: implementation of an **Extended Kalman Filter** for mobile robot localisation, analysis of filter performance, and evaluation of state estimation uncertainty over time.

- `Homework3/` (ROS 2 package): implementation of a **Proportional-Derivative** (PD) controller for geometric trajectory tracking, integration of the Twiddle algorithm for dynamic hyperparameter optimization, and analysis of cross-track error convergence over multiple laps. The directory is structured as follows:

    - `standard/`: baseline PD controller using static, hand-tuned gains.
    - `advanced/`: enhanced controller integrating the Twiddle algorithm for real-time dynamic hyperparameter optimization.
    - `report/`: technical report.

- `Homework4/` (ROS 2 package): implementation of a **reactive navigation system** for a simulated mobile robot in the Flatland 2D environment. The robot navigates a bounded arena using a 360° LiDAR sensor, detects and removes four goal objects via laser and odometry data, and avoids obstacles through two navigation strategies. The system was evaluated across 12 configurations (2 navigation modes × 3 linear speeds × 2 laser window sizes), repeated 10 times on three maps of increasing complexity. The directory is structured as follows:

    - `src/homework4/`: ROS 2 package containing the controller node, launch file, world definitions, map image generator, experiment results, and plotting script.
    - `report/`: technical report.