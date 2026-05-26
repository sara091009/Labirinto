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
    def _init_(self, cella_x, cella_y, velocita):
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

            