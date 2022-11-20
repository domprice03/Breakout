import pygame as pg
import sys
import random
from pygame.locals import *


class Paddle:
    def __init__(self):
        self.width = 160
        self.height = 20
        self.rect = Rect(WIDTH / 2 - 80, HEIGHT - 40, self.width, self.height)
        self.left = False
        self.right = False
        self.accelerating = False
        self.velocity = 5
        self.acceleration = 0.5
        self.invincibility_frames = 0       # Needed to stop one collision registering multiple times.
        self.effect_time = 0

    def draw(self):
        pg.draw.rect(screen, WHITE, self.rect)

    def move(self):
        if self.left and self.right:
            self.accelerating = False
        elif self.right and self.rect.x <= WIDTH - self.rect.w:
            self.accelerating = True
            self.rect.x += self.velocity
        elif self.left and self.rect.x >= 0:
            self.accelerating = True
            self.rect.x -= self.velocity

        if self.accelerating and self.velocity <= 20:
            self.velocity += self.acceleration
        elif not self.accelerating:
            self.velocity = 5

    def decrement(self):
        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1
        if self.effect_time > -1:
            self.effect_time -= 1
        if self.effect_time == 0:
            # Need a more sophisticated way to decrease width uniformly from left and right.
            self.rect.w = self.width


class Ball:
    def __init__(self):
        self.rect = pg.Rect(WIDTH/2 - 5, HEIGHT/2 - 5, 10, 10)
        self.velocity = pg.Vector2(random.randrange(-5, 5), 8)
        self.damage = 1
        self.invincibility_frames = 0       # Confusingly, this pertains to wall collisions.
        self.effect_time = 0

    def draw(self):
        pg.draw.rect(screen, WHITE, self.rect)

    def move_x(self):
        self.rect.x += self.velocity.x

    def move_y(self):
        self.rect.y += self.velocity.y

    def collide_horizontal_surface(self):
        self.velocity.y = -1 * self.velocity.y

    def collide_vertical_surface(self):
        self.velocity.x = -1 * self.velocity.x

    def collisions(self):
        # Ball gets stuck in wall for no apparent reason when colliding at a very small angle to the wall.
        if self.invincibility_frames == 0:
            if self.rect.x <= 0 or self.rect.x >= WIDTH-10:
                self.collide_vertical_surface()
                # self.invincibility_frames = 4
            if self.rect.y <= 0:
                self.collide_horizontal_surface()
                # self.invincibility_frames = 4

    def decrement(self):
        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1
        '''if self.effect_time > 0:
            self.effect_time -= 1'''


class Block:
    def __init__(self, x, y):
        self.rect = pg.Rect(x, y, 80, 25)
        self.invincibility_frames = 0       # Needed to stop one collision registering multiples times.

    def draw(self):
        pg.draw.rect(screen, self.colour, self.rect)

    def hit_by_ball(self, ball):
        self.health -= ball.damage
        colours = {-4:BLACK, -3:BLACK, -2:BLACK, -1:BLACK, 0:BLACK, 1: WHITE, 2: YELLOW, 3: ORANGE}
        self.colour = colours[self.health]

    def decrement_invincibility_frames(self):
        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1


class Block1(Block):
    # Standard block, requiring one hit to break.
    def __init__(self, x, y):
        super().__init__(x, y)
        self.colour = WHITE
        self.health = 1


class Block2(Block):
    # Tough block. Requires two hits to break.
    def __init__(self, x, y):
        super().__init__(x, y)
        self.colour = YELLOW
        self.health = 2


class Block3(Block):
    # Reinforced tough block. Requires three hits to break.
    def __init__(self, x, y):
        super().__init__(x, y)
        self.colour = ORANGE
        self.health = 3


class PowerUp():
    def __init__(self):
        self.velocity = 3

    def move(self):
        self.rect.y += self.velocity

    def draw(self):
        pg.draw.rect(screen, self.colour, self.rect)

    def drop_powerup(self):
        if random.uniform(0, 1) <= self.probability:
            return True

    def set_rect(self, x, y):
        self.rect = pg.Rect(x, y, 25, 25)

    def hit_paddle(self, balls, paddle):
        if self.rect.colliderect(paddle.rect):
            self.effect(balls, paddle)


class ExtraBall(PowerUp):
    def __init__(self):
        super().__init__()
        self.colour = GREEN
        self.probability = 0.05

    def effect(self, balls):
        balls.append(Ball())


class EnlargePaddle(PowerUp):
    def __init__(self):
        super().__init__()
        self.colour = BLUE
        self.probability = 0.05

    def effect(self, paddle):
        paddle.rect.w = paddle.width * 2
        paddle.effect_time = FPS * 5    # Effect lasts 5 seconds. Need to add animation.


class ExtraDamage(PowerUp):
    def __init__(self):
        super().__init__()
        self.colour = RED
        self.probability = 0.05

    def effect(self, ball):
        # Piercing to regular blocks and extra damage to tough blocks. Damage decreases to 1 after collisions.
        ball.damage = 5


