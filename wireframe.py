"""
3D room renderer — clean flat-shaded + wireframe style.

Solid face fills for depth, bright thick wireframe outlines on top.
Dark background, vivid Arcade-inspired neon palette.

Coordinate system: x=right, y=up (0=floor), z=into room.
Camera elevated at ~30° above floor for a clear overview.
"""

import pygame
import math


# ---------------------------------------------------------------------------
# Camera  —  elevated perspective, wider FOV, less squishing
# ---------------------------------------------------------------------------

_EYE    = ( 0.0,  7.5, -7.5)   # high + back
_TARGET = ( 0.0,  1.0,  5.0)   # look at mid-room, floor level
_UP     = ( 0.0,  1.0,  0.0)
_FOV    = 60.0


def _build_basis(eye, target, up):
    fx, fy, fz = target[0]-eye[0], target[1]-eye[1], target[2]-eye[2]
    fl = math.sqrt(fx*fx + fy*fy + fz*fz)
    fx, fy, fz = fx/fl, fy/fl, fz/fl
    rx = up[1]*fz - up[2]*fy
    ry = up[2]*fx - up[0]*fz
    rz = up[0]*fy - up[1]*fx
    rl = math.sqrt(rx*rx + ry*ry + rz*rz)
    rx, ry, rz = rx/rl, ry/rl, rz/rl
    ux = fy*rz - fz*ry          # true up = cross(forward, right)
    uy = fz*rx - fx*rz
    uz = fx*ry - fy*rx
    return (rx,ry,rz), (ux,uy,uz), (fx,fy,fz)


_R, _U, _F = _build_basis(_EYE, _TARGET, _UP)


def project(x, y, z, vp_cx, vp_cy, vp_hw, vp_hh):
    """World → screen pixel. Returns (sx, sy) or None if behind camera."""
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
    e = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    return v, e


def _box_faces(x, y, z, w, h, d):
    """6 face quads — back-to-front order for painter's algorithm."""
    return [
        [(x,y+h,z),(x+w,y+h,z),(x+w,y+h,z+d),(x,y+h,z+d)],     # top
        [(x,y,z+d),(x+w,y,z+d),(x+w,y+h,z+d),(x,y+h,z+d)],     # back face
        [(x,y,z),(x,y+h,z),(x,y+h,z+d),(x,y,z+d)],              # left
        [(x+w,y,z),(x+w,y+h,z),(x+w,y+h,z+d),(x+w,y,z+d)],     # right
        [(x,y,z),(x+w,y,z),(x+w,y+h,z),(x,y+h,z)],              # front face
        [(x,y,z),(x+w,y,z),(x+w,y,z+d),(x,y,z+d)],              # bottom
    ]


def _circle(cx, y, cz, r, n=12):
    """Flat circle in the XZ plane at height y."""
    v = [(cx + r*math.cos(2*math.pi*i/n), y, cz + r*math.sin(2*math.pi*i/n))
         for i in range(n)]
    e = [(i,(i+1)%n) for i in range(n)]
    return v, e


def _lines(*pts):
    v = list(pts)
    e = [(i, i+1) for i in range(len(v)-1)]
    return v, e


def _add(verts, edges, new_v, new_e):
    off = len(verts)
    verts.extend(new_v)
    edges.extend((a+off, b+off) for a, b in new_e)


def _table(cx, cz, w, d, th=2.2, leg=0.12):
    top_y = th - 0.15
    v, e = _box(cx-w/2, top_y, cz-d/2, w, 0.18, d)
    for lx, lz in [(cx-w/2+0.06, cz-d/2+0.06), (cx+w/2-leg-0.06, cz-d/2+0.06),
                   (cx-w/2+0.06, cz+d/2-leg-0.06), (cx+w/2-leg-0.06, cz+d/2-leg-0.06)]:
        _add(v, e, *_box(lx, 0, lz, leg, top_y, leg))
    return v, e


def _room_shell(hw, h, depth, step=1.0):
    """Floor grid + wall outlines + ceiling ring."""
    v, e = [], []
    x = -hw
    while x <= hw + 0.001:
        _add(v, e, [(x, 0, 0), (x, 0, depth)], [(0, 1)])
        x += step
    z = 0
    while z <= depth + 0.001:
        _add(v, e, [(-hw, 0, z), (hw, 0, z)], [(0, 1)])
        z += step
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
# Drawing — batched face fills  +  thick glow wireframe
# ---------------------------------------------------------------------------

def _draw_faces_batch(surface, faces, vp_cx, vp_cy, vp_hw, vp_hh):
    """Project & fill all faces in one SRCALPHA blit (painter's order)."""
    if not faces:
        return
    vw, vh = int(vp_hw * 2), int(vp_hh * 2)
    ox, oy = int(vp_cx - vp_hw), int(vp_cy - vp_hh)
    layer  = pygame.Surface((vw, vh), pygame.SRCALPHA)
    for pts3d, color, alpha in faces:
        pts2d, valid = [], True
        for x, y, z in pts3d:
            p = project(x, y, z, vp_cx, vp_cy, vp_hw, vp_hh)
            if p is None:
                valid = False
                break
            pts2d.append((p[0] - ox, p[1] - oy))
        if valid and len(pts2d) >= 3:
            r, g, b = min(255, color[0]), min(255, color[1]), min(255, color[2])
            pygame.draw.polygon(layer, (r, g, b, alpha), pts2d)
    surface.blit(layer, (ox, oy))


