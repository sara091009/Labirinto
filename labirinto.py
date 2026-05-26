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