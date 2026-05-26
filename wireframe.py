"""
Wireframe 3D room renderer — Manim-inspired aesthetic.

Dark background, neon glow lines, proper perspective camera.
Each room is geometry (vertices + edges) drawn with bloom layers.

Coordinate system: x=right, y=up (0=floor), z=into room (0=near camera).
Camera: (0, 3.8, -9) looking at (0, 1.2, 4.5).
"""

import pygame
import math


# ---------------------------------------------------------------------------
# Camera — CORRECT view matrix construction
# ---------------------------------------------------------------------------

_EYE    = (0.0, 3.8, -9.0)
_TARGET = (0.0, 1.2,  4.5)
_UP     = (0.0, 1.0,  0.0)
_FOV    = 54.0


def _build_basis(eye, target, up):
    # Forward
    fx, fy, fz = target[0]-eye[0], target[1]-eye[1], target[2]-eye[2]
    fl = math.sqrt(fx*fx + fy*fy + fz*fz)
    fx, fy, fz = fx/fl, fy/fl, fz/fl
    # Right = cross(world_up, forward)
    rx = up[1]*fz - up[2]*fy
    ry = up[2]*fx - up[0]*fz
    rz = up[0]*fy - up[1]*fx
    rl = math.sqrt(rx*rx + ry*ry + rz*rz)
    rx, ry, rz = rx/rl, ry/rl, rz/rl
    # True up = cross(forward, right)  — NOTE: corrected cross-product order
    ux = fy*rz - fz*ry
    uy = fz*rx - fx*rz
    uz = fx*ry - fy*rx
    return (rx,ry,rz), (ux,uy,uz), (fx,fy,fz)


_R, _U, _F = _build_basis(_EYE, _TARGET, _UP)


def project(x, y, z, vp_cx, vp_cy, vp_hw, vp_hh):
    """World → screen. Returns (sx, sy) or None if behind camera."""
    dx, dy, dz = x-_EYE[0], y-_EYE[1], z-_EYE[2]
    cx =  dx*_R[0] + dy*_R[1] + dz*_R[2]
    cy =  dx*_U[0] + dy*_U[1] + dz*_U[2]
    cz =  dx*_F[0] + dy*_F[1] + dz*_F[2]
    if cz < 0.05:
        return None
    f = 1.0 / math.tan(math.radians(_FOV / 2))
    return (int(vp_cx + cx/cz * f * vp_hw),
            int(vp_cy - cy/cz * f * vp_hh))


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _box(x, y, z, w, h, d):
    v = [(x,   y,   z),   (x+w, y,   z),   (x+w, y+h, z),   (x,   y+h, z),
         (x,   y,   z+d), (x+w, y,   z+d), (x+w, y+h, z+d), (x,   y+h, z+d)]
    e = [(0,1),(1,2),(2,3),(3,0), (4,5),(5,6),(6,7),(7,4), (0,4),(1,5),(2,6),(3,7)]
    return v, e


def _circle(cx, y, cz, r, n=12):
    """Flat polygon in the XZ plane at height y."""
    v = [(cx + r*math.cos(2*math.pi*i/n), y, cz + r*math.sin(2*math.pi*i/n))
         for i in range(n)]
    e = [(i,(i+1)%n) for i in range(n)]
    return v, e


def _lines(*pts):
    """Simple polyline from a list of (x,y,z) points."""
    v = list(pts)
    e = [(i, i+1) for i in range(len(v)-1)]
    return v, e


def _add(verts, edges, new_v, new_e):
    off = len(verts)
    verts.extend(new_v)
    edges.extend((a+off, b+off) for a, b in new_e)


def _table(cx, cz, w, d, th=2.2, leg=0.10):
    top_y = th - 0.15
    v, e = _box(cx-w/2, top_y, cz-d/2, w, 0.15, d)
    for lx, lz in [(cx-w/2+0.05, cz-d/2+0.05),
                   (cx+w/2-leg-0.05, cz-d/2+0.05),
                   (cx-w/2+0.05, cz+d/2-leg-0.05),
                   (cx+w/2-leg-0.05, cz+d/2-leg-0.05)]:
        _add(v, e, *_box(lx, 0, lz, leg, top_y, leg))
    return v, e