def _draw_group(surface, verts, edges, color, vp_cx, vp_cy, vp_hw, vp_hh,
                alpha_core=220, glow=True, lw=2):
    r, g, b = min(255, color[0]), min(255, color[1]), min(255, color[2])
    pts = [project(x, y, z, vp_cx, vp_cy, vp_hw, vp_hh) for x, y, z in verts]
    layers = [(lw + 7, max(1, int(alpha_core * 0.07))),
              (lw + 3, max(1, int(alpha_core * 0.20))),
              (lw,     alpha_core)] if glow else [(lw, alpha_core)]
    vw, vh = int(vp_hw * 2), int(vp_hh * 2)
    ox, oy = int(vp_cx - vp_hw), int(vp_cy - vp_hh)
    for width, alpha in layers:
        layer = pygame.Surface((vw, vh), pygame.SRCALPHA)
        for i, j in edges:
            if i < len(pts) and j < len(pts) and pts[i] and pts[j]:
                p1 = (pts[i][0] - ox, pts[i][1] - oy)
                p2 = (pts[j][0] - ox, pts[j][1] - oy)
                if (max(p1[0], p2[0]) < -8 or min(p1[0], p2[0]) > vw + 8
                 or max(p1[1], p2[1]) < -8 or min(p1[1], p2[1]) > vh + 8):
                    continue
                pygame.draw.line(layer, (r, g, b, alpha), p1, p2, width)
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
        self._room_faces = []   # (pts3d, color, alpha)  — painted first
        self._objects    = {}   # slot → (verts, edges, color)
        self._obj_faces  = {}   # slot → [(pts3d, color)]
        self._build()

    def _build(self): pass

    # --- geometry helpers ---

    def _face(self, pts, color, alpha=65):
        self._room_faces.append((pts, color, alpha))

    def _add_shell_faces(self, hw, h, depth):
        """Solid tinted fills for room shell. Painted back-to-front."""
        rc = self.ROOM_COLOR
        def f(t): return tuple(int(c * t) for c in rc)
        self._face([(-hw,h,0),(hw,h,0),(hw,h,depth),(-hw,h,depth)], f(0.10), 130)
        self._face([(-hw,0,depth),(hw,0,depth),(hw,h,depth),(-hw,h,depth)], f(0.20), 190)
        self._face([(-hw,0,0),(-hw,0,depth),(-hw,h,depth),(-hw,h,0)], f(0.15), 165)
        self._face([(hw,0,0),(hw,0,depth),(hw,h,depth),(hw,h,0)],     f(0.15), 165)
        self._face([(-hw,0,0),(hw,0,0),(hw,0,depth),(-hw,0,depth)],   f(0.28), 210)

    def _obj(self, name, v, e, color):
        self._objects[name] = (v, e, color)

    def _obj_face(self, slot, pts, color):
        self._obj_faces.setdefault(slot, []).append((pts, color))

    def _obj_box(self, slot, x, y, z, w, h, d, color):
        """Register box wireframe AND box face fills in one call."""
        v, e = _box(x, y, z, w, h, d)
        if slot not in self._objects:
            self._objects[slot] = (v, e, color)
        else:
            sv, se, sc = self._objects[slot]
            _add(sv, se, v, e)
        for pts in _box_faces(x, y, z, w, h, d):
            self._obj_face(slot, pts, color)

    # --- draw ---

    def draw(self, surface, t, vp_x=186, vp_y=4, vp_w=490, vp_h=332,
             active_slots=None):
        vp_cx = vp_x + vp_w // 2
        vp_cy = vp_y + vp_h // 2
        vp_hw = vp_w / 2
        vp_hh = vp_h / 2

        # 1. Room face fills (floor, walls)
        _draw_faces_batch(surface, self._room_faces, vp_cx, vp_cy, vp_hw, vp_hh)

        # 2. Object face fills — inactive first, then active on top
        inactive_f, active_f = [], []
        for slot, face_list in self._obj_faces.items():
            deco = slot.startswith("_")
            occ  = deco or bool(active_slots and slot in active_slots)
            a    = 140 if occ else 60
            sc   = 0.80 if occ else 0.35
            for pts, col in face_list:
                tint = tuple(min(255, int(c * sc)) for c in col)
                (active_f if occ else inactive_f).append((pts, tint, a))
        _draw_faces_batch(surface, inactive_f, vp_cx, vp_cy, vp_hw, vp_hh)
        _draw_faces_batch(surface, active_f,   vp_cx, vp_cy, vp_hw, vp_hh)

        # 3. Room shell wireframe (dim grid + outlines)
        pulse = (math.sin(t * 0.9) + 1) / 2
        rc = tuple(int(c * (0.38 + 0.14 * pulse)) for c in self.ROOM_COLOR)
        _draw_group(surface, self._shell_v, self._shell_e, rc,
                    vp_cx, vp_cy, vp_hw, vp_hh, alpha_core=150, glow=True, lw=1)

        # 4. Object wireframe edges
        for slot, (v, e, col) in self._objects.items():
            deco = slot.startswith("_")
            occ  = deco or bool(active_slots and slot in active_slots)
            gp   = (math.sin(t * 3.5 + hash(slot) % 7) + 1) / 2 if occ else 0
            c    = (tuple(min(255, int(c2 * (0.85 + 0.40 * gp))) for c2 in col)
                    if occ else tuple(int(c2 * 0.55) for c2 in col))
            al   = 255 if occ else 175
            lw   = 2 if (occ and not deco) else 1
            _draw_group(surface, v, e, c, vp_cx, vp_cy, vp_hw, vp_hh,
                        alpha_core=al, glow=True, lw=lw)


# ---------------------------------------------------------------------------
# Kitchen  —  amber, cyan fridge, orange stove, white table
# ---------------------------------------------------------------------------

