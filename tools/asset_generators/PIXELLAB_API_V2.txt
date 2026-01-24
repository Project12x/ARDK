# Pixel Lab API - v2 API Documentation
Version: dev
Generated: 2025-12-11

## Overview


## Base URL
https://api.pixellab.ai/v2

## Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer YOUR_API_TOKEN
```

Get your API token at: https://pixellab.ai/account

## Response Format
All responses follow this structure:
```json
{
  "success": true,
  "data": {},
  "error": null,
  "usage": {
    "credits_used": 0,
    "generations_used": 0,
    "remaining_credits": 100,
    "remaining_generations": 50
  }
}
```

## Available Endpoints

# Account

## GET /balance
**Get balance**
Tags: Account

Returns the current balance for your account.

### Responses
- **200**: Successfully retrieved balance
- **401**: Invalid API token

# Animate

## POST /animate-with-skeleton
**Animate with skeleton**
Tags: Animate

Creates a pixel art animation based on the provided parameters. Called "Animate with skeleton" in the plugin.

### Parameters

### Request Body
- `image_size`: object (required)
- `image_size.width`: integer (min=16.0, max=256.0) (required)
  Image width in pixels
- `image_size.height`: integer (min=16.0, max=256.0) (required)
  Image height in pixels
- `guidance_scale`: number (min=1.0, max=20.0, default=4.0) (optional)
  How closely to follow the reference image and skeleton keypoints
- `view`: enum[side, low top-down, high top-down] (optional)
- `direction`: enum[north, north-east, east, ...] (optional)
- `isometric`: boolean (default=False) (optional)
  Generate in isometric view
- `oblique_projection`: boolean (default=False) (optional)
  Generate in oblique projection
- `init_images`: array | null (optional)
  Initial images to start the generation from
- `init_image_strength`: integer (min=1.0, max=999.0, default=300) (optional)
  Strength of the initial image influence
- `skeleton_keypoints`: array[array] (optional)
  Skeleton points
- `reference_image`: object (required)
  A base64 encoded image.

Attributes:
    type (Literal["base64"]): Always "base64" to indicate the image encoding type
    base64 (str): The base64 encoded image data
    format (str): The image format (e.g., "png", "jpeg")
- `reference_image.type`: string (default=base64) (optional)
  Image data type
- `reference_image.base64`: string (required)
  Base64 encoded image data
- `reference_image.format`: string (default=png) (optional)
  Image format
- `inpainting_images`: array[any] (optional)
  Images used for showing the model with connected skeleton
- `mask_images`: array[any] (optional)
  Inpainting / mask image (black and white image, where the white is where the model should inpaint)
- `color_image`: object | null (optional)
  Forced color palette, image containing colors used for palette
- `seed`: integer | null (optional)
  Seed decides the starting noise

### Responses
- **200**: Successfully generated image
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests
- **529**: Rate limit exceeded

## POST /animate-with-text
**Animate with text**
Tags: Animate

Creates a pixel art animation based on text description and parameters.

### Parameters

### Request Body
- `image_size`: object (required)
- `image_size.width`: integer (min=64.0, max=64.0) (required)
  Image width in pixels
- `image_size.height`: integer (min=64.0, max=64.0) (required)
  Image height in pixels
- `description`: string (required)
  Character description
- `negative_description`: string | null (optional)
  Negative prompt to guide what not to generate
- `action`: string (required)
  Action description
- `text_guidance_scale`: number | null (optional)
  How closely to follow the text prompts
- `image_guidance_scale`: number | null (optional)
  How closely to follow the reference image
- `n_frames`: integer | null (optional)
  Length of full animation (the model will always generate 4 frames)
- `start_frame_index`: integer | null (optional)
  Starting frame index of the full animation
- `view`: enum[side, low top-down, high top-down] (optional)
- `direction`: enum[north, north-east, east, ...] (optional)
- `init_images`: array | null (optional)
  Initial images to start the generation from
- `init_image_strength`: integer (min=1.0, max=999.0, default=300) (optional)
  Strength of the initial image influence
- `reference_image`: object (required)
  A base64 encoded image.

Attributes:
    type (Literal["base64"]): Always "base64" to indicate the image encoding type
    base64 (str): The base64 encoded image data
    format (str): The image format (e.g., "png", "jpeg")
- `reference_image.type`: string (default=base64) (optional)
  Image data type
- `reference_image.base64`: string (required)
  Base64 encoded image data
- `reference_image.format`: string (default=png) (optional)
  Image format
- `inpainting_images`: array[any] (optional)
  Existing animation frames to guide the generation
- `mask_images`: array | null (optional)
  Inpainting / mask image (black and white image, where the white is where the model should inpaint)
- `color_image`: object | null (optional)
  Forced color palette, image containing colors used for palette
- `seed`: integer | null (optional)
  Seed for reproducible results (0 for random)

### Responses
- **200**: Successfully generated animation
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests
- **529**: Rate limit exceeded

## POST /animate-with-text-v2
**Animate with text (v2)**
Tags: Animate

Generate pixel art animation from text.

### Parameters

### Request Body
- `reference_image`: object (required)
  A base64 encoded image.

Attributes:
    type (Literal["base64"]): Always "base64" to indicate the image encoding type
    base64 (str): The base64 encoded image data
    format (str): The image format (e.g., "png", "jpeg")
- `reference_image.type`: string (default=base64) (optional)
  Image data type
- `reference_image.base64`: string (required)
  Base64 encoded image data
- `reference_image.format`: string (default=png) (optional)
  Image format
- `reference_image_size`: object (required)
- `reference_image_size.width`: integer (min=32.0, max=128.0) (required)
  Reference image width in pixels (32x32, 64x64, or 128x128)
- `reference_image_size.height`: integer (min=32.0, max=128.0) (required)
  Reference image height in pixels (32x32, 64x64, or 128x128)
- `action`: string (minLen=1, maxLen=500) (required)
  Action description (e.g., 'walk', 'jump', 'attack')
- `image_size`: object (required)
- `image_size.width`: integer (min=32.0, max=128.0) (required)
  Image width in pixels (32x32, 64x64, or 128x128)
- `image_size.height`: integer (min=32.0, max=128.0) (required)
  Image height in pixels (32x32, 64x64, or 128x128)
- `seed`: integer | null (optional)
  Seed for reproducible generation (0 for random)
- `no_background`: boolean | null (optional)
  Remove background from generated frames

### Responses
- **200**: Successfully generated animation
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests

## POST /estimate-skeleton
**Estimate skeleton**
Tags: Animate

Estimates the skeleton of a character, returning a list of keypoints to use with the skeleton animation tool.

### Parameters

### Request Body
- `image`: object (optional)
  A base64 encoded image.

Attributes:
    type (Literal["base64"]): Always "base64" to indicate the image encoding type
    base64 (str): The base64 encoded image data
    format (str): The image format (e.g., "png", "jpeg")
- `image.type`: string (default=base64) (optional)
  Image data type
- `image.base64`: string (required)
  Base64 encoded image data
- `image.format`: string (default=png) (optional)
  Image format

### Responses
- **200**: Successfully generated image
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests
- **529**: Rate limit exceeded

# Background Jobs

## GET /background-jobs/{job_id}
**Get background job status**
Tags: Background Jobs

Check the status and results of a background job.

### Parameters
- `job_id` [path]: string (required)

### Responses
- **200**: Successfully retrieved job status
- **401**: Invalid API token
- **404**: Job not found or doesn't belong to user
- **429**: Too many requests
- **422**: Validation Error

# Character Management

## GET /characters
**List user's characters**
Tags: Character Management

List all characters created by the authenticated user.

### Parameters
- `limit` [query]: integer (min=1, max=100) (optional)
  Maximum number of characters to return
- `offset` [query]: integer (min=0) (optional)
  Number of characters to skip

### Responses
- **200**: Successfully retrieved character list
- **401**: Invalid API token
- **422**: Invalid pagination parameters
- **429**: Too many requests

## GET /characters/{character_id}
**Get character details**
Tags: Character Management

Get detailed information about a specific character.

### Parameters
- `character_id` [path]: string (required)

### Responses
- **200**: Successfully retrieved character details
- **401**: Invalid API token
- **403**: Character belongs to another user
- **404**: Character not found
- **429**: Too many requests
- **422**: Validation Error

## DELETE /characters/{character_id}
**Delete a character and all associated data**
Tags: Character Management

Delete a character (v2 API for external customers).

### Parameters
- `character_id` [path]: string (required)

### Responses
- **200**: Successful Response
- **422**: Validation Error

## GET /characters/{character_id}/zip
**Export character as ZIP**
Tags: Character Management

Download a character with all animations as a ZIP file.

### Parameters
- `character_id` [path]: string (required)

### Responses
- **200**: ZIP file download containing character data
- **423**: Character or animations still being generated
- **404**: Character not found
- **422**: Validation Error

## PATCH /characters/{character_id}/tags
**Update character tags**
Tags: Character Management

Update the tags for a specific character.

### Parameters
- `character_id` [path]: string (required)

### Request Body
- `tags`: array[string] (required)
  List of tags to assign to the character

### Responses
- **200**: Tags updated successfully
- **400**: Invalid tag format or validation error
- **401**: Invalid API token
- **403**: Character belongs to another user
- **404**: Character not found
- **429**: Too many requests
- **422**: Validation Error

# Character from template

## POST /create-character-with-4-directions
**Create character with 4 directions**
Tags: Character from template

Generate a character or object facing 4 cardinal directions (south, west, east, north).

### Parameters

### Request Body
- `description`: string (minLen=1, maxLen=2000) (required)
  Description of the character or object to generate
- `image_size`: object (required)
- `image_size.width`: integer (min=32.0, max=400.0) (required)
  Canvas width in pixels (character will be ~60% of canvas size)
- `image_size.height`: integer (min=32.0, max=400.0) (required)
  Canvas height in pixels (character will be ~60% of canvas size)
- `async_mode`: boolean | null (optional)
  Process asynchronously (always true for character creation)
- `text_guidance_scale`: number | null (optional)
  How closely to follow the text description (higher = more faithful)
- `outline`: string | null (optional)
  Outline style (thin, medium, thick, none)
- `shading`: string | null (optional)
  Shading style (soft, hard, flat, none)
- `detail`: string | null (optional)
  Detail level (low, medium, high)
- `view`: string | null (optional)
  Camera view angle (side, low top-down, high top-down, perspective)
- `isometric`: boolean | null (optional)
  Generate in isometric view
- `color_image`: object | null (optional)
  Color palette reference image
- `force_colors`: boolean | null (optional)
  Force the use of colors from color_image
- `proportions`: null (optional)
  Character body proportions (preset or custom values)
- `seed`: integer | null (optional)
  Seed for reproducible generation
- `output_type`: string | null (optional)
  Output format (always dict for external API)

### Responses
- **200**: Successfully generated 4-rotation images
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests

## POST /create-character-with-8-directions
**Create character with 8 directions**
Tags: Character from template

Generate a character or object facing 8 directions (all cardinal and diagonal directions).

### Parameters

### Request Body
- `description`: string (minLen=1, maxLen=2000) (required)
  Description of the character or object to generate
- `image_size`: object (required)
- `image_size.width`: integer (min=32.0, max=400.0) (required)
  Canvas width in pixels (character will be ~60% of canvas size)
- `image_size.height`: integer (min=32.0, max=400.0) (required)
  Canvas height in pixels (character will be ~60% of canvas size)
- `async_mode`: boolean | null (optional)
  Process asynchronously (always true - no synchronous processing yet)
- `text_guidance_scale`: number | null (optional)
  How closely to follow the text description (higher = more faithful)
- `outline`: string | null (optional)
  Outline style (thin, medium, thick, none)
- `shading`: string | null (optional)
  Shading style (soft, hard, flat, none)
- `detail`: string | null (optional)
  Detail level (low, medium, high)
- `view`: string | null (optional)
  Camera view angle (side, low top-down, high top-down, perspective)
- `isometric`: boolean | null (optional)
  Generate in isometric view
- `color_image`: object | null (optional)
  Color palette reference image
- `force_colors`: boolean | null (optional)
  Force the use of colors from color_image
- `proportions`: null (optional)
  Character body proportions (preset or custom values)
- `seed`: integer | null (optional)
  Seed for reproducible generation
- `output_type`: string | null (optional)
  Output format (always dict for external API)

### Responses
- **200**: Successfully generated 8-rotation images
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests

## POST /characters/animations
**Create Character Animation**
Tags: Character from template

Animate an existing character (background processing)

### Parameters

### Request Body
- `character_id`: string (required)
  ID of existing character to animate
- `animation_name`: string | null (optional)
  Name for this animation (defaults to action_description if not provided)
- `description`: string | null (optional)
  Description of the character or object to animate (uses character's original if not specified)
- `action_description`: string | null (optional)
  Action description (e.g., 'walking', 'running', 'jumping'). If not provided, uses default description based on template_animation_id.
- `async_mode`: boolean | null (optional)
  Process in background (always true - no foreground processing yet)
- `template_animation_id`: enum[backflip, breathing-idle, cross-punch, ...] (required)
  Animation template ID (required). Available: `backflip`, `breathing-idle`, `cross-punch`, `crouched-walking`, `crouching`, `drinking`, `falling-back-death`, `fight-stance-idle-8-frames`, `fireball`, `flying-kick`, ...
- `text_guidance_scale`: number | null (optional)
  How closely to follow the text description (higher = more faithful)
- `outline`: string | null (optional)
  Outline style (uses character's original if not specified)
- `shading`: string | null (optional)
  Shading style (uses character's original if not specified)
- `detail`: string | null (optional)
  Detail level (uses character's original if not specified)
- `directions`: array | null (optional)
  List of directions to animate (south, north, east, west, etc.). If None, animates all available directions.
- `isometric`: boolean | null (optional)
  Generate in isometric view
- `color_image`: object | null (optional)
  Color palette reference image
- `force_colors`: boolean | null (optional)
  Force the use of colors from color_image
- `seed`: integer | null (optional)
  Seed for reproducible generation

### Responses
- **200**: Successful Response
- **422**: Validation Error

## POST /animate-character
**Animate character with template**
Tags: Character from template

Animate an existing character with multiple frames showing movement or action.

### Parameters

### Request Body
- `character_id`: string (required)
  ID of existing character to animate
- `animation_name`: string | null (optional)
  Name for this animation (defaults to action_description if not provided)
- `description`: string | null (optional)
  Description of the character or object to animate (uses character's original if not specified)
- `action_description`: string | null (optional)
  Action description (e.g., 'walking', 'running', 'jumping'). If not provided, uses default description based on template_animation_id.
- `async_mode`: boolean | null (optional)
  Process in background (always true - no foreground processing yet)
- `template_animation_id`: enum[backflip, breathing-idle, cross-punch, ...] (required)
  Animation template ID (required). Available: `backflip`, `breathing-idle`, `cross-punch`, `crouched-walking`, `crouching`, `drinking`, `falling-back-death`, `fight-stance-idle-8-frames`, `fireball`, `flying-kick`, ...
- `text_guidance_scale`: number | null (optional)
  How closely to follow the text description (higher = more faithful)
- `outline`: string | null (optional)
  Outline style (uses character's original if not specified)
- `shading`: string | null (optional)
  Shading style (uses character's original if not specified)
- `detail`: string | null (optional)
  Detail level (uses character's original if not specified)
- `directions`: array | null (optional)
  List of directions to animate (south, north, east, west, etc.). If None, animates all available directions.
- `isometric`: boolean | null (optional)
  Generate in isometric view
- `color_image`: object | null (optional)
  Color palette reference image
- `force_colors`: boolean | null (optional)
  Force the use of colors from color_image
- `seed`: integer | null (optional)
  Seed for reproducible generation

### Responses
- **200**: Successfully started character animation in background
- **401**: Invalid API token
- **402**: Insufficient credits
- **404**: Character not found
- **422**: Validation error
- **429**: Too many requests

# Create Image

## POST /create-image-pixflux
**Create image (pixflux)**
Tags: Create Image

Creates a pixel art image based on the provided parameters. Called "Create image (new)" in the plugin.

### Parameters

### Request Body
- `description`: string (required)
  Text description of the image to generate
- `negative_description`: string (default=) (optional)
  (Deprecated)
- `image_size`: object (required)
- `image_size.width`: integer (min=16.0, max=400.0) (required)
  Image width in pixels
- `image_size.height`: integer (min=16.0, max=400.0) (required)
  Image height in pixels
- `text_guidance_scale`: number (min=1.0, max=20.0, default=8) (optional)
  How closely to follow the text description
- `outline`: string | null (optional)
  Outline style reference (weakly guiding)
- `shading`: string | null (optional)
  Shading style reference (weakly guiding)
- `detail`: string | null (optional)
  Detail style reference (weakly guiding)
- `view`: string | null (optional)
  Camera view angle (weakly guiding)
- `direction`: string | null (optional)
  Subject direction (weakly guiding)
- `isometric`: boolean (default=False) (optional)
  Generate in isometric view (weakly guiding)
- `no_background`: boolean (default=False) (optional)
  Generate with transparent background, (blank background over 200x200 area)
- `background_removal_task`: enum[remove_simple_background, remove_complex_background] (default=remove_simple_background) (optional)
  Background removal complexity. 'remove_simple_background' is faster, 'remove_complex_background' handles complex edges better
- `init_image`: object | null (optional)
  Initial image to start from
- `init_image_strength`: integer (min=1.0, max=999.0, default=300) (optional)
  Strength of the initial image influence
- `color_image`: object | null (optional)
  Forced color palette, image containing colors used for palette
- `seed`: integer | null (optional)
  Seed decides the starting noise

### Responses
- **200**: Successfully generated image
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests
- **529**: Rate limit exceeded

## POST /create-image-bitforge
**Create image (bitforge)**
Tags: Create Image

Generates a pixel art image based on the provided parameters. Called "Create S-M image" in the plugin.

### Parameters

### Request Body
- `description`: string (required)
  Text description of the image to generate
- `negative_description`: string (default=) (optional)
  Text description of what to avoid in the generated image
- `image_size`: object (required)
- `image_size.width`: integer (min=16.0, max=200.0) (required)
  Image width in pixels
- `image_size.height`: integer (min=16.0, max=200.0) (required)
  Image height in pixels
- `text_guidance_scale`: number (min=1.0, max=20.0, default=8.0) (optional)
  How closely to follow the text description
- `extra_guidance_scale`: number (min=0.0, max=20.0, default=3.0) (optional)
  (Deprecated)
- `style_strength`: number (min=0.0, max=100.0, default=0.0) (optional)
  Strength of the style transfer (0-100)
- `outline`: string | null (optional)
  Outline style reference
- `shading`: string | null (optional)
  Shading style reference
- `detail`: string | null (optional)
  Detail style reference
- `view`: string | null (optional)
  Camera view angle
- `direction`: string | null (optional)
  Subject direction
- `isometric`: boolean (default=False) (optional)
  Generate in isometric view
- `oblique_projection`: boolean (default=False) (optional)
  Generate in oblique projection
- `no_background`: boolean (default=False) (optional)
  Generate with transparent background
- `coverage_percentage`: number | null (optional)
  Percentage of the canvas to cover
- `init_image`: object | null (optional)
  Initial image to start from
- `init_image_strength`: integer (min=1.0, max=999.0, default=300) (optional)
  Strength of the initial image influence
- `style_image`: object | null (optional)
  Reference image for style transfer
- `inpainting_image`: object | null (optional)
  Reference image which is inpainted
- `mask_image`: object | null (optional)
  Inpainting / mask image (black and white image, where the white is where the model should inpaint)
- `color_image`: object | null (optional)
  Forced color palette, image containing colors used for palette
- `skeleton_guidance_scale`: number (min=0.0, max=5.0, default=1.0) (optional)
  How closely to follow the skeleton keypoints
- `skeleton_keypoints`: array | null (optional)
  Skeleton points. Warning! Sizes that are not 16x16, 32x32 and 64x64 can cause the generations to be lower quality
- `seed`: integer | null (optional)
  Seed decides the starting noise

### Responses
- **200**: Successfully generated image
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests
- **529**: Rate limit exceeded

## POST /generate-image-v2
**Generate pixel art images (v2)**
Tags: Create Image

Generate pixel art images from text description.

### Parameters

### Request Body
- `description`: string (minLen=1, maxLen=2000) (required)
  Description of the image to generate
- `image_size`: object (required)
- `image_size.width`: integer (min=32.0, max=256.0) (required)
  Image width in pixels (32, 64, 128, or 256)
- `image_size.height`: integer (min=32.0, max=256.0) (required)
  Image height in pixels (32, 64, 128, or 256)
- `seed`: integer | null (optional)
  Seed for reproducible generation
- `no_background`: boolean | null (optional)
  Remove background from generated images
- `reference_images`: array | null (optional)
  Optional reference images for subject guidance (up to 4)
- `style_image`: object | null (optional)
  Optional style image for pixel size and style reference
- `style_options`: object (optional)
  Options for what to copy from the style image.
- `style_options.color_palette`: boolean (default=True) (optional)
  Copy color palette from style image
- `style_options.outline`: boolean (default=True) (optional)
  Copy outline style
- `style_options.detail`: boolean (default=True) (optional)
  Copy detail level
- `style_options.shading`: boolean (default=True) (optional)
  Copy shading style

### Responses
- **200**: Successfully generated images
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests

## POST /generate-with-style-v2
**Generate images matching a style (v2)**
Tags: Create Image

Generate new pixel art images that match the style of reference images.

### Parameters

### Request Body
- `style_images`: array[object] (required)
  Style reference images (1-4 images)
- `description`: string (minLen=1, maxLen=2000) (required)
  Description of what to generate
- `image_size`: object (required)
- `image_size.width`: integer (min=32.0, max=256.0) (required)
  Image width (32, 64, 128, or 256)
- `image_size.height`: integer (min=32.0, max=256.0) (required)
  Image height (32, 64, 128, or 256)
- `style_description`: string | null (optional)
  Description of the style to match
- `seed`: integer | null (optional)
  Seed for reproducible generation
- `no_background`: boolean | null (optional)
  Remove background from generated images

### Responses
- **200**: Successfully generated images
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests

# Create map

## POST /tilesets
**Create a tileset asynchronously**
Tags: Create map

Creates a Wang tileset (16 tiles for standard, 23 for transition_size=1.0) in the background and returns immediately with job ID

### Parameters

### Request Body
- `lower_description`: string (minLen=1) (required)
  Description of the lower/base terrain level (e.g., 'ocean', 'grass', 'lava')
- `upper_description`: string (minLen=1) (required)
  Description of the upper/elevated terrain level (e.g., 'sand', 'stone', 'snow')
- `transition_description`: string (default=) (optional)
  Optional description of transition area between lower and upper
- `lower_base_tile_id`: string | null (optional)
  Optional ID to identify the lower base tile in metadata
- `upper_base_tile_id`: string | null (optional)
  Optional ID to identify the upper base tile in metadata
- `tile_size`: object (optional)
- `tile_size.width`: enum[16, 32] (default=16) (optional)
  Individual tile width in pixels (16 or 32)
- `tile_size.height`: enum[16, 32] (default=16) (optional)
  Individual tile height in pixels (16 or 32)
- `text_guidance_scale`: number (min=1.0, max=20.0, default=8.0) (optional)
  How closely to follow the text descriptions (default: 8.0)
- `outline`: string | null (optional)
  Outline style reference
- `shading`: string | null (optional)
  Shading style reference
- `detail`: string | null (optional)
  Detail style reference
- `view`: enum[low top-down, high top-down] (optional)
  Camera view options supported for tileset generation
- `tile_strength`: number (min=0.1, max=2.0, default=1.0) (optional)
  Strength of tile pattern adherence
- `tileset_adherence_freedom`: number (min=0.0, max=900.0, default=500.0) (optional)
  How flexible it will be when following tileset structure, higher values means more flexibility
- `tileset_adherence`: number (min=0.0, max=500.0, default=100.0) (optional)
  How much it will follow the reference/texture image and follow tileset structure
- `transition_size`: enum[0.0, 0.25, 0.5, ...] (default=0.0) (optional)
  Size of transition area (0 = no transition, 0.25 = quarter tile, 0.5 = half tile, 1.0 = full tile)
- `lower_reference_image`: object | null (optional)
  Reference image for lower terrain style
- `upper_reference_image`: object | null (optional)
  Reference image for upper terrain style
- `transition_reference_image`: object | null (optional)
  Reference image for transition area style
- `color_image`: object | null (optional)
  Reference image for color palette
- `seed`: integer | null (optional)
  Seed for reproducible generation

### Responses
- **202**: Tileset creation started, returns job ID
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests
- **529**: Rate limit exceeded

## POST /create-tileset
**Create top-down tileset (async processing)**
Tags: Create map

Creates a complete tileset for game development with seamlessly connecting tiles.

### Parameters

### Request Body
- `lower_description`: string (minLen=1) (required)
  Description of the lower/base terrain level (e.g., 'ocean', 'grass', 'lava')
- `upper_description`: string (minLen=1) (required)
  Description of the upper/elevated terrain level (e.g., 'sand', 'stone', 'snow')
- `transition_description`: string (default=) (optional)
  Optional description of transition area between lower and upper
- `lower_base_tile_id`: string | null (optional)
  Optional ID to identify the lower base tile in metadata
- `upper_base_tile_id`: string | null (optional)
  Optional ID to identify the upper base tile in metadata
- `tile_size`: object (optional)
- `tile_size.width`: enum[16, 32] (default=16) (optional)
  Individual tile width in pixels (16 or 32)
- `tile_size.height`: enum[16, 32] (default=16) (optional)
  Individual tile height in pixels (16 or 32)
- `text_guidance_scale`: number (min=1.0, max=20.0, default=8.0) (optional)
  How closely to follow the text descriptions (default: 8.0)
- `outline`: string | null (optional)
  Outline style reference
- `shading`: string | null (optional)
  Shading style reference
- `detail`: string | null (optional)
  Detail style reference
- `view`: enum[low top-down, high top-down] (optional)
  Camera view options supported for tileset generation
- `tile_strength`: number (min=0.1, max=2.0, default=1.0) (optional)
  Strength of tile pattern adherence
- `tileset_adherence_freedom`: number (min=0.0, max=900.0, default=500.0) (optional)
  How flexible it will be when following tileset structure, higher values means more flexibility
- `tileset_adherence`: number (min=0.0, max=500.0, default=100.0) (optional)
  How much it will follow the reference/texture image and follow tileset structure
- `transition_size`: enum[0.0, 0.25, 0.5, ...] (default=0.0) (optional)
  Size of transition area (0 = no transition, 0.25 = quarter tile, 0.5 = half tile, 1.0 = full tile)
- `lower_reference_image`: object | null (optional)
  Reference image for lower terrain style
- `upper_reference_image`: object | null (optional)
  Reference image for upper terrain style
- `transition_reference_image`: object | null (optional)
  Reference image for transition area style
- `color_image`: object | null (optional)
  Reference image for color palette
- `seed`: integer | null (optional)
  Seed for reproducible generation

### Responses
- **202**: Successful Response
- **200**: Successfully generated tileset
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests
- **529**: Rate limit exceeded

## GET /tilesets/{tileset_id}
**Get generated tileset by ID**
Tags: Create map

Retrieve a completed tileset by its UUID.

### Parameters
- `tileset_id` [path]: string (required)

### Responses
- **200**: Successfully retrieved tileset
- **423**: Tileset is still being generated
- **404**: Tileset not found
- **401**: Invalid API token
- **422**: Validation Error

## POST /create-isometric-tile
**Create isometric tile (async processing)**
Tags: Create map

Creates a isometric tile based on the provided parameters.

### Parameters

### Request Body
- `description`: string (required)
  Text description of the image to generate
- `image_size`: object (required)
- `image_size.width`: integer (min=16.0, max=64.0) (required)
  Image width in pixels. Sizes above 24px often give better results.
- `image_size.height`: integer (min=16.0, max=64.0) (required)
  Image height in pixels. Sizes above 24px often give better results.
- `text_guidance_scale`: number (min=1.0, max=20.0, default=8) (optional)
  How closely to follow the text description
- `outline`: string | null (optional)
  Outline style for the tile
- `shading`: string | null (optional)
  Shading complexity
- `detail`: string | null (optional)
  Level of detail in the tile
- `init_image`: object | null (optional)
  Initial image to start from
- `init_image_strength`: integer (min=1.0, max=999.0, default=300) (optional)
  Strength of the initial image influence
- `isometric_tile_size`: integer | null (optional)
  Size of the isometric tile. Recommended sizes: 16, 32. Can be omitted for default.
- `isometric_tile_shape`: enum[thick tile, thin tile, block] (default=block) (optional)
  Tile thickness. Thicker tiles allow more height variation in game maps. thin tile: ~15% canvas height, thick tile: ~25% height, block: ~50% height
- `color_image`: object | null (optional)
  Forced color palette, image containing colors used for palette
- `seed`: integer | null (optional)
  Seed decides the starting noise

### Responses
- **202**: Successful Response
- **200**: Successfully generated image
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests
- **529**: Rate limit exceeded

## GET /isometric-tiles/{tile_id}
**Get generated isometric tile by ID**
Tags: Create map

Retrieve a completed isometric tile by its UUID.

### Parameters
- `tile_id` [path]: string (required)

### Responses
- **200**: Successfully retrieved tile
- **404**: Tile not found
- **401**: Invalid API token
- **423**: Tile still processing
- **422**: Validation Error

# Documentation

## GET /llms.txt
**Get LLM-friendly API documentation**
Tags: Documentation

Returns API documentation formatted for Large Language Models (LLMs).

### Responses
- **200**: LLM-friendly API documentation

# Edit

## POST /edit-image
**Edit image**
Tags: Edit

Edit an existing pixel art image based on a text description.

### Parameters

### Request Body
- `image`: object (required)
  A base64 encoded image.

Attributes:
    type (Literal["base64"]): Always "base64" to indicate the image encoding type
    base64 (str): The base64 encoded image data
    format (str): The image format (e.g., "png", "jpeg")
- `image.type`: string (default=base64) (optional)
  Image data type
- `image.base64`: string (required)
  Base64 encoded image data
- `image.format`: string (default=png) (optional)
  Image format
- `image_size`: object (required)
- `image_size.width`: integer (min=16.0, max=400.0) (required)
  Image width in pixels (16-400)
- `image_size.height`: integer (min=16.0, max=400.0) (required)
  Image height in pixels (16-400)
- `description`: string (minLen=1, maxLen=500) (required)
  Text description of the edit to apply
- `width`: integer (min=16.0, max=400.0) (required)
  Target canvas width in pixels (16-400)
- `height`: integer (min=16.0, max=400.0) (required)
  Target canvas height in pixels (16-400)
- `seed`: integer | null (optional)
  Seed for reproducible generation (0 for random)
- `no_background`: boolean | null (optional)
  Generate with transparent background
- `text_guidance_scale`: number | null (optional)
  How closely to follow the text description (1.0-10.0)
- `color_image`: object | null (optional)
  Color reference image for style guidance

### Responses
- **200**: Successful Response
- **422**: Validation Error

## POST /edit-images-v2
**Edit pixel art images (v2)**
Tags: Edit

Edit pixel art images using text or reference image.

### Parameters

### Request Body
- `method`: enum[edit_with_text, edit_with_reference] (default=edit_with_text) (optional)
  Edit method: 'edit_with_text' or 'edit_with_reference'
- `edit_images`: array[object] (required)
  Images to edit (1-16 images depending on size)
- `image_size`: object (required)
- `image_size.width`: integer (min=32.0, max=256.0) (required)
  Image width in pixels
- `image_size.height`: integer (min=32.0, max=256.0) (required)
  Image height in pixels
- `description`: string | null (optional)
  Edit description (required for edit_with_text method)
- `reference_image`: object | null (optional)
  Reference image (required for edit_with_reference method)
- `seed`: integer | null (optional)
  Seed for reproducible generation
- `no_background`: boolean | null (optional)
  Remove background from edited images

### Responses
- **200**: Successfully edited images
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests

# Image Operations

## POST /image-to-pixelart
**Convert image to pixel art**
Tags: Image Operations

Convert regular images to pixel art style.

### Parameters

### Request Body
- `image`: object (required)
  A base64 encoded image.

Attributes:
    type (Literal["base64"]): Always "base64" to indicate the image encoding type
    base64 (str): The base64 encoded image data
    format (str): The image format (e.g., "png", "jpeg")
- `image.type`: string (default=base64) (optional)
  Image data type
- `image.base64`: string (required)
  Base64 encoded image data
- `image.format`: string (default=png) (optional)
  Image format
- `image_size`: object (required)
  Image dimensions
- `image_size.width`: integer (min=16.0, max=1280.0) (required)
  Width in pixels
- `image_size.height`: integer (min=16.0, max=1280.0) (required)
  Height in pixels
- `output_size`: object (required)
  Output dimensions
- `output_size.width`: integer (min=16.0, max=320.0) (required)
  Width in pixels
- `output_size.height`: integer (min=16.0, max=320.0) (required)
  Height in pixels
- `text_guidance_scale`: number | null (optional)
  How closely to follow pixel art style
- `seed`: integer | null (optional)
  Seed for reproducible generation

### Responses
- **200**: Successfully converted image
- **400**: Invalid image size constraints
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests

## POST /resize
**Resize pixel art image**
Tags: Image Operations

Intelligently resize pixel art images while maintaining pixel art aesthetics.

### Parameters

### Request Body
- `description`: string (minLen=1, maxLen=2000) (required)
  Description of your character
- `reference_image`: object (required)
  A base64 encoded image.

Attributes:
    type (Literal["base64"]): Always "base64" to indicate the image encoding type
    base64 (str): The base64 encoded image data
    format (str): The image format (e.g., "png", "jpeg")
- `reference_image.type`: string (default=base64) (optional)
  Image data type
- `reference_image.base64`: string (required)
  Base64 encoded image data
- `reference_image.format`: string (default=png) (optional)
  Image format
- `reference_image_size`: object (required)
  Image dimensions
- `reference_image_size.width`: integer (min=16.0, max=200.0) (required)
  Width in pixels
- `reference_image_size.height`: integer (min=16.0, max=200.0) (required)
  Height in pixels
- `target_size`: object (required)
  Image dimensions
- `target_size.width`: integer (min=16.0, max=200.0) (required)
  Width in pixels
- `target_size.height`: integer (min=16.0, max=200.0) (required)
  Height in pixels
- `view`: string | null (optional)
  Camera view angle
- `direction`: string | null (optional)
  Directional view
- `isometric`: boolean | null (optional)
  Isometric perspective
- `oblique_projection`: boolean | null (optional)
  Oblique projection (beta)
- `no_background`: boolean | null (optional)
  Remove background
- `color_image`: object | null (optional)
  Forced color palette, image containing colors used for palette
- `init_image`: object | null (optional)
  Initial image to start from
- `init_image_strength`: number | null (optional)
  Strength of initial image influence
- `seed`: integer | null (optional)
  Seed for reproducible generation

### Responses
- **200**: Successfully resized image
- **400**: Invalid image size constraints
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests

# Inpaint

## POST /inpaint
**Inpaint image**
Tags: Inpaint

Creates a pixel art image based on the provided parameters. Called "Inpaint" in the plugin.

### Parameters

### Request Body
- `description`: string (required)
  Text description of the image to generate
- `negative_description`: string (default=) (optional)
  Text description of what to avoid in the generated image
- `image_size`: object (required)
- `image_size.width`: integer (min=16.0, max=200.0) (required)
  Image width in pixels
- `image_size.height`: integer (min=16.0, max=200.0) (required)
  Image height in pixels
- `text_guidance_scale`: number (min=1.0, max=10.0, default=3.0) (optional)
  How closely to follow the text description
- `extra_guidance_scale`: number (min=0.0, max=20.0, default=3.0) (optional)
  (Deprecated)
- `outline`: string | null (optional)
  Outline style reference
- `shading`: string | null (optional)
  Shading style reference
- `detail`: string | null (optional)
  Detail style reference
- `view`: string | null (optional)
  Camera view angle
- `direction`: string | null (optional)
  Subject direction
- `isometric`: boolean (default=False) (optional)
  Generate in isometric view
- `oblique_projection`: boolean (default=False) (optional)
  Generate in oblique projection
- `no_background`: boolean (default=False) (optional)
  Generate with transparent background
- `init_image`: object | null (optional)
  Initial image to start from
- `init_image_strength`: integer (min=1.0, max=999.0, default=300) (optional)
  Strength of the initial image influence
- `inpainting_image`: object (required)
  A base64 encoded image.

Attributes:
    type (Literal["base64"]): Always "base64" to indicate the image encoding type
    base64 (str): The base64 encoded image data
    format (str): The image format (e.g., "png", "jpeg")
- `inpainting_image.type`: string (default=base64) (optional)
  Image data type
- `inpainting_image.base64`: string (required)
  Base64 encoded image data
- `inpainting_image.format`: string (default=png) (optional)
  Image format
- `mask_image`: object (required)
  A base64 encoded image.

Attributes:
    type (Literal["base64"]): Always "base64" to indicate the image encoding type
    base64 (str): The base64 encoded image data
    format (str): The image format (e.g., "png", "jpeg")
- `mask_image.type`: string (default=base64) (optional)
  Image data type
- `mask_image.base64`: string (required)
  Base64 encoded image data
- `mask_image.format`: string (default=png) (optional)
  Image format
- `color_image`: object | null (optional)
  Forced color palette, image containing colors used for palette
- `seed`: integer | null (optional)
  Seed decides the starting noise

### Responses
- **200**: Successfully generated image
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests
- **529**: Rate limit exceeded

# Map Objects

## POST /map-objects
**Create map object**
Tags: Map Objects

Creates a pixel art object with transparent background for game maps.

### Parameters

### Request Body
- `description`: string (minLen=1, maxLen=2000) (required)
  Object description (e.g., 'wooden barrel', 'stone fountain')
- `image_size`: object (optional)
  Image dimensions for map objects.

Supports any aspect ratio:
- Both width and height: 32px minimum, 400px maximum
- Basic mode (no inpainting): max 400×400 total area (160,000 pixels)
- Inpainting mode: max 192×192 total area (36,864 pixels)
- Common sizes: 64×64, 128×128, 192×192, 256×128, 384×96
- `image_size.width`: integer (min=32.0, max=400.0) (required)
  Width in pixels (32-400)
- `image_size.height`: integer (min=32.0, max=400.0) (required)
  Height in pixels (32-400)
- `view`: enum[low top-down, high top-down, side] (default=high top-down) (optional)
  Camera angle
- `outline`: string | null (optional)
  Outline style
- `shading`: string | null (optional)
  Shading complexity
- `detail`: string | null (optional)
  Level of detail
- `text_guidance_scale`: number (min=1.0, max=20.0, default=8.0) (optional)
  How closely to follow the description
- `init_image`: object | null (optional)
  Initial image to start from
- `init_image_strength`: integer (min=1.0, max=999.0, default=300) (optional)
  Strength of initial image influence
- `color_image`: object | null (optional)
  Image containing colors for forced palette
- `background_image`: object | null (optional)
  Background/map image for style matching. Required when using inpainting.
- `inpainting`: object | object | object | null (optional)
  Inpainting configuration for style matching. Options: mask (custom), oval (auto-generated), rectangle (auto-generated)
- `seed`: integer | null (optional)
  Seed for reproducible generation

### Responses
- **200**: Object generation queued
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests

# Rotate

## POST /rotate
**Rotate character or object**
Tags: Rotate

Rotates a pixel art image based on the provided parameters. Called "Rotate" in the plugin.

### Parameters

### Request Body
- `image_size`: object (required)
- `image_size.width`: integer (min=16.0, max=200.0) (required)
  Image width in pixels
- `image_size.height`: integer (min=16.0, max=200.0) (required)
  Image height in pixels
- `image_guidance_scale`: number (min=1.0, max=20.0, default=3.0) (optional)
  How closely to follow the reference image
- `view_change`: integer | null (optional)
  How many degrees to tilt the subject
- `direction_change`: integer | null (optional)
  How many degrees to rotate the subject
- `from_view`: string | null (optional)
  From camera view angle
- `to_view`: string | null (optional)
  To camera view angle
- `from_direction`: string | null (optional)
  From subject direction
- `to_direction`: string | null (optional)
  From subject direction
- `isometric`: boolean (default=False) (optional)
  Generate in isometric view
- `oblique_projection`: boolean (default=False) (optional)
  Generate in oblique projection
- `init_image`: object | null (optional)
  Initial image to start from
- `init_image_strength`: integer (min=1.0, max=999.0, default=300) (optional)
  Strength of the initial image influence
- `mask_image`: object | null (optional)
  Inpainting / mask image. Requires init image! (black and white image, where the white is where the model should inpaint)
- `from_image`: object (required)
  A base64 encoded image.

Attributes:
    type (Literal["base64"]): Always "base64" to indicate the image encoding type
    base64 (str): The base64 encoded image data
    format (str): The image format (e.g., "png", "jpeg")
- `from_image.type`: string (default=base64) (optional)
  Image data type
- `from_image.base64`: string (required)
  Base64 encoded image data
- `from_image.format`: string (default=png) (optional)
  Image format
- `color_image`: object | null (optional)
  Forced color palette, image containing colors used for palette
- `seed`: integer | null (optional)
  Seed decides the starting noise

### Responses
- **200**: Successfully generated image
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests
- **529**: Rate limit exceeded

## POST /generate-8-rotations-v2
**Generate 8 rotational views (v2)**
Tags: Rotate

Generate 8 rotational views of a character or object.

### Parameters

### Request Body
- `method`: enum[rotate_character, create_with_style, create_from_concept] (default=rotate_character) (optional)
  Generation method: 'rotate_character' rotates an existing character, 'create_with_style' creates new character matching style, 'create_from_concept' creates from concept art
- `image_size`: object (required)
- `image_size.width`: integer (min=32.0, max=84.0) (required)
  Image width (32-84 pixels)
- `image_size.height`: integer (min=32.0, max=84.0) (required)
  Image height (32-84 pixels)
- `reference_image`: object | null (optional)
  Image to rotate (rotate_character) or style reference
- `concept_image`: object | null (optional)
  Concept art image (only for create_from_concept method)
- `description`: string | null (optional)
  Description of the character/item
- `style_description`: string | null (optional)
  Description of the visual style
- `view`: enum[low top-down, high top-down, side] (default=low top-down) (optional)
  Camera perspective angle
- `seed`: integer | null (optional)
  Seed for reproducible generation
- `no_background`: boolean | null (optional)
  Remove background from generated images

### Responses
- **200**: Successfully generated 8 rotations
- **401**: Invalid API token
- **402**: Insufficient credits
- **422**: Validation error
- **429**: Too many requests

## Usage Examples

### Create a Character (Python)
```python
import requests

