"""
Memory palace data model.
Rooms contain containers; containers hold one or more elements.
Save/load lives here — JSON written to saves/player.json.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List


SAVE_PATH = os.path.join("saves", "player.json")


@dataclass
class Container:
    description: str            # user's free-text label ("a shiny diamond")
    shape: str                  # name from SHAPES constant
    elements: List[str] = field(default_factory=list)  # element names stored here


@dataclass
class Room:
    name: str
    containers: List[Container] = field(default_factory=list)
    room_type: str = ""          # "kitchen" | "bedroom" | "garage" | "" for custom

    def add_container(self, container: Container):
        self.containers.append(container)

    def find_container(self, description: str):
        desc = description.lower()
        return next((c for c in self.containers if desc in c.description.lower()), None)


@dataclass
class Palace:
    rooms: List[Room] = field(default_factory=list)
    learned: List[str] = field(default_factory=list)   # element names completed

    # ------------------------------------------------------------------
    # Room helpers
    # ------------------------------------------------------------------

    def get_or_create_room(self, name: str) -> Room:
        name = name.strip().lower()
        room = next((r for r in self.rooms if r.name.lower() == name), None)
        if not room:
            room = Room(name=name)
            self.rooms.append(room)
        return room

    def store_element(self, element_name: str, container: Container, room_name: str):
        """Place an element into a container inside a named room."""
        room = self.get_or_create_room(room_name)
        existing = room.find_container(container.description)
        if existing:
            if element_name not in existing.elements:
                existing.elements.append(element_name)
        else:
            container.elements.append(element_name)
            room.add_container(container)
        if element_name not in self.learned:
            self.learned.append(element_name)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self):
        os.makedirs("saves", exist_ok=True)
        with open(SAVE_PATH, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def ensure_prebuilt_rooms(self):
        """Add the three prebuilt rooms if they don't already exist."""
        from wireframe import PREBUILT_NAMES
        existing = {r.room_type for r in self.rooms}
        for rt in PREBUILT_NAMES:
            if rt not in existing:
                self.rooms.append(Room(name=rt.capitalize(), room_type=rt))

    @classmethod
    def load(cls) -> "Palace":
        if not os.path.exists(SAVE_PATH):
            return cls()
        with open(SAVE_PATH) as f:
            data = json.load(f)
        palace = cls(learned=data.get("learned", []))
        for r in data.get("rooms", []):
            room = Room(name=r["name"], room_type=r.get("room_type", ""))
            for c in r.get("containers", []):
                room.containers.append(Container(**c))
            palace.rooms.append(room)
        return palace
