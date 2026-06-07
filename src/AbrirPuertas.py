import pygame
import math
import numpy as np
import random
import sys
import time

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

W, H = 600, 600
CX, CY = W // 2, H // 2
FPS = 60

# ── Paleta cyberpunk ────────────────────────────────────────
C_BG       = (5,  10,  14)
C_TEAL     = (29, 233, 182)
C_TEAL_DIM = (10,  80,  60)
C_ORANGE   = (255, 107,  53)
C_RED      = (255,  23,  68)
C_DARK     = (10,  26,  34)
C_GRID     = (29, 233, 182, 15)
C_WHITE    = (224, 247, 250)


# ── Síntesis de audio ────────────────────────────────────────
SR = 44100

def synth(freq, duration, wave='sine', vol=0.18, attack=0.01):
    """Genera un array de sonido sintetizado."""
    n = int(SR * duration)
    t = np.linspace(0, duration, n, False)
    if wave == 'sine':
        s = np.sin(2 * np.pi * freq * t)
    elif wave == 'square':
        s = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == 'sawtooth':
        s = 2 * (t * freq - np.floor(0.5 + t * freq))
    else:
        s = np.sin(2 * np.pi * freq * t)
    env = np.ones(n)
    atk = min(int(SR * attack), n)
    env[:atk] = np.linspace(0, 1, atk)
    rel = min(int(SR * 0.05), n - atk)
    if rel > 0:
        env[-rel:] = np.linspace(1, 0, rel)
    s = (s * env * vol * 32767).astype(np.int16)
    stereo = np.column_stack([s, s])
    return pygame.sndarray.make_sound(stereo)

def mix_sounds(*arrays):
    """Mezcla varios arrays de sonido sumando (con clipping)."""
    max_len = max(len(a) for a in arrays)
    out = np.zeros(max_len, dtype=np.float32)
    for a in arrays:
        f = a.astype(np.float32)
        out[:len(f)] += f
    out = np.clip(out, -32767, 32767).astype(np.int16)
    return pygame.sndarray.make_sound(out)

# Pre-sintetizar banco de sonidos
SND = {
    'tick':    synth(880, 0.04, 'square', 0.09),
    'hotzone': synth(440, 0.06, 'sawtooth', 0.12),
    'fail1':   synth(220, 0.12, 'sawtooth', 0.16),
    'fail2':   synth(190, 0.12, 'sawtooth', 0.14),
    'pin1':    synth(330, 0.09, 'square', 0.14),
    'pin2':    synth(550, 0.09, 'sine',   0.10),
    'pin3':    synth(770, 0.09, 'square', 0.12),
    'win1':    synth(523, 0.22, 'sine', 0.18),
    'win2':    synth(659, 0.22, 'sine', 0.18),
    'win3':    synth(784, 0.22, 'sine', 0.18),
    'win4':    synth(1047,0.22, 'sine', 0.18),
}


# ── Partícula ────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 5.0)
        self.x, self.y = float(x), float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.life = 1.0
        self.r = random.uniform(2, 5)

    def update(self):
        self.x += self.vx; self.y += self.vy
        self.vx *= 0.91;   self.vy *= 0.91
        self.life -= 0.03; self.r *= 0.96

    def draw(self, surf):
        if self.life <= 0: return
        a = int(self.life * 255)
        col = (*self.color, a)
        s = pygame.Surface((int(self.r*2+2), int(self.r*2+2)), pygame.SRCALPHA)
        pygame.draw.circle(s, col, (int(self.r+1), int(self.r+1)), max(1,int(self.r)))
        surf.blit(s, (int(self.x - self.r), int(self.y - self.r)))


# ── Pin ──────────────────────────────────────────────────────
class Pin:
    def __init__(self, difficulty):
        span = max(10, 28 - difficulty * 3)
        self.center = random.uniform(30, 330)
        self.span   = span
        self.start  = self.center - span / 2
        self.set    = False

    def in_zone(self, angle_deg):
        a = angle_deg % 360
        return self.start <= a <= self.start + self.span


