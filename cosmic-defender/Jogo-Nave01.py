import pygame
import random
import sys
import json
from os import path
from math import atan2, radians, sin, cos

# Inicialização
pygame.init()
pygame.mixer.init()

# Configurações do jogo
LARGURA = 1280
ALTURA = 720
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Cosmic Defender Pro")

# Cores
PRETO = (0, 0, 0)
CINZA = (100, 100, 100)
VERMELHO = (255, 0, 0)
AZUL = (0, 120, 255)
BRANCO = (255, 255, 255)
FUNDO = (10, 10, 30)
VERDE = (0, 255, 0)

# Configurações de arquivo
HIGHSCORE_FILE = "highscore.json"

# Estados do jogo
MENU = 0
JOGANDO = 1
GAME_OVER = 2

# Constantes
BOSS_INTERVAL = 100
ENEMY_SPAWN_LEVEL = 70

# Inicialização de sons (corrigido)
game_over_sound = None
explosion_sound = None
damage_sound = None
start_sound = None

try:
    game_over_sound = pygame.mixer.Sound('sounds/soundsgame_over.wav')
    explosion_sound = pygame.mixer.Sound('sounds/soundsexplosion.wav')
    damage_sound = pygame.mixer.Sound('sounds/soundsdamage.wav')
    start_sound = pygame.mixer.Sound('sounds/start.wav')
    pygame.mixer.music.load('sounds/loop1.ogg')  # caminho do arquivo
    
    # Configurar volumes
    game_over_sound.set_volume(10)
    explosion_sound.set_volume(0.3)
    damage_sound.set_volume(0.8)
    start_sound.set_volume(10)
    pygame.mixer.music.set_volume(0.5)  # volume da música (0.0 a 1.0)
    pygame.mixer.music.play(-1)  # -1 para repetir infinitamente
except Exception as e:
    print(f"Erro ao carregar sons: {e}")

# Classe para efeitos de partículas (mantido igual)
class Particula(pygame.sprite.Sprite):
    def __init__(self, pos, color=VERMELHO):
        super().__init__()
        self.image = pygame.Surface((6, 6))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        self.velocidade = pygame.math.Vector2(random.uniform(-3, 3), random.uniform(-3, 3))
        self.tempo_vida = 20
        self.timer = 0

    def update(self):
        self.rect.move_ip(self.velocidade)
        self.timer += 1
        if self.timer >= self.tempo_vida:
            self.kill()

