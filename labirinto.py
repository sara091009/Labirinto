import pygame
import sys
import random
import math

# Inizializzazione Pygame
pygame.init()

# --- USO DELLE TUPLE PER I COLORI ---
COLORI = {
    "STRADA": (255, 255, 255),
    "MURO": (50, 50, 50),
    "GIOCATORE": (255, 0, 0),
    "INVISIBILE": (255, 150, 150),
    "MOSTRO": (0, 0, 0),
    "MONETA": (255, 215, 0),
    "CHIAVE": (0, 0, 255),
    "USCITA": (0, 200, 0),
    "TESTO": (30, 30, 30),
    "ATTIVO": (0, 150, 0)
}

DIMENSIONE_CELLA = 40
font = pygame.font.SysFont("Arial", 14, bold=True)

orologio = pygame.time.Clock()
gioco_attivo = True

def genera_labirinto_casuale(righe, colonne):
    """Genera un labirinto con corridoi multipli collegati per evitare vicoli ciechi totali."""
    griglia = [["#"] * colonne for _ in range(righe)]
    visitati = set()

    def scava(r, c):
        visitati.add((r, c))
        griglia[r][c] = "."
        direzioni = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(direzioni)
        
        for dr, dc in direzioni:
            nr, nc = r + dr, c + dc
            if 0 < nr < righe - 1 and 0 < nc < colonne - 1 and (nr, nc) not in visitati:
                griglia[r + dr // 2][c + dc // 2] = "."
                scava(nr, nc)

    scava(1, 1)
    
    # Abbattiamo muri casuali per creare bivi e percorsi alternativi (Anelli)
    for r in range(1, righe - 1):
        for c in range(1, colonne - 1):
            if griglia[r][c] == "#" and random.random() < 0.25:
                if (griglia[r-1][c] == "." and griglia[r+1][c] == ".") or (griglia[r][c-1] == "." and griglia[r][c+1] == "."):
                    griglia[r][c] = "."

    # Zona iniziale sicura del giocatore (1,1) e vicinanze sempre libere
    griglia[1][1] = "."
    griglia[1][2] = "."
    griglia[2][1] = "."
    
    # Posizionamento e sblocco sicuro dell'uscita
    griglia[righe - 2][colonne - 2] = "E"
    griglia[righe - 2][colonne - 3] = "."
    griglia[righe - 3][colonne - 2] = "."
        
    return griglia


class Mostro:

    def __init__(self, cella_x, cella_y, velocita):

        self.cella_partenza_x = cella_x
        self.cella_partenza_y = cella_y
        self.rect = pygame.Rect(cella_x * DIMENSIONE_CELLA + 6, cella_y * DIMENSIONE_CELLA + 6, 28, 28)
        self.velocita = velocita
        self.direzioni_possibili = ((0, self.velocita), (0, -self.velocita), (self.velocita, 0), (-self.velocita, 0))
        self.dx, self.dy = random.choice(self.direzioni_possibili)
        
        self.frame_bloccato = 0
        self.timer_stordimento_aggro = 0

    def reset_posizione(self):
        """Riporta il mostro alla sua cella di nascita e azzera il tracciamento."""
        self.rect.x = self.cella_partenza_x * DIMENSIONE_CELLA + 6
        self.rect.y = self.cella_partenza_y * DIMENSIONE_CELLA + 6
        self.frame_bloccato = 0
        self.timer_stordimento_aggro = pygame.time.get_ticks() + 1500  # Calmo per 1.5 secondi dopo il reset
        self.cambia_direzione()

    def aggiorna(self, lista_muri, giocatore_rect, invisibile):
        tempo_attuale = pygame.time.get_ticks()
        dist_x = giocatore_rect.centerx - self.rect.centerx
        dist_y = giocatore_rect.centery - self.rect.centery
        distanza = math.hypot(dist_x, dist_y)

        if invisibile or tempo_attuale < self.timer_stordimento_aggro:
            if random.randint(1, 40) == 1: self.cambia_direzione()
        elif distanza < DIMENSIONE_CELLA * 4 and self.frame_bloccato < 10:
            if abs(dist_x) > abs(dist_y):
                self.dx = self.velocita if dist_x > 0 else -self.velocita
                self.dy = 0
            else:
                self.dx = 0
                self.dy = self.velocita if dist_y > 0 else -self.velocita
        else:
            if random.randint(1, 60) == 1: self.cambia_direzione()

        is_colliding = False
        pos_precedente = (self.rect.x, self.rect.y)

        self.rect.x += self.dx
        for muro in lista_muri:
            if self.rect.colliderect(muro):
                if self.dx > 0: self.rect.right = muro.left
                if self.dx < 0: self.rect.left = muro.right
                is_colliding = True

        self.rect.y += self.dy
        for muro in lista_muri:
            if self.rect.colliderect(muro):
                if self.dy > 0: self.rect.bottom = muro.top
                if self.dy < 0: self.rect.top = muro.bottom
                is_colliding = True

        if is_colliding and (self.rect.x, self.rect.y) == pos_precedente:
            self.frame_bloccato += 1
            if self.frame_bloccato >= 10:
                self.timer_stordimento_aggro = tempo_attuale + 2000
                self.frame_bloccato = 0
                self.cambia_direzione_laterale()
        else:
            if not is_colliding: self.frame_bloccato = max(0, self.frame_bloccato - 1)

        if is_colliding: self.cambia_direzione_laterale()

    def cambia_direzione(self):
        self.dx, self.dy = random.choice(self.direzioni_possibili)

    def cambia_direzione_laterale(self):
        if self.dx != 0:
            self.dx = 0
            self.dy = random.choice((self.velocita, -self.velocita))
        else:
            self.dy = 0
            self.dx = random.choice((self.velocita, -self.velocita))

livello_attuale = 1
dimensione_mappa = (11, 11)

def avvia_livello(livello, dimensioni):
    righe, colonne = dimensioni
    mappa_generata = genera_labirinto_casuale(righe, colonne)
    
    muri_rect, monete_rect, strade_libere, strade_per_mostri = [], [], [], []
    uscita_rect = None
    riga_sicurezza = righe // 2

    for y in range(righe):
        for x in range(colonne):
            rect = pygame.Rect(x * DIMENSIONE_CELLA, y * DIMENSIONE_CELLA, DIMENSIONE_CELLA, DIMENSIONE_CELLA)
            if mappa_generata[y][x] == "#": muri_rect.append(rect)
            elif mappa_generata[y][x] == "E": uscita_rect = rect
            elif mappa_generata[y][x] == "." and (x, y) not in [(1,1), (1,2), (2,1)]:
                strade_libere.append((x, y))
                if y > riga_sicurezza and (x, y) != (colonne-2, righe-2): strade_per_mostri.append((x, y))

    random.shuffle(strade_libere)
    random.shuffle(strade_per_mostri)
    if not strade_per_mostri: strade_per_mostri = strade_libere.copy()

    # Spacchettamento delle tuple geometriche
    cx, cy = strade_libere.pop()
    chiave_rect = pygame.Rect(cx * DIMENSIONE_CELLA, cy * DIMENSIONE_CELLA, DIMENSIONE_CELLA, DIMENSIONE_CELLA)
    
    for _ in range(3 + livello):
        if strade_libere:
            mx, my = strade_libere.pop()
            monete_rect.append(pygame.Rect(mx * DIMENSIONE_CELLA, my * DIMENSIONE_CELLA, DIMENSIONE_CELLA, DIMENSIONE_CELLA))

    mostri_generati = []
    for _ in range(1 + livello):
        if strade_per_mostri:
            ox, oy = strade_per_mostri.pop()
            mostri_generati.append(Mostro(ox, oy, min(2 + (livello // 2), 4)))

    risoluzione = (colonne * DIMENSIONE_CELLA, (righe * DIMENSIONE_CELLA) + 55)
    schermo_gioco = pygame.display.set_mode(risoluzione)
    pygame.display.set_caption(f"Labirinto con Skill - Livello {livello}")

    giocatore = pygame.Rect(1 * DIMENSIONE_CELLA + 6, 1 * DIMENSIONE_CELLA + 6, 28, 28)
    return schermo_gioco, mappa_generata, muri_rect, monete_rect, chiave_rect, uscita_rect, mostri_generati, giocatore, 2 + (livello // 2), False

schermo, mappa, muri, monete, chiave_rect, uscita_rect, lista_mostri, giocatore_rect, monete_necessarie, ha_chiave = avvia_livello(livello_attuale, dimensione_mappa)

velocita_base, monete_totali, durata_scatto, durata_invisibilita = 4, 0, 0, 0

while gioco_attivo:
    orologio.tick(60)
    tempo_attuale = pygame.time.get_ticks()
    
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT: gioco_attivo = False
        elif evento.type == pygame.KEYDOWN:
            if (evento.key == pygame.K_1 or evento.key == pygame.K_KP1) and monete_totali >= 1 and tempo_attuale > durata_scatto:
                monete_totali -= 1
                durata_scatto = tempo_attuale + 3000
                                # ... (Le righe sopra appartengono alla gestione eventi dentro il ciclo while) ...
                print("⚡ Skill Scatto Attivata!")
            if (evento.key == pygame.K_2 or evento.key == pygame.K_KP2) and monete_totali >= 2 and tempo_attuale > durata_invisibilita:
                # Allineato a 16 spazi (dentro la gestione eventi di pressione dei tasti)
                monete_totali -= 2
                durata_invisibilita = tempo_attuale + 4000
                print("👻 Skill Invisibilità Attivata!")

    # Variabili di stato delle skill (Allineato a 4 spazi: dentro il ciclo while)
    scatto_attivo = tempo_attuale < durata_scatto
    invisibilita_attiva = tempo_attuale < durata_invisibilita
    velocita_corrente = velocita_base * 2 if scatto_attivo else velocita_base

    # Lettura degli input direzionali continui (Allineato a 4 spazi)
    tasti = pygame.key.get_pressed()
    dx, dy = 0, 0
    if tasti[pygame.K_w] or tasti[pygame.K_UP]:    dy = -velocita_corrente
    if tasti[pygame.K_s] or tasti[pygame.K_DOWN]:  dy = velocita_corrente
    if tasti[pygame.K_a] or tasti[pygame.K_LEFT]:  dx = -velocita_corrente
    if tasti[pygame.K_d] or tasti[pygame.K_RIGHT]: dx = velocita_corrente

    # Movimento e collisione asse X (Allineato a 4 spazi)
    giocatore_rect.x += dx
    for muro in muri:
        # Dentro il ciclo for dei muri: 8 spazi
        if giocatore_rect.colliderect(muro):
            # Dentro l'if di collisione della X: 12 spazi
            if dx > 0: giocatore_rect.right = muro.left
            if dx < 0: giocatore_rect.left = muro.right

    # Movimento e collisione asse Y (Allineato a 4 spazi)
    giocatore_rect.y += dy
    for muro in muri:
        # Dentro il ciclo for dei muri: 8 spazi
        if giocatore_rect.colliderect(muro):
            # Dentro l'if di collisione della Y: 12 spazi
            if dy > 0: giocatore_rect.bottom = muro.top
            if dy < 0: giocatore_rect.top = muro.bottom

    # Aggiornamento IA dei nemici (Allineato a 4 spazi)
    for mostro in lista_mostri:
        # Dentro il ciclo for dei mostri: 8 spazi
        mostro.aggiorna(muri, giocatore_rect, invisibilita_attiva)

    # 🔍 CORREZIONE INTERAZIONI MONETE (Allineato a 4 spazi: sistemati gli spazi errati in eccesso)
    for moneta in monete[:]:
        # Dentro il ciclo for delle monete: 8 spazi
        if giocatore_rect.colliderect(moneta):
            # Dentro l'if di collisione moneta: 12 spazi
            monete.remove(moneta)
            monete_totali += 1

    # Raccolta Chiave Blu (Allineato a 4 spazi)
    if chiave_rect and giocatore_rect.colliderect(chiave_rect):
        # Dentro l'if della chiave: 8 spazi
        ha_chiave = True
        chiave_rect = None

    # Controllo Collisioni con Mostri (Allineato a 4 spazi)
    for mostro in lista_mostri:
        # Dentro il ciclo for dei mostri: 8 spazi
        if giocatore_rect.colliderect(mostro.rect):
            # Dentro la collisione con il mostro: 12 spazi
            if not invisibilita_attiva:
                # Se non sei invisibile (Reset con protezione spawn): 16 spazi
                print("👾 Catturato! Protezione attiva: i bot vengono allontanati dallo spawn.")
                giocatore_rect.x = 1 * DIMENSIONE_CELLA + 6
                giocatore_rect.y = 1 * DIMENSIONE_CELLA + 6
                for m in lista_mostri:
                    # Rientrato dentro l'if di reset: 20 spazi
                    m.reset_posizione()
                break 
            else:
                # Se sei invisibile (Mostro respinto): 16 spazi
                mostro.cambia_direzione()
                mostro.rect.x += mostro.dx * 8
                mostro.rect.y += mostro.dy * 8

    # Controllo Uscita Verde (Allineato a 4 spazi)
    if giocatore_rect.colliderect(uscita_rect):
        # Dentro il controllo dell'uscita: 8 spazi
        if ha_chiave and monete_totali >= monete_necessarie:
            # Livello superato con successo: 12 spazi
            livello_attuale += 1
            vecchie_righe, vecchie_colonne = dimensione_mappa
            dimensione_mappa = (vecchie_righe + 2, vecchie_colonne + 2)
            ha_chiave = False
            schermo, mappa, muri, monete, chiave_rect, uscita_rect, lista_mostri, giocatore_rect, monete_necessarie, ha_chiave = avvia_livello(livello_attuale, dimensione_mappa)
        else:
            # Bloccato se mancano i requisiti: 12 spazi
            if dx != 0: giocatore_rect.x -= dx * 2
            if dy != 0: giocatore_rect.y -= dy * 2

    # --- RENDERING GRAFICO --- (Allineato a 4 spazi)
    schermo.fill(COLORI["STRADA"])
    
    for muro in muri:
        # Dentro il ciclo for dei muri: 8 spazi
        pygame.draw.rect(schermo, COLORI["MURO"], muro)
        
    pygame.draw.rect(schermo, COLORI["USCITA"], uscita_rect)

    if chiave_rect:
        # Dentro il controllo della chiave: 8 spazi
        pygame.draw.rect(schermo, COLORI["CHIAVE"], chiave_rect.inflate(-16, -16))
        
    for moneta in monete:
        # Dentro il ciclo for delle monete: 8 spazi
        pygame.draw.circle(schermo, COLORI["MONETA"], moneta.center, 7)
        
    for mostro in lista_mostri:
        # Dentro il ciclo for dei mostri: 8 spazi
        pygame.draw.rect(schermo, COLORI["MOSTRO"], mostro.rect)
        
    pygame.draw.rect(schermo, COLORI["INVISIBILE"] if invisibilita_attiva else COLORI["GIOCATORE"], giocatore_rect)

    # BARRA HUD IN BASSO (Allineato a 4 spazi)
    altezza_interfaccia = 55
    regione_interfaccia = pygame.Rect(0, schermo.get_height() - altezza_interfaccia, schermo.get_width(), altezza_interfaccia)
    pygame.draw.rect(schermo, (230, 230, 230), regione_interfaccia)
    
    testo_info = font.render(f"Lvl: {livello_attuale} | Monete: {monete_totali}/{monete_necessarie} | Chiave: {'SÌ' if ha_chiave else 'NO'}", True, COLORI["TESTO"])
    schermo.blit(testo_info, (10, schermo.get_height() - 48))
    
    testo_s1 = font.render(f"1-Scatto (Costo: 1)", True, COLORI["ATTIVO"] if scatto_attivo else COLORI["TESTO"])
    testo_s2 = font.render(f"2-Invisibile (Costo: 2)", True, COLORI["ATTIVO"] if invisibilita_attiva else COLORI["TESTO"])
    schermo.blit(testo_s1, (10, schermo.get_height() - 24))
    schermo.blit(testo_s2, (160, schermo.get_height() - 24))

    pygame.display.flip()

# <--- Fine del ciclo "while gioco_attivo" (Il codice torna completamente a inizio riga)
pygame.quit()
sys.exit()
