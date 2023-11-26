import pygame as pg 
from pygame.locals import *
import math
import sys

# Initializing the pygame library and several variable and constants
pg.init()

WIDTH, HEIGHT = 1200,900
display = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Solar System Simulation")
font = pg.font.get_default_font()
FONT = pg.font.Font(font, 14)
static_text = pg.font.Font(font, 16)
clock = pg.time.Clock()

G = 6.6743e-11
AU = 1.496e11
scale = 50 / AU
timescale = 900
step = 1
text_toggle = True
line_toggle = True
x_offset = 0
y_offset = 0
moons = {}

#The basic planet class containing all the attributes and methods to draw and move a planet
class Planet():        
    def __init__(self, x, y, name, mass, radius, color, sun, initial_v_x, line_limit, line_step):
        self.x = x
        self.y = y
        self.name = name
        self.mass = mass
        self.radius = radius
        self.color = color
        
        self.sun = sun
        self.dis_to_sun = 0
        
        self.ivx = initial_v_x
        self.v = pg.Vector2()
        self.v.x = self.ivx
        self.line_points = []
        self.line_limit = line_limit
        self.line_step = line_step
        
    #Calculates a moon offset so the moon doesn't clip into the planet
    def moon_offset(self, planet):
        dx = self.x - planet.x
        dy = self.y - planet.y
        return dx * scale, dy * scale
        
    #Calculate the attractive forces of one body to another
    def attraction(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        d = math.sqrt(dx**2 + dy**2)
        if other.sun:
            self.dis_to_sun = d
        angle = math.atan2(dy, dx)
        force = G * self.mass * other.mass / d**2  # F = ma
        fx = force * math.cos(angle)
        fy = force * math.sin(angle)
        return fx, fy
    
    #Updates the position of the current planet based on the forces acting on it
    def update_pos(self, bodies):
        t_fx = t_fy = 0
        for body in bodies:
            if body == self:
                continue
            fx, fy = self.attraction(body)
            t_fx += fx
            t_fy += fy
        
        self.v.x += t_fx / self.mass * timescale
        self.v.y += t_fy / self.mass * timescale
        
        self.x += self.v.x * timescale
        self.y += self.v.y * timescale
        if self.name not in moons.keys():
            if len(self.line_points) > self.line_limit:
                    del self.line_points[0]
            self.line_points.append((self.x,self.y))                    
    
    #Draws the body
    def draw(self, planet_dict):
        if self.name in moons:
            dx, dy = self.moon_offset(planet_dict[moons[self.name]])
        else:
            dx = dy = 0
        x = self.x * scale + WIDTH / 2 + 100 - x_offset + dx * math.sqrt(scale * AU)
        y = self.y * scale + HEIGHT / 2 - y_offset + dy * math.sqrt(scale * AU)
        
        if line_toggle and self.name not in moons:
            if len(self.line_points) > self.line_step * 2 and not self.sun:
                scaled_points = []
                sliced = self.line_points[::self.line_step]
                sliced.append(self.line_points[-1])
                for point in sliced:
                    px, py = point
                    px = px * scale + WIDTH / 2 + 100 - x_offset + dx * math.sqrt(scale * AU)
                    py = py * scale + HEIGHT / 2 - y_offset + dy * math.sqrt(scale * AU)
                    scaled_points.append((px,py))
                
                pg.draw.lines(display, self.color, False, scaled_points, 2)
                
        if self.name == "Saturn": #Saturns ring
            pg.draw.circle(display, (206,184,184), (x, y), self.radius * (math.log((scale * AU / 50), 5) + 0.1) + 6, 4)
            
        pg.draw.circle(display, self.color, (x, y), self.radius * (math.log((scale * AU / 50), 5) + 0.1))
        if not self.sun and text_toggle and self.name not in moons:
            name_text = FONT.render(f"{self.name}", 1, (255,255,255))
            draw_y_off = self.radius * scale * AU / 50
            display.blit(name_text, (x - name_text.get_width()/2, y - name_text.get_height()/2 - draw_y_off))

#Class for a System, the point is to make it easier to create moons and planets and position them to start because its all relative
class System():
    def __init__(self, center):
        self.center = center
        self.bodies = [self.center]
        
    def add_body(self, y, name, mass, radius, color, ivx, line_limit, line_step):
        self.bodies.append(Planet(self.center.x, self.center.y + y, name, mass, radius, color, False, self.center.ivx + ivx, line_limit, line_step))
        
    def add_system(self, y, name, mass, radius, color, sun, ivx, line_limit, line_step):
        self.bodies.append(System(Planet(self.center.x, self.center.y + y, name, mass, radius, color, sun, ivx, line_limit, line_step)))

#Takes a system and gathers all the bodies in that system in a dictionary
def congragate(system):
    planet_dict = {}
    for body in system.bodies:
        if type(body) == Planet:
            planet_dict.update({body.name: body})
        else:
            planet_dict.update(congragate(body))
    return planet_dict

#Gets the offset for the current center body
def get_offset(body):
    return body.x * scale, body.y * scale

#Creates the solar system and all the bodies in it (except most moons)
solar_system = System(Planet(0, 0, "Sun", 1.989e30, 15, (253, 184, 19), True, 0, 0, 1))
solar_system.add_system(1 * AU, "Earth", 5.972e24, 7, (107,147,214), False, 29.78e3, 17500, 150)
solar_system.bodies[1].add_body(-384400e3, "Moon", 7.34767301e22, 3, (128,128,128), -1.022e3, 20, 1)
moons.update({"Moon": "Earth"})
solar_system.add_system(1.5 * AU, "Mars", 6.39e23, 5, (193,68,14), False, 24.08e3, 32500, 300)
solar_system.bodies[2].add_body(23436e3, "Deimos", 1.8e15, 1, (138,119,163), 1.3513e3, 20, 1) #No Phobos, it was bugging out
moons.update({"Deimos": "Mars"})
solar_system.add_system(-0.7 * AU, "Venus", 4.867e24, 6, (165,124,27), False, -35.02e3, 10000, 100)
solar_system.add_system(-0.4 * AU, "Mercury", 3.285e23, 4, (173,168,165), False, -47e3, 7000, 70)
solar_system.add_system(-5.2 * AU, "Jupiter", 1.89813e27, 14, (227,220,203), False, -13.06e3, 300000, 1000)
solar_system.add_system(9.5 * AU, "Saturn", 5.683e26, 13, (234,214,184), False, 9.6725e3, 600000, 2000)
solar_system.add_system(18.2 * AU, "Uranus", 8.681e25, 10, (172, 229, 238), False, 6.81e3, 750000, 2500)
solar_system.add_system(-30 * AU, "Neptune", 1.024e26, 10, (63,84,186), False, 5.43e3, 2000000, 10000)

#List of only the planet names, no moons
planet_names = ["Sun", "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]

#Main program
def main():
    running = True
    planet_dict = congragate(solar_system)
    global scale, timescale, step, line_toggle, text_toggle, current_center, x_offset, y_offset
    current_center = planet_dict["Sun"]
    x_offset = current_center.x * scale
    y_offset = current_center.y * scale
        
    while running:
        clock.tick(60)        
        
        #Even handling
        keys = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                #Toggle certain visual elements
                if event.key == K_t:
                    if text_toggle == False:
                        text_toggle = True
                    else:
                        text_toggle = False
                if event.key == K_l:
                    if line_toggle == False:
                        line_toggle = True
                    else:
                        line_toggle = False
                
                #Speed up/slow down
                if event.key == K_LEFT:
                    if step >= 2:
                        step -= 1
                    elif timescale == 225:
                        pass
                    else:
                        timescale /= 2
                    
                if event.key == K_RIGHT:
                    if timescale == 1800 and step < 24:
                        step += 1
                    elif step == 24:
                        pass
                    else:
                        timescale *= 2
                    
                #Swap planet view
                if event.key == K_a:
                    if planet_names.index(current_center.name) == 0:
                        current_center = planet_dict[planet_names[-1]]
                        x_offset, y_offset = get_offset(current_center)
                    else:
                        current_center = planet_dict[planet_names[planet_names.index(current_center.name) - 1]]
                        x_offset, y_offset = get_offset(current_center)
                if event.key == K_d:
                    if planet_names.index(current_center.name) == len(planet_names) - 1:
                        current_center = planet_dict[planet_names[0]]
                        x_offset, y_offset = get_offset(current_center) 
                    else:
                        current_center = planet_dict[planet_names[planet_names.index(current_center.name) + 1]]
                        x_offset, y_offset = get_offset(current_center)
                        
        #Handle closing the application
        if keys[K_ESCAPE]:
            running = False
            pg.quit()
            sys.exit()
        
        #Zoom in and out
        if keys[K_UP]:
            scale += 1 / AU
        if keys[K_DOWN]:
            if scale >= 5.5/AU:
                scale -= 1 / AU
            
        #Wipe background
        display.fill((0,0,0))
        
        #Calculate new offset
        x_offset, y_offset = get_offset(current_center)  
        
        #Update position of all bodies
        for i in range(step):
            for body in planet_dict.values():
                body.update_pos(planet_dict.values())
            
        #Draw all the bodies
        for body in planet_dict.values():
            body.draw(planet_dict)
        
        #Blit all the static text like distance to sun and scale, step, and timescale
        for i, name in enumerate(planet_names, 0):
            distance_text = FONT.render(f"Km from Sun ({planet_dict[name].name}):{round(planet_dict[name].dis_to_sun/1000, 1)}", 1, planet_dict[name].color)
            display.blit(distance_text, (10, 115 + i * 25))            
        
        display.blit(static_text.render(f"Scale (relative): {round(scale * AU, 0)}", True, (255,255,255)), (10, 55))
        display.blit(static_text.render(f"Steps: {step}", True, (255,255,255)), (10, 75))
        display.blit(static_text.render(f"Timescale: {timescale}", True, (255,255,255)), (10, 95))
        
        pg.display.flip()
        
if __name__ == "__main__": main()