def _room_shell(hw, h, depth, step=1.0):
    """Floor grid + back wall + side walls + ceiling perimeter."""
    v, e = [], []
    # Floor grid
    x = -hw
    while x <= hw+0.001:
        _add(v, e, [(x,0,0),(x,0,depth)], [(0,1)]); x += step
    z = 0
    while z <= depth+0.001:
        _add(v, e, [(-hw,0,z),(hw,0,z)], [(0,1)]); z += step
    # Back wall
    _add(v, e, [(-hw,0,depth),(hw,0,depth),(hw,h,depth),(-hw,h,depth)],
         [(0,1),(1,2),(2,3),(3,0)])
    # Side walls
    for sx in (-hw, hw):
        _add(v, e, [(sx,0,0),(sx,0,depth),(sx,h,depth),(sx,h,0)],
             [(0,1),(1,2),(2,3),(3,0),(0,3)])
    # Ceiling ring
    _add(v, e, [(-hw,h,0),(hw,h,0),(hw,h,depth),(-hw,h,depth)],
         [(0,1),(1,2),(2,3),(3,0)])
    return v, e


# ---------------------------------------------------------------------------
# Glow drawing
# ---------------------------------------------------------------------------

def _draw_group(surface, verts, edges, color, vp_cx, vp_cy, vp_hw, vp_hh,
                alpha_core=220, glow=True):
    r, g, b = min(255,color[0]), min(255,color[1]), min(255,color[2])
    pts = [project(x,y,z,vp_cx,vp_cy,vp_hw,vp_hh) for x,y,z in verts]
    layers = [(7, max(1,int(alpha_core*0.08))),
              (3, max(1,int(alpha_core*0.22))),
              (1, alpha_core)] if glow else [(1, alpha_core)]
    vw, vh = int(vp_hw*2), int(vp_hh*2)
    ox, oy = int(vp_cx-vp_hw), int(vp_cy-vp_hh)
    for width, alpha in layers:
        layer = pygame.Surface((vw, vh), pygame.SRCALPHA)
        for i, j in edges:
            if i < len(pts) and j < len(pts) and pts[i] and pts[j]:
                p1 = (pts[i][0]-ox, pts[i][1]-oy)
                p2 = (pts[j][0]-ox, pts[j][1]-oy)
                if (max(p1[0],p2[0]) < -8 or min(p1[0],p2[0]) > vw+8
                 or max(p1[1],p2[1]) < -8 or min(p1[1],p2[1]) > vh+8):
                    continue
                pygame.draw.line(layer, (r,g,b,alpha), p1, p2, width)
        surface.blit(layer, (ox, oy))


# ---------------------------------------------------------------------------
# Base room class
# ---------------------------------------------------------------------------

class WireRoom:
    NAME       = "Room"
    ROOM_COLOR = (120, 200, 255)
    SLOTS      = []

    def __init__(self):
        self._shell_v, self._shell_e = [], []
        self._objects = {}   # slot → (verts, edges, color)
        self._build()

    def _build(self): pass

    def _obj(self, name, v, e, color):
        self._objects[name] = (v, e, color)

    def draw(self, surface, t, vp_x=186, vp_y=4, vp_w=450, vp_h=352,
             active_slots=None):
        vp_cx, vp_cy = vp_x + vp_w//2, vp_y + vp_h//2
        vp_hw, vp_hh = vp_w/2, vp_h/2

        # Breathing shell
        pulse = (math.sin(t * 0.9) + 1) / 2
        rc = tuple(int(c * (0.18 + 0.10 * pulse)) for c in self.ROOM_COLOR)
        _draw_group(surface, self._shell_v, self._shell_e, rc,
                    vp_cx, vp_cy, vp_hw, vp_hh, alpha_core=110, glow=True)

        for slot, (v, e, col) in self._objects.items():
            occupied = bool(active_slots and slot in active_slots)
            if occupied:
                gp = (math.sin(t * 3.5 + hash(slot) % 7) + 1) / 2
                c  = tuple(min(255, int(c2*(0.8+0.5*gp))) for c2 in col)
                al = 245
            else:
                c  = tuple(int(c2*0.6) for c2 in col)
                al = 155
            _draw_group(surface, v, e, c, vp_cx, vp_cy, vp_hw, vp_hh,
                        alpha_core=al, glow=True)


