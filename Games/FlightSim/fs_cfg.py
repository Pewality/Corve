# fs_cfg.py - every tunable setting for the flight sim lives here.

# ---- controls / camera ----
INVERT_PITCH = False   # True = Up pulls the nose up
START_CHASE = True     # start in third-person view
CHASE_D = 14.0         # chase camera distance behind the plane
CHASE_H = 4.0          # chase camera height above the plane

# ---- speed / smoothness ----
FPS = 20               # target frame rate
LINE_BUDGET = 130      # max wireframe lines per frame (world); lower = faster
LOD_MIN = 0.45         # adaptive detail never drops below this (0.45 = 45% draw distance)
CACHE_R = 500          # how far around you the world is generated
RESEED = 60            # regenerate when you move this far from the cache centre
DEBUG = False          # True = show lines-per-frame at the bottom

# ---- flying / landing ----
LAND_MAX_SPEED = 75
SINK_LIMIT = 18        # max descent rate (units/s) for a good landing
TAKEOFF_SPEED = 50

# ---- camera optics ----
FOCAL = 34.0           # ~90 degree FOV on the 72px screen
NEAR = 1.0
EYE = 2.0              # cockpit eye height

# ---- world layout ----
CELL = 120             # terrain cell (mountains / radio towers)
REGION = 600           # settlement region (towns / cities)
GRID = 60              # ground grid spacing
MAP_SCALES = (10, 24, 56)   # world units per map pixel

# ---- level-of-detail distances (squared) ----
DRAW_R2 = 380 * 380
MID_D2 = 220 * 220
NEAR_D2 = 100 * 100
HOUSE_D2 = 150 * 150

# ---- object kinds ----
K_MTN, K_LAT, K_SKY, K_MID, K_HOUSE = 0, 1, 2, 3, 4
CORN = ((-1, -1), (1, -1), (1, 1), (-1, 1))
