import pygame
import sys

# --- CONFIGURACIÓN GENERAL ---
WIDTH, HEIGHT = 800, 500
FPS = 60

# Paleta de colores estilo Retro/CRT de RoboCop
COLOR_BG = (15, 5, 5)
COLOR_GRID_BG = (40, 10, 10)
COLOR_RED_BRIGHT = (255, 40, 40)
COLOR_RED_DIM = (130, 20, 20)
COLOR_TEXT = (255, 80, 80)
COLOR_WHITE = (255, 255, 255)

# --- SECUENCIAS DE LOS PUZZLES (5x5) ---
# En cada secuencia, una sola opción complementa el patrón izquierdo y produce
# una matriz completa de 1s en la suma celda a celda.
SECUENCIAS = [
    {
        "patron": [
            [1, 1, 0, 0, 0],
            [1, 1, 1, 0, 0],
            [0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        "opciones": [
            [
                [0, 0, 1, 1, 1],
                [0, 0, 0, 1, 1],
                [1, 0, 0, 1, 0],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
            ],
            [
                [0, 0, 1, 1, 1],
                [0, 0, 0, 1, 1],
                [1, 0, 0, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
            ],
            [
                [0, 0, 0, 1, 1],
                [0, 0, 0, 1, 1],
                [1, 0, 0, 0, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
            ],
            [
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ],
        ],
    },
    {
        "patron": [
            [1, 0, 0, 1, 0],
            [1, 1, 0, 1, 0],
            [0, 1, 1, 0, 0],
            [0, 0, 1, 1, 0],
            [0, 0, 0, 1, 1],
        ],
        "opciones": [
            [
                [0, 1, 1, 0, 1],
                [0, 0, 1, 0, 1],
                [1, 0, 0, 1, 1],
                [1, 1, 0, 0, 1],
                [1, 1, 1, 0, 0],
            ],
            [
                [0, 1, 1, 0, 0],
                [0, 0, 1, 0, 1],
                [1, 0, 0, 1, 1],
                [1, 1, 0, 0, 1],
                [1, 1, 1, 0, 0],
            ],
            [
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
            ],
            [
                [0, 1, 1, 0, 1],
                [0, 0, 0, 0, 1],
                [1, 0, 0, 1, 1],
                [1, 1, 0, 0, 1],
                [1, 1, 1, 0, 0],
            ],
        ],
    },
    {
        "patron": [
            [0, 1, 1, 0, 0],
            [0, 1, 0, 0, 1],
            [1, 0, 0, 1, 0],
            [1, 1, 0, 1, 0],
            [0, 0, 1, 0, 1],
        ],
        "opciones": [
            [
                [1, 0, 0, 1, 1],
                [1, 0, 1, 1, 0],
                [0, 1, 1, 0, 1],
                [0, 0, 1, 0, 1],
                [1, 1, 0, 1, 0],
            ],
            [
                [1, 0, 0, 1, 1],
                [1, 0, 1, 1, 0],
                [0, 1, 1, 1, 1],
                [0, 0, 1, 0, 1],
                [1, 1, 0, 1, 0],
            ],
            [
                [1, 0, 0, 1, 1],
                [1, 0, 1, 1, 0],
                [0, 1, 1, 0, 1],
                [0, 0, 1, 0, 0],
                [1, 1, 0, 1, 0],
            ],
            [
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ],
        ],
    },
]

class PuzzleGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Wingman Cyber Puzzle UI")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier New", 18, bold=True)
        self.large_font = pygame.font.SysFont("Courier New", 36, bold=True)
        self.medium_font = pygame.font.SysFont("Courier New", 24, bold=True)
        
        # Estado del juego
        self.estado_pantalla = "INICIO"  # INICIO, JUGANDO, RESUMEN
        self.indice_secuencia = 0
        self.indice_seleccionado = 0
        self.target_scroll_y = 0
        self.current_scroll_y = 0
        self.estado_resultado = None  # Puede ser "EXITO", "FALLO" o None
        self.timer_resultado = 0
        self.avanzar_secuencia = False
        self.finalizar_juego = False

        # Métricas del evento
        self.intentos_correctos = 0
        self.intentos_fallidos = 0
        self.tiempo_inicio_evento = 0
        self.tiempo_total_segundos = 0

    def get_patron_actual(self):
        return SECUENCIAS[self.indice_secuencia]["patron"]

    def get_opciones_actuales(self):
        return SECUENCIAS[self.indice_secuencia]["opciones"]

    def verificar_solucion(self):
        """Comprueba si la pieza del centro encaja perfectamente."""
        patron = self.get_patron_actual()
        pieza_actual = self.get_opciones_actuales()[self.indice_seleccionado]
        
        for r in range(5):
            for c in range(5):
                suma = patron[r][c] + pieza_actual[r][c]
                if suma != 1:
                    return False
        return True

    def iniciar_evento(self):
        self.estado_pantalla = "JUGANDO"
        self.tiempo_inicio_evento = pygame.time.get_ticks()

    def registrar_intento(self):
        if self.verificar_solucion():
            self.intentos_correctos += 1
            self.estado_resultado = "EXITO"

            if self.indice_secuencia < len(SECUENCIAS) - 1:
                self.avanzar_secuencia = True
            else:
                self.finalizar_juego = True
        else:
            self.intentos_fallidos += 1
            self.estado_resultado = "FALLO"

        self.timer_resultado = pygame.time.get_ticks()

    def avanzar_a_siguiente_secuencia(self):
        self.indice_secuencia += 1
        self.indice_seleccionado = 0
        self.target_scroll_y = 0
        self.current_scroll_y = 0
        self.avanzar_secuencia = False

    def terminar_evento(self):
        self.tiempo_total_segundos = (pygame.time.get_ticks() - self.tiempo_inicio_evento) / 1000.0
        self.estado_pantalla = "RESUMEN"
        self.finalizar_juego = False

    def draw_intro(self):
        self.screen.fill(COLOR_BG)
        pygame.draw.rect(self.screen, COLOR_RED_DIM, (20, 20, WIDTH - 40, HEIGHT - 40), 2)

        titulo = self.large_font.render("SECUENCIAS DE PATRONES", True, COLOR_RED_BRIGHT)
        self.screen.blit(titulo, (WIDTH // 2 - titulo.get_width() // 2, 80))

        lineas = [
            "Instrucciones:",
            "1) Observa la matriz objetivo de la izquierda.",
            "2) Identifica el patron faltante.",
            "3) Usa FLECHA ARRIBA/ABAJO para elegir una figura.",
            "4) Presiona ENTER para confirmar.",
            "Completa las 3 secuencias para finalizar.",
            "",
            "Presiona ENTER o ESPACIO para iniciar.",
        ]

        y = 170
        for linea in lineas:
            texto = self.font.render(linea, True, COLOR_TEXT)
            self.screen.blit(texto, (80, y))
            y += 34

    def draw_summary(self):
        self.screen.fill(COLOR_BG)
        pygame.draw.rect(self.screen, COLOR_RED_DIM, (20, 20, WIDTH - 40, HEIGHT - 40), 2)

        titulo = self.large_font.render("RESUMEN DEL EVENTO", True, COLOR_RED_BRIGHT)
        self.screen.blit(titulo, (WIDTH // 2 - titulo.get_width() // 2, 90))

        resumen = [
            f"Intentos correctos: {self.intentos_correctos}",
            f"Intentos fallidos: {self.intentos_fallidos}",
            f"Tiempo total: {self.tiempo_total_segundos:.2f} s",
        ]

        y = 210
        for linea in resumen:
            texto = self.medium_font.render(linea, True, COLOR_WHITE)
            self.screen.blit(texto, (WIDTH // 2 - texto.get_width() // 2, y))
            y += 55

        salir = self.font.render("Presiona ENTER o ESC para salir.", True, COLOR_TEXT)
        self.screen.blit(salir, (WIDTH // 2 - salir.get_width() // 2, 400))

    def draw_matrix(self, matrix, x, y, size_cell=25, alpha_bg=False):
        """Dibuja una rejilla de 5x5 basada en una matriz."""
        for r in range(5):
            for c in range(5):
                rect = pygame.Rect(x + c * size_cell, y + r * size_cell, size_cell - 2, size_cell - 2)
                if matrix[r][c] == 1:
                    pygame.draw.rect(self.screen, COLOR_RED_BRIGHT, rect)
                else:
                    bg_color = COLOR_GRID_BG if alpha_bg else COLOR_BG
                    pygame.draw.rect(self.screen, bg_color, rect)
                    pygame.draw.rect(self.screen, COLOR_RED_DIM, rect, 1)

    def draw_scanlines(self):
        """Efecto visual de monitor CRT antiguo."""
        for y in range(0, HEIGHT, 3):
            scanline = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
            scanline.fill((0, 0, 0, 85))  # Líneas negras semitransparentes
            self.screen.blit(scanline, (0, y))

    def run(self):
        running = True
        while running:
            opciones_actuales = self.get_opciones_actuales()

            # 1. MANEJO DE EVENTOS
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if self.estado_pantalla == "INICIO":
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.iniciar_evento()

                    elif self.estado_pantalla == "JUGANDO" and self.estado_resultado is None:
                        if event.key == pygame.K_UP and self.indice_seleccionado > 0:
                            self.indice_seleccionado -= 1
                        elif event.key == pygame.K_DOWN and self.indice_seleccionado < len(opciones_actuales) - 1:
                            self.indice_seleccionado += 1
                        elif event.key == pygame.K_RETURN:
                            self.registrar_intento()

                    elif self.estado_pantalla == "RESUMEN":
                        if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                            running = False

            # 2. ACTUALIZACIONES (Animación de Scroll Suave)
            if self.estado_pantalla == "JUGANDO":
                # Cada bloque en el menú derecho ocupa aprox 160 px de alto en espacio
                self.target_scroll_y = self.indice_seleccionado * -160
                # Interpolación lineal para suavizado (Lerp)
                self.current_scroll_y += (self.target_scroll_y - self.current_scroll_y) * 0.2

                if self.estado_resultado:
                    ahora = pygame.time.get_ticks()
                    if ahora - self.timer_resultado >= 1600:
                        if self.estado_resultado == "EXITO":
                            if self.avanzar_secuencia:
                                self.avanzar_a_siguiente_secuencia()
                            elif self.finalizar_juego:
                                self.terminar_evento()
                        self.estado_resultado = None

            # 3. RENDERIZADO
            if self.estado_pantalla == "INICIO":
                self.draw_intro()

            elif self.estado_pantalla == "JUGANDO":
                patron_actual = self.get_patron_actual()

                self.screen.fill(COLOR_BG)

                # Dibujar Interfaz Estética (Bordes y Textos)
                pygame.draw.rect(self.screen, COLOR_RED_DIM, (20, 20, WIDTH - 40, HEIGHT - 40), 2)
                texto_header = self.font.render("Link / Active-Hack / CYBER_LINK", True, COLOR_TEXT)
                self.screen.blit(texto_header, (40, 35))

                progreso = self.font.render(
                    f"SECUENCIA {self.indice_secuencia + 1} / {len(SECUENCIAS)}", True, COLOR_TEXT
                )
                self.screen.blit(progreso, (540, 35))

                # --- PANEL IZQUIERDO (Objetivo fijo) ---
                lbl_target = self.font.render("[ MATRIZ OBJETIVO ]", True, COLOR_TEXT)
                self.screen.blit(lbl_target, (100, 100))
                self.draw_matrix(patron_actual, 100, 140, size_cell=35)

                # --- PANEL DERECHO (Selector con Scroll) ---
                lbl_select = self.font.render("[ SELECCIONAR PIEZA ]", True, COLOR_TEXT)
                self.screen.blit(lbl_select, (480, 100))

                clip_surface = pygame.Surface((250, 300))
                clip_surface.fill(COLOR_BG)

                for i, opcion in enumerate(opciones_actuales):
                    y_pos = 90 + (i * 160) + self.current_scroll_y

                    if i == self.indice_seleccionado:
                        pygame.draw.rect(clip_surface, COLOR_RED_BRIGHT, (25, y_pos - 10, 165, 145), 2)
                        lbl_arrow1 = self.font.render(">", True, COLOR_RED_BRIGHT)
                        lbl_arrow2 = self.font.render("<", True, COLOR_RED_BRIGHT)
                        clip_surface.blit(lbl_arrow1, (5, y_pos + 50))
                        clip_surface.blit(lbl_arrow2, (200, y_pos + 50))

                    for r in range(5):
                        for c in range(5):
                            rect = pygame.Rect(45 + c * 22, y_pos + r * 22, 20, 20)
                            if opcion[r][c] == 1:
                                pygame.draw.rect(clip_surface, COLOR_RED_BRIGHT, rect)
                            else:
                                pygame.draw.rect(clip_surface, COLOR_GRID_BG, rect, 1)

                self.screen.blit(clip_surface, (480, 140))
                pygame.draw.rect(self.screen, COLOR_RED_DIM, (475, 135, 260, 310), 1)

                # --- MONITOREO DE ESTADOS DE VICTORIA / ERROR ---
                if self.estado_resultado:
                    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    if self.estado_resultado == "EXITO":
                        overlay.fill((0, 40, 0, 200))
                        txt = self.large_font.render("ACIERTO", True, COLOR_WHITE)
                    else:
                        overlay.fill((40, 0, 0, 200))
                        txt = self.large_font.render("INTENTO FALLIDO", True, COLOR_RED_BRIGHT)

                    self.screen.blit(overlay, (0, 0))
                    self.screen.blit(
                        txt,
                        (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - txt.get_height() // 2),
                    )

            else:
                self.draw_summary()

            # Renderizado final del post-procesado visual
            self.draw_scanlines()
            
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = PuzzleGame()
    game.run()