class KitchenRoom(WireRoom):
    NAME       = "Kitchen"
    ROOM_COLOR = (255, 210,  40)
    SLOTS      = ["fridge", "stove", "table"]

    def _build(self):
        HW, H, D = 4.5, 4.5, 8.5
        self._shell_v, self._shell_e = _room_shell(HW, H, D)
        self._add_shell_faces(HW, H, D)

        # ---- Ceiling lamp ----
        lv, le = [(0, H, 4.5), (0, 3.1, 4.5)], [(0, 1)]
        _add(lv, le, *_circle(0, 3.1, 4.5, 0.70, 10))
        _add(lv, le, *_circle(0, 2.85, 4.5, 0.48, 8))
        for a in [0, math.pi/2, math.pi, 3*math.pi/2]:
            _add(lv, le, [(0.70*math.cos(a), 3.1, 4.5 + 0.70*math.sin(a)),
                          (0.48*math.cos(a), 2.85, 4.5 + 0.48*math.sin(a))], [(0, 1)])
        self._obj("_lamp", lv, le, (255, 255, 180))
        self._obj_face("_lamp",
            [(-0.70,3.1,3.8),(0.70,3.1,3.8),(0.70,3.1,5.2),(-0.70,3.1,5.2)],
            (255, 255, 180))

        # ---- L-shaped counter + wall cabinets ----
        cv, ce = [], []
        _add(cv, ce, *_box(-HW, 0, 7.2, HW*2, 2.3, 0.9))   # back counter
        _add(cv, ce, *_box(-HW, 0, 2.6, 0.9, 2.3, 4.6))    # side counter
        _add(cv, ce, *_box(-4.0, 2.9, 7.4, 7.0, 1.5, 0.6)) # wall cabinets
        _add(cv, ce, *_box(-1.0, 2.3, 7.2, 1.2, 0.15, 0.8)) # sink basin
        _add(cv, ce, [(-0.4, 2.45, 7.2), (-0.4, 2.9, 7.2), (-0.4, 2.9, 6.9)],
             [(0, 1), (1, 2)])                                # tap
        self._obj("_counter", cv, ce, (200, 175, 120))
        for pts in _box_faces(-HW, 0, 7.2, HW*2, 2.3, 0.9):
            self._obj_face("_counter", pts, (180, 155, 100))

        # ---- Fridge ----
        fv, fe = [], []
        _add(fv, fe, *_box(-4.1, 0, 6.0, 1.3, 4.3, 1.0))
        _add(fv, fe, [(-4.1, 1.7, 6.0), (-2.8, 1.7, 6.0)], [(0, 1)])
        _add(fv, fe, [(-4.1, 3.4, 6.0), (-2.8, 3.4, 6.0)], [(0, 1)])
        _add(fv, fe, [(-2.88, 3.2, 6.08), (-2.88, 2.5, 6.08)], [(0, 1)])
        _add(fv, fe, *_circle(-3.45, 0.65, 6.0, 0.24, 8))
        self._obj("fridge", fv, fe, (0, 220, 255))
        self._obj_box("fridge", -4.1, 0, 6.0, 1.3, 4.3, 1.0, (0, 190, 230))

        # ---- Stove ----
        sv, se = [], []
        _add(sv, se, *_box(-3.6, 2.3, 7.1, 2.2, 0.06, 0.8))  # flat top
        for bx, bz in [(-3.2, 7.32), (-2.2, 7.32), (-3.2, 7.68), (-2.2, 7.68)]:
            _add(sv, se, *_circle(bx, 2.38, bz, 0.28, 12))
            _add(sv, se, *_circle(bx, 2.38, bz, 0.10, 6))
        _add(sv, se, *_box(-3.6, 2.36, 7.9, 2.2, 0.9, 0.06))  # back panel
        for kx in [-3.4, -2.9, -2.4, -1.9]:
            _add(sv, se, *_circle(kx, 2.75, 7.9, 0.08, 6))
        self._obj("stove", sv, se, (255, 100, 20))
        self._obj_box("stove", -3.6, 2.3, 7.1, 2.2, 1.0, 0.8, (230, 80, 15))

        # ---- Table + chairs ----
        tv, te = _table(0.5, 3.5, 2.8, 1.6)
        _add(tv, te, *_box(-0.85, 0, 2.0, 0.95, 0.85, 0.85))
        _add(tv, te, *_box(-0.85, 0.85, 2.85, 0.95, 1.4, 0.1))
        _add(tv, te, *_box(0.65, 0, 4.8, 0.95, 0.85, 0.85))
        _add(tv, te, *_box(0.65, 0.85, 4.8, 0.95, 1.4, 0.1))
        self._obj("table", tv, te, (220, 240, 255))
        self._obj_box("table", -0.65, 2.05, 2.55, 2.6, 0.18, 1.6, (200, 220, 240))

        # ---- Window ----
        wv = [(-1.3, 2.1, D - 0.04), (1.3, 2.1, D - 0.04),
              (1.3, 4.0, D - 0.04), (-1.3, 4.0, D - 0.04)]
        we = [(0, 1), (1, 2), (2, 3), (3, 0)]
        _add(wv, we, [(0, 2.1, D-0.04), (0, 4.0, D-0.04)], [(0, 1)])
        _add(wv, we, [(-1.3, 3.05, D-0.04), (1.3, 3.05, D-0.04)], [(0, 1)])
        self._obj("_window", wv, we, (160, 230, 255))


# ---------------------------------------------------------------------------
# Bedroom  —  violet, hot-pink bed, teal dresser, neon-green poster
# ---------------------------------------------------------------------------

