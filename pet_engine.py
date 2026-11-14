from enum import Enum, auto

class PetMood(Enum):
    HAPPY = auto()
    NEUTRAL = auto()
    HUNGRY = auto()
    TIRED = auto()
    CRITICAL = auto()
    DEAD = auto()

class ActionResult(Enum):
    SUCCESS = auto()
    PET_DEAD = auto()
    TOO_FULL = auto()
    TOO_TIRED = auto()
    ALREADY_SLEEPING = auto()

class Pet:
    MAX_STAT = 100.0

    def __init__(self, name: str, hunger_rate: float = 2.0, energy_rate: float = 1.5, happy_rate: float = 1.2):
        self.name = name
        self.hunger = 20.0      # 0 = full, 100 = starving
        self.energy = 80.0      # 0 = exhausted, 100 = rested
        self.happiness = 80.0   # 0 = depressed, 100 = ecstatic
        self.is_sleeping = False
        self.is_alive = True
        self.age_seconds = 0.0

        # Decay rates per second (customizable via subclasses)
        self.hunger_rate = hunger_rate
        self.energy_rate = energy_rate
        self.happy_rate = happy_rate

    def tick(self, dt: float) -> PetMood:
        """Advance simulation state by dt seconds."""
        if not self.is_alive:
            return PetMood.DEAD

        self.age_seconds += dt
        self.hunger = self._clamp(self.hunger + self.hunger_rate * dt)

        if self.is_sleeping:
            self.energy = self._clamp(self.energy + (self.energy_rate * 4.0) * dt)
            self.happiness = self._clamp(self.happiness - (self.happy_rate * 0.3) * dt)
            if self.energy >= self.MAX_STAT:
                self.is_sleeping = False
        else:
            self.energy = self._clamp(self.energy - self.energy_rate * dt)
            self.happiness = self._clamp(self.happiness - self.happy_rate * dt)

        if self.hunger >= self.MAX_STAT or (self.energy <= 0 and self.happiness <= 0):
            self.is_alive = False
            self.is_sleeping = False

        return self.mood

    def feed(self, amount: float = 25.0) -> ActionResult:
        if not self.is_alive:
            return ActionResult.PET_DEAD
        if self.hunger <= 5.0:
            return ActionResult.TOO_FULL

        self.is_sleeping = False
        self.hunger = self._clamp(self.hunger - amount)
        self.happiness = self._clamp(self.happiness + 5.0)
        return ActionResult.SUCCESS

    def play(self, fun_boost: float = 20.0, energy_cost: float = 15.0) -> ActionResult:
        if not self.is_alive:
            return ActionResult.PET_DEAD
        if self.energy < energy_cost:
            return ActionResult.TOO_TIRED

        self.is_sleeping = False
        self.happiness = self._clamp(self.happiness + fun_boost)
        self.energy = self._clamp(self.energy - energy_cost)
        self.hunger = self._clamp(self.hunger + 8.0)
        return ActionResult.SUCCESS

    def toggle_sleep(self) -> ActionResult:
        if not self.is_alive:
            return ActionResult.PET_DEAD
        if self.is_sleeping:
            return ActionResult.ALREADY_SLEEPING

        self.is_sleeping = True
        return ActionResult.SUCCESS

    @property
    def mood(self) -> PetMood:
        if not self.is_alive:
            return PetMood.DEAD
        if self.hunger >= 80 or self.energy <= 15 or self.happiness <= 15:
            return PetMood.CRITICAL
        if self.is_sleeping or self.energy <= 35:
            return PetMood.TIRED
        if self.hunger >= 60:
            return PetMood.HUNGRY
        if self.happiness >= 70:
            return PetMood.HAPPY
        return PetMood.NEUTRAL

    def get_snapshot(self) -> dict:
        """Pure data transfer object for any UI/serializer."""
        return {
            "name": self.name,
            "species": self.__class__.__name__,
            "hunger": round(self.hunger, 1),
            "energy": round(self.energy, 1),
            "happiness": round(self.happiness, 1),
            "is_sleeping": self.is_sleeping,
            "is_alive": self.is_alive,
            "mood": self.mood.name,
            "age": int(self.age_seconds),
        }

    @staticmethod
    def _clamp(val: float) -> float:
        return max(0.0, min(Pet.MAX_STAT, val))


class DragonPet(Pet):
    """Subclass example: gets hungry fast, loses happiness slowly."""
    def __init__(self, name: str):
        super().__init__(name, hunger_rate=3.5, energy_rate=1.2, happy_rate=0.8)


class RabbitPet(Pet):
    """Subclass example: needs frequent play/attention, eats lightly."""
    def __init__(self, name: str):
        super().__init__(name, hunger_rate=1.5, energy_rate=1.8, happy_rate=2.5)