import pygame

# Initialize Pygame
pygame.init()

# Load sprite sheet image
sprite_sheet = pygame.image.load("../images/GoblinArcher-Sheet.png")

# Define the size of each frame
frame_size = (150, 150)

# Loop through the sprite sheet and slice each frame
frames = []
for y in range(0, sprite_sheet.get_height(), frame_size[1]):
    for x in range(0, sprite_sheet.get_width(), frame_size[0]):
        # Check if x and y are within bounds
        if x + frame_size[0] <= sprite_sheet.get_width() and y + frame_size[1] <= sprite_sheet.get_height():
            frame_rect = pygame.Rect(x, y, frame_size[0], frame_size[1])
            frame_image = sprite_sheet.subsurface(frame_rect)
            frames.append(frame_image)

print('done')