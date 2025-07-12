# Adventure Game with Speech-to-Speech Integration
import os
# os.environ['SDL_VIDEODRIVER'] = 'cocoa'  # Use native macOS window system (removed for Windows compatibility)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np
import sys
import textwrap
import openai
from dotenv import load_dotenv
import time
import logging

# Import our enhanced dialogue system
from enhanced_dialogue_system import EnhancedDialogueSystem

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Ensure OpenAI API Key is loaded
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("[OpenAI] API key not found. Please set OPENAI_API_KEY in your .env file.")
    sys.exit(1)

openai.api_key = api_key
client = openai
print("[OpenAI] API key loaded successfully.")

# Initialize Pygame with macOS specific settings
pygame.init()
display = (800, 600)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 2)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
screen = pygame.display.get_surface()

# Set up the camera and perspective
glEnable(GL_DEPTH_TEST)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)

# Set up basic lighting
glEnable(GL_LIGHTING)
glEnable(GL_LIGHT0)
glLightfv(GL_LIGHT0, GL_POSITION, [0, 5, 5, 1])
glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1])
glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1])

# Enable blending for transparency
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Initial camera position
glTranslatef(0.0, 0.0, -5)

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
TILE_SIZE = 32
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
GRAY = (128, 128, 128)

# Menu constants
TITLE = "Venture Builder AI"
SUBTITLE = "Our Digital Employees"
MENU_BG_COLOR = (0, 0, 0)
MENU_TEXT_COLOR = (0, 255, 0)
MENU_HIGHLIGHT_COLOR = (0, 200, 0)

def draw_cube():
    vertices = [
        # Front face
        [-0.5, -0.5,  0.5],
        [ 0.5, -0.5,  0.5],
        [ 0.5,  0.5,  0.5],
        [-0.5,  0.5,  0.5],
        # Back face
        [-0.5, -0.5, -0.5],
        [-0.5,  0.5, -0.5],
        [ 0.5,  0.5, -0.5],
        [ 0.5, -0.5, -0.5],
    ]
    
    surfaces = [
        [0, 1, 2, 3],  # Front
        [3, 2, 6, 5],  # Top
        [0, 3, 5, 4],  # Left
        [1, 7, 6, 2],  # Right
        [4, 5, 6, 7],  # Back
        [0, 4, 7, 1],  # Bottom
    ]
    
    glBegin(GL_QUADS)
    for surface in surfaces:
        glNormal3f(0, 0, 1)
        for vertex in surface:
            glVertex3fv(vertices[vertex])
    glEnd()