class BedroomRoom(WireRoom):
    NAME       = "Bedroom"
    ROOM_COLOR = (180,  50, 255)
    SLOTS      = ["bed", "dresser", "poster"]

    def _build(self):
        HW, H, D = 4.5, 4.5, 8.5
        self._shell_v, self._shell_e = _room_shell(HW, H, D)
        self._add_shell_faces(HW, H, D)

        # ---- Ceiling fan ----
        cfv, cfe = [(0, H, 4.5), (0, H - 0.25, 4.5)], [(0, 1)]
        _add(cfv, cfe, *_circle(0, H - 0.25, 4.5, 0.28, 8))
        for ang in [0, math.pi/2, math.pi, 3*math.pi/2]:
            a2 = ang + 0.25
            bv = [(0, H-0.3, 4.5),
                  (1.4*math.cos(ang),   H-0.3, 4.5 + 1.4*math.sin(ang)),
                  (1.4*math.cos(a2)*0.9, H-0.32, 4.5 + 1.4*math.sin(a2)*0.9),
                  (0, H-0.32, 4.5)]
            _add(cfv, cfe, bv, [(0,1),(1,2),(2,3),(3,0)])
        self._obj("_fan", cfv, cfe, (210, 180, 255))

        # ---- Rug (concentric ovals) ----
        rv, re = [], []
        for r in [2.4, 1.7, 1.0]:
            _add(rv, re, *_circle(0, 0.02, 4.5, r, 20))
        self._obj("_rug", rv, re, (140, 50, 210))
        self._obj_face("_rug",
            [(-2.4, 0.01, 2.1), (2.4, 0.01, 2.1),
             (2.4, 0.01, 6.9), (-2.4, 0.01, 6.9)],
            (120, 30, 190))

        # ---- Bed ----
        bv, be = [], []
        _add(bv, be, *_box(-HW + 0.1, 0.45, 2.1, 3.6, 0.75, 4.8))  # mattress
        _add(bv, be, *_box(-HW + 0.1, 0.45, 1.8, 3.6, 2.0, 0.35))  # headboard
        _add(bv, be, *_box(-HW + 0.1, 0.45, 6.9, 3.6, 0.75, 0.22)) # footboard
        _add(bv, be, *_box(-4.1, 1.2, 2.0, 1.3, 0.25, 1.0))  # pillow 1
        _add(bv, be, *_box(-2.5, 1.2, 2.0, 1.3, 0.25, 1.0))  # pillow 2
        _add(bv, be, *_box(-4.2, 1.2, 4.1, 3.4, 0.20, 2.9))  # blanket
        for dy in [0.8, 1.3, 1.7]:
            _add(bv, be, [(-HW+0.1, 0.45+dy, 1.8), (-HW+3.7, 0.45+dy, 1.8)], [(0,1)])
        self._obj("bed", bv, be, (255, 50, 180))
        self._obj_box("bed", -HW+0.1, 0.45, 2.1, 3.6, 0.75, 4.8, (230, 40, 160))

        # ---- Nightstand + cone lamp ----
        nsv, nse = [], []
        _add(nsv, nse, *_box(-4.2, 0, 7.0, 1.1, 1.9, 1.0))
        _add(nsv, nse, [(-3.75, 1.9, 7.4), (-3.75, 2.7, 7.4)], [(0, 1)])
        _add(nsv, nse, *_circle(-3.75, 3.1, 7.4, 0.45, 8))
        _add(nsv, nse, *_circle(-3.75, 2.7, 7.4, 0.22, 6))
        self._obj("_nightstand", nsv, nse, (80, 230, 210))
        self._obj_box("_nightstand", -4.2, 0, 7.0, 1.1, 1.9, 1.0, (60, 200, 180))

        # ---- Dresser + mirror ----
        dv, de = [], []
        _add(dv, de, *_box(2.7, 0, 6.1, 1.6, 3.4, 1.0))
        for dy in [0.95, 1.90, 2.85]:
            _add(dv, de, [(2.7, dy, 6.1), (4.3, dy, 6.1)], [(0, 1)])
        for dy in [0.5, 1.45, 2.4]:
            _add(dv, de, [(3.25, dy+0.28, 6.03), (3.75, dy+0.28, 6.03)], [(0, 1)])
        mir = [(2.85, 3.4, 6.0), (4.15, 3.4, 6.0), (4.15, 5.0, 6.0), (2.85, 5.0, 6.0)]
        _add(dv, de, mir, [(0,1),(1,2),(2,3),(3,0)])
        self._obj("dresser", dv, de, (0, 255, 200))
        self._obj_box("dresser", 2.7, 0, 6.1, 1.6, 3.4, 1.0, (0, 220, 170))
        self._obj_face("dresser", mir, (40, 180, 210))

        # ---- Poster with neon star ----
        pv, pe = [], []
        _add(pv, pe, *_box(-1.0, 1.5, D-0.07, 2.0, 2.6, 0.06))
        n = 10
        cy_star = 2.8
        star = [(0 + (0.78 if i % 2 == 0 else 0.36) * math.cos(math.pi/2 + 2*math.pi*i/n),
                 cy_star + (0.78 if i % 2 == 0 else 0.36) * math.sin(math.pi/2 + 2*math.pi*i/n),
                 D - 0.05) for i in range(n)]
        _add(pv, pe, star, [(i, (i+1) % n) for i in range(n)])
        self._obj("poster", pv, pe, (80, 255, 60))
        self._obj_face("poster",
            [(-1.0, 1.5, D-0.06), (1.0, 1.5, D-0.06),
             (1.0, 4.1, D-0.06), (-1.0, 4.1, D-0.06)],
            (50, 200, 40))


# ---------------------------------------------------------------------------
# Garage  —  electric green, lime car, amber workbench
# ---------------------------------------------------------------------------

