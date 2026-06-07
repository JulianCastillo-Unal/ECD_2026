import pygame
import sys
import time

# --- CONFIGURACIÓN ---
NEGRO = (0, 8, 0)
VERDE_OSCURO = (0, 40, 0)
VERDE_MEDIO = (0, 120, 40)
VERDE_NEON = (0, 255, 120)
VERDE_CLARO = (140, 255, 180)
BLANCO = (190, 255, 200)
GRIS_OSCURO = (0, 28, 0)
ROJO = (255, 80, 80)
AMARILLO = (0, 255, 160)
AZUL_ELECTRICO = (0, 220, 120)

ANCHO, ALTO = 800, 600
TAM_CELDA = 80
OFFSET_X, OFFSET_Y = 100, 100
GRID_ANCHO, GRID_ALTO = 6, 5 

COMP_TYPES = {
    'CABLE': {'name': 'CABLE', 'color': VERDE_CLARO, 'symbol': '||', 'func': lambda v: v},
    'ADD3':  {'name': '+3V',    'color': AZUL_ELECTRICO, 'symbol': '+3', 'func': lambda v: v + 3},
    'MULT2': {'name': 'x2V',    'color': AMARILLO, 'symbol': 'x2', 'func': lambda v: v * 2},
    'START': {'name': 'INICIO', 'color': VERDE_NEON,  'symbol': '5V', 'func': lambda v: v},
    'END':   {'name': 'FINAL',  'color': ROJO,   'symbol': '16', 'func': lambda v: v}
}

META_VOLTAJE = 16

# --- INICIALIZACIÓN ---
pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Spider-Circuit Trainer - CT Edition")
reloj = pygame.time.Clock()
fuente_peq = pygame.font.SysFont("Consolas", 16, bold=True)
fuente_med = pygame.font.SysFont("Consolas", 26, bold=True)
fuente_grande = pygame.font.SysFont("Consolas", 34, bold=True)

# --- ESTADO DEL JUEGO ---
grid = [[None for _ in range(GRID_ANCHO)] for _ in range(GRID_ALTO)]

inventario = [
    {'type': 'CABLE', 'rect': pygame.Rect(650, 100, 60, 60)},
    {'type': 'CABLE', 'rect': pygame.Rect(650, 170, 60, 60)},
    {'type': 'ADD3',  'rect': pygame.Rect(650, 240, 60, 60)},
    {'type': 'ADD3',  'rect': pygame.Rect(650, 310, 60, 60)},
    {'type': 'MULT2', 'rect': pygame.Rect(650, 380, 60, 60)}
]

grid[2][0] = 'START'  # type: ignore
grid[2][5] = 'END'    # type: ignore

componente_arrastrando = None
status_msg = "Conecta el circuito y pulsa VERIFICAR."
status_color = VERDE_CLARO
mostrar_instrucciones = True
inicio_evento = None
tiempo_final_evento = None
intentos_fallidos = 0
intentos_correctos = 0
mensaje_final = ""
evento_completado = False


def formatear_tiempo(segundos):
    return f"{segundos:.2f}s"

# --- FUNCIONES DE DIBUJO ---
def dibujar_grilla():
    for f in range(GRID_ALTO):
        for c in range(GRID_ANCHO):
            rect = pygame.Rect(OFFSET_X + c * TAM_CELDA, OFFSET_Y + f * TAM_CELDA, TAM_CELDA, TAM_CELDA)
            pygame.draw.rect(pantalla, VERDE_CLARO, rect, 1)
            if f == 2:
                pygame.draw.line(pantalla, VERDE_NEON, (rect.left, rect.centery), (rect.right, rect.centery), 1)

def dibujar_componente(tipo, x, y, size):
    comp = COMP_TYPES[tipo]
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(pantalla, comp['color'], rect, 0, 8)
    pygame.draw.rect(pantalla, VERDE_NEON, rect, 2, 8)
    texto = fuente_peq.render(comp['symbol'], True, NEGRO)
    text_rect = texto.get_rect(center=rect.center)
    pantalla.blit(texto, text_rect)