# ---------------------------------------------------------------------------
# Kitchen  — bright amber/yellow, neon cyan fridge, hot orange stove
# ---------------------------------------------------------------------------

class KitchenRoom(WireRoom):
    NAME       = "Kitchen"
    ROOM_COLOR = (255, 210,  40)
    SLOTS      = ["fridge", "stove", "table"]

    def _build(self):
        self._shell_v, self._shell_e = _room_shell(4.5, 4.5, 8.5)

        # ---- Ceiling lamp ----
        lv, le = [(0,4.5,4.5),(0,3.1,4.5)], [(0,1)]
        _add(lv, le, *_circle(0, 3.1, 4.5, 0.65, 10))
        _add(lv, le, *_circle(0, 2.9, 4.5, 0.45,  8))
        for a in [0, math.pi/2, math.pi, 3*math.pi/2]:
            _add(lv, le,
                 [(0.65*math.cos(a), 3.1, 4.5+0.65*math.sin(a)),
                  (0.45*math.cos(a), 2.9, 4.5+0.45*math.sin(a))], [(0,1)])
        self._obj("_lamp", lv, le, (255, 250, 180))

        # ---- Counter + cabinets ----
        cv, ce = [], []
        _add(cv, ce, *_box(-4.5, 0, 7.0, 9.0, 2.3, 0.85))   # back counter
        _add(cv, ce, *_box(-4.5, 0, 2.5, 0.85, 2.3, 4.5))   # side counter
        _add(cv, ce, *_box(-4.0, 2.9, 7.2, 7.0, 1.5, 0.6))  # wall cabinets
        _add(cv, ce, *_box(-1.0, 2.3, 7.1, 1.2, 0.15, 0.75)) # sink basin
        # Sink faucet
        _add(cv, ce, [(-0.4, 2.45, 7.1),(-0.4, 2.9, 7.1),(-0.4, 2.9, 6.8)],
             [(0,1),(1,2)])
        self._obj("_counter", cv, ce, (200, 175, 120))

        # ---- Fridge ----
        fv, fe = [], []
        _add(fv, fe, *_box(-4.2, 0, 6.0, 1.2, 4.4, 0.95))
        _add(fv, fe, [(-4.2,1.6,6.0),(-3.0,1.6,6.0)], [(0,1)])  # shelf line
        _add(fv, fe, [(-3.05,3.2,6.07),(-3.05,2.5,6.07)], [(0,1)]) # handle
        # Freezer panel line
        _add(fv, fe, [(-4.2,3.3,6.0),(-3.0,3.3,6.0)], [(0,1)])
        # Logo circle
        _add(fv, fe, *_circle(-3.6, 0.6, 6.0, 0.22, 8))
        self._obj("fridge", fv, fe, (0, 220, 255))  # electric cyan

        # ---- Stove ----
        sv, se = [], []
        _add(sv, se, *_box(-3.5, 2.3, 7.05, 2.0, 0.05, 0.75)) # flat top
        for bx, bz in [(-3.1,7.25),(-2.1,7.25),(-3.1,7.6),(-2.1,7.6)]:
            _add(sv, se, *_circle(bx, 2.38, bz, 0.26, 12))
            _add(sv, se, *_circle(bx, 2.38, bz, 0.10,  6))
        _add(sv, se, *_box(-3.5, 2.35, 7.8, 2.0, 0.85, 0.05)) # back panel
        # Knobs
        for kx in [-3.3, -2.8, -2.3, -1.8]:
            _add(sv, se, *_circle(kx, 2.7, 7.8, 0.07, 6))
        self._obj("stove", sv, se, (255,  90,  10))  # hot orange

        # ---- Table + chairs ----
        tv, te = _table(0.5, 3.5, 2.8, 1.6)
        # Chair 1
        _add(tv, te, *_box(-0.8, 0, 2.0, 0.9, 0.8, 0.8))
        _add(tv, te, *_box(-0.8, 0.8, 2.8, 0.9, 1.3, 0.1))
        # Chair 2
        _add(tv, te, *_box(0.7, 0, 4.8, 0.9, 0.8, 0.8))
        _add(tv, te, *_box(0.7, 0.8, 4.8, 0.9, 1.3, 0.1))
        self._obj("table", tv, te, (220, 240, 255))

        # ---- Window ----
        wv = [(-1.2,2.0,8.48),(1.2,2.0,8.48),(1.2,3.9,8.48),(-1.2,3.9,8.48)]
        we = [(0,1),(1,2),(2,3),(3,0)]
        _add(wv, we, [(0,2.0,8.48),(0,3.9,8.48)], [(0,1)])
        _add(wv, we, [(-1.2,2.95,8.48),(1.2,2.95,8.48)], [(0,1)])
        self._obj("_window", wv, we, (160, 220, 255))