class GarageRoom(WireRoom):
    NAME       = "Garage"
    ROOM_COLOR = (  0, 255, 140)
    SLOTS      = ["car", "workbench"]

    def _build(self):
        HW, H, D = 5.5, 4.5, 10.0
        self._shell_v, self._shell_e = _room_shell(HW, H, D)
        self._add_shell_faces(HW, H, D)

        # ---- Garage door (front panel) ----
        gdv = [(-HW, 0, 0.3), (HW, 0, 0.3), (HW, 4.2, 0.3), (-HW, 4.2, 0.3)]
        gde = [(0,1),(1,2),(2,3),(3,0)]
        for dy in [1.0, 2.0, 3.0]:
            _add(gdv, gde, [(-HW, dy, 0.3), (HW, dy, 0.3)], [(0, 1)])
        for dx in [-2.2, 0, 2.2]:
            _add(gdv, gde, [(dx, 0, 0.3), (dx, 4.2, 0.3)], [(0, 1)])
        self._obj("_garagedoor", gdv, gde, (0, 190, 110))
        self._obj_face("_garagedoor",
            [(-HW, 0, 0.3), (HW, 0, 0.3), (HW, 4.2, 0.3), (-HW, 4.2, 0.3)],
            (0, 140, 80))

        # ---- Fluorescent ceiling lights ----
        for lx in [-2.8, 2.8]:
            lv = [(lx-0.07, H-0.15, 3.8), (lx+0.07, H-0.15, 3.8),
                  (lx+0.07, H-0.15, 7.8), (lx-0.07, H-0.15, 7.8)]
            le = [(0,1),(1,2),(2,3),(3,0)]
            _add(lv, le, [(lx, H-0.2, 3.8), (lx, H-0.2, 7.8)], [(0, 1)])
            self._obj(f"_light{int(lx)}", lv, le, (210, 255, 220))

        # ---- Car ----
        cv, ce = [], []
        _add(cv, ce, *_box(-3.5, 0.65, 2.0, 6.5, 1.1, 3.0))   # body
        _add(cv, ce, *_box(-2.0, 1.75, 2.2, 3.8, 1.2, 2.5))   # cab
        # windscreen slopes
        _add(cv, ce, [(-3.5,0.65,2.0),(-2.0,1.75,2.2),(-2.0,1.75,4.7),(-3.5,0.65,5.0)],
             [(0,1),(1,2),(2,3),(3,0),(0,3),(1,2)])
        _add(cv, ce, [(1.8,1.75,2.2),(2.9,0.65,2.0),(2.9,0.65,5.0),(1.8,1.75,4.7)],
             [(0,1),(1,2),(2,3),(3,0)])
        # left side window
        _add(cv, ce, [(-2.0,1.75,2.2),(-2.0,2.95,2.4),(-2.0,2.95,4.5),(-2.0,1.75,4.7)],
             [(0,1),(1,2),(2,3),(3,0)])
        # door lines
        _add(cv, ce, [(-2.0,0.65,3.6),(-2.0,1.75,3.6)], [(0,1)])
        _add(cv, ce, [(1.8, 0.65,3.6),(1.8,1.75,3.6)],  [(0,1)])
        # 4 wheels
        for wx, wz in [(-2.5, 2.3), (-2.5, 4.7), (2.1, 2.3), (2.1, 4.7)]:
            _add(cv, ce, *_circle(wx, 0.62, wz, 0.62, 16))
            _add(cv, ce, *_circle(wx, 0.62, wz, 0.26, 8))
            _add(cv, ce, *_circle(wx, 0.62, wz, 0.09, 5))
            for sa in [0, math.pi/3, 2*math.pi/3, math.pi, 4*math.pi/3, 5*math.pi/3]:
                _add(cv, ce,
                     [(wx+0.09*math.cos(sa), 0.62, wz+0.09*math.sin(sa)),
                      (wx+0.26*math.cos(sa), 0.62, wz+0.26*math.sin(sa))], [(0,1)])
        # bumpers + headlights
        _add(cv, ce, *_box(-3.65, 0.65, 1.75, 6.8, 0.45, 0.22))
        _add(cv, ce, *_box(-3.65, 0.65, 5.0,  6.8, 0.45, 0.22))
        _add(cv, ce, *_circle(-3.1, 0.95, 1.92, 0.27, 8))
        _add(cv, ce, *_circle( 2.6, 0.95, 1.92, 0.27, 8))
        self._obj("car", cv, ce, (0, 255, 70))
        self._obj_box("car", -3.5, 0.65, 2.0, 6.5, 1.1, 3.0, (0, 220, 60))
        self._obj_box("car", -2.0, 1.75, 2.2, 3.8, 1.2, 2.5, (0, 200, 55))

        # ---- Workbench + tools ----
        wbv, wbe = _table(4.4, 7.5, 2.5, 1.3, th=3.1)
        _add(wbv, wbe, *_box(3.3, 3.1, 8.2, 2.4, 1.7, 0.07))  # pegboard
        # hammer
        _add(wbv, wbe, [(3.8, 3.5, 8.15), (3.8, 4.4, 8.15)], [(0, 1)])
        _add(wbv, wbe, *_box(3.62, 4.4, 8.12, 0.36, 0.25, 0.06))
        # wrench
        _add(wbv, wbe, [(4.55, 3.4, 8.15), (4.55, 4.4, 8.15)], [(0, 1)])
        _add(wbv, wbe, *_circle(4.55, 3.42, 8.14, 0.20, 8))
        _add(wbv, wbe, *_circle(4.55, 4.38, 8.14, 0.15, 6))
        # vice + oil stain
        _add(wbv, wbe, *_box(3.35, 3.1, 7.3, 0.75, 0.60, 0.60))
        _add(wbv, wbe, [(3.35, 3.40, 7.65), (4.1, 3.40, 7.65)], [(0, 1)])
        _add(wbv, wbe, *_circle(2.4, 0.01, 6.5, 0.65, 12))
        _add(wbv, wbe, *_circle(2.4, 0.01, 6.5, 0.32, 8))
        self._obj("workbench", wbv, wbe, (255, 175, 0))
        self._obj_box("workbench", 3.25, 0, 6.9, 2.5, 3.1, 1.3, (220, 150, 0))


