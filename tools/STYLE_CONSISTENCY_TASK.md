# Style Consistency System

Implement a style consistency system for the PixelLab asset generation pipeline. Generated assets within a project, and especially level tilesets, should share a cohesive visual style, color palette, and artistic theme unless explicitly overridden.

Study the existing pipeline in `tools/` and PixelLab API docs at <https://api.pixellab.ai/v2/llms.txt> to understand how reference images, color palettes, and style parameters can enforce visual consistency across multiple generations.

The system should be project-agnostic - usable for any game or platform the pipeline supports.
