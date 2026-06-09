import pygame
import numpy as np
import random

pygame.init()

print("started")

WIDTH, HEIGHT = 1400, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Relativistic Black Hole Chaos Sandbox")

clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 16)


class Slider:
    def __init__(self, x, y, w, min_v, max_v, value, label):
        self.rect = pygame.Rect(x, y, w, 20)
        self.min = min_v
        self.max = max_v
        self.value = value
        self.label = label
        self.dragging = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            t = (event.pos[0] - self.rect.x) / self.rect.width
            t = max(0, min(1, t))
            self.value = self.min + t * (self.max - self.min)

    def draw(self, surf):
        pygame.draw.rect(surf, (40, 40, 50), self.rect)
        t = (self.value - self.min) / (self.max - self.min)
        x = self.rect.x + int(t * self.rect.width)
        pygame.draw.circle(surf, (220, 220, 240), (x, self.rect.y + 10), 6)
        text = font.render(f"{self.label}: {self.value:.2f}", True, (255, 255, 255))
        surf.blit(text, (self.rect.x, self.rect.y - 18))


class Body:
    def __init__(self, name, mass, radius, pos, vel, color, is_black_hole=False):
        self.name = name
        self.mass = mass
        self.is_black_hole = is_black_hole

        c = 299792458
        if self.is_black_hole:
            self.radius = (2 * 6.6743e-11 * self.mass) / (c**2)
            self.disk_positions = None
            self.disk_velocities = None
            self.disk_heat = None
            self._generate_accretion_disk()
        else:
            self.radius = radius

        self.position = np.array(pos, dtype=float)
        self.velocity = np.array(vel, dtype=float)
        self.color = pygame.Color(color)
        self.trail = []

    def _generate_accretion_disk(self):
        num_particles = 200
        disk_min = self.radius * 2.5
        disk_max = self.radius * 9.0

        radii = np.random.uniform(disk_min, disk_max, num_particles)
        angles = np.random.uniform(0, 2 * np.pi, num_particles)

        g = 6.6743e-11
        speeds = np.sqrt((g * self.mass) / radii)

        x = radii * np.cos(angles)
        y = radii * np.sin(angles)

        # FIX: Keep Z-axis variance proportional to the disk's radius scale, not 1e10!
        z = np.random.uniform(-self.radius * 0.1, self.radius * 0.1, num_particles)
        self.disk_positions = np.stack((x, y, z), axis=1)

        vx = -speeds * np.sin(angles)
        vy = speeds * np.cos(angles)
        vz = np.zeros(num_particles)
        self.disk_velocities = np.stack((vx, vy, vz), axis=1)

        self.disk_heat = 1.0 - (radii - disk_min) / (disk_max - disk_min)

    def add_trail(self):
        self.trail.append(self.position.copy())
        if len(self.trail) > 150:
            self.trail.pop(0)


class PhysicsEngine:
    def update(self, bodies, dt, G_multiplier, noise, drag):
        G = 6.6743e-11 * G_multiplier
        for b in bodies:
            if b.is_black_hole: continue

            # Chaos Sandbox perturbations
            rand = np.random.uniform(-1, 1, 3) * noise * 1e-5
            b.velocity += rand * dt
            b.velocity *= (1.0 - drag)

            for other in bodies:
                if other is b: continue
                r = other.position - b.position
                d = np.sqrt(np.dot(r, r))
                if d > 0:
                    b.velocity += (G * other.mass * r / (d**3)) * dt

            speed = np.linalg.norm(b.velocity)
            if speed > 2.997e8:
                b.velocity *= 2.997e8 / speed

            b.position += b.velocity * dt
            b.add_trail()


class CollisionSystem:
    def process(self, bodies):
        remove = set()
        for i in range(len(bodies)):
            for j in range(i + 1, len(bodies)):
                a, b = bodies[i], bodies[j]
                if a in remove or b in remove: continue
                dist = np.linalg.norm(a.position - b.position)
                if dist < (a.radius + b.radius):
                    if a.is_black_hole or b.is_black_hole:
                        remove.add(b if a.is_black_hole else a)
        bodies[:] = [b for b in bodies if b not in remove]


