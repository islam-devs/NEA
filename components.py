import random
from abc import ABC, abstractmethod

class Component(ABC):
    def __init__(self, name:str, mass:float, lengthSlots:int, radialOffset: float, category: str):

        if not name or not name.strip():
            raise ValueError("Component name cannot be empty")
        if mass <= 0:
            raise ValueError(f"'{name}': mass must be positive (got {mass}g)")
        if not isinstance(lengthSlots, int) or lengthSlots < 1:
            raise ValueError(
                f"'{name}': lengthSlots must be a positive integer (got {lengthSlots})"
            )
        if radialOffset < 0:
            raise ValueError(f"'{name}': radialOffset must be non-negative (got {radialOffset}mm)")

        self.name = name
        self.mass = float(mass)
        self.lengthSlots = int(lengthSlots)
        self.radialOffset = float(radialOffset)
        self.category = category

    @abstractmethod
    def validatePlacement(self, startSlot: int, numTotalSlots: int) -> tuple[bool,str]:
        raise NotImplementedError

    @abstractmethod
    def mutate(self, numTotalSlots: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def validStartSlots(self, numTotalSlots: int) -> list[int]:
        raise NotImplementedError

    # Shared utility
    def midpoint(self, startSlot: int) -> float:
        # Geometric centre of component when placed at the given start slot
        return startSlot + (self.lengthSlots - 1) / 2.0

    def boundsCheck(self, startSlot: int,numTotalSlots: int) -> tuple[bool, str]:

        endSlot = startSlot + self.lengthSlots - 1
        if startSlot < 0:
            return False, (
                f"'{self.name}': startSlot {startSlot} is negative")
        if endSlot >= numTotalSlots:
            return False, (
                f"'{self.name}': occupies slots {startSlot}–{endSlot} "
                f"but rocket only has {numTotalSlots} slots "
                f"(0–{numTotalSlots - 1})")
        return True, ""
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}("
                f"name='{self.name}', "
                f"mass={self.mass}g, "
                f"slots={self.lengthSlots}, "
                f"offset={self.radialOffset}mm)")
 
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Component):
            return NotImplemented
        return (self.name == other.name
                and self.mass == other.mass
                and self.lengthSlots == other.lengthSlots
                and self.radialOffset == other.radialOffset
                and self.category == other.category)





 
class Parachute(Component):

    def __init__(self, name: str, mass: float,lengthSlots: int, radialOffset: float = 0.0):
        super().__init__(name, mass, lengthSlots,radialOffset, category="parachute")


    def forwardLimit(self, numTotalSlots: int) -> int:
        #Last slot the component's END may occupy (inclusive).
        return numTotalSlots // 3

 
    def validatePlacement(self, startSlot: int,numTotalSlots: int) -> tuple[bool, str]:
        inBounds, reason = self.boundsCheck(startSlot, numTotalSlots)

        if not inBounds:
            return False, reason
 
        limit = self.forwardLimit(numTotalSlots)
        end   = startSlot + self.lengthSlots - 1
        if end > limit:
            return False, (
                f"'{self.name}' (parachute): must end by slot {limit} "
                f"(top-third rule), but would occupy slots "
                f"{startSlot}–{end}")
        return True, ""
 
    def mutate(self, numTotalSlots: int) -> int:
        limit     = self.forwardLimit(numTotalSlots)
        maxStart = max(0, limit - self.lengthSlots + 1)
        return random.randint(0, maxStart)
 
    def validStartSlots(self, numTotalSlots: int) -> list[int]:
        limit     = self.forwardLimit(numTotalSlots)
        maxStart = max(0, limit - self.lengthSlots + 1)
        return list(range(0, maxStart + 1))

class Battery(Component):

    def __init__(self, name: str, mass: float,
                lengthSlots: int, radialOffset: float = 0.0):
        super().__init__(name, mass, lengthSlots, radialOffset, category="battery")
 
    def validatePlacement(self, startSlot: int,
                           numTotalSlots: int) -> tuple[bool, str]:
        return self.boundsCheck(startSlot, numTotalSlots)
 
    def mutate(self, numTotalSlots: int) -> int:
        maxStart = max(0, numTotalSlots - self.lengthSlots)
        return random.randint(0, maxStart)
 
    def validStartSlots(self, numTotalSlots: int) -> list[int]:
        maxStart = max(0, numTotalSlots - self.lengthSlots)
        return list(range(0, maxStart + 1))

class PayloadMass(Component):
    def __init__(self, name: str, mass: float, lengthSlots: int, radialOffset: float = 0.0):
        super().__init__(name, mass, lengthSlots,
                            radialOffset, category="payload")

    def validatePlacement(self, startSlot: int,
                           numTotalSlots: int) -> tuple[bool, str]:
        return self.boundsCheck(startSlot, numTotalSlots)
 
    def mutate(self, numTotalSlots: int) -> int:
        maxStart = max(0, numTotalSlots - self.lengthSlots)
        return random.randint(0, maxStart)
 
    def validStartSlots(self, numTotalSlots: int) -> list[int]:
        maxStart = max(0, numTotalSlots - self.lengthSlots)
        return list(range(0, maxStart + 1))




class FinWeight(Component):

    def __init__(self, name: str, mass: float,
                lengthSlots: int, radialOffset: float = 0.0):
        super().__init__(name, mass, lengthSlots,
                            radialOffset, category="finWeight")
 
    def aftLimit(self, numTotalSlots: int) -> int:
        #First slot the component may START at (inclusive).#
        return (numTotalSlots * 3) // 4
 
    def validatePlacement(self, startSlot: int,
                           numTotalSlots: int) -> tuple[bool, str]:
        inBounds, reason = self.boundsCheck(startSlot,
                                               numTotalSlots)
        if not inBounds:
            return False, reason
 
        limit = self.aftLimit(numTotalSlots)
        if startSlot < limit:
            return False, (
                f"'{self.name}' (finWeight): must start at or after "
                f"slot {limit} (bottom-quarter rule), got {startSlot}")
        return True, ""
 
    def mutate(self, numTotalSlots: int) -> int:
        limit     = self.aftLimit(numTotalSlots)
        maxStart = max(limit, numTotalSlots - self.lengthSlots)
        return random.randint(limit, maxStart)
 
    def validStartSlots(self, numTotalSlots: int) -> list[int]:
        limit     = self.aftLimit(numTotalSlots)
        maxStart = max(limit, numTotalSlots - self.lengthSlots)
        if maxStart < limit:
            return []
        return list(range(limit, maxStart + 1))
 
