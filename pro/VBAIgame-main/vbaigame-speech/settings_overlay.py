import pygame

class SettingsOverlay:
    def __init__(self, font=None):
        self.active = False
        self.width = 540
        self.height = 360
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA).convert_alpha()
        self.font = font or pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        self.input_volume = 1.0
        self.output_volume = 1.0
        self.default_mode = 'speech'  # or 'text'
        self.voice_preview_callback = None
        self.selected_voice = None
        self.npc_voices = {}
        self.message = ''
        # Device selection
        self.input_devices = []  # List of (idx, name)
        self.selected_input_device = None
        self.input_device_callback = None

    def set_input_devices(self, devices, selected_idx=None):
        self.input_devices = devices
        self.selected_input_device = selected_idx

    def set_input_device_callback(self, callback):
        self.input_device_callback = callback

    def set_npc_voices(self, npc_voices):
        self.npc_voices = npc_voices

    def set_voice_preview_callback(self, callback):
        self.voice_preview_callback = callback

    def open(self):
        self.active = True
        self.message = ''

    def close(self):
        self.active = False
        self.message = ''

    def handle_event(self, event):
        """Handle overlay events: ESC to close, mouse for sliders and buttons"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Translate mouse pos to overlay-local
            ox, oy = 138, 98
            lx, ly = mx - ox, my - oy
            # Input volume slider (x: 180-380, y: 72)
            if 180 <= lx <= 380 and 72 <= ly <= 92:
                self._dragging = 'input'
                self._set_volume_from_mouse(lx, 'input')
            # Output volume slider (x: 180-380, y: 104)
            elif 180 <= lx <= 380 and 104 <= ly <= 124:
                self._dragging = 'output'
                self._set_volume_from_mouse(lx, 'output')
            # Input device dropdown (x: 180-500, y: 136+24*i)
            elif 180 <= lx <= 500:
                if self.input_devices:
                    y_base = 152
                    for i, (idx, name) in enumerate(self.input_devices):
                        by = y_base + i*28
                        if by <= ly <= by+24:
                            self.selected_input_device = idx
                            if self.input_device_callback:
                                self.input_device_callback(idx)
                            self.message = f"Selected input device: {name}"
                            break
            # Voice preview buttons (y: 164+28*i)
            elif 48 <= lx <= 360:
                for i, npc in enumerate(self.npc_voices):
                    by = 164 + i*28
                    if by <= ly <= by+24:
                        self.selected_voice = npc
                        if self.voice_preview_callback:
                            self.voice_preview_callback(npc)
                        self.message = f"Previewing {npc}..."
                        break
        elif event.type == pygame.MOUSEBUTTONUP:
            self._dragging = None
        elif event.type == pygame.MOUSEMOTION and hasattr(self, '_dragging') and self._dragging:
            mx, my = event.pos
            lx = mx - 138
            if self._dragging == 'input':
                self._set_volume_from_mouse(lx, 'input')
            elif self._dragging == 'output':
                self._set_volume_from_mouse(lx, 'output')

    def _set_volume_from_mouse(self, lx, which):
        v = min(1.0, max(0.0, (lx-180)/200))
        if which == 'input':
            self.input_volume = v
        else:
            self.output_volume = v

    def render(self, main_surface):
        """Draw overlay with interactive sliders and buttons"""
        if not self.active:
            return
        # Draw background with shadow
        shadow = pygame.Surface((self.width+16, self.height+16), pygame.SRCALPHA)
        shadow.fill((0,0,0,120))
        main_surface.blit(shadow, (130, 90))
        self.surface.fill((34, 40, 48, 240))
        pygame.draw.rect(self.surface, (255,255,255,220), (0,0,self.width,self.height), 2, border_radius=18)
        y = 24
        title = self.font.render('Settings', True, (120,220,255))
        self.surface.blit(title, (24, y))
        y += 48
        # Input volume slider
        in_vol = self.small_font.render(f'Input Volume: {int(self.input_volume*100)}%', True, (220,220,220))
        self.surface.blit(in_vol, (24, y))
        pygame.draw.rect(self.surface, (80,180,80), (180, y+4, 200, 16), border_radius=8)
        pygame.draw.circle(self.surface, (180,255,180), (180+int(self.input_volume*200), y+12), 12)
        y += 32
        # Output volume slider
        out_vol = self.small_font.render(f'Output Volume: {int(self.output_volume*100)}%', True, (220,220,220))
        self.surface.blit(out_vol, (24, y))
        pygame.draw.rect(self.surface, (80,80,180), (180, y+4, 200, 16), border_radius=8)
        pygame.draw.circle(self.surface, (180,220,255), (180+int(self.output_volume*200), y+12), 12)
        y += 32
        # Input device dropdown
        if self.input_devices:
            dev_lbl = self.small_font.render('Input Device:', True, (220,220,220))
            self.surface.blit(dev_lbl, (24, y))
            y += 28
            for i, (idx, name) in enumerate(self.input_devices):
                is_selected = (idx == self.selected_input_device)
                dev_rect = pygame.Rect(180, y + i*28, 320, 24)
                pygame.draw.rect(self.surface, (60,90,160) if is_selected else (44,44,44), dev_rect, border_radius=8)
                dev_text = self.small_font.render(f"{name} (#{idx})", True, (255,255,255) if is_selected else (200,200,200))
                self.surface.blit(dev_text, (190, y + i*28 + 2))
            y += max(28*len(self.input_devices), 28)
        # Mode
        mode = self.small_font.render(f'Mode: {self.default_mode}', True, (220,220,220))
        self.surface.blit(mode, (24, y))
        y += 32
        # Voice preview
        self.surface.blit(self.small_font.render('NPC Voice Preview:', True, (220,220,220)), (24, y))
        y += 28
        for i, (npc, vinfo) in enumerate(self.npc_voices.items()):
            btn_rect = pygame.Rect(48, y + i*28, 320, 24)
            color = (180,255,180) if self.selected_voice==npc else (200,200,200)
            pygame.draw.rect(self.surface, (60,90,60) if self.selected_voice==npc else (44,44,44), btn_rect, border_radius=8)
            btn = self.small_font.render(f'{npc}: {vinfo["voice"]} ▶️', True, color)
            self.surface.blit(btn, (56, y + i*28 + 2))
        # Message
        if self.message:
            msg_surface = self.small_font.render(self.message, True, (255,180,80))
            self.surface.blit(msg_surface, (24, self.height-40))
        main_surface.blit(self.surface, (138, 98))
