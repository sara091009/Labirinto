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