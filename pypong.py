import pygame
import matplotlib.pyplot as plt
import numpy as np
import time

# VARIABLES:
width = 1280
height = 762
border = 20

bgColor = (0, 0, 0, 255)
fgColor = (0, 170, 0, 255)

velocity = 4



# CLASSES:
class Ball:

    RADIUS = 10

    def __init__(self, x, v, color=(0, 170, 0, 255)):
        self.x = np.array(x, dtype=np.float)
        self.v = np.array(v, dtype=np.float)
        self.color = color
    
    def updatePosition_simple(self):
        global width, height, border

        new_x = self.x[0] + self.v[0]
        if new_x <= border+self.RADIUS and self.v[0] < 0:
            new_x = border + self.RADIUS + (border + self.RADIUS - new_x)
            self.v[0] = - self.v[0]
        
        new_y = self.x[1] + self.v[1]

        self.x = np.array([new_x, new_y])
    
    def updatePosition_general(self, walls):
        global border, width, height
        v_abs = np.sum(self.v * self.v)
        if v_abs == 0:
            return
        collision = []
        kmin = 1
        for i, wall in enumerate(walls):
            wp = wall.wall_point
            wn = wall.wall_normal
            thickness = wall.thickness / 2
            denominator = np.sum(wn*self.v)
            sign = -1 if denominator > 0 else 1
            wp = wp + sign * (self.RADIUS + thickness) * wn
            if denominator == 0:
                continue
            k = np.sum(wn * (wp - self.x))/denominator
            if k >= 0 and k <= kmin:
                x_impact = self.x + k * self.v
                point_along_line = np.sum((x_impact - wp) * wall.wall_vec)
                if point_along_line < 0 or point_along_line > wall.length:
                    continue
                collision = [i, k, wn, denominator]
                kmin = k
        
        if len(collision) == 4:
            i, k, wn, denominator = collision
            dx2 = (self.v - 2 * denominator * wn)
            xnew = self.x + k * self.v
            vnew = np.sqrt(v_abs/np.sum(dx2*dx2)) * dx2
            if xnew[0] < self.RADIUS + thickness or xnew[0] > width - (self.RADIUS + thickness):
                print(width - (self.RADIUS + thickness), (self.RADIUS + thickness))
                vnew = np.array([0,0])
                print(xnew)
            self.x = xnew
            self.v = vnew
            self.updatePosition_general([w for j,w in enumerate(walls) if j != i])
            self.v = self.v
            return
        self.x = self.x + self.v
        return

    def drawPosition(self, canvas):
        pygame.draw.circle(canvas, self.color, tuple(self.x), self.RADIUS)
    

    def blankPosition(self, canvas, bgColor):
        pygame.draw.circle(canvas, bgColor, tuple(self.x), self.RADIUS)
    
    def updateDraw(self, canvas, walls, bgColor):
        self.blankPosition(canvas, bgColor)
        #self.updatePosition_simple()
        self.updatePosition_general(walls)
        self.drawPosition(canvas)
        if self.v[1] > 0 and self.v[0] > 0:
            angle = np.arctan(self.v[1]/self.v[0])
        elif self.v[1] >= 0 and self.v[0] <= 0:
            angle = np.pi + (np.arctan(self.v[1]/self.v[0]) if self.v[0] != 0 else np.pi/2)
        elif self.v[1] <= 0 and self.v[0] <= 0:
            angle = np.pi + (np.arctan(self.v[1]/self.v[0]) if self.v[0] != 0 else 3*np.pi/2)
        elif self.v[1] < 0 and self.v[0] >= 0:
            angle = 2*np.pi + np.arctan(self.v[1]/self.v[0])

        return angle/np.pi * 180

                
class Wall:

    def __init__(self, wall_point, wall_normal, length, thickness, color=(0, 170, 0, 255)):
        self.wall_point = np.array(wall_point)
        self.wall_normal = np.array(wall_normal)
        self.wall_normal = self.wall_normal / np.sqrt(np.sum(self.wall_normal * self.wall_normal))
        self.wall_vec = np.array([-self.wall_normal[1], self.wall_normal[0]])
        self.length = length
        self.thickness = thickness
        self.color = color

    def draw(self, canvas, color):
        p1 = self.wall_point + self.wall_normal * self.thickness/2
        p2 = p1 + self.length * self.wall_vec
        p3 = p2 - self.wall_normal * self.thickness
        p4 = p1 - self.wall_normal * self.thickness
        pygame.draw.polygon(canvas, color, (p1, p2, p3, p4))
    
    def show(self, canvas):
        self.draw(canvas, self.color)

    def hide(self, canvas):
        self.draw(canvas, (0,0,0,255))

    



        

