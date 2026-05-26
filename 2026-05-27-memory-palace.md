---
layout: post
title: "Memory Palace (Periodic Table Edition)"
date: 2026-05-27
team: "Aaron Elk"
tools: "Claude Code, Python, pygame-ce"
github_repo: "https://github.com/ae-314/memory-palace"
demo_link: ""
summary: "Memorize the Periodic Table of Elements by building your own Memory Palace. Place elements into containers inside vivid 3D wireframe rooms, then recall them with flashcard and quiz modes."
categories: project
---

## Project Overview

Memory Palace (Periodic Table Edition) is a retro Pygame game that helps you memorize all 118 chemical elements using the ancient **Method of Loci** — the memory palace technique. You build imaginary rooms, fill them with memorable containers, and associate each element with a vivid image in a place you've invented.

## Problem

The periodic table has 118 elements, each with a name, symbol, atomic number, group, period, mass, category, properties, and uses. Rote memorization doesn't stick. Memory techniques do — but there was no fun, visual tool that combined the memory palace method with the periodic table in a game format.

## What We Built

A chunky-pixel Pygame desktop app (640×360 internal resolution, scaled 2×) where you:

- **Discover** elements one by one on full-screen illustrated element cards with animated orbital decorations
- **Place** each element into a container (chosen from 1,078 Kenney 1-Bit Pack pixel-art sprites) inside one of six prebuilt 3D rooms — press 1–6 to instantly select Kitchen, Bedroom, Garage, Living Room, Library, or Bathroom
- **Browse** your palace in the MY ROOMS screen — a two-panel view with a scrollable room list on the left and a live 3D wireframe room on the right, showing every stored container
- **Test yourself** with multiple-choice quiz rounds triggered every 5 elements, or browse the full flashcard deck at any time from the home menu

## 3D Wireframe Rooms

Six prebuilt rooms rendered with a custom perspective camera (30° elevation, 60° FOV) and a Manim/Arcade-inspired aesthetic:

| Room | Colour | Furnishings |
|------|--------|-------------|
| Kitchen | Amber | Fridge, stove with burners, L-counter, hanging lamp, window |
| Bedroom | Violet | Bed with pillows, dresser + mirror, neon star poster, ceiling fan |
| Garage | Electric green | Detailed car with wheels & spokes, workbench, tools on pegboard |
| Living Room | Hot magenta | L-shaped sofa, flat-screen TV, coffee table, wall art |
| Library | Electric blue | Writing desk, tall bookcase with books, armchair, chandelier |
| Bathroom | Cyan | Bathtub with taps, pedestal sink, toilet, mirror, towel rack |

Each room uses solid tinted face fills for walls and floor (painter's algorithm, one SRCALPHA blit per pass) with bright neon wireframe edges on top. Active slots pulse with a glow animation.

## How We Used Claude Code

The entire project was built in a multi-session pair-programming workflow with Claude Code:

- Designed and iterated on the game architecture (state machine, screen protocol, palace data model with JSON save/load)
- Integrated the Kenney 1-Bit Pack CC0 sprite sheet (49 × 22 = 1,078 tiles) with a full in-game tile picker
- Built a custom 3D perspective renderer from scratch — correct view-matrix construction (cross-product basis), perspective divide, and a three-layer glow compositing system
- Implemented painter's algorithm solid face fills for an Arcade-inspired "clean 3D" aesthetic
- Wired up six richly detailed room classes with 3D geometry (boxes, circles, polylines), slot-based element placement, and pulse animations

## Screenshots

**Home screen** — animated starfield title with twinkling menu:

![Home screen](https://raw.githubusercontent.com/ae-314/memory-palace/main/assets/screenshots/memory_palace_home_screen.png)

**Element card** — full-screen element card with category colour, animated orbital decoration, and 1/2/3… room shortcuts:

![Element card](https://raw.githubusercontent.com/ae-314/memory-palace/main/assets/screenshots/memory_palace_card_and_rooms.png)

**MY ROOMS — Kitchen** — 3D wireframe kitchen with neon glow lines and solid face fills:

![Kitchen wireframe](https://raw.githubusercontent.com/ae-314/memory-palace/main/assets/screenshots/memory_palace_kitchen.png)

**MY ROOMS — Bedroom** — violet wireframe bedroom with hot-pink bed, teal dresser, and neon-green star poster:

![Bedroom wireframe](https://raw.githubusercontent.com/ae-314/memory-palace/main/assets/screenshots/memory_palace_bedroom.png)

**Flashcard mode** — full-screen element cards with properties, uses, and fun facts:

![Flashcard mode](https://raw.githubusercontent.com/ae-314/memory-palace/main/assets/screenshots/memory_palace_flash_cards.png)

## GitHub Repository

[View the project repository](https://github.com/ae-314/memory-palace)

## Demo

Screen recording coming soon (YouTube link TBD).

## What We Learned

- How to structure a multi-file Pygame project cleanly (strict file responsibilities: no game logic in ui.py, no pygame calls in palace.py)
- How to build a correct 3D perspective camera from scratch — view matrix, basis vectors, perspective divide — and debug subtle orientation bugs (cross-product order)
- How to use painter's algorithm with SRCALPHA surface batching for semi-transparent face fills without per-frame allocation overhead
- How to use Claude Code to iterate rapidly on visual design: describe what looks wrong, get targeted geometry or camera fixes back immediately
- How breaking a big feature ("make rooms look 3D") into small concrete sub-tasks makes progress visible and reversible

## Future Improvements

- Screen recording / YouTube demo
- Sound effects and background music (Pygame mixer)
- Custom room builder (add your own rooms beyond the six prebuilt ones)
- Quiz result tracking and progress charts
- More quiz modes (fill-in-the-blank, symbol recognition)
- Victory screen when all 118 elements are learned