class Renderer3D:
    def __init__(self):
        self.zoom = 2e-9
        self.cam = np.array([0.0, 0.0, 0.0])
        self.angle_x = 0.4
        self.angle_y = 0.6
        self._generate_starfield()

    def _generate_starfield(self):
        self.stars = []
        for _ in range(150):
            x = random.uniform(-1, 1)
            y = random.uniform(-1, 1)
            z = random.uniform(-1, 1)
            vec = np.array([x, y, z])
            vec /= np.linalg.norm(vec)
            brightness = random.randint(120, 240)
            self.stars.append((vec, brightness))

    def get_rotation_matrix(self):
        rx = np.array([
            [1, 0, 0],
            [0, np.cos(self.angle_x), -np.sin(self.angle_x)],
            [0, np.sin(self.angle_x), np.cos(self.angle_x)]
        ])
        ry = np.array([
            [np.cos(self.angle_y), 0, np.sin(self.angle_y)],
            [0, 1, 0],
            [-np.sin(self.angle_y), 0, np.cos(self.angle_y)]
        ])
        return np.dot(ry, rx)

    def project(self, p, rot_mat, apply_com=True):
        rel = (p - self.cam) if apply_com else p
        rotated = np.dot(rot_mat, rel)
        x = WIDTH / 2 + rotated[0] * self.zoom
        y = HEIGHT / 2 + rotated[1] * self.zoom
        return int(x), int(y), rotated[2]

    def draw_background_stars(self, surf, rot_mat):
        for star_vec, bright in self.stars:
            rot_star = np.dot(rot_mat, star_vec)
            if rot_star[2] > -0.2:
                sx = int(WIDTH / 2 + rot_star[0] * (WIDTH / 1.5))
                sy = int(HEIGHT / 2 + rot_star[1] * (HEIGHT / 1.5))
                if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                    surf.set_at((sx, sy), (bright, bright, min(255, bright + 10)))

    def _draw_advanced_black_hole(self, surf, b, rot_mat):
        bh_sx, bh_sy, bh_depth = self.project(b.position, rot_mat)
        boosted_r = max(12, int(b.radius * self.zoom * 2e4))
        einstein_r = boosted_r * 1.5

        c = 299792458

        # Vectorized math for all 2500 particles at once
        global_positions = b.disk_positions + b.position - self.cam
        rotated_positions = np.dot(global_positions, rot_mat.T)
        rotated_velocities = np.dot(b.disk_velocities, rot_mat.T)

        screen_x_arr = (WIDTH / 2 + rotated_positions[:, 0] * self.zoom).astype(int)
        screen_y_arr = (HEIGHT / 2 + rotated_positions[:, 1] * self.zoom).astype(int)
        depth_arr = rotated_positions[:, 2]
        vz_arr = rotated_velocities[:, 2]

        beta = vz_arr / c
        gamma = 1.0 / np.sqrt(1.0 - np.clip(beta**2, 0.0, 0.95))
        doppler_factor = 1.0 / (gamma * (1.0 - beta))
        brightness_arr = np.clip(0.35 + doppler_factor * b.disk_heat * 0.75, 0, 1)

        # Vectorized Relativistic Gravitational Lensing
        dx = screen_x_arr - bh_sx
        dy = screen_y_arr - bh_sy
        r_screen = np.sqrt(dx**2 + dy**2)

        # Apply warp calculation only where particles are in front of the black hole
        mask = (r_screen > 0) & (depth_arr < bh_depth)
        warp = np.zeros_like(r_screen)
        warp[mask] = (einstein_r**2) / (r_screen[mask] * 0.4)

        screen_x_arr[mask] += ((dx[mask] / r_screen[mask]) * warp[mask] * 0.6).astype(int)
        screen_y_arr[mask] += ((dy[mask] / r_screen[mask]) * warp[mask] * 0.6).astype(int)

        # Pre-calculate colors vectorially
        r_vals = np.zeros(len(b.disk_positions), dtype=int)
        g_vals = np.zeros(len(b.disk_positions), dtype=int)
        b_vals = np.zeros(len(b.disk_positions), dtype=int)

        approaching = vz_arr > 0
        receding = ~approaching

        # Doppler Blue-shift (Approaching)
        if np.any(approaching):
            blue_shift = np.minimum(1.0, doppler_factor[approaching]**2 * 0.4)
            r_vals[approaching] = (brightness_arr[approaching] * 216).astype(int)
            g_vals[approaching] = (brightness_arr[approaching] * 255 * np.minimum(1.0, 0.65 + blue_shift)).astype(int)
            b_vals[approaching] = (brightness_arr[approaching] * 255).astype(int)

        # Doppler Red-shift (Receding)
        if np.any(receding):
            red_shift = np.minimum(1.0, np.abs(vz_arr[receding]) / (c * 0.12))
            r_vals[receding] = (brightness_arr[receding] * 255).astype(int)
            g_vals[receding] = (brightness_arr[receding] * 170 * (1 - red_shift)).astype(int)
            b_vals[receding] = (brightness_arr[receding] * 90 * (1 - red_shift)).astype(int)

        # Clip color boundaries securely
        r_vals = np.clip(r_vals, 0, 255)
        g_vals = np.clip(g_vals, 0, 255)
        b_vals = np.clip(b_vals, 0, 255)

        # Sort particles by depth securely
        sort_indices = np.argsort(depth_arr)[::-1]

        # Blit directly to the pixel array (Massive cloud performance boost)
        px_array = pygame.PixelArray(surf)
        for i in sort_indices:
            px, py = screen_x_arr[i], screen_y_arr[i]
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                if (px - bh_sx)**2 + (py - bh_sy)**2 > (boosted_r - 2)**2:
                    px_array[px, py] = (r_vals[i], g_vals[i], b_vals[i])
        del px_array # Unlock surface for rendering

        # Event horizon black core shadow
        pygame.draw.circle(surf, (1, 0, 4), (bh_sx, bh_sy), boosted_r)
        pygame.draw.circle(surf, (255, 200, 110), (bh_sx, bh_sy), boosted_r + 2, 2)

    def draw(self, surf, bodies):
        surf.fill((1, 0, 4))
        rot_mat = self.get_rotation_matrix()

        self.draw_background_stars(surf, rot_mat)

        render_queue = []
        for b in bodies:
            sx, sy, depth = self.project(b.position, rot_mat)

            trail_pts = []
            for p in b.trail:
                tx, ty, t_depth = self.project(p, rot_mat)
                tx = max(-2000, min(4000, tx))
                ty = max(-2000, min(4000, ty))
                trail_pts.append((tx, ty))

            render_queue.append((depth, b, sx, sy, trail_pts))

        render_queue.sort(key=lambda item: item[0], reverse=True)

        for depth, b, x, y, trail_pts in render_queue:
            if b.is_black_hole:
                self._draw_advanced_black_hole(surf, b, rot_mat)
                continue

            if len(trail_pts) > 2:
                dimmed_color = (int(b.color.r // 2.5), int(b.color.g // 2.5), int(b.color.b // 2.5))
                pygame.draw.lines(surf, dimmed_color, False, trail_pts, 1)

            pygame.draw.circle(surf, b.color, (x, y), 6)


def center_of_mass(bodies):
    total_mass = sum(b.mass for b in bodies)
    if total_mass == 0: return np.array([0.0, 0.0, 0.0])
    return sum(b.mass * b.position for b in bodies) / total_mass


# --- ENGINE SETUP ---
physics = PhysicsEngine()
collisions = CollisionSystem()
renderer = Renderer3D()

bodies = [
    Body("Singularity", 6e31, 0, [0, 0, 0], [0, 0, 0], (0, 0, 0), is_black_hole=True),
    Body("Blue Planet", 5.97e24, 6e6, [1.3e11, 0, 0], [0, 155000, 0], (120, 200, 255)),
    Body("Purple Planet", 4e25, 2e7, [0, 0, 1.6e11], [135000, 0, 0], (210, 110, 255))
]

gravity_slider = Slider(20, 40, 200, 0.1, 5.0, 1.0, "Gravity")
time_slider = Slider(20, 90, 200, 1.0, 40.0, 12.0, "Time Compression")
noise_slider = Slider(20, 140, 200, 0.0, 10.0, 0.0, "Chaos Noise")
drag_slider = Slider(20, 190, 200, 0.0, 0.01, 0.0, "Accretion Drag")
sliders = [gravity_slider, time_slider, noise_slider, drag_slider]

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        for s in sliders:
            s.handle(event)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]: renderer.angle_x += 0.03
    if keys[pygame.K_s]: renderer.angle_x -= 0.03
    if keys[pygame.K_a]: renderer.angle_y += 0.03
    if keys[pygame.K_d]: renderer.angle_y -= 0.03

    steps = max(1, int(time_slider.value))
    for _ in range(steps):
        physics.update(bodies, 1800, gravity_slider.value, noise_slider.value, drag_slider.value)
        collisions.process(bodies)

    com = center_of_mass(bodies)
    renderer.cam = com

    max_dist = max(np.linalg.norm(b.position - com) for b in bodies) if bodies else 1e9
    max_dist = max(max_dist, 1e9)
    renderer.zoom = HEIGHT / (2.4 * max_dist)

    renderer.draw(screen, bodies)

    for s in sliders:
        s.draw(screen)

    # Frame metrics
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (0, 255, 100))
    screen.blit(fps_text, (WIDTH - 100, 20))
    controls_text = font.render("Use W, A, S, D to rotate view angle seamlessly!", True, (140, 140, 160))
    screen.blit(controls_text, (20, HEIGHT - 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