# ---------------------------------------------------------------------------
# Living Room  —  hot magenta, sofa, TV, coffee table
# ---------------------------------------------------------------------------

class LivingRoom(WireRoom):
    NAME       = "Living Room"
    ROOM_COLOR = (255,  60, 160)
    SLOTS      = ["sofa", "tv", "coffee_table"]

    def _build(self):
        HW, H, D = 5.0, 4.5, 9.0
        self._shell_v, self._shell_e = _room_shell(HW, H, D)
        self._add_shell_faces(HW, H, D)

        # ---- Pendant light cluster ----
        for px, pz in [(-1.2, 4.5), (0, 4.5), (1.2, 4.5)]:
            h_drop = 1.0 + abs(px) * 0.3
            lv = [(px, H, pz), (px, H - h_drop, pz)]; le = [(0, 1)]
            _add(lv, le, *_circle(px, H - h_drop, pz, 0.22, 8))
            self._obj("_pendant", lv, le, (255, 230, 130))

        # ---- Sofa (L-shaped, left wall) ----
        sv, se = [], []
        # main body
        _add(sv, se, *_box(-HW+0.1, 0.5, 1.8, 3.2, 0.8, 2.2))  # seat
        _add(sv, se, *_box(-HW+0.1, 0.5, 1.6, 3.2, 1.8, 0.22)) # backrest
        _add(sv, se, *_box(-HW+0.1, 0.5, 1.6, 0.22, 1.8, 2.2)) # left arm
        _add(sv, se, *_box(-HW+3.08,0.5, 1.6, 0.22, 1.8, 2.2)) # right arm
        # chaise longue extension
        _add(sv, se, *_box(-HW+0.1, 0.5, 4.0, 2.0, 0.8, 1.8))
        _add(sv, se, *_box(-HW+0.1, 0.5, 5.8, 2.0, 1.5, 0.22))
        # cushions
        for cz in [2.1, 3.1]:
            _add(sv, se, *_box(-HW+0.5, 1.3, cz, 1.1, 0.35, 0.9))
            _add(sv, se, *_box(-HW+1.7, 1.3, cz, 1.1, 0.35, 0.9))
        self._obj("sofa", sv, se, (255, 80, 180))
        self._obj_box("sofa", -HW+0.1, 0.5, 1.8, 3.2, 0.8, 2.2, (230, 60, 160))
        self._obj_box("sofa", -HW+0.1, 0.5, 1.6, 3.2, 1.8, 0.22, (210, 50, 145))

        # ---- TV + stand ----
        tv, te = [], []
        # stand
        _add(tv, te, *_box(2.8, 0, 7.5, 2.2, 1.5, 0.7))
        _add(tv, te, *_box(3.5, 1.5, 7.55, 0.8, 0.12, 0.6))  # shelf
        # screen frame
        _add(tv, te, *_box(2.6, 1.62, 7.48, 2.6, 1.9, 0.12))
        # screen inside
        sc_pts = [(2.72, 1.75, 7.45), (5.08, 1.75, 7.45),
                  (5.08, 3.42, 7.45), (2.72, 3.42, 7.45)]
        _add(tv, te, sc_pts, [(0,1),(1,2),(2,3),(3,0)])
        self._obj("tv", tv, te, (0, 210, 255))
        self._obj_box("tv", 2.8, 0, 7.5, 2.2, 1.5, 0.7, (0, 160, 200))
        self._obj_box("tv", 2.6, 1.62, 7.48, 2.6, 1.9, 0.12, (0, 30, 50))
        self._obj_face("tv", sc_pts, (0, 60, 100))

        # ---- Coffee table ----
        ctv, cte = _table(0, 3.2, 2.4, 1.4, th=1.2)
        # magazine on table
        _add(ctv, cte, *_box(-0.6, 1.22, 2.7, 1.1, 0.04, 0.7))
        self._obj("coffee_table", ctv, cte, (255, 220, 80))
        self._obj_box("coffee_table", -1.2, 1.05, 2.5, 2.4, 0.15, 1.4, (230, 195, 60))

        # ---- Wall art diptych ----
        for wx, wy in [(-1.4, 2.2), (0.8, 2.2)]:
            av = [(wx, wy, D-0.05), (wx+1.0, wy, D-0.05),
                  (wx+1.0, wy+1.6, D-0.05), (wx, wy+1.6, D-0.05)]
            ae = [(0,1),(1,2),(2,3),(3,0)]
            _add(av, ae, [(wx+0.5, wy+0.3, D-0.04), (wx+0.5, wy+1.3, D-0.04)],
                 [(0, 1)])
            self._obj("_art", av, ae, (255, 150, 200))


# ---------------------------------------------------------------------------
# Library  —  electric blue, warm desk, tall bookcase
# ---------------------------------------------------------------------------

