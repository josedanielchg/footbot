std_msgs/Header header

# Reach-goal state. Image-derived only; never from Gazebo poses.

bool ball_visible
bool goal_visible
bool stale

float32 ball_confidence
float32 goal_confidence

float32 ball_center_error
float32 goal_center_error

float32 ball_angle_rad
float32 goal_angle_rad

float32 ball_radius_px
float32 goal_width_px

bool has_ball_control
bool ball_goal_aligned

bool goal_memory_active
float32 goal_memory_age_sec