def dibujar_inventario():
    bg_rect = pygame.Rect(620, 80, 120, 400)
    pygame.draw.rect(pantalla, GRIS_OSCURO, bg_rect, 0, 10)
    pygame.draw.rect(pantalla, VERDE_NEON, bg_rect, 2, 10)
    txt_inv = fuente_med.render("INV.", True, VERDE_NEON)
    pantalla.blit(txt_inv, (645, 45))

    for item in inventario:
        if item != componente_arrastrando:
            dibujar_componente(item['type'], item['rect'].x, item['rect'].y, item['rect'].width)

def dibujar_estado():
    txt_meta = fuente_med.render(f"OBJETIVO: {META_VOLTAJE}V", True, VERDE_CLARO)
    pantalla.blit(txt_meta, (OFFSET_X, 30))

    txt_status = fuente_peq.render(status_msg, True, status_color)
    pantalla.blit(txt_status, (OFFSET_X, ALTO - 60))

    txt_contadores = fuente_peq.render(
        f"FALLIDOS: {intentos_fallidos}   CORRECTOS: {intentos_correctos}",
        True,
        VERDE_CLARO,
    )
    pantalla.blit(txt_contadores, (OFFSET_X, ALTO - 35))

    global btn_verificar
    btn_verificar = pygame.Rect(ANCHO - 200, ALTO - 80, 150, 50)
    pygame.draw.rect(pantalla, VERDE_MEDIO, btn_verificar, 0, 10)
    pygame.draw.rect(pantalla, VERDE_NEON, btn_verificar, 2, 10)
    txt_btn = fuente_peq.render("VERIFICAR", True, NEGRO)
    pantalla.blit(txt_btn, txt_btn.get_rect(center=btn_verificar.center))


def dibujar_panel_mensaje(titulo, lineas, subtitulo=None):
    panel = pygame.Rect(70, 80, ANCHO - 140, ALTO - 160)
    sombra = pygame.Rect(panel.x + 6, panel.y + 6, panel.width, panel.height)
    pygame.draw.rect(pantalla, VERDE_OSCURO, sombra, 0, 14)
    pygame.draw.rect(pantalla, GRIS_OSCURO, panel, 0, 14)
    pygame.draw.rect(pantalla, VERDE_NEON, panel, 2, 14)

    titulo_txt = fuente_grande.render(titulo, True, VERDE_NEON)
    pantalla.blit(titulo_txt, (panel.x + 30, panel.y + 25))

    y = panel.y + 90
    for linea in lineas:
        texto = fuente_peq.render(linea, True, VERDE_CLARO)
        pantalla.blit(texto, (panel.x + 30, y))
        y += 28

    if subtitulo:
        sub_txt = fuente_peq.render(subtitulo, True, VERDE_NEON)
        pantalla.blit(sub_txt, (panel.x + 30, panel.bottom - 45))


def dibujar_pantalla_inicial():
    lineas = [
        "OBJETIVO: conectar el circuito y hacer que el voltaje final sea 16V.",
        "CONTROLES:",
        "- Arrastra componentes desde el inventario con clic izquierdo.",
        "- Suelta el componente sobre una celda vacia del circuito.",
        "- Haz clic en VERIFICAR para comprobar el recorrido.",
        "- Puedes quitar un componente de la grilla arrastrandolo de nuevo.",
    ]
    dibujar_panel_mensaje(
        "SISTEMA EN MODO DIAGNOSTICO",
        lineas,
        "Presiona cualquier tecla o haz clic para iniciar.",
    )


def dibujar_pantalla_final():
    tiempo_total = tiempo_final_evento if tiempo_final_evento is not None else 0.0
    lineas = [
        "El circuito fue validado correctamente.",
        f"Intentos fallidos: {intentos_fallidos}",
        f"Intentos correctos: {intentos_correctos}",
        f"Tiempo del evento: {formatear_tiempo(tiempo_total)}",
    ]
    dibujar_panel_mensaje(
        "EVENTO COMPLETADO",
        lineas,
        "Cierra la ventana para salir.",
    )