# Classe da Nave (corrigido o uso de sons)
class Nave(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.images = []
        try:
            for i in range(1, 4):
                img = pygame.image.load(path.join('img', f'nave{i}.png')).convert_alpha()
                img = pygame.transform.scale(img, (60, 45))
                self.images.append(img)
            self.image = self.images[0]
        except Exception as e:
            print(f"Erro ao carregar imagens: {e}")
            self.image = pygame.Surface((60, 45), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, AZUL, [(30, 0), (0, 45), (60, 45)])
        
        self.rect = self.image.get_rect(center=(LARGURA//2, ALTURA-80))
        self.velocidade = 10
        self.vidas_max = 6
        self.vidas = self.vidas_max
        self.invencivel = False
        self.tempo_invencivel = 0
        self.upgrade_level = 0
        self.auto_tiro = False
        self.last_shot = 0

    def update(self, teclas):
        if len(self.images) >= 3:
            if self.upgrade_level < 10:
                self.image = self.images[0]
            elif 10 <= self.upgrade_level < 20:
                self.image = self.images[1]
            else:
                self.image = self.images[2]

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.rect.x -= self.velocidade
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.rect.x += self.velocidade
        self.rect.clamp_ip(TELA.get_rect())

        if self.invencivel and pygame.time.get_ticks() > self.tempo_invencivel:
            self.invencivel = False

        self.vidas_max = 3 + (self.upgrade_level // 5)
        if self.upgrade_level >= 20:
            self.auto_tiro = True

    def atirar(self):
        agora = pygame.time.get_ticks()
        if self.auto_tiro:
            if agora - self.last_shot > 300 - (self.upgrade_level * 5):
                self.last_shot = agora
                return Tiro(self.rect.centerx, self.rect.top)
        else:
            if agora - self.last_shot > 500 - (self.upgrade_level * 10):
                self.last_shot = agora
                return Tiro(self.rect.centerx, self.rect.top)
        return None

    def tomar_dano(self):
        if not self.invencivel:
            dano = max(1, 3 - (self.upgrade_level // 15))
            self.vidas -= dano
            self.invencivel = True
            self.tempo_invencivel = pygame.time.get_ticks() + 2000
            if damage_sound:  # Verificação adicionada
                damage_sound.play()
            return self.vidas <= 0
        return False

# Classe dos Tiros (mantido igual)
class Tiro(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 20))
        self.image.fill(VERMELHO)
        self.rect = self.image.get_rect(center=(x, y))
        self.velocidade = -15

    def update(self):
        self.rect.y += self.velocidade
        if self.rect.bottom < 0:
            self.kill()

# Classe dos Meteoros (corrigido colisão)
                # ... (código anterior mantido igual até a definição da classe Meteoro)

class Meteoro(pygame.sprite.Sprite):
    def __init__(self, tamanho=3):
        super().__init__()
        self.tamanho = tamanho
        tamanhos = {3: 80, 2: 50, 1: 30}
        
        try:
            # Carrega a imagem do meteoro
            self.image_original = pygame.image.load(path.join('meteoros', 'meteoro.png')).convert_alpha()
            # Redimensiona conforme o tamanho
            self.image = pygame.transform.scale(self.image_original, 
                                               (tamanhos[tamanho], tamanhos[tamanho]))
        except Exception as e:
            print(f"Erro ao carregar imagem do meteoro: {e}")
            # Fallback: círculo cinza
            self.image = pygame.Surface((tamanhos[tamanho], tamanhos[tamanho]), pygame.SRCALPHA)
            cores = {3: (80,80,80), 2: (120,120,120), 1: (160,160,160)}
            pygame.draw.circle(self.image, cores[tamanho], 
                              (tamanhos[tamanho]//2, tamanhos[tamanho]//2), 
                              tamanhos[tamanho]//2)
        
        self.rect = self.image.get_rect(center=(random.randint(0, LARGURA), -100))
        self.velocidade = random.randint(2, 3) + (3 - self.tamanho)*1.5
        self.radius = tamanhos[tamanho]//2

    def update(self):
        self.rect.y += self.velocidade
        if self.rect.top > ALTURA:
            self.kill()

    def split(self):
        if self.tamanho > 1:
            for _ in range(2):
                novo_meteoro = Meteoro(self.tamanho - 1)
                novo_meteoro.rect.center = self.rect.center
                yield novo_meteoro

# ... (restante do código mantido igual)

# Sistema de estrelas de fundo (mantido igual)
class Estrela:
    def __init__(self):
        self.pos = pygame.math.Vector2(random.randint(0, LARGURA), random.randint(0, ALTURA))
        self.vel = random.uniform(0.1, 0.5)
        self.size = random.randint(1, 2)
    
    def update(self):
        self.pos.y += self.vel
        if self.pos.y > ALTURA:
            self.pos = pygame.math.Vector2(random.randint(0, LARGURA), 0)

# Funções do jogo (mantido igual)
def carregar_highscore():
    try:
        if path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, 'r') as f:
                return json.load(f).get('highscore', 0)
        else:
            with open(HIGHSCORE_FILE, 'w') as f:
                json.dump({'highscore': 0}, f)
            return 0
    except:
        return 0

def salvar_highscore(pontuacao):
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump({'highscore': pontuacao}, f)
    except:
        pass

def desenhar_botao(surface, texto, x, y, largura, altura, cor_normal, cor_hover):
    mouse = pygame.mouse.get_pos()
    clique = pygame.mouse.get_pressed()
    rect = pygame.Rect(x, y, largura, altura)
    
    if x < mouse[0] < x + largura and y < mouse[1] < y + altura:
        pygame.draw.rect(surface, cor_hover, rect)
        if clique[0]:
            return True
    else:
        pygame.draw.rect(surface, cor_normal, rect)
    
    fonte = pygame.font.Font(None, 36)
    texto_surf = fonte.render(texto, True, BRANCO)
    texto_rect = texto_surf.get_rect(center=rect.center)
    surface.blit(texto_surf, texto_rect)
    return False

# Inicialização do jogo (mantido igual)
todos_sprites = pygame.sprite.Group()
meteoros = pygame.sprite.Group()
tiros = pygame.sprite.Group()
particulas = pygame.sprite.Group()
estrelas = [Estrela() for _ in range(100)]

nave = Nave()
todos_sprites.add(nave)

pontos = 0
highscore = carregar_highscore()
estado_jogo = MENU
relogio = pygame.time.Clock()
pygame.time.set_timer(pygame.USEREVENT, 500)

# Loop principal (corrigido colisões e sons)
while True:
    relogio.tick(60)
    
    # Eventos
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif evento.type == pygame.USEREVENT and estado_jogo == JOGANDO:
            meteoros.add(Meteoro())

    # Estados do jogo
    if estado_jogo == MENU:
        TELA.fill(FUNDO)
        
        # Título
        fonte_titulo = pygame.font.Font(None, 100)
        titulo = fonte_titulo.render("COSMIC DEFENDER", True, AZUL)
        TELA.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 100))
        
        # Botão Iniciar
        if desenhar_botao(TELA, "INICIAR JOGO", LARGURA//2 - 100, 300, 200, 50, VERDE, (0, 200, 0)):
            estado_jogo = JOGANDO
            if start_sound:  # Verificação adicionada
                start_sound.play()
            try:
                pygame.mixer.music.play(-1)
                print("Música começou no início do jogo!")
            except Exception as e:
                print(f"Erro ao tocar música: {e}")


        # High Score
        fonte_score = pygame.font.Font(None, 36)
        texto_score = fonte_score.render(f"High Score: {highscore}", True, BRANCO)
        TELA.blit(texto_score, (LARGURA//2 - texto_score.get_width()//2, 400))
        
        pygame.display.flip()
        continue

    elif estado_jogo == JOGANDO:
        teclas = pygame.key.get_pressed()
        nave.update(teclas)
        tiros.update()
        meteoros.update()
        particulas.update()

        # Tiro automático
        tiro = nave.atirar()
        if tiro:
            tiros.add(tiro)

        # Atualizar estrelas
        for estrela in estrelas:
            estrela.update()

        # Colisões tiros-meteoros (corrigido)
        for tiro in tiros.copy():
            hits = pygame.sprite.spritecollide(tiro, meteoros, True, pygame.sprite.collide_circle)
            if hits:
                pontos += sum(100 // hit.tamanho for hit in hits)
                tiro.kill()
                if explosion_sound:
                    explosion_sound.play()
                
                for hit in hits:
                    for _ in range(15):
                        particulas.add(Particula(hit.rect.center, CINZA))
                    
                    for novo_meteoro in hit.split():
                        meteoros.add(novo_meteoro)

        # Colisão nave-meteoros (corrigido)
        hits = pygame.sprite.spritecollide(nave, meteoros, True, pygame.sprite.collide_circle)
        if hits and not nave.invencivel:
            if explosion_sound:
                explosion_sound.play()
            for _ in range(30):
                particulas.add(Particula(nave.rect.center, AZUL))
            if nave.tomar_dano():
                if game_over_sound:
                    game_over_sound.play()
                estado_jogo = GAME_OVER

        # Atualizar highscore
        if pontos > highscore:
            highscore = pontos
            salvar_highscore(highscore)

    elif estado_jogo == GAME_OVER:
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_r]:
            if pygame.mixer.get_init():  # Verificação segura
                pygame.mixer.stop()
            estado_jogo = JOGANDO
            pontos = 0
            todos_sprites.empty()
            meteoros.empty()
            tiros.empty()
            particulas.empty()
            nave = Nave()
            todos_sprites.add(nave)

    # Renderização (mantido igual)
    TELA.fill(FUNDO)
    
    # Fundo estrelado
    for estrela in estrelas:
        pygame.draw.circle(TELA, BRANCO, (int(estrela.pos.x), int(estrela.pos.y)), estrela.size)

    # Elementos do jogo
    todos_sprites.draw(TELA)
    tiros.draw(TELA)
    meteoros.draw(TELA)
    particulas.draw(TELA)

    # UI
    fonte = pygame.font.Font(None, 36)
    texto_score = fonte.render(f"Score: {pontos}", True, BRANCO)
    texto_highscore = fonte.render(f"High Score: {highscore}", True, BRANCO)
    texto_vidas = fonte.render(f"Vidas: {nave.vidas}/{nave.vidas_max}", True, VERMELHO)
    texto_upgrade = fonte.render(f"Upgrade Level: {nave.upgrade_level}", True, VERDE)
    
    TELA.blit(texto_score, (20, 20))
    TELA.blit(texto_highscore, (20, 60))
    TELA.blit(texto_vidas, (LARGURA - 200, 20))
    TELA.blit(texto_upgrade, (LARGURA - 200, 60))

    # Botão de Upgrade
    if estado_jogo == JOGANDO:
        if desenhar_botao(TELA, f"UPGRADE (60)", LARGURA - 200, 100, 180, 40, (100,100,100), VERDE):
            if pontos >= 60 and nave.upgrade_level < 100:
                pontos -= 60
                nave.upgrade_level += 1

    # Tela de Game Over
    if estado_jogo == GAME_OVER:
        fonte_go = pygame.font.Font(None, 72)
        texto_go = fonte_go.render("GAME OVER", True, VERMELHO)
        TELA.blit(texto_go, (LARGURA//2 - texto_go.get_width()//2, ALTURA//2 - 50))
        
        fonte_reiniciar = pygame.font.Font(None, 36)
        texto_reiniciar = fonte_reiniciar.render("Pressione R para recomeçar", True, BRANCO)
        TELA.blit(texto_reiniciar, (LARGURA//2 - texto_reiniciar.get_width()//2, ALTURA//2 + 20))

    pygame.display.flip()