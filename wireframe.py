"""
Wireframe 3D room renderer — Manim-inspired aesthetic.

Rooms are defined as collections of 3D edges. A perspective camera projects
them onto the screen. Glow is achieved by drawing each edge three times:
wide + dim → medium → bright core. This produces the characteristic bloom
that makes Manim animations look so distinctive.

Coordinate system:
  x — right
  y — up  (0 = floor, 5 = ceiling)
  z — into room (0 = near camera, 8-10 = back wall)

Camera: (0, 4, -8) looking toward (0, 1.5, 4).
"""

import pygame
import math


# ---------------------------------------------------------------------------
# Camera / projection
# ---------------------------------------------------------------------------

_EYE    = (0.0, 4.0, -8.0)
_TARGET = (0.0, 1.5,  4.0)
_UP     = (0.0, 1.0,  0.0)
_FOV    = 52.0   # degrees

def _build_basis(eye, target, up):
    """Return (right, true_up, forward) unit vectors for the camera."""
    fx, fy, fz = (target[i] - eye[i] for i in range(3))
    fl = math.sqrt(fx*fx + fy*fy + fz*fz)
    fx, fy, fz = fx/fl, fy/fl, fz/fl

    rx = up[1]*fz - up[2]*fy
    ry = up[2]*fx - up[0]*fz
    rz = up[0]*fy - up[1]*fx
    rl = math.sqrt(rx*rx + ry*ry + rz*rz)
    rx, ry, rz = rx/rl, ry/rl, rz/rl

    ux = ry*fz - rz*fy
    uy = rz*fx - rx*fz
    uz = rx*fy - ry*fx

    return (rx,ry,rz), (ux,uy,uz), (fx,fy,fz)

_R, _U, _F = _build_basis(_EYE, _TARGET, _UP)


def project(x, y, z, vp_cx, vp_cy, vp_half_w, vp_half_h):
    """
    Project a world-space point into a 2-D viewport.
    vp_cx/cy — viewport centre in screen pixels.
    vp_half_w/h — half-extents of the viewport.
    Returns (sx, sy) or None if behind camera.
    """
    dx, dy, dz = x - _EYE[0], y - _EYE[1], z - _EYE[2]
    cam_x =  dx*_R[0] + dy*_R[1] + dz*_R[2]
    cam_y =  dx*_U[0] + dy*_U[1] + dz*_U[2]
    cam_z =  dx*_F[0] + dy*_F[1] + dz*_F[2]
    if cam_z < 0.05:
        return None
    f = 1.0 / math.tan(math.radians(_FOV / 2))
    sx = int(vp_cx + cam_x / cam_z * f * vp_half_w)
    sy = int(vp_cy - cam_y / cam_z * f * vp_half_h)
    return sx, sy


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _box(x, y, z, w, h, d):
    """Return (verts, edges) for an axis-aligned box."""
    v = [
        (x,   y,   z),   (x+w, y,   z),   (x+w, y+h, z),   (x,   y+h, z),  # front
        (x,   y,   z+d), (x+w, y,   z+d), (x+w, y+h, z+d), (x,   y+h, z+d) # back
    ]
    e = [(0,1),(1,2),(2,3),(3,0),
         (4,5),(5,6),(6,7),(7,4),
         (0,4),(1,5),(2,6),(3,7)]
    return v, e


def _table(cx, cz, w, d, table_h=2.2, leg_thick=0.10):
    """Return (verts, edges) for a table centred at (cx, 0, cz)."""
    top_y = table_h - 0.15
    verts, edges = _box(cx-w/2, top_y, cz-d/2, w, 0.15, d)
    # four legs
    for lx, lz in [(cx-w/2+0.05, cz-d/2+0.05),
                   (cx+w/2-0.05-leg_thick, cz-d/2+0.05),
                   (cx-w/2+0.05, cz+d/2-0.05-leg_thick),
                   (cx+w/2-0.05-leg_thick, cz+d/2-0.05-leg_thick)]:
        lv, le = _box(lx, 0, lz, leg_thick, top_y, leg_thick)
        off = len(verts)
        verts.extend(lv)
        edges.extend((a+off, b+off) for a, b in le)
    return verts, edges