response = requests.post(
    "https://api.pixellab.ai/v2/create-character-with-4-directions",
    headers={
        "Authorization": "Bearer YOUR_TOKEN",
        "Content-Type": "application/json"
    },
    json={
        "description": "brave knight with shining armor",
        "image_size": {"width": 64, "height": 64}
    }
)

job_id = response.json()['background_job_id']
character_id = response.json()['character_id']
```

### Check Job Status
```python
status_response = requests.get(
    "https://api.pixellab.ai/v2/background-jobs/{job_id}",
    headers={
        "Authorization": "Bearer YOUR_TOKEN"
    }
)

if status_response.json()['status'] == 'completed':
    print('Character ready!')
```

## Error Codes
- **400**: Bad Request - Invalid parameters
- **401**: Unauthorized - Invalid or missing token
- **402**: Payment Required - Insufficient credits
- **403**: Forbidden - Feature not available for your tier
- **404**: Not Found - Resource doesn't exist
- **423**: Locked - Resource still being generated
- **429**: Too Many Requests - Rate limit exceeded
- **500**: Internal Server Error

## Support
- Documentation: https://api.pixellab.ai/v2/docs
- Python Client: https://github.com/pixellab-code/pixellab-python
- Discord: https://discord.gg/pBeyTBF8T7
- Email: support@pixellab.ai