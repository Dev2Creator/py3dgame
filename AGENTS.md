# AGENTS.md - py3dgame

This is the authoritative project specification supplied by the project owner.
Where it conflicts with the current implementation, the specification wins and
the gap must be reported, not hidden.

AGENTS.md — py3dgame
1. Project Identity
Project: py3dgame﻿Distribution: py3dgame﻿Import package: py3dgame﻿Installation: pip install py3dgame﻿Project type: Python game development library and engine.﻿Vision: Build a comprehensive Python-native 2D and 3D game development library with capabilities inspired by Pygame, Godot, and Unity.﻿The library must allow developers to create complete games using Python.﻿This is an independent engine. Do not turn it into a wrapper around Unity, Godot, or Pygame.
2. Most Important Architectural Principle
py3dgame is fundamentally a Python LIBRARY.﻿It is not primarily a standalone game editor, GUI application, or game launcher.﻿The following must work:﻿pip install py3dgame﻿import py3dgame﻿A developer must be able to create, configure, run, and distribute games using Python code.﻿The runtime must work independently of the optional visual editor.﻿The public Python API is the most important product interface.
3. Primary Objectives
Build a library supporting:
2D game development.
3D game development.
Cartoon and stylized 3D rendering.
Real-time GPU rendering.
Scene management.
Entity-component architecture.
Physics and collisions.
Character controllers.
Skeletal animation.
Audio playback.
Input management.
Materials and shaders.
Lighting and shadows.
Particle systems.
Asset importing.
Game UI.
Debugging and profiling.
Game packaging.
Prioritize a powerful, easy-to-use Python API.
4. Python-First Development
Python is the primary language for:
Game development.
Gameplay logic.
Scene creation.
Entity management.
Component creation.
Animation control.
Input handling.
Asset management.
Engine configuration.
Development tools.
Native libraries and GPU backends are permitted for performance-critical operations.﻿Do not implement expensive rendering operations through unnecessary Python loops.﻿Do not sacrifice performance by forcing all internal operations to be pure Python.﻿However, developers must not need C++, C#, or GDScript to use the engine.
5. Public API Requirements
Design a clean, consistent, documented Python API.﻿Example target:﻿import py3dgame as p3d game = p3d.Game( title="My First Game", width=1280, height=720 ) scene = p3d.Scene("Main") cube = p3d.Mesh.cube() scene.add(cube) game.load_scene(scene) game.run()﻿This is an API design target, not permission to expose unimplemented methods.﻿Every public method must have a real implementation and appropriate tests.﻿Use:
Python type hints.
Meaningful exceptions.
Consistent naming.
Sensible defaults.
Clear documentation.
Predictable object lifecycles.
Avoid unnecessary API complexity.
6. Engine Architecture
Keep the library modular.﻿Expected subsystems:
core
platform
graphics
rendering
renderer2d
renderer3d
scene
entities
components
physics
animation
audio
input
assets
materials
shaders
lighting
particles
ui
scripting
debugging
profiling
math
utilities
exporters
The editor must remain optional.﻿Do not introduce circular dependencies.﻿Keep backend implementations behind stable interfaces.
7. Rendering Requirements
2D
Sprites.
Sprite sheets.
Texture atlases.
Tilemaps.
2D cameras.
Sprite animations.
Parallax.
2D lighting.
Particles.
Collision visualization.
3D
Mesh rendering.
Textures.
Materials.
Perspective cameras.
Orthographic cameras.
Lighting.
Shadows.
Skyboxes.
Environment maps.
Transparency.
Instancing.
Frustum culling.
Post-processing.
GPU acceleration.
Cartoon rendering
This is a major project priority.﻿Implement real functionality for:
Toon shading.
Cel shading.
Outlines.
Stylized shadows.
Low-poly graphics.
Flat shading.
Vibrant materials.
Stylized fog.
Cartoon water.
Stylized particles.
Do not present shader presets as implemented when they are merely labels.
8. Physics
Provide a consistent Python-facing physics API.﻿Support:
Rigid bodies.
Static and dynamic bodies.
Collision detection.
Collision response.
Box colliders.
Sphere colliders.
Capsule colliders.
Mesh colliders.
Raycasting.
Gravity.
Friction.
Triggers.
Character controllers.
Collision layers.
Use a stable fixed timestep.﻿Evaluate suitable maintained physics backends before implementation.
9. Animation
Support:
Skeletal animation.
Bone hierarchies.
Keyframes.
Animation clips.
Animation blending.
State machines.
Animation events.
GLTF/GLB animation importing.
Keep animation APIs straightforward.
10. Assets
Support appropriate formats:
GLTF.
GLB.
OBJ.
PNG.
JPEG.
WebP.
WAV.
OGG.
MP3 where supported.
Fonts.
Sprite sheets.
Create an asset management system with caching, loading, unloading, validation, and dependency tracking.
11. Audio and Input
Audio:
Background music.
Sound effects.
2D audio.
3D spatial audio.
Volume.
Pitch.
Looping.
Audio mixing.
Input:
Keyboard.
Mouse.
Gamepad.
Input actions.
Configurable bindings.
Input callbacks.
12. Editor Policy
A visual editor is desirable, but it is not the foundation of the library.﻿Build it only after the underlying runtime systems work.﻿Editor dependencies must be optional.﻿A developer who only installs the runtime must not need PySide6.﻿The editor must use the public engine architecture rather than bypassing it.
13. Packaging Is Mandatory
The package must support:﻿pip install py3dgame﻿Use modern packaging standards and pyproject.toml.﻿Ensure:
Correct package discovery.
Runtime dependencies.
Optional dependency groups.
Version metadata.
License metadata.
README metadata.
Wheel generation.
Source distribution generation.
Test the installed wheel in a clean virtual environment.﻿Do not assume the source repository being importable means the installed distribution works.﻿The package must be tested outside its source directory.﻿Do not publish to PyPI without explicit authorization.
14. Optional Dependencies
Separate essential and optional dependencies.﻿For example:﻿pip install py3dgame﻿For additional features, provide documented extras such as:﻿pip install "py3dgame[editor]" pip install "py3dgame[physics]" pip install "py3dgame[all]"﻿Only expose extras that actually exist and have been tested.﻿Avoid installing heavy editor dependencies for ordinary game runtime users.
15. Testing Policy
Use automated tests.﻿Test:
Public imports.
Core lifecycle.
Scene management.
Entities and components.
Rendering.
Physics.
Asset importing.
Audio.
Packaging.
Installation.
Example projects.
Every completed feature requires tests.﻿Every fixed bug should receive a regression test where practical.﻿Do not hide errors using broad exception handling.
16. Performance Policy
Prioritize:
GPU rendering.
Draw-call batching.
Instancing.
Efficient memory usage.
Asset caching.
Spatial partitioning.
Resource unloading.
Object pooling.
Fixed timestep physics.
Benchmark before making performance claims.﻿Target practical consumer hardware, including integrated graphics where possible.
17. Code Quality
Mandatory standards:
Readable Python.
Type hints.
Modular architecture.
Consistent formatting.
Meaningful variable names.
Proper exception handling.
Documentation.
Automated tests.
No unnecessary duplication.
No hardcoded machine-specific paths.
No fake implementations.
No dead public APIs.
Never generate hundreds of empty classes to make the project look complete.﻿Never claim a feature is finished until it works.
18. Development Workflow
Work incrementally.﻿Priority order:
Package foundation.
Application lifecycle.
Window and input.
2D renderer.
3D renderer.
Materials and lighting.
Cartoon rendering.
Scene and entity systems.
Physics.
Animation.
Audio.
UI.
Particles.
Editor.
Optimization.
Documentation.
Release preparation.
Each milestone must have working code and tests.﻿Do not skip foundational milestones.
19. Required Examples
Maintain runnable examples:
Hello World.
Basic 2D game.
2D platformer.
Basic 3D scene.
Cartoon 3D world.
Character controller.
Physics playground.
Animated character.
Particle effects.
Complete small game.
Examples must use the public py3dgame API.
20. Agent Behaviour
Before modifying code:
Inspect the repository.
Read this AGENTS.md.
Understand the existing architecture.
Identify completed and incomplete functionality.
Preserve working functionality.
Plan the implementation.
Make focused changes.
Run relevant tests.
Verify packaging where appropriate.
Update documentation.
Do not rewrite the entire project unnecessarily.﻿Do not introduce dependencies without explaining their purpose.﻿Do not change public APIs casually.﻿Do not create duplicate implementations of existing systems.﻿Do not report tests as passed unless they were actually executed.﻿If a feature is blocked by a backend limitation, explain the limitation and propose a technically sound alternative.
21. Definition of Done
A feature is complete only when:
Its implementation exists.
Its public API works.
It has appropriate tests.
Errors are handled correctly.
Documentation exists.
It works with the installed package where applicable.
No existing functionality has been unnecessarily broken.
22. First Assignment
Start by inspecting the existing repository.﻿Then:
Produce a concise architecture assessment.
Select compatible rendering, windowing, physics, and audio backends.
Establish the package structure.
Configure pyproject.toml.
Implement the initial runtime.
Implement a working window and game loop.
Add basic input handling.
Add automated tests.
Build the wheel.
Test installation in a clean virtual environment.
Provide a working example.
Do not stop at planning.﻿Actually implement the first milestone.
PROJECT NORTH STAR
py3dgame — Create games. Write Python.﻿A professional Python-native game development library for creating 2D games, 3D worlds, animated characters, and cartoon-style interactive experiences.﻿The library comes first. The editor comes second.﻿Real functionality comes before feature counts.﻿Performance comes before marketing claims.﻿Architecture comes before unnecessary complexity.