class Main:
    def __init__(self, block_map, miss_align):
        self.paddle = Paddle()
        self.num_balls = 1
        self.balls = [Ball() for i in range(self.num_balls)]
        self.blocks = []
        self.powerups = []      # Contains powerups and their locations.

        for y, row in enumerate(block_map):
            for x, block in enumerate(row):
                if miss_align:
                    # Odd rows are offset by 0.5 to the left to create the effect of a brick wall.
                    if y % 2 == 1:
                        X = x - 0.5
                    else:
                        X = x
                else:
                    X = x
                # block == '0' represents empty space.
                if block == '1':
                    self.blocks.append(Block1(X * 80, y * 25))
                elif block == '2':
                    self.blocks.append(Block2(X * 80, y * 25))
                elif block == '3':
                    self.blocks.append(Block3(X * 80, y * 25))

    def update(self):
        self.paddle.move()

        for ball in self.balls:
            ball.move_x()
            if ball.rect.colliderect(self.paddle.rect) and self.paddle.invincibility_frames == 0:
                ball.collide_vertical_surface()
                # Invincibility frames cause issues when multiple balls collide in quick succession.
                self.paddle.invincibility_frames = 2
                # The following may cause very slight issues if the paddle isn't moving.
                if self.paddle.right:
                    ball.velocity.x += self.paddle.velocity
                elif self.paddle.left:
                    ball.velocity.x -= self.paddle.velocity
            for i, block in enumerate(self.blocks):
                if ball.rect.colliderect(block.rect) and block.invincibility_frames == 0:
                    if ball.damage <= block.health:
                        ball.collide_vertical_surface()
                    else:       # High damage shots are piercing.
                        ball.damage -= block.health  # Damage decreases with successive hits.
                    self.block_hit(block, ball, i)

            ball.move_y()
            if ball.rect.colliderect(self.paddle.rect) and self.paddle.invincibility_frames == 0:
                ball.collide_horizontal_surface()
                self.paddle.invincibility_frames = 2
                if self.paddle.right:
                    ball.velocity.x += self.paddle.velocity * 0.1
                elif self.paddle.left:
                    ball.velocity.x -= self.paddle.velocity * 0.1
            for i, block in enumerate(self.blocks):
                if ball.rect.colliderect(block.rect) and block.invincibility_frames == 0:
                    if ball.damage <= block.health:
                        ball.collide_horizontal_surface()
                    else:       # High damage shots are piercing.
                        ball.damage -= block.health  # Damage decreases with successive hits.
                    self.block_hit(block, ball, i)
                block.decrement_invincibility_frames()

            ball.collisions()
            ball.decrement()

        for i, powerup in enumerate(self.powerups):
            powerup.move()
            # Code can be simplified by passing all parameters to powerup.hit_paddle
            if powerup.rect.colliderect(self.paddle.rect):
                if type(powerup).__name__ == 'ExtraBall':
                    powerup.effect(self.balls)
                elif type(powerup).__name__ == 'EnlargePaddle':
                    powerup.effect(self.paddle)
                elif type(powerup).__name__ == 'ExtraDamage':
                    for ball in self.balls:
                        powerup.effect(ball)
                self.powerups.pop(i)

        self.paddle.decrement()

    def draw_elements(self):
        self.paddle.draw()
        for ball in self.balls:
            ball.draw()
        for block in self.blocks:
            block.draw()
        for powerup in self.powerups:
            powerup.draw()

    def block_hit(self, block, ball, i):
        block.hit_by_ball(ball)
        block.invincibility_frames = 4
        if block.health <= 0:
            self.blocks.pop(i)
            self.check_powerups(block)

    def check_powerups(self, block):
        # If multiple powerups drop from one block then it's visually confusing.
        if ExtraBall.drop_powerup(ExtraBall()):
            self.powerups.append(ExtraBall())
            self.powerups[-1].set_rect(block.rect.x, block.rect.y)
        if EnlargePaddle.drop_powerup(EnlargePaddle()):
            self.powerups.append(EnlargePaddle())
            self.powerups[-1].set_rect(block.rect.x, block.rect.y)
        if ExtraDamage.drop_powerup(ExtraDamage()):
            self.powerups.append(ExtraDamage())
            self.powerups[-1].set_rect(block.rect.x, block.rect.y)


pg.init()
clock = pg.time.Clock()
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

WIDTH = HEIGHT = 800
screen = pg.display.set_mode((WIDTH, HEIGHT), 0, 32)
pg.display.set_caption("Breakout")

COR = 1       # Coefficient of restitution

block_map = [['0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
             ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
             ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
             ['0', '0', '0', '0', '0', '0', '0', '0', '0', '0'],
             ['0', '0', '1', '1', '1', '1', '1', '1', '0', '0'],
             ['0', '1', '1', '2', '1', '1', '2', '1', '1', '0'],
             ['0', '0', '1', '1', '3', '3', '1', '1', '0', '0'],
             ['0', '1', '1', '2', '1', '1', '2', '1', '1', '0'],
             ['0', '0', '1', '1', '1', '1', '1', '1', '0', '0'],]

main_game = Main(block_map, False)


def main():
    def draw_screen():
        screen.fill(BLACK)
        main_game.draw_elements()
        pg.display.update()

    while True:
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RIGHT:
                    main_game.paddle.right = True
                if event.key == pg.K_LEFT:
                    main_game.paddle.left = True
                main_game.paddle.accelerating = True
            if event.type == pg.KEYUP:
                if event.key == pg.K_RIGHT:
                    main_game.paddle.right = False
                if event.key == pg.K_LEFT:
                    main_game.paddle.left = False
                main_game.paddle.accelerating = False

        main_game.update()

        draw_screen()
        clock.tick(FPS)


def main_menu():
    title_font = pg.font.SysFont("comicsans", 70)
    run = True
    while run:
        title_label = title_font. render("Press space to begin...", 1, WHITE)
        screen.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 350))
        pg.display.update()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                main()


if __name__ == "__main__":
    main_menu()