class LibraryRoom(WireRoom):
    NAME       = "Library"
    ROOM_COLOR = ( 30, 130, 255)
    SLOTS      = ["desk", "bookcase", "armchair"]

    def _build(self):
        HW, H, D = 4.5, 4.5, 8.5
        self._shell_v, self._shell_e = _room_shell(HW, H, D)
        self._add_shell_faces(HW, H, D)

        # ---- Chandelier ----
        chv = [(0, H, 4.5), (0, 3.5, 4.5)]; che = [(0, 1)]
        _add(chv, che, *_circle(0, 3.5, 4.5, 0.9, 12))
        for a in range(6):
            ang = a * math.pi / 3
            rx, rz = 0.9*math.cos(ang), 4.5 + 0.9*math.sin(ang)
            _add(chv, che, [(rx, 3.5, rz), (rx*0.6, 3.15, rz*0.6 + 4.5*0.4)], [(0, 1)])
            _add(chv, che, *_circle(rx, 3.0, rz, 0.10, 6))
        self._obj("_chandelier", chv, che, (255, 230, 120))

        # ---- Writing desk + lamp ----
        dv, de = _table(-2.5, 6.0, 3.5, 1.8, th=2.5)
        # desk lamp
        _add(dv, de, [(-2.5, 2.5, 5.5), (-2.5, 3.6, 5.5),
                      (-2.2, 3.8, 5.3), (-1.8, 3.8, 5.3)], [(0,1),(1,2),(2,3)])
        _add(dv, de, *_circle(-1.8, 3.8, 5.3, 0.35, 8))
        # books on desk
        for i, bx in enumerate([-3.9, -3.5, -3.1, -2.7]):
            _add(dv, de, *_box(bx, 2.5, 5.0, 0.25, 0.6 + i*0.08, 0.65))
        # inkwell
        _add(dv, de, *_circle(-1.5, 2.5, 6.2, 0.14, 8))
        self._obj("desk", dv, de, (255, 180, 60))
        self._obj_box("desk", -4.25, 0, 5.1, 3.5, 2.5, 1.8, (220, 150, 40))

        # ---- Tall bookcase (right wall) ----
        bcv, bce = [], []
        _add(bcv, bce, *_box(3.0, 0, 5.5, 1.4, H, 1.1))
        for shelf_y in [0.9, 1.8, 2.7, 3.6]:
            _add(bcv, bce, [(3.0, shelf_y, 5.5), (4.4, shelf_y, 5.5)], [(0, 1)])
            # books on each shelf
            x = 3.08
            while x < 4.3:
                bw = 0.12 + (hash(int(x*10) + int(shelf_y*10)) % 8) * 0.02
                bh = 0.5 + (hash(int(x*100)) % 5) * 0.06
                _add(bcv, bce, *_box(x, shelf_y+0.02, 5.52, bw, bh, 0.9))
                x += bw + 0.02
        self._obj("bookcase", bcv, bce, (100, 180, 255))
        self._obj_box("bookcase", 3.0, 0, 5.5, 1.4, H, 1.1, (60, 130, 210))

        # ---- Armchair ----
        acv, ace = [], []
        _add(acv, ace, *_box(-1.5, 0.4, 2.5, 2.2, 0.75, 1.8))  # seat
        _add(acv, ace, *_box(-1.5, 0.4, 2.3, 2.2, 2.0, 0.22))  # back
        _add(acv, ace, *_box(-1.5, 0.4, 2.3, 0.22, 2.0, 1.8))  # left arm
        _add(acv, ace, *_box( 0.48,0.4, 2.3, 0.22, 2.0, 1.8))  # right arm
        _add(acv, ace, *_box(-1.2, 1.15, 2.45, 0.85, 0.28, 0.75))  # cushion
        _add(acv, ace, *_box( 0.05,1.15, 2.45, 0.85, 0.28, 0.75))
        # footstool
        _add(acv, ace, *_box(-1.0, 0.3, 4.4, 1.6, 0.55, 1.2))
        self._obj("armchair", acv, ace, (80, 200, 255))
        self._obj_box("armchair", -1.5, 0.4, 2.5, 2.2, 0.75, 1.8, (50, 160, 230))
        self._obj_box("armchair", -1.5, 0.4, 2.3, 2.2, 2.0, 0.22, (40, 140, 210))

        # ---- Framed map on wall ----
        mv = [(-3.5, 2.2, D-0.05), (0.5, 2.2, D-0.05),
              (0.5, 4.0, D-0.05), (-3.5, 4.0, D-0.05)]
        me = [(0,1),(1,2),(2,3),(3,0)]
        for gx in [-2.5, -1.5, -0.5]:
            _add(mv, me, [(gx, 2.2, D-0.04), (gx, 4.0, D-0.04)], [(0,1)])
        for gy in [2.8, 3.4]:
            _add(mv, me, [(-3.5, gy, D-0.04), (0.5, gy, D-0.04)], [(0,1)])
        self._obj("_map", mv, me, (150, 220, 255))
        self._obj_face("_map", mv[:4], (20, 60, 120))


# ---------------------------------------------------------------------------
# Bathroom  —  cyan, white tub, chrome sink, mirror
# ---------------------------------------------------------------------------