# ---------------------------------------------------------------------------
# Bedroom  — electric violet, hot pink bed, teal dresser, neon green poster
# ---------------------------------------------------------------------------

class BedroomRoom(WireRoom):
    NAME       = "Bedroom"
    ROOM_COLOR = (180,  50, 255)
    SLOTS      = ["bed", "dresser", "poster"]

    def _build(self):
        self._shell_v, self._shell_e = _room_shell(4.5, 4.5, 8.5)

        # ---- Ceiling fan ----
        cfv, cfe = [(0,4.5,4.5),(0,4.25,4.5)], [(0,1)]
        _add(cfv, cfe, *_circle(0, 4.25, 4.5, 0.25, 8))  # motor hub
        for ang in [0, math.pi/2, math.pi, 3*math.pi/2]:
            # Blade as narrow parallelogram
            a2 = ang + 0.25
            bv = [(0,4.2,4.5),
                  (1.3*math.cos(ang),   4.2, 4.5+1.3*math.sin(ang)),
                  (1.3*math.cos(a2)*0.9,4.18,4.5+1.3*math.sin(a2)*0.9),
                  (0,4.18,4.5)]
            _add(cfv, cfe, bv, [(0,1),(1,2),(2,3),(3,0)])
        self._obj("_fan", cfv, cfe, (210, 180, 255))

        # ---- Rug ----
        rv, re = [], []
        _add(rv, re, *_circle(0, 0.02, 4.5, 2.2, 16))
        _add(rv, re, *_circle(0, 0.02, 4.5, 1.6, 16))
        _add(rv, re, *_circle(0, 0.02, 4.5, 0.9, 12))
        self._obj("_rug", rv, re, (120, 40, 180))

        # ---- Bed ----
        bv, be = [], []
        _add(bv, be, *_box(-4.3, 0.4, 2.0, 3.5, 0.7, 4.6))  # mattress
        _add(bv, be, *_box(-4.3, 0.4, 1.7, 3.5, 1.9, 0.3))  # headboard
        _add(bv, be, *_box(-4.3, 0.4, 6.6, 3.5, 0.7, 0.2))  # footboard
        _add(bv, be, *_box(-4.0, 1.1, 1.9, 1.2, 0.22, 0.9)) # pillow 1
        _add(bv, be, *_box(-2.5, 1.1, 1.9, 1.2, 0.22, 0.9)) # pillow 2
        _add(bv, be, *_box(-4.2, 1.1, 3.9, 3.3, 0.18, 2.8)) # blanket
        # Headboard decoration lines
        for dy in [0.7, 1.2, 1.6]:
            _add(bv, be, [(-4.3,0.4+dy,1.7),(-0.8,0.4+dy,1.7)], [(0,1)])
        self._obj("bed", bv, be, (255,  50, 180))  # hot pink

        # ---- Nightstand + lamp ----
        nsv, nse = [], []
        _add(nsv, nse, *_box(-4.2, 0, 6.8, 1.0, 1.8, 0.9))
        _add(nsv, nse, [(-3.9,1.8,7.15),(-3.9,2.6,7.15)], [(0,1)]) # lamp stem
        _add(nsv, nse, *_circle(-3.9, 3.0, 7.15, 0.4, 8))  # shade ring
        _add(nsv, nse, *_circle(-3.9, 2.6, 7.15, 0.2, 6))  # base ring
        self._obj("_nightstand", nsv, nse, (80, 230, 210))

        # ---- Dresser + mirror ----
        dv, de = [], []
        _add(dv, de, *_box(2.8, 0, 6.0, 1.5, 3.2, 0.9))
        for dy in [0.9, 1.8, 2.7]:
            _add(dv, de, [(2.8,dy,6.0),(4.3,dy,6.0)], [(0,1)])
        for dy in [0.45, 1.35, 2.25]:
            _add(dv, de, [(3.3,dy+0.3,5.93),(3.8,dy+0.3,5.93)], [(0,1)])
        _add(dv, de, *_box(2.9, 3.2, 5.96, 1.3, 1.9, 0.05))  # mirror
        mir = [(3.05,3.4,5.92),(4.1,3.4,5.92),(4.1,4.85,5.92),(3.05,4.85,5.92)]
        _add(dv, de, mir, [(0,1),(1,2),(2,3),(3,0)])
        self._obj("dresser", dv, de, (0, 255, 200))  # electric teal

        # ---- Poster with star ----
        pv, pe = [], []
        _add(pv, pe, *_box(-1.0, 1.4, 8.46, 2.0, 2.8, 0.05))
        # 5-point neon star
        n = 10
        star = [(0 + (0.75 if i%2==0 else 0.35)*math.cos(math.pi/2+2*math.pi*i/n),
                 2.8 + (0.75 if i%2==0 else 0.35)*math.sin(math.pi/2+2*math.pi*i/n),
                 8.44) for i in range(n)]
        _add(pv, pe, star, [(i,(i+1)%n) for i in range(n)])
        self._obj("poster", pv, pe, (80, 255,  60))  # neon green