# ── Juego principal ──────────────────────────────────────────
class LockpickGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("LOCKPICK_SYS v2.7 — CYBERPUNK EDITION")
        self.clock  = pygame.time.Clock()
        self.font_m = pygame.font.SysFont('Courier New', 18, bold=True)
        self.font_s = pygame.font.SysFont('Courier New', 13)
        self.font_xs = pygame.font.SysFont('Courier New', 11)
        self.font_l = pygame.font.SysFont('Courier New', 32, bold=True)

        self.lives      = 3
        self.level      = 1
        self.difficulty = 1.0
        self.state      = 'idle'   # idle | playing | fail | win
        self.screen_state = 'intro'  # intro | playing | summary

        # Métricas del evento
        self.correct_attempts = 0
        self.failed_attempts = 0
        self.event_start = None
        self.event_time = 0.0
        self.final_result = ''
        self._init_level()

    def start_event(self):
        self.correct_attempts = 0
        self.failed_attempts = 0
        self.event_start = time.perf_counter()
        self.event_time = 0.0
        self.final_result = ''

        self.lives = 3
        self.level = 1
        self.difficulty = 1.0
        self._init_level()
        self.screen_state = 'playing'

    def finish_event(self, result):
        if self.screen_state != 'playing':
            return
        self.final_result = result
        if self.event_start is not None:
            self.event_time = time.perf_counter() - self.event_start
        self.turning = False
        self.screen_state = 'summary'

    def _init_level(self):
        n = 2 + min(int(self.difficulty), 4)
        self.pins        = [Pin(self.difficulty) for _ in range(n)]
        self.current_pin = 0
        self.lock_angle  = 0.0   # radianes
        self.turning     = False
        self.particles   = []
        self.shake       = 0.0
        self.flash       = 0.0
        self.flash_col   = C_RED
        self.win_anim    = 0.0
        self.tick_timer  = 0
        self.hotzone_timer = 0
        self.status      = 'mantén ESPACIO para girar'
        self.status_col  = C_TEAL_DIM
        self.scan_y      = 0.0
        self.state       = 'playing'

    # ── Input ────────────────────────────────────────────────
    def press(self):
        self.turning = True

    def release(self):
        if not self.turning: return
        self.turning = False
        if self.state != 'playing': return
        pin = self.pins[self.current_pin]
        angle_deg = math.degrees(self.lock_angle) % 360
        if pin.in_zone(angle_deg):
            self.correct_attempts += 1
            pin.set = True
            self._spawn(CX, CY, C_TEAL, 22)
            pygame.time.set_timer(pygame.USEREVENT+1, 0)
            SND['pin1'].play(); SND['pin2'].play(0, 0, 60); SND['pin3'].play(0, 0, 120)
            self.current_pin += 1
            if self.current_pin >= len(self.pins):
                self.state    = 'win'
                self.win_anim = 1.0
                self.status   = '>>> ACCESO CONCEDIDO <<<'
                self.status_col = C_TEAL
                SND['win1'].play(); SND['win2'].play(0,0,120)
                SND['win3'].play(0,0,240); SND['win4'].play(0,0,360)
            else:
                self.status = f'pin fijado — siguiente ({self.current_pin+1}/{len(self.pins)})'
                self.status_col = C_TEAL
        else:
            self.failed_attempts += 1
            self.lives -= 1
            self.shake  = 1.0
            self.flash  = 1.0
            self.flash_col = C_RED
            self._spawn(CX, CY, C_RED, 28)
            SND['fail1'].play(); SND['fail2'].play(0, 0, 80)
            if self.lives <= 0:
                self.state  = 'fail'
                self.status = '>>> ACCESO DENEGADO <<<'
                self.status_col = C_RED
            else:
                self._init_level()
                self.lives = max(self.lives, 0)  # conservar vidas
                self.status = f'cerrojo reiniciado — {self.lives} intentos restantes'
                self.status_col = C_ORANGE

    def _spawn(self, x, y, col, n):
        for _ in range(n):
            self.particles.append(Particle(x, y, col))

    # ── Update ───────────────────────────────────────────────
    def update(self, dt):
        self.scan_y = (self.scan_y + 0.6) % H

        if self.shake > 0: self.shake = max(0, self.shake - 0.07)
        if self.flash > 0: self.flash = max(0, self.flash - 0.06)
        if self.win_anim > 0:
            self.win_anim = max(0, self.win_anim - 0.015)
            if self.win_anim == 0 and self.state == 'win':
                self.finish_event('ACCESO CONCEDIDO')

        if self.state == 'fail' and self.flash == 0:
            self.finish_event('ACCESO DENEGADO')

        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.life > 0]

        if self.turning and self.state == 'playing':
            mx, _ = pygame.mouse.get_pos()
            direction = 1 if mx > CX else -1
            speed = (0.022 + self.difficulty * 0.004) * direction
            self.lock_angle += speed

            in_hz = self._in_hotzone()
            self.tick_timer += 1
            self.hotzone_timer += 1
            if in_hz and self.hotzone_timer > 5:
                SND['hotzone'].play(); self.hotzone_timer = 0
            elif not in_hz and self.tick_timer > 12:
                SND['tick'].play(); self.tick_timer = 0

    def _in_hotzone(self):
        if self.current_pin >= len(self.pins): return False
        a = math.degrees(self.lock_angle) % 360
        return self.pins[self.current_pin].in_zone(a)

    # ── Draw ─────────────────────────────────────────────────
    def draw(self):
        ox = oy = 0
        if self.shake > 0:
            ox = random.randint(-1,1) * int(10 * self.shake)
            oy = random.randint(-1,1) * int(10 * self.shake)

        surf = pygame.Surface((W, H))
        surf.fill(C_BG)

        # Flash overlay
        if self.flash > 0:
            fl = pygame.Surface((W, H), pygame.SRCALPHA)
            fl.fill((*self.flash_col, int(self.flash * 80)))
            surf.blit(fl, (0, 0))

        # Scan line
        pygame.draw.line(surf, (*C_TEAL, 12), (0, int(self.scan_y)), (W, int(self.scan_y)))

        # Grid circles
        R_RING = 170
        for r in range(200, 60, -28):
            pygame.draw.circle(surf, (*C_TEAL, 8), (CX, CY), r, 1)

        # Hot zones (arc approximation via polygon)
        if self.state == 'playing':
            for i, pin in enumerate(self.pins):
                if pin.set: continue
                arc_col = (*C_TEAL, 40 if i == self.current_pin else 15)
                pts = []
                steps = 30
                for s in range(steps+1):
                    a = math.radians(pin.start + pin.span * s/steps) - math.pi/2
                    pts.append((CX + math.cos(a)*R_RING, CY + math.sin(a)*R_RING))
                for s in range(steps, -1, -1):
                    a = math.radians(pin.start + pin.span * s/steps) - math.pi/2
                    ir = R_RING - (26 if i == self.current_pin else 14)
                    pts.append((CX + math.cos(a)*ir, CY + math.sin(a)*ir))
                if len(pts) > 2:
                    arc_surf = pygame.Surface((W, H), pygame.SRCALPHA)
                    pygame.draw.polygon(arc_surf, arc_col, pts)
                    surf.blit(arc_surf, (0,0))
                # border arc lines
                if i == self.current_pin:
                    for s in range(steps):
                        a1 = math.radians(pin.start + pin.span*s/steps) - math.pi/2
                        a2 = math.radians(pin.start + pin.span*(s+1)/steps) - math.pi/2
                        p1 = (CX+math.cos(a1)*R_RING, CY+math.sin(a1)*R_RING)
                        p2 = (CX+math.cos(a2)*R_RING, CY+math.sin(a2)*R_RING)
                        pygame.draw.line(surf, C_TEAL, (int(p1[0]),int(p1[1])), (int(p2[0]),int(p2[1])), 2)

        # Set pin markers
        for pin in self.pins:
            if not pin.set: continue
            mid_a = math.radians(pin.start + pin.span/2) - math.pi/2
            px = int(CX + math.cos(mid_a)*R_RING)
            py = int(CY + math.sin(mid_a)*R_RING)
            pygame.draw.circle(surf, C_TEAL, (px, py), 7)
            pygame.draw.circle(surf, (*C_TEAL, 80), (px, py), 12, 1)

        # Lock body
        lock_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.circle(lock_surf, (*C_DARK, 255), (CX, CY), 82)
        pygame.draw.circle(lock_surf, (*C_TEAL, 200), (CX, CY), 82, 2)

        # Notches on lock rim
        NOTCH_N = 24
        for i in range(NOTCH_N):
            a = self.lock_angle + (i / NOTCH_N) * math.tau
            x1 = CX + math.cos(a) * 75; y1 = CY + math.sin(a) * 75
            x2 = CX + math.cos(a) * 82; y2 = CY + math.sin(a) * 82
            pygame.draw.line(lock_surf, (*C_TEAL, 80),
                             (int(x1),int(y1)), (int(x2),int(y2)), 1)

        # Pins inside lock
        for i, pin in enumerate(self.pins):
            col = C_TEAL if pin.set else (C_ORANGE if i==self.current_pin else C_DARK)
            raised = not pin.set
            rot = self.lock_angle
            local_x = -6
            local_y = -70 + i*22
            if raised: local_y -= 8

            cos_r, sin_r = math.cos(rot), math.sin(rot)
            wx = CX + local_x*cos_r - local_y*sin_r
            wy = CY + local_x*sin_r + local_y*cos_r

            bw, bh = 12, 20 if raised else 12
            pin_rect = pygame.Surface((bw, bh), pygame.SRCALPHA)
            pin_rect.fill((*col, 220))
            border_col = C_TEAL if pin.set else (C_ORANGE if i==self.current_pin else (30,60,70))
            pygame.draw.rect(pin_rect, border_col, (0,0,bw,bh), 1)
            rotated = pygame.transform.rotate(pin_rect, -math.degrees(rot))
            lock_surf.blit(rotated, (int(wx-rotated.get_width()/2), int(wy-rotated.get_height()/2)))

        surf.blit(lock_surf, (0,0))

        # Needle
        if self.state == 'playing':
            needle_len = R_RING + 24
            na = self.lock_angle - math.pi/2
            nx = CX + math.cos(na)*needle_len
            ny = CY + math.sin(na)*needle_len
            in_hz = self._in_hotzone()
            needle_col = C_ORANGE if in_hz else C_TEAL
            pygame.draw.line(surf, needle_col, (CX,CY), (int(nx),int(ny)), 2)
            pygame.draw.circle(surf, needle_col, (int(nx),int(ny)), 7)
            pygame.draw.circle(surf, (*needle_col,100), (int(nx),int(ny)), 12, 1)

        # Win animation
        if self.win_anim > 0:
            wa = 1 - self.win_anim
            r = int(self.win_anim * 240)
            win_s = pygame.Surface((W,H), pygame.SRCALPHA)
            pygame.draw.circle(win_s, (*C_TEAL, int(self.win_anim*120)), (CX,CY), r, 3)
            surf.blit(win_s,(0,0))
            txt = self.font_l.render('ACCESO CONCEDIDO', True, (*C_TEAL, int(min(255,wa*600))))
            surf.blit(txt, (CX-txt.get_width()//2, 60))

        # Particles
        for p in self.particles:
            p.draw(surf)

        # HUD
        lvl_txt = self.font_m.render(f'NIVEL {self.level:02d}', True, C_TEAL)
        surf.blit(lvl_txt, (20, 16))
        pin_txt = self.font_m.render(f'PIN {self.current_pin+1}/{len(self.pins)}', True, C_WHITE)
        surf.blit(pin_txt, (CX - pin_txt.get_width()//2, 16))
        for i in range(3):
            col = C_TEAL if i < self.lives else C_DARK
            pygame.draw.circle(surf, col, (W-30-i*22, 24), 7)
        status_txt = self.font_s.render(self.status.upper(), True, self.status_col)
        surf.blit(status_txt, (CX - status_txt.get_width()//2, H-36))
        diff_txt = self.font_s.render(f'DIFICULTAD {self.difficulty:.1f}', True, C_DARK)
        surf.blit(diff_txt, (20, H-36))

        # Blit con shake offset
        self.screen.fill(C_BG)
        self.screen.blit(surf, (ox, oy))
        pygame.display.flip()

    def draw_intro(self):
        self.screen.fill(C_BG)
        panel = pygame.Surface((W - 60, H - 90), pygame.SRCALPHA)
        panel.fill((8, 20, 26, 210))
        self.screen.blit(panel, (30, 45))
        pygame.draw.rect(self.screen, C_TEAL_DIM, (30, 45, W - 60, H - 90), 2)

        title = self.font_m.render('LOCKPICK_SYS // INSTRUCCIONES', True, C_TEAL)
        self.screen.blit(title, (CX - title.get_width() // 2, 75))

        lines = [
            'Objetivo: fija todos los pines dentro de la zona activa.',
            'Controles:',
            '- Mantener ESPACIO o clic sostenido para girar la ganzua.',
            '- Mover el mouse izquierda/derecha para cambiar sentido de giro.',
            '- Soltar ESPACIO/clic para intentar fijar el pin actual.',
            '- ESC para salir.',
            '',
            'Presiona ENTER para iniciar el evento.',
        ]
        y = 125
        for line in lines:
            text = self.font_s.render(line, True, C_WHITE if line else C_TEAL)
            self.screen.blit(text, (55, y))
            y += 29

        pygame.display.flip()

    def draw_summary(self):
        self.screen.fill(C_BG)
        panel = pygame.Surface((W - 80, H - 130), pygame.SRCALPHA)
        panel.fill((8, 20, 26, 220))
        self.screen.blit(panel, (40, 65))
        pygame.draw.rect(self.screen, C_TEAL_DIM, (40, 65, W - 80, H - 130), 2)

        title = self.font_m.render('RESUMEN DEL EVENTO', True, C_TEAL)
        self.screen.blit(title, (CX - title.get_width() // 2, 95))

        result = self.font_s.render(self.final_result, True, C_ORANGE if 'DENEGADO' in self.final_result else C_TEAL)
        self.screen.blit(result, (CX - result.get_width() // 2, 132))

        total_intentos = self.correct_attempts + self.failed_attempts
        precision = (self.correct_attempts / total_intentos * 100.0) if total_intentos > 0 else 0.0
        tiempo_promedio = (self.event_time / total_intentos) if total_intentos > 0 else 0.0

        summary_lines = [
            f'Intentos correctos: {self.correct_attempts}',
            f'Intentos fallidos: {self.failed_attempts}',
            f'Tiempo total del evento: {self.event_time:.2f} s',
            f'Porcentaje de acierto: {precision:.1f}%',
            f'Tiempo promedio por intento: {tiempo_promedio:.2f} s',
            '',
            'Presiona R para reiniciar o ESC para salir.',
        ]
        y = 180
        for line in summary_lines:
            color = C_WHITE if line else C_TEAL
            text = self.font_s.render(line, True, color)
            self.screen.blit(text, (CX - text.get_width() // 2, y))
            y += 30

        pygame.display.flip()

    # ── Ciclo ─────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if self.screen_state == 'intro' and event.key == pygame.K_RETURN:
                        self.start_event()
                    if self.screen_state == 'summary' and event.key == pygame.K_r:
                        self.screen_state = 'intro'
                    if self.screen_state == 'playing' and event.key == pygame.K_SPACE:
                        self.press()
                if event.type == pygame.KEYUP:
                    if self.screen_state == 'playing' and event.key == pygame.K_SPACE:
                        self.release()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.screen_state == 'playing':
                        self.press()
                if event.type == pygame.MOUSEBUTTONUP:
                    if self.screen_state == 'playing':
                        self.release()

            if self.screen_state == 'intro':
                self.draw_intro()
            elif self.screen_state == 'playing':
                self.update(dt)
                self.draw()
            else:
                self.draw_summary()


if __name__ == '__main__':
    LockpickGame().run()