def verificar_circuito():
    global status_msg, status_color, intentos_fallidos, intentos_correctos, mensaje_final, evento_completado, tiempo_final_evento
    current_v = 5 
    f, c = 2, 0   
    
    status_msg = "Verificando..."
    status_color = VERDE_NEON
    
    while True:
        c += 1
        if c >= GRID_ANCHO:
            intentos_fallidos += 1
            status_msg = f"Error: El circuito no llega al FINAL. Fallidos: {intentos_fallidos}"
            status_color = ROJO
            return False

        tipo_comp = grid[f][c]

        if tipo_comp is None:
            intentos_fallidos += 1
            status_msg = f"Error: Circuito roto en celda ({f},{c}). Fallidos: {intentos_fallidos}"
            status_color = ROJO
            return False
        
        comp_info = COMP_TYPES[tipo_comp]
        
        if tipo_comp == 'END':
            if current_v == META_VOLTAJE:
                intentos_correctos += 1
                tiempo_final_evento = time.perf_counter() - inicio_evento if inicio_evento else 0.0
                status_msg = (
                    f"ÉXITO: {current_v}V | Fallidos: {intentos_fallidos} | "
                    f"Correctos: {intentos_correctos} | Tiempo: {formatear_tiempo(tiempo_final_evento)}"
                )
                status_color = VERDE_NEON
                mensaje_final = status_msg
                evento_completado = True
                return True
            else:
                intentos_fallidos += 1
                status_msg = (
                    f"FALLO: Voltaje final fue {current_v}V. Se necesita {META_VOLTAJE}V. "
                    f"Fallidos: {intentos_fallidos}"
                )
                status_color = ROJO
                return False

        current_v = comp_info['func'](current_v)

# --- CICLO PRINCIPAL ---
ejecutando = True
while ejecutando:
    pantalla.fill(NEGRO)
    dibujar_grilla()
    dibujar_inventario()
    dibujar_estado()

    for f in range(GRID_ALTO):
        for c in range(GRID_ANCHO):
            tipo = grid[f][c]
            if tipo:
                dibujar_componente(tipo, OFFSET_X + c * TAM_CELDA + 10, OFFSET_Y + f * TAM_CELDA + 10, TAM_CELDA - 20)

    if componente_arrastrando:
        mx, my = pygame.mouse.get_pos()
        dibujar_componente(componente_arrastrando['type'], mx - 30, my - 30, 60)

    if mostrar_instrucciones:
        dibujar_pantalla_inicial()
    elif evento_completado:
        dibujar_pantalla_final()

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

        elif mostrar_instrucciones and evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            mostrar_instrucciones = False
            status_msg = "Conecta el circuito y pulsa VERIFICAR."
            inicio_evento = time.perf_counter()
        
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1: 
                mx, my = pygame.mouse.get_pos()
                
                for item in inventario:
                    if item['rect'].collidepoint(mx, my):
                        componente_arrastrando = item
                        break
                
                grid_c = (mx - OFFSET_X) // TAM_CELDA
                grid_f = (my - OFFSET_Y) // TAM_CELDA
                if 0 <= grid_c < GRID_ANCHO and 0 <= grid_f < GRID_ALTO:
                    tipo_en_grilla = grid[grid_f][grid_c]
                    if tipo_en_grilla and tipo_en_grilla not in ['START', 'END']:
                        grid[grid_f][grid_c] = None 
                        for item in inventario:
                            if item['type'] == tipo_en_grilla and item['rect'].x == 650:
                                componente_arrastrando = item
                                break

                if btn_verificar.collidepoint(mx, my):
                    verificar_circuito()

        elif evento.type == pygame.MOUSEBUTTONUP:
            if evento.button == 1 and componente_arrastrando:
                mx, my = pygame.mouse.get_pos()
                grid_c = (mx - OFFSET_X) // TAM_CELDA
                grid_f = (my - OFFSET_Y) // TAM_CELDA
                
                if 0 <= grid_c < GRID_ANCHO and 0 <= grid_f < GRID_ALTO:
                    if grid[grid_f][grid_c] is None:
                        grid[grid_f][grid_c] = componente_arrastrando['type']
                
                componente_arrastrando = None

    pygame.display.flip()
    reloj.tick(60)

pygame.quit()
sys.exit()