# ---------------------------------------------------------------------------
# Garage  — electric green, lime car, amber workbench
# ---------------------------------------------------------------------------

class GarageRoom(WireRoom):
    NAME       = "Garage"
    ROOM_COLOR = ( 0, 255, 140)
    SLOTS      = ["car", "workbench"]

    def _build(self):
        self._shell_v, self._shell_e = _room_shell(5.5, 4.5, 10.0)

        # ---- Garage door (front wall z≈0.25) ----
        gdv = [(-5.5,0,0.25),(5.5,0,0.25),(5.5,4.0,0.25),(-5.5,4.0,0.25)]
        gde = [(0,1),(1,2),(2,3),(3,0)]
        for dy in [0.9, 1.8, 2.7]:
            _add(gdv, gde, [(-5.5,dy,0.25),(5.5,dy,0.25)], [(0,1)])
        # Vertical door segments
        for dx in [-2.0, 0, 2.0]:
            _add(gdv, gde, [(dx,0,0.25),(dx,4.0,0.25)], [(0,1)])
        self._obj("_garagedoor", gdv, gde, (0, 180, 100))

        # ---- Fluorescent ceiling lights ----
        for lx in [-2.5, 2.5]:
            lv = [(lx-0.06,4.38,3.5),(lx+0.06,4.38,3.5),
                  (lx+0.06,4.38,7.5),(lx-0.06,4.38,7.5)]
            le = [(0,1),(1,2),(2,3),(3,0)]
            _add(lv, le, [(lx,4.33,3.5),(lx,4.33,7.5)], [(0,1)])  # glow line
            self._obj(f"_light{int(lx)}", lv, le, (200, 255, 210))

        # ---- Car ----
        cv, ce = [], []
        _add(cv, ce, *_box(-3.2, 0.6, 1.8, 6.0, 1.0, 2.8))  # body
        _add(cv, ce, *_box(-1.8, 1.6, 2.0, 3.4, 1.15, 2.4)) # cab
        # Windscreen (front)
        _add(cv, ce, [(-3.2,0.6,1.8),(-1.8,1.6,2.0),
                       (-1.8,1.6,4.4),(-3.2,0.6,4.6)],
             [(0,1),(1,2),(2,3),(3,0),(0,3),(1,2)])
        # Rear window
        _add(cv, ce, [(1.6,1.6,2.0),(2.8,0.6,1.8),
                       (2.8,0.6,4.6),(1.6,1.6,4.4)],
             [(0,1),(1,2),(2,3),(3,0)])
        # Side windows (left)
        _add(cv, ce, [(-1.8,1.6,2.0),(-1.8,2.75,2.25),
                       (-1.8,2.75,4.15),(-1.8,1.6,4.4)],
             [(0,1),(1,2),(2,3),(3,0)])
        # Door lines
        _add(cv, ce, [(-1.8,0.6,3.3),(-1.8,1.6,3.3)], [(0,1)])
        _add(cv, ce, [(1.6,0.6,3.3),(1.6,1.6,3.3)], [(0,1)])
        # 4 round wheels
        for wx, wz in [(-2.3,2.0),(-2.3,4.6),(1.7,2.0),(1.7,4.6)]:
            _add(cv, ce, *_circle(wx, 0.58, wz, 0.58, 16))
            _add(cv, ce, *_circle(wx, 0.58, wz, 0.25,  8))  # hub
            _add(cv, ce, *_circle(wx, 0.58, wz, 0.08,  5))  # lug
            # Spokes
            for spoke_a in [0, math.pi/3, 2*math.pi/3, math.pi, 4*math.pi/3, 5*math.pi/3]:
                _add(cv, ce,
                     [(wx+0.08*math.cos(spoke_a),0.58,wz+0.08*math.sin(spoke_a)),
                      (wx+0.25*math.cos(spoke_a),0.58,wz+0.25*math.sin(spoke_a))],
                     [(0,1)])
        # Front/rear bumpers
        _add(cv, ce, *_box(-3.35,0.6,1.6,6.3,0.4,0.2))
        _add(cv, ce, *_box(-3.35,0.6,4.8,6.3,0.4,0.2))
        # Headlights
        _add(cv, ce, *_circle(-3.0, 0.9, 1.78, 0.25, 8))
        _add(cv, ce, *_circle( 2.4, 0.9, 1.78, 0.25, 8))
        self._obj("car", cv, ce, (0, 255,  70))  # lime green

        # ---- Workbench ----
        wbv, wbe = _table(4.5, 7.5, 2.4, 1.2, th=3.0)
        _add(wbv, wbe, *_box(3.4, 3.0, 8.15, 2.2, 1.6, 0.06))  # pegboard
        # Tools on pegboard
        _add(wbv, wbe, [(3.85,3.4,8.1),(3.85,4.3,8.1)], [(0,1)])    # hammer handle
        _add(wbv, wbe, *_box(3.7, 4.3, 8.08, 0.32, 0.22, 0.05))     # hammer head
        _add(wbv, wbe, [(4.5,3.3,8.1),(4.5,4.3,8.1)], [(0,1)])       # wrench handle
        _add(wbv, wbe, *_circle(4.5, 3.35, 8.09, 0.18, 8))           # wrench end
        _add(wbv, wbe, *_circle(4.5, 4.25, 8.09, 0.14, 6))
        # Vice on bench surface
        _add(wbv, wbe, *_box(3.4,3.0,7.3,0.7,0.55,0.55))
        _add(wbv, wbe, [(3.4,3.28,7.58),(4.1,3.28,7.58)], [(0,1)])   # screw
        # Oil stain on floor
        _add(wbv, wbe, *_circle(2.5, 0.01, 6.5, 0.6, 10))
        _add(wbv, wbe, *_circle(2.5, 0.01, 6.5, 0.3,  8))
        self._obj("workbench", wbv, wbe, (255, 175,   0))  # amber


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PREBUILT       = {"kitchen": KitchenRoom, "bedroom": BedroomRoom, "garage": GarageRoom}
PREBUILT_NAMES = ["kitchen", "bedroom", "garage"]
PREBUILT_SLOTS = {
    "kitchen": ["fridge", "stove", "table"],
    "bedroom": ["bed",    "dresser", "poster"],
    "garage":  ["car",    "workbench"],
}

_cache: dict = {}

def get_room(room_type: str):
    k = room_type.lower()
    if k not in _cache:
        cls = PREBUILT.get(k)
        if cls:
            _cache[k] = cls()
    return _cache.get(k)