def draw_sphere(radius, slices, stacks):
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        z0 = math.sin(lat0)
        zr0 = math.cos(lat0)
        
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        z1 = math.sin(lat1)
        zr1 = math.cos(lat1)
        
        glBegin(GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2 * math.pi * float(j) / slices
            x = math.cos(lng)
            y = math.sin(lng)
            
            glNormal3f(x * zr0, y * zr0, z0)
            glVertex3f(x * zr0 * radius, y * zr0 * radius, z0 * radius)
            glNormal3f(x * zr1, y * zr1, z1)
            glVertex3f(x * zr1 * radius, y * zr1 * radius, z1 * radius)
        glEnd()

# [Include all the existing classes: World, Player, NPC, MenuScreen with minimal changes]
# I'll include the key classes here but they remain largely the same

class World:
    def __init__(self):
        self.size = 5
        self.colors = {
            'floor': (0.76, 0.6, 0.42),
            'walls': (0.85, 0.85, 0.85),
            'desk': (0.6, 0.4, 0.2),
            'chair': (0.2, 0.2, 0.2),
            'computer': (0.1, 0.1, 0.1),
            'plant': (0.2, 0.5, 0.2),
            'partition': (0.3, 0.3, 0.3)
        }
    
    def draw_desk(self, x, z, rotation=0):
        glPushMatrix()
        glTranslatef(x, 0, z)
        glRotatef(rotation, 0, 1, 0)
        
        # Desk top
        glColor3f(*self.colors['desk'])
        glBegin(GL_QUADS)
        glVertex3f(-0.4, 0.4, -0.3)
        glVertex3f(0.4, 0.4, -0.3)
        glVertex3f(0.4, 0.4, 0.3)
        glVertex3f(-0.4, 0.4, 0.3)
        glEnd()
        
        # Desk legs
        for x_offset, z_offset in [(-0.35, -0.25), (0.35, -0.25), (-0.35, 0.25), (0.35, 0.25)]:
            glBegin(GL_QUADS)
            glVertex3f(x_offset-0.02, 0, z_offset-0.02)
            glVertex3f(x_offset+0.02, 0, z_offset-0.02)
            glVertex3f(x_offset+0.02, 0.4, z_offset-0.02)
            glVertex3f(x_offset-0.02, 0.4, z_offset-0.02)
            glEnd()
        
        # Computer monitor
        glColor3f(*self.colors['computer'])
        glTranslatef(-0.15, 0.4, 0)
        glBegin(GL_QUADS)
        glVertex3f(-0.1, 0, -0.05)
        glVertex3f(0.1, 0, -0.05)
        glVertex3f(0.1, 0.2, -0.05)
        glVertex3f(-0.1, 0.2, -0.05)
        glEnd()
        
        glPopMatrix()
    
    def draw_chair(self, x, z, rotation=0):
        glPushMatrix()
        glTranslatef(x, 0, z)
        glRotatef(rotation, 0, 1, 0)
        glColor3f(*self.colors['chair'])
        
        # Seat
        glBegin(GL_QUADS)
        glVertex3f(-0.15, 0.25, -0.15)
        glVertex3f(0.15, 0.25, -0.15)
        glVertex3f(0.15, 0.25, 0.15)
        glVertex3f(-0.15, 0.25, 0.15)
        glEnd()
        
        # Back
        glBegin(GL_QUADS)
        glVertex3f(-0.15, 0.25, -0.15)
        glVertex3f(0.15, 0.25, -0.15)
        glVertex3f(0.15, 0.5, -0.15)
        glVertex3f(-0.15, 0.5, -0.15)
        glEnd()
        
        # Chair legs
        for x_offset, z_offset in [(-0.12, -0.12), (0.12, -0.12), (-0.12, 0.12), (0.12, 0.12)]:
            glBegin(GL_QUADS)
            glVertex3f(x_offset-0.02, 0, z_offset-0.02)
            glVertex3f(x_offset+0.02, 0, z_offset-0.02)
            glVertex3f(x_offset+0.02, 0.25, z_offset-0.02)
            glVertex3f(x_offset-0.02, 0.25, z_offset-0.02)
            glEnd()
        
        glPopMatrix()
    
    def draw_plant(self, x, z):
        glPushMatrix()
        glTranslatef(x, 0, z)
        
        # Plant pot
        glColor3f(0.4, 0.2, 0.1)
        pot_radius = 0.1
        pot_height = 0.15
        segments = 8
        
        glBegin(GL_QUADS)
        for i in range(segments):
            angle1 = (i / segments) * 2 * math.pi
            angle2 = ((i + 1) / segments) * 2 * math.pi
            x1 = math.cos(angle1) * pot_radius
            z1 = math.sin(angle1) * pot_radius
            x2 = math.cos(angle2) * pot_radius
            z2 = math.sin(angle2) * pot_radius
            glVertex3f(x1, 0, z1)
            glVertex3f(x2, 0, z2)
            glVertex3f(x2, pot_height, z2)
            glVertex3f(x1, pot_height, z1)
        glEnd()
        
        # Plant leaves
        glColor3f(*self.colors['plant'])
        glTranslatef(0, pot_height, 0)
        leaf_size = 0.15
        num_leaves = 6
        for i in range(num_leaves):
            angle = (i / num_leaves) * 2 * math.pi
            x = math.cos(angle) * leaf_size
            z = math.sin(angle) * leaf_size
            glBegin(GL_TRIANGLES)
            glVertex3f(0, 0, 0)
            glVertex3f(x, leaf_size, z)
            glVertex3f(z, leaf_size/2, -x)
            glEnd()
        
        glPopMatrix()
    
    def draw_partition_walls(self, x, z):
        glColor3f(0.3, 0.3, 0.3)
        
        # Back wall
        glPushMatrix()
        glTranslatef(x, 0, z)
        glScalef(0.05, 1.0, 1.0)
        draw_cube()
        glPopMatrix()
        
        # Side wall
        glPushMatrix()
        glTranslatef(x, 0, z + 0.5)
        glRotatef(90, 0, 1, 0)
        glScalef(0.05, 1.0, 0.8)
        draw_cube()
        glPopMatrix()
    
    def draw(self):
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Draw floor
        glBegin(GL_QUADS)
        glColor3f(*self.colors['floor'])
        glNormal3f(0, 1, 0)
        glVertex3f(-self.size, 0, -self.size)
        glVertex3f(-self.size, 0, self.size)
        glVertex3f(self.size, 0, self.size)
        glVertex3f(self.size, 0, -self.size)
        glEnd()
        
        # Draw walls
        glBegin(GL_QUADS)
        glColor3f(*self.colors['walls'])
        
        # Front wall
        glVertex3f(-self.size, 0, -self.size)
        glVertex3f(self.size, 0, -self.size)
        glVertex3f(self.size, 2, -self.size)
        glVertex3f(-self.size, 2, -self.size)
        
        # Back wall
        glVertex3f(-self.size, 0, self.size)
        glVertex3f(self.size, 0, self.size)
        glVertex3f(self.size, 2, self.size)
        glVertex3f(-self.size, 2, self.size)
        
        # Left wall
        glVertex3f(-self.size, 0, -self.size)
        glVertex3f(-self.size, 0, self.size)
        glVertex3f(-self.size, 2, self.size)
        glVertex3f(-self.size, 2, -self.size)
        
        # Right wall
        glVertex3f(self.size, 0, -self.size)
        glVertex3f(self.size, 0, self.size)
        glVertex3f(self.size, 2, self.size)
        glVertex3f(self.size, 2, -self.size)
        glEnd()
        
        # Draw office furniture
        self.draw_desk(-4, -2, 90)
        self.draw_chair(-3.5, -2, 90)
        self.draw_partition_walls(-4, -2)
        
        self.draw_desk(4, 1, -90)
        self.draw_chair(3.5, 1, -90)
        self.draw_partition_walls(4, 1)
        
        # Plants in corners
        self.draw_plant(-4.5, -4.5)
        self.draw_plant(4.5, -4.5)
        self.draw_plant(-4.5, 4.5)
        self.draw_plant(4.5, 4.5)

class Player:
    def __init__(self):
        self.pos = [0, 0.5, 0]
        self.rot = [0, 0, 0]
        self.speed = 0.3
        self.mouse_sensitivity = 0.5
    
    def move(self, dx, dz):
        angle = math.radians(-self.rot[1])
        
        move_x = (dx * math.cos(angle) + dz * math.sin(angle)) * self.speed
        move_z = (-dx * math.sin(angle) + dz * math.cos(angle)) * self.speed
        
        new_x = self.pos[0] + move_x
        new_z = self.pos[2] + move_z
        
        room_limit = 4.5
        if abs(new_x) < room_limit:
            self.pos[0] = new_x
        if abs(new_z) < room_limit:
            self.pos[2] = new_z
    
    def update_rotation(self, dx, dy):
        self.rot[1] += dx * self.mouse_sensitivity

class NPC:
    def __init__(self, x, y, z, role="HR"):
        self.scale = 0.6
        self.pos = [x, 0.65, z]
        self.size = 0.5
        self.role = role
        
        self.skin_color = (0.8, 0.7, 0.6)
        self.hair_color = (0.2, 0.15, 0.1) if role == "HR" else (0.3, 0.3, 0.3)
        
        if role == "HR":
            self.clothes_primary = (0.8, 0.2, 0.2)
            self.clothes_secondary = (0.6, 0.15, 0.15)
        else:
            self.clothes_primary = (0.2, 0.3, 0.8)
            self.clothes_secondary = (0.15, 0.2, 0.6)
    
    def draw(self):
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        glScalef(self.scale, self.scale, self.scale)
        
        # Head
        glColor3f(*self.skin_color)
        draw_sphere(0.12, 16, 16)
        
        # Hair
        glColor3f(*self.hair_color)
        glPushMatrix()
        glTranslatef(0, 0.05, 0)
        draw_sphere(0.13, 16, 16)
        glPopMatrix()
        
        # Body
        glColor3f(*self.clothes_primary)
        glPushMatrix()
        glTranslatef(0, -0.3, 0)
        glScalef(0.3, 0.4, 0.2)
        draw_cube()
        glPopMatrix()
        
        # Arms
        glColor3f(*self.clothes_secondary)
        for x_offset in [-0.2, 0.2]:
            glPushMatrix()
            glTranslatef(x_offset, -0.3, 0)
            glScalef(0.1, 0.4, 0.1)
            draw_cube()
            glPopMatrix()
        
        # Legs
        for x_offset in [-0.1, 0.1]:
            glPushMatrix()
            glTranslatef(x_offset, -0.8, 0)
            glScalef(0.1, 0.5, 0.1)
            draw_cube()
            glPopMatrix()
        
        glPopMatrix()

class MenuScreen:
    def __init__(self):
        self.font_large = pygame.font.Font(None, 74)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.active = True
        self.start_time = time.time()
    
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        
        center_y = WINDOW_HEIGHT // 2
        title_y = center_y - 100
        subtitle_y = center_y - 20
        prompt_y = center_y + 100
        
        elapsed_time = time.time() - self.start_time
        title_chars = int(min(len(TITLE), elapsed_time * 15))
        partial_title = TITLE[:title_chars]
        title_surface = self.font_large.render(partial_title, True, MENU_TEXT_COLOR)
        title_x = (WINDOW_WIDTH - title_surface.get_width()) // 2
        surface.blit(title_surface, (title_x, title_y))
        
        if elapsed_time > len(TITLE) / 15:
            subtitle_alpha = min(255, int((elapsed_time - len(TITLE) / 15) * 255))
            subtitle_surface = self.font_medium.render(SUBTITLE, True, MENU_TEXT_COLOR)
            subtitle_surface.set_alpha(subtitle_alpha)
            subtitle_x = (WINDOW_WIDTH - subtitle_surface.get_width()) // 2
            surface.blit(subtitle_surface, (subtitle_x, subtitle_y))
        
        if elapsed_time > (len(TITLE) / 15 + 1):
            if int(elapsed_time * 2) % 2:
                prompt_text = "Press ENTER to start"
                prompt_surface = self.font_small.render(prompt_text, True, MENU_TEXT_COLOR)
                prompt_x = (WINDOW_WIDTH - prompt_surface.get_width()) // 2
                surface.blit(prompt_surface, (prompt_x, prompt_y))
        
        for y in range(0, WINDOW_HEIGHT, 4):
            pygame.draw.line(surface, (0, 50, 0), (0, y), (WINDOW_WIDTH, y))
        
        texture_data = pygame.image.tostring(surface, "RGBA", True)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WINDOW_WIDTH, WINDOW_HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(0, 0)
        glTexCoord2f(1, 1); glVertex2f(WINDOW_WIDTH, 0)
        glTexCoord2f(1, 0); glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
        glTexCoord2f(0, 0); glVertex2f(0, WINDOW_HEIGHT)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        
        # Reset OpenGL state for 3D rendering
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (WINDOW_WIDTH / WINDOW_HEIGHT), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glEnable(GL_DEPTH_TEST)
        pygame.display.flip()

class Game3D:
    def __init__(self):
        self.menu = MenuScreen()
        self.player = Player()
        self.world = World()
        
        # Use the enhanced dialogue system instead of the original
        self.dialogue = EnhancedDialogueSystem(api_key)
        
        self.hr_npc = NPC(-3.3, 0, -2, "HR")
        self.ceo_npc = NPC(3.3, 0, 1, "CEO")
        self.interaction_distance = 2.0
        self.last_interaction_time = 0
    
    def move_player_away_from_npc(self, npc_pos):
        dx = self.player.pos[0] - npc_pos[0]
        dz = self.player.pos[2] - npc_pos[2]
        
        distance = math.sqrt(dx*dx + dz*dz)
        if distance > 0:
            dx /= distance
            dz /= distance
        
        self.player.pos[0] = npc_pos[0] + (dx * 3)
        self.player.pos[2] = npc_pos[2] + (dz * 3)
    
    def run(self):
        running = True
        clock = pygame.time.Clock()
        
        while running:
            if self.menu.active:
                # Menu loop
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN and time.time() - self.menu.start_time > (len(TITLE) / 15 + 1):
                            self.menu.active = False
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                
                self.menu.render()
            else:
                # Main game loop
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            pygame.mouse.set_visible(True)
                            pygame.event.set_grab(False)
                            running = False
                        
                        # Handle dialogue input and check for exit command
                        if self.dialogue.active:
                            result = self.dialogue.handle_input(event)
                            if isinstance(result, dict) and result.get("command") == "move_player_back":
                                # Move player away from the current NPC
                                current_npc = self.hr_npc if self.dialogue.current_npc == "HR" else self.ceo_npc
                                self.move_player_away_from_npc(current_npc.pos)
                    
                    elif event.type == pygame.MOUSEMOTION:
                        x, y = event.rel
                        self.player.update_rotation(x, y)
                
                # Handle keyboard input for movement (blocked during dialogue)
                if not self.dialogue.active:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_w]: self.player.move(0, -1)
                    if keys[pygame.K_s]: self.player.move(0, 1)
                    if keys[pygame.K_a]: self.player.move(-1, 0)
                    if keys[pygame.K_d]: self.player.move(1, 0)
                
                # Check NPC interactions
                current_time = time.time()
                if current_time - self.last_interaction_time > 0.5:
                    # Check distance to HR NPC
                    dx = self.player.pos[0] - self.hr_npc.pos[0]
                    dz = self.player.pos[2] - self.hr_npc.pos[2]
                    hr_distance = math.sqrt(dx*dx + dz*dz)
                    
                    # Check distance to CEO NPC
                    dx = self.player.pos[0] - self.ceo_npc.pos[0]
                    dz = self.player.pos[2] - self.ceo_npc.pos[2]
                    ceo_distance = math.sqrt(dx*dx + dz*dz)
                    
                    if hr_distance < self.interaction_distance and not self.dialogue.active:
                        self.dialogue.start_conversation("HR", self.player.pos)
                        self.last_interaction_time = current_time
                    elif ceo_distance < self.interaction_distance and not self.dialogue.active:
                        self.dialogue.start_conversation("CEO", self.player.pos)
                        self.last_interaction_time = current_time
                
                # Clear the screen and depth buffer
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                
                # Save the current matrix
                glPushMatrix()
                
                # Apply player rotation and position
                glRotatef(self.player.rot[0], 1, 0, 0)
                glRotatef(self.player.rot[1], 0, 1, 0)
                glTranslatef(-self.player.pos[0], -self.player.pos[1], -self.player.pos[2])
                
                # Draw the world and NPCs
                self.world.draw()
                self.hr_npc.draw()
                self.ceo_npc.draw()
                
                # Restore the matrix
                glPopMatrix()
                
                # Render dialogue system (if active)
                self.dialogue.render()
                
                # Swap the buffers
                pygame.display.flip()
                
                # Maintain 60 FPS
                clock.tick(60)
        
        # Cleanup
        if hasattr(self.dialogue, '_cleanup'):
            self.dialogue._cleanup()
        pygame.quit()

# Create and run game
if __name__ == "__main__":
    try:
        game = Game3D()
        game.run()
    except Exception as e:
        logger.error(f"Game crashed: {e}")
        pygame.quit()
        sys.exit(1)
