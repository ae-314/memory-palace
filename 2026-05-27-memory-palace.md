---
layout: post
title: "Memory Palace (Periodic Table Edition)"
date: 2026-05-27
team: "Aaron Elk"
tools: "Claude Code, Python, pygame-ce"
github_repo: "https://github.com/ae-314/memory-palace"
demo_link: ""
summary: "Memorize the Periodic Table of Elements by building your own Memory Palace. Choose containers and rooms to store the elements you discover, and then try to recall the elements later via flashcard multiple choice quiz, or just go through the card deck."
categories: project
---

## Project Overview

Memory Palace (Periodic Table Edition) is a retro 8-bit Pygame game that helps you memorize all 118 chemical elements using the ancient **Method of Loci** — the memory palace technique. You build imaginary rooms, fill them with memorable containers, and associate each element with a vivid image in a place you've invented.

## Problem

The periodic table has 118 elements, each with a name, symbol, atomic number, group, period, mass, category, properties, and uses. Rote memorization doesn't stick. Memory techniques do — but there was no fun, visual tool that combined the memory palace method with the periodic table.

## What We Built

A chunky-pixel Pygame desktop app where you:

- **Discover** elements one by one on illustrated element cards
- **Place** each element into a container (chosen from 1,078 Kenney 1-Bit Pack pixel-art sprites) inside a named room of your palace
- **Decorate** your rooms — each room gets a unique color palette and four corner furniture sprites (chests, shelves, barrels, cabinets…) so every room feels distinct
- **Browse** your palace via the MY ROOMS screen — a two-panel view with a scrollable room list on the left and a full decorated room on the right, showing every container at large scale with its element labels
- **Test yourself** with multiple-choice quiz rounds (triggered every 5 elements) or browse the full flashcard deck at any time

## How We Used Claude Code

The entire project was built in a multi-session pair-programming workflow with Claude Code:

- Designed and iterated on the game architecture (state machine, screen protocol, palace data model)
- Integrated the Kenney 1-Bit Pack CC0 sprite sheet (49 × 22 tiles = 1,078 sprites), including a full in-game tile picker
- Designed the Stardew Valley–inspired top-down room renderer with wainscoting, tinted floors, and ambient decorations
- Built the two-panel RoomsScreen with deterministic per-room decoration sets
- Wired up save/load (JSON), quiz scheduling, and element data for all 118 elements

## Screenshots

**Home screen** — animated starfield title with twinkling menu:

![Home screen]({{ "/assets/images/memory-palace/memory_palace_home_screen.png" | relative_url }})

**Palace + element card** — split view showing your palace rooms on the left and the current element card on the right:

![Palace and element card]({{ "/assets/images/memory-palace/memory_palace_card_and_rooms.png" | relative_url }})

**MY ROOMS** — two-panel room browser: scrollable room list with mini sprite previews on the left, full decorated room with corner furniture sprites and labelled containers on the right:

![MY ROOMS view]({{ "/assets/images/memory-palace/memory_palace_my_rooms.png" | relative_url }})

**Flashcard mode** — full-screen element cards with category colour, properties, uses, and a fun fact:

![Flashcard mode]({{ "/assets/images/memory-palace/memory_palace_flash_cards.png" | relative_url }})

## GitHub Repository

[View the project repository](https://github.com/ae-314/memory-palace)

## Demo

Screen recording coming soon (YouTube link TBD).

## What We Learned

- How to structure a multi-file Pygame project cleanly (strict file responsibilities: no game logic in ui.py, no pygame calls in palace.py)
- How to use Claude Code to iterate rapidly on visual design — describing what looked wrong and getting targeted fixes
- How to integrate CC0 open-source game assets (Kenney 1-Bit Pack) and build a custom sprite picker on top of them
- How breaking a big feature ("make rooms look like Stardew Valley") into small concrete sub-tasks ("simpler floor", "corner decos", "two-panel view") makes progress visible and reversible

## Future Improvements

- Screen recording / YouTube demo
- Sound effects and background music (Pygame mixer)
- Animated room transitions
- More quiz modes (fill-in-the-blank, element symbol recognition)
- Mobile / web port
- Victory screen when all 118 elements are learned