def _room_shell(hw, h, depth):
    """Floor, back wall, two side walls (open front, no ceiling — gives better view)."""
    verts, edges = [], []
    def add(v, e):
        off = len(verts); verts.extend(v)
        edges.extend((a+off, b+off) for a,b in e)

    # floor grid
    step = 1.0
    gx = -hw
    while gx <= hw + 0.001:
        add([(gx, 0, 0), (gx, 0, depth)], [(0,1)])
        gx += step
    gz = 0
    while gz <= depth + 0.001:
        add([(-hw, 0, gz), (hw, 0, gz)], [(0,1)])
        gz += step

    # back wall outline
    bwv = [(-hw,0,depth),( hw,0,depth),( hw,h,depth),(-hw,h,depth)]
    bwe = [(0,1),(1,2),(2,3),(3,0)]
    add(bwv, bwe)

    # side walls (left and right)
    for sx in (-hw, hw):
        swv = [(sx,0,0),(sx,0,depth),(sx,h,depth),(sx,h,0)]
        swe = [(0,1),(1,2),(2,3),(3,0),(0,3)]
        add(swv, swe)

    return verts, edges


# ---------------------------------------------------------------------------
# Glow drawing
# ---------------------------------------------------------------------------

def _draw_group(surface, verts, edges, color, vp_cx, vp_cy, vp_hw, vp_hh,
                alpha_core=220, glow=True):
    """Draw a set of edges with optional bloom glow."""
    r, g, b = color
    pts = [project(x, y, z, vp_cx, vp_cy, vp_hw, vp_hh) for x,y,z in verts]

    layers = [(5, max(1,int(alpha_core*0.12))),
              (3, max(1,int(alpha_core*0.28))),
              (1, alpha_core)] if glow else [(1, alpha_core)]

    for width, alpha in layers:
        layer = pygame.Surface((int(vp_hw*2), int(vp_hh*2)), pygame.SRCALPHA)
        ox = int(vp_cx - vp_hw)
        oy = int(vp_cy - vp_hh)
        for i, j in edges:
            if pts[i] and pts[j]:
                lp1 = (pts[i][0]-ox, pts[i][1]-oy)
                lp2 = (pts[j][0]-ox, pts[j][1]-oy)
                # simple clip: skip if both points far off viewport
                if (max(lp1[0],lp2[0]) < -20 or min(lp1[0],lp2[0]) > vp_hw*2+20
                 or max(lp1[1],lp2[1]) < -20 or min(lp1[1],lp2[1]) > vp_hh*2+20):
                    continue
                pygame.draw.line(layer, (r,g,b,alpha), lp1, lp2, width)
        surface.blit(layer, (ox, oy))


# ---------------------------------------------------------------------------
# Base room class
# ---------------------------------------------------------------------------