class Paddle(Wall):

    ANGLE = 0.01
    
    def __init__(self, paddle_point, paddle_normal, length, thickness, color=(0, 170, 0, 255)):
        Wall.__init__(self, paddle_point, paddle_normal, length, thickness)
        self.turned = 0

    def update(self, screen):
        global border, height
        self.hide(screen)
        newY = pygame.mouse.get_pos()[1]
        if newY > border + self.length/2 and newY <  height - border - self.length/2:
            self.wall_point[1] = newY - self.length/2
        self.show(screen)

    def turnLeft(self, screen):
        if self.turned == 0:
            self.hide(screen)
            self.wall_normal = normalizeVec(rotateVec(self.wall_normal, self.ANGLE))
            self.wall_vec = normalToDirection(self.wall_normal)
            self.show(screen)
            self.turned = 0

    def turnRight(self, screen):
        if self.turned == 0:
            self.hide(screen)
            self.wall_normal = normalizeVec(rotateVec(self.wall_normal, -self.ANGLE))
            self.wall_vec = normalToDirection(self.wall_normal)
            self.show(screen)
            self.turned = 0
    
    def centerTilt(self, screen):
        self.hide(screen)
        if self.turned == -1:
            alpha = -self.ANGLE
        elif self.turned == 1:
            alpha = self.ANGLE
        else:
            alpha = 0
        self.wall_normal = normalizeVec(rotateVec(self.wall_normal, alpha))
        self.wall_vec = normalToDirection(self.wall_normal)
        self.show(screen)
        self.turned = 0


def rotateVec(vec, angle):
    rotation = np.array([
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)]
        ]) 
    return np.sum(rotation * vec, axis=1)

def normalizeVec(vec):
    return  vec / np.sqrt(np.sum(vec * vec))

def normalToDirection(vec):
    return np.array([-vec[1], vec[0]])


# Initialize pygame
pygame.init()
nvec = np.array([-height//2, 2*width//3])
screen = pygame.display.set_mode((width,height))
playball = Ball((width//2, height//2), (-velocity, -velocity*2), color=fgColor)
walls = []
walls.append(Wall((0,0), (0, -1), width, border*2))
# walls.append(Wall((0,0), (1, 0), height, border*2))
# walls.append(Wall((width, 0), (1, 0), width, border*2))
walls.append(Wall((0, height), (0, -1), width, border*2))

for wall in walls:
    wall.show(screen)

playball.drawPosition(screen)
paddle = Paddle((width - 100, height//2 + 100), (1,0), 200, 5)
paddle2 = Paddle((100, height//2 + 100), (1, 0), 200, 5)


walls.append(paddle)
walls.append(paddle2)
paddle.show(screen)
paddle2.show(screen)

# Mainloop
count = 0
clock = pygame.time.Clock()

pygame.display.flip()

# while True:
#     e = pygame.event.poll()
#     if pygame.mouse.get_pressed(num_buttons=3)[0]:
#         break

t = time.time()
while True:
    e = pygame.event.poll()
    if e.type == pygame.QUIT:
        break
    now = time.time()
    clock.tick_busy_loop(120)
    if now - t > 1:
        count += 1
        t = now
    pygame.display.flip()

    mouse_press = pygame.mouse.get_pressed(num_buttons=3)
    if mouse_press[0] and (not mouse_press[2]):
        paddle.turnLeft(screen)
        paddle2.turnLeft(screen)
    elif mouse_press[2] and (not mouse_press[0]):
        paddle.turnRight(screen)
        paddle2.turnRight(screen)
    else:
        paddle.centerTilt(screen)
        paddle2.centerTilt(screen)
    playball.updateDraw(screen, walls, bgColor)
    paddle.update(screen)
    paddle2.update(screen)
    if playball.x[0] < 0 or playball.x[0] > width:
        break
# Clean-up and Quit
pygame.quit()