class BathroomRoom(WireRoom):
    NAME       = "Bathroom"
    ROOM_COLOR = (  0, 230, 255)
    SLOTS      = ["bathtub", "sink", "toilet"]

    def _build(self):
        HW, H, D = 4.0, 4.5, 8.0
        self._shell_v, self._shell_e = _room_shell(HW, H, D)
        self._add_shell_faces(HW, H, D)

        # ---- Recessed ceiling light grid ----
        for li, (lx, lz) in enumerate([(-2, 2.5), (0, 2.5), (2, 2.5), (-1, 5.5), (1, 5.5)]):
            lv = []; le = []
            _add(lv, le, *_circle(lx, H-0.08, lz, 0.28, 10))
            _add(lv, le, *_circle(lx, H-0.08, lz, 0.14, 6))
            self._obj(f"_light{li}", lv, le, (220, 255, 255))

        # ---- Bathtub ----
        bv, be = [], []
        _add(bv, be, *_box(-HW+0.15, 0.0, 1.4, 3.6, 0.72, 1.8))   # outer
        _add(bv, be, *_box(-HW+0.35, 0.18, 1.55, 3.2, 0.54, 1.5))  # inner
        # taps on rim (back wall side)
        for tx in [-3.3, -2.7]:
            _add(bv, be, [(tx, 0.72, 3.15), (tx, 1.1, 3.15),
                          (tx, 1.1, 2.95), (tx, 0.72, 2.95)], [(0,1),(1,2),(2,3)])
        _add(bv, be, *_circle(-3.0, 0.72, 3.05, 0.18, 8))  # drain
        self._obj("bathtub", bv, be, (210, 240, 255))
        self._obj_box("bathtub", -HW+0.15, 0.0, 1.4, 3.6, 0.72, 1.8, (180, 220, 240))
        self._obj_face("bathtub",
            [(-HW+0.35, 0.72, 1.55), (-HW+3.55, 0.72, 1.55),
             (-HW+3.55, 0.72, 3.05), (-HW+0.35, 0.72, 3.05)],
            (150, 200, 230))

        # ---- Pedestal sink ----
        sv, se = [], []
        _add(sv, se, *_box(0.8, 0, 6.4, 1.4, 2.7, 0.05))  # pedestal
        _add(sv, se, *_box(0.6, 2.7, 6.25, 1.8, 0.22, 0.75))   # basin rim
        _add(sv, se, *_box(0.75, 2.34, 6.3, 1.5, 0.36, 0.65))  # basin bowl
        # taps
        for tx in [1.0, 1.8]:
            _add(sv, se, [(tx, 2.92, 6.3), (tx, 3.2, 6.3), (tx, 3.2, 6.15)],
                 [(0,1),(1,2)])
        _add(sv, se, *_circle(1.4, 2.92, 6.55, 0.10, 6))  # drain
        self._obj("sink", sv, se, (200, 240, 255))
        self._obj_box("sink", 0.6, 2.7, 6.25, 1.8, 0.22, 0.75, (180, 225, 240))
        self._obj_box("sink", 0.75, 2.34, 6.3, 1.5, 0.36, 0.65, (160, 210, 235))

        # ---- Toilet ----
        tv, te = [], []
        _add(tv, te, *_box(2.2, 0, 6.6, 1.5, 1.0, 1.3))   # base
        _add(tv, te, *_box(2.1, 1.0, 6.5, 1.7, 0.14, 1.5)) # seat rim
        _add(tv, te, *_box(2.3, 1.0, 7.96, 1.3, 1.4, 0.5)) # tank
        _add(tv, te, *_circle(3.0, 1.14, 7.2, 0.55, 10))   # bowl
        _add(tv, te, *_circle(3.0, 1.14, 7.2, 0.30, 8))
        self._obj("toilet", tv, te, (180, 240, 255))
        self._obj_box("toilet", 2.2, 0, 6.6, 1.5, 1.0, 1.3, (160, 220, 240))
        self._obj_box("toilet", 2.3, 1.0, 7.96, 1.3, 1.4, 0.5, (150, 210, 230))

        # ---- Mirror + shelf ----
        mirv = [(0.4, 3.3, D-0.05), (3.8, 3.3, D-0.05),
                (3.8, H-0.3, D-0.05), (0.4, H-0.3, D-0.05)]
        mire = [(0,1),(1,2),(2,3),(3,0)]
        _add(mirv, mire, *_box(-0.1, 3.2, D-0.08, 4.4, 0.10, 0.35))  # shelf
        self._obj("_mirror", mirv, mire, (160, 240, 255))
        self._obj_face("_mirror", mirv[:4], (10, 50, 80))

        # ---- Towel rack ----
        trv = [(-3.0, 2.8, D-0.05), (-1.2, 2.8, D-0.05)]; tre = [(0, 1)]
        _add(trv, tre, [(-3.0, 2.8, D-0.05), (-3.0, 2.4, D-0.05)], [(0,1)])
        _add(trv, tre, [(-1.2, 2.8, D-0.05), (-1.2, 2.4, D-0.05)], [(0,1)])
        # folded towels
        for tz in [D-0.06, D-0.20]:
            _add(trv, tre, [(-2.9, 2.82, tz), (-1.3, 2.82, tz)], [(0,1)])
        self._obj("_towelrack", trv, tre, (0, 220, 240))


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PREBUILT = {
    "kitchen":     KitchenRoom,
    "bedroom":     BedroomRoom,
    "garage":      GarageRoom,
    "living_room": LivingRoom,
    "library":     LibraryRoom,
    "bathroom":    BathroomRoom,
}

PREBUILT_NAMES = ["kitchen", "bedroom", "garage", "living_room", "library", "bathroom"]

PREBUILT_SLOTS = {
    "kitchen":     ["fridge", "stove", "table"],
    "bedroom":     ["bed", "dresser", "poster"],
    "garage":      ["car", "workbench"],
    "living_room": ["sofa", "tv", "coffee_table"],
    "library":     ["desk", "bookcase", "armchair"],
    "bathroom":    ["bathtub", "sink", "toilet"],
}

_cache: dict = {}


def get_room(room_type: str):
    k = room_type.lower()
    if k not in _cache:
        cls = PREBUILT.get(k)
        if cls:
            _cache[k] = cls()
    return _cache.get(k)