class WireRoom:
    NAME       = "Room"
    ROOM_COLOR = (120, 180, 220)   # structural lines colour
    SLOTS      = []                # ordered list of slot names

    def __init__(self):
        # Room shell (floor grid + walls)
        self._shell_v, self._shell_e = [], []
        # Per-slot geometry: {slot_name: (verts, edges, color)}
        self._objects = {}
        self._build()

    def _build(self): pass  # subclasses override

    def draw(self, surface, t,
             vp_x=186, vp_y=4, vp_w=450, vp_h=352,
             active_slots=None):
        """Draw the room into the given viewport rectangle."""
        vp_cx = vp_x + vp_w // 2
        vp_cy = vp_y + vp_h // 2
        vp_hw = vp_w / 2
        vp_hh = vp_h / 2

        # Breathing floor brightness
        pulse = (math.sin(t * 0.8) + 1) / 2
        rc = tuple(int(c * (0.45 + 0.15 * pulse)) for c in self.ROOM_COLOR)
        _draw_group(surface, self._shell_v, self._shell_e, rc,
                    vp_cx, vp_cy, vp_hw, vp_hh, alpha_core=90, glow=True)

        # Objects
        for slot, (v, e, col) in self._objects.items():
            occupied = active_slots and slot in active_slots
            if occupied:
                glow_pulse = (math.sin(t * 3.0 + hash(slot) % 6) + 1) / 2
                c = tuple(min(255, int(c * (0.8 + 0.4 * glow_pulse))) for c in col)
            else:
                c = tuple(int(c * 0.55) for c in col)
            _draw_group(surface, v, e, c,
                        vp_cx, vp_cy, vp_hw, vp_hh,
                        alpha_core=200 if occupied else 130,
                        glow=True)

    def slot_label_pos(self, slot, vp_x=186, vp_y=4, vp_w=450, vp_h=352):
        """Return the screen position of a slot's centre label."""
        if slot not in self._objects:
            return (vp_x + vp_w//2, vp_y + vp_h//2)
        v, _, _ = self._objects[slot]
        # Average of the object's vertices projected to screen
        vp_cx = vp_x + vp_w//2; vp_cy = vp_y + vp_h//2
        vp_hw = vp_w/2;          vp_hh = vp_h/2
        pts = [project(x,y,z,vp_cx,vp_cy,vp_hw,vp_hh) for x,y,z in v]
        pts = [p for p in pts if p]
        if not pts:
            return (vp_cx, vp_cy)
        return (sum(p[0] for p in pts)//len(pts),
                min(p[1] for p in pts) - 14)


# ---------------------------------------------------------------------------
# Kitchen
# ---------------------------------------------------------------------------

class KitchenRoom(WireRoom):
    NAME       = "Kitchen"
    ROOM_COLOR = (255, 210, 100)   # warm yellow
    SLOTS      = ["fridge", "stove", "table"]

    def _build(self):
        self._shell_v, self._shell_e = _room_shell(4.5, 4.5, 8.0)

        # Fridge — tall box, back-left corner
        fv, fe = _box(-4.0, 0, 6.5, 1.1, 4.2, 1.0)
        # add handle
        hv = [(-2.9, 2.5, 6.8), (-2.9, 2.5, 7.2),
              (-2.9, 2.8, 6.8), (-2.9, 2.8, 7.2)]
        he = [(0,1),(2,3),(0,2),(1,3)]
        off = len(fv); fv.extend(hv); fe.extend((a+off,b+off) for a,b in he)
        self._objects["fridge"] = (fv, fe, (130, 200, 255))  # ice blue

        # Stove — back wall, left of centre
        sv, se = _box(-2.0, 0, 7.0, 2.0, 2.5, 0.9)
        # burner rings (flat circles approximated as squares on top)
        for bx, bz in [(-1.6, 7.2), (-0.6, 7.2), (-1.6, 7.6), (-0.6, 7.6)]:
            bv, be = _box(bx, 2.5, bz, 0.4, 0.02, 0.4)
            off = len(sv); sv.extend(bv); se.extend((a+off,b+off) for a,b in be)
        self._objects["stove"] = (sv, se, (255, 140,  60))  # warm orange

        # Table — centre of room
        tv, te = _table(0.5, 3.5, 2.8, 1.6)
        self._objects["table"] = (tv, te, (230, 230, 210))  # near-white


# ---------------------------------------------------------------------------
# Bedroom
# ---------------------------------------------------------------------------

class BedroomRoom(WireRoom):
    NAME       = "Bedroom"
    ROOM_COLOR = (130, 110, 220)   # soft purple
    SLOTS      = ["bed", "dresser", "poster"]

    def _build(self):
        self._shell_v, self._shell_e = _room_shell(4.5, 4.5, 8.0)

        # Bed — left side, facing camera
        bv, be = _box(-4.0, 0, 2.0, 3.2, 0.7, 4.5)
        # headboard
        hv, he = _box(-4.0, 0, 1.7, 3.2, 1.8, 0.3)
        off = len(bv); bv.extend(hv); be.extend((a+off,b+off) for a,b in he)
        # pillow suggestion (flat box on top)
        pv, pe = _box(-3.7, 0.7, 1.9, 1.0, 0.2, 0.8)
        off = len(bv); bv.extend(pv); be.extend((a+off,b+off) for a,b in pe)
        self._objects["bed"] = (bv, be, (180, 140, 255))  # lavender

        # Dresser — right side, back
        dv, de = _box(2.8, 0, 6.0, 1.5, 3.0, 0.9)
        # drawer lines
        for dy in [0.8, 1.6, 2.4]:
            lv = [(2.8, dy, 6.0), (4.3, dy, 6.0)]
            off = len(dv); dv.extend(lv); de.extend([(off, off+1)])
        # handles
        for dy in [0.4, 1.2, 2.0]:
            hv2 = [(3.4, dy+0.25, 5.95), (3.7, dy+0.25, 5.95)]
            off = len(dv); dv.extend(hv2); de.extend([(off, off+1)])
        self._objects["dresser"] = (dv, de, (80, 220, 200))  # teal

        # Poster — frame on back wall
        pov, poe = _box(-1.0, 1.5, 7.92, 2.0, 2.5, 0.05)
        # inner frame lines
        inner = [(-0.7, 1.8, 7.92), (0.7, 1.8, 7.92),   # bottom inner
                 ( 0.7, 3.7, 7.92), (-0.7, 3.7, 7.92)]
        ie = [(0,1),(1,2),(2,3),(3,0)]
        off = len(pov); pov.extend(inner); poe.extend((a+off,b+off) for a,b in ie)
        self._objects["poster"] = (pov, poe, (255, 110, 180))  # pink


# ---------------------------------------------------------------------------
# Garage
# ---------------------------------------------------------------------------

class GarageRoom(WireRoom):
    NAME       = "Garage"
    ROOM_COLOR = ( 80, 220, 160)   # industrial green
    SLOTS      = ["car", "workbench"]

    def _build(self):
        self._shell_v, self._shell_e = _room_shell(5.5, 4.5, 10.0)

        # Car — simplified bounding + cabin + wheels
        # body
        cv, ce = _box(-3.0, 0.4, 2.0, 5.5, 1.0, 2.5)
        # cabin (raised centre section)
        cab_v, cab_e = _box(-2.0, 1.4, 2.2, 3.2, 1.0, 2.0)
        off = len(cv); cv.extend(cab_v); ce.extend((a+off,b+off) for a,b in cab_e)
        # windscreen divider
        ws = [(-2.0, 1.4, 2.2), (-2.0, 2.4, 2.4),
              ( 1.2, 2.4, 2.4), ( 1.2, 1.4, 2.2)]
        we = [(0,1),(1,2),(2,3),(3,0)]
        off = len(cv); cv.extend(ws); ce.extend((a+off,b+off) for a,b in we)
        # wheels (diamond approximation in 2D, extruded)
        for wx, wz in [(-2.2, 2.0), (1.8, 2.0), (-2.2, 4.0), (1.8, 4.0)]:
            wr = 0.55
            wv = [(wx, 0.4+wr, wz), (wx-wr, 0.4, wz), (wx, 0.4-wr+0.3, wz),
                  (wx+wr, 0.4, wz), (wx, 0.4+wr, wz+0.3), (wx-wr, 0.4, wz+0.3),
                  (wx, 0.4-wr+0.3, wz+0.3), (wx+wr, 0.4, wz+0.3)]
            we2 = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
            off = len(cv); cv.extend(wv); ce.extend((a+off,b+off) for a,b in we2)
        self._objects["car"] = (cv, ce, (80, 255, 140))  # bright green

        # Workbench — right side
        wbv, wbe = _table(4.2, 7.5, 2.5, 1.2, table_h=3.0)
        # pegboard back panel
        pbv, pbe = _box(3.0, 3.0, 8.1, 2.5, 1.5, 0.05)
        off = len(wbv); wbv.extend(pbv); wbe.extend((a+off,b+off) for a,b in pbe)
        self._objects["workbench"] = (wbv, wbe, (255, 200,  80))  # amber


# ---------------------------------------------------------------------------
# Room registry
# ---------------------------------------------------------------------------

PREBUILT = {
    "kitchen":   KitchenRoom,
    "bedroom":   BedroomRoom,
    "garage":    GarageRoom,
}

PREBUILT_NAMES  = ["kitchen", "bedroom", "garage"]
PREBUILT_SLOTS  = {
    "kitchen": ["fridge", "stove", "table"],
    "bedroom": ["bed",    "dresser", "poster"],
    "garage":  ["car",    "workbench"],
}

_room_cache: dict = {}

def get_room(room_type: str) -> WireRoom:
    """Return a cached WireRoom instance for the given type key."""
    key = room_type.lower()
    if key not in _room_cache:
        cls = PREBUILT.get(key)
        if cls:
            _room_cache[key] = cls()
    return _room_cache.get(key)
