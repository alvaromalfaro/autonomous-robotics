- `Homework1.ipynb`: implementation of **Monte Carlo Localization**, analysis of simulation results, proposed improvement for the Kidnapped Robot problem,
  and evaluation of how the number of particles affects pose estimation. Run the notebook to reproduce the simulations.
  
- `Homework2.ipynb`: implementation of an **Extended Kalman Filter** for mobile robot localisation, analysis of filter performance, and evaluation of state estimation uncertainty over time.

- `Homework3/` (ROS 2 package): implementation of a **Proportional-Derivative** (PD) controller for geometric trajectory tracking, integration of the Twiddle algorithm for dynamic hyperparameter optimization, and analysis of cross-track error convergence over multiple laps. The directory is structured as follows:

    - `standard/`: baseline PD controller using static, hand-tuned gains.
    - `advanced/`: enhanced controller integrating the Twiddle algorithm for real-time dynamic hyperparameter optimization.
    - `report/`: technical report.