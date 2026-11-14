import asyncio
import json
import sys
import pygame
from pet_engine import DragonPet, RabbitPet, PetMood, ActionResult

# Detect if running in browser via pygbag/emscripten
IS_WEB = sys.platform == "emscripten"
if IS_WEB:
    import platform
    window = getattr(platform, "window", None)
else:
    window = None

WIDTH, HEIGHT = 480, 420
COLORS = {
    "BG": (28, 32, 40),
    "CARD": (42, 48, 60),
    "TEXT": (235, 240, 245),
    "BAR_BG": (20, 24, 30),
    "HUNGER": (230, 126, 34),
    "ENERGY": (52, 152, 219),
    "HAPPY": (46, 204, 113),
    "BTN": (70, 82, 102),
    PetMood.HAPPY: (46, 204, 113),
    PetMood.NEUTRAL: (149, 165, 166),
    PetMood.HUNGRY: (243, 156, 18),
    PetMood.TIRED: (155, 89, 182),
    PetMood.CRITICAL: (231, 76, 60),
    PetMood.DEAD: (90, 90, 90),
}

class TamagotchiUI:
    def __init__(self):
        pygame.display.init()
        pygame.font.init()
        self.scale = self._calc_scale()
        self.screen = pygame.display.set_mode((self._s(WIDTH), self._s(HEIGHT)))
        pygame.display.set_caption("OOP Tamagotchi")
        if window and hasattr(window, "canvas"):
            window.canvas.style.imageRendering = "auto"

        self.font = pygame.font.Font(None, self._s(22))
        self.big_font = pygame.font.Font(None, self._s(32))
        self._mem_save = None

        self.pet = RabbitPet("Mochi")
        self.status_msg = "Take care of your pet!"
        self.load_save_data()

        self.buttons = {
            "feed": pygame.Rect(40, 330, 110, 45),
            "play": pygame.Rect(185, 330, 110, 45),
            "sleep": pygame.Rect(330, 330, 110, 45),
        }

    def _calc_scale(self) -> float:
        if not window:
            return 1.0
        dpr = float(getattr(window, "devicePixelRatio", 1.0) or 1.0)
        cw = float(getattr(window, "innerWidth", WIDTH) or WIDTH)
        ch = float(getattr(window, "innerHeight", HEIGHT) or HEIGHT)
        return max(1.0, min(cw / WIDTH, ch / HEIGHT)) * dpr

    def _s(self, val: float) -> int:
        return round(val * self.scale)

    def _r(self, x: float, y: float, w: float, h: float) -> pygame.Rect:
        return pygame.Rect(self._s(x), self._s(y), self._s(w), self._s(h))

    def load_save_data(self):
        """Load state from browser localStorage or memory fallback."""
        raw = self._mem_save
        if window:
            try:
                raw = window.localStorage.getItem("tamagotchi_save") or raw
            except Exception:
                pass  # Sandboxed iframe (e.g., VS Code Simple Browser) blocks localStorage

        if raw:
            data = json.loads(raw)
            self.pet = DragonPet(data["name"]) if data["species"] == "DragonPet" else RabbitPet(data["name"])
            self.pet.hunger = data["hunger"]
            self.pet.energy = data["energy"]
            self.pet.happiness = data["happiness"]
            self.pet.is_sleeping = data["is_sleeping"]
            self.pet.is_alive = data["is_alive"]
            self.status_msg = "Loaded save!"

    def save_game_data(self):
        """Save state to browser localStorage with silent in-memory fallback."""
        try:
            payload = json.dumps(self.pet.get_snapshot())
            self._mem_save = payload
            if window:
                window.localStorage.setItem("tamagotchi_save", payload)
        except Exception:
            pass

    async def run(self):
        clock = pygame.time.Clock()
        running = True
        save_timer = 0.0

        while running:
            # No framerate arg: avoids blocking SDL_Delay() in browser Wasm
            dt = min(clock.tick() / 1000.0, 0.1)
            save_timer += dt

            if save_timer >= 10.0:
                self.save_game_data()
                save_timer = 0.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.pet = DragonPet("Ignis") if isinstance(self.pet, RabbitPet) else RabbitPet("Mochi")
                    self.status_msg = f"Adopted {self.pet.name}!"
                    self.save_game_data()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    touch_id = getattr(pygame, "TOUCH_MOUSEID", None)
                    if touch_id is None or getattr(event, "which", None) != touch_id:
                        self._handle_click((event.pos[0] / self.scale, event.pos[1] / self.scale))
                elif event.type == pygame.FINGERDOWN:
                    pos = (event.x * WIDTH, event.y * HEIGHT)
                    self._handle_click(pos)
                
            self.pet.tick(dt)
            self._draw()
            
            # CRITICAL FOR WASM: Yield control back to browser event loop
            await asyncio.sleep(0)

        pygame.quit()

    def _handle_click(self, pos: tuple[float, float]):
        res = None
        if self.buttons["feed"].collidepoint(pos):
            res = self.pet.feed()
        elif self.buttons["play"].collidepoint(pos):
            res = self.pet.play()
        elif self.buttons["sleep"].collidepoint(pos):
            res = self.pet.toggle_sleep()

        if res:
            self.status_msg = f"Action: {res.name}"

    def _draw_bar(self, label: str, value: float, y: int, color: tuple[int, int, int]):
        self.screen.blit(self.font.render(f"{label}: {int(value)}%", True, COLORS["TEXT"]), (self._s(40), self._s(y)))
        bg_rect = self._r(180, y, 260, 20)
        fill_rect = self._r(180, y, 260 * (value / 100.0), 20)
        r = max(1, self._s(4))
        pygame.draw.rect(self.screen, COLORS["BAR_BG"], bg_rect, border_radius=r)
        pygame.draw.rect(self.screen, color, fill_rect, border_radius=r)

    def _draw(self):
        state = self.pet.get_snapshot()
        self.screen.fill(COLORS["BG"])

        avatar_color = COLORS[self.pet.mood]
        pygame.draw.circle(self.screen, avatar_color, (self._s(WIDTH // 2), self._s(95)), self._s(45))
        if state["is_sleeping"]:
            self.screen.blit(self.font.render("Zzz...", True, COLORS["TEXT"]), (self._s(WIDTH // 2 + 50), self._s(60)))

        title = f"{state['name']} ({state['species']}) - {state['mood']}"
        self.screen.blit(self.big_font.render(title, True, COLORS["TEXT"]), (self._s(40), self._s(15)))

        self._draw_bar("Fullness", 100 - state["hunger"], 165, COLORS["HUNGER"])
        self._draw_bar("Energy", state["energy"], 205, COLORS["ENERGY"])
        self._draw_bar("Happy", state["happiness"], 245, COLORS["HAPPY"])

        self.screen.blit(self.font.render(f"{self.status_msg} | [R] Switch", True, COLORS["TEXT"]), (self._s(40), self._s(290)))
        btn_r = max(1, self._s(6))
        for label, rect in self.buttons.items():
            s_rect = self._r(rect.x, rect.y, rect.w, rect.h)
            pygame.draw.rect(self.screen, COLORS["BTN"], s_rect, border_radius=btn_r)
            txt = self.font.render(label.upper(), True, COLORS["TEXT"])
            self.screen.blit(txt, txt.get_rect(center=s_rect.center))

        pygame.display.flip()

if __name__ == "__main__":
    asyncio.run(TamagotchiUI().run())