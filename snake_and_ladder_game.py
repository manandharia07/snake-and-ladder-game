import pygame
import random
import sys
import time
import math  # Added for the pulsing effect

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1000, 800  # Increased width to accommodate sidebar
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake and Ladder Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
BROWN = (165, 42, 42)
LIGHT_GRAY = (240, 240, 240)
MEDIUM_GRAY = (220, 220, 220)

# Game constants
GRID_SIZE = 10
BOARD_SIZE = 800  # Fixed board size
CELL_SIZE = BOARD_SIZE // GRID_SIZE
SIDEBAR_WIDTH = WIDTH - BOARD_SIZE
DICE_SIZE = 100
DICE_POS = (BOARD_SIZE + (SIDEBAR_WIDTH - DICE_SIZE) // 2, HEIGHT // 2 - DICE_SIZE // 2)
PLAYER_RADIUS = 15

# Fonts
TITLE_FONT = pygame.font.SysFont('Arial', 32)  # Slightly smaller title font
FONT = pygame.font.SysFont('Arial', 22)        # Standard font
SMALL_FONT = pygame.font.SysFont('Arial', 16)  # Smaller font for messages
DICE_FONT = pygame.font.SysFont('Arial', 60)   # Large font for dice

# Define snakes and ladders
# Format: {position_from: position_to}
SNAKES = {
    16: 6,
    47: 26,
    49: 11,
    56: 53,
    62: 19,
    64: 60,
    87: 24,
    93: 73,
    95: 75,
    98: 78
}

LADDERS = {
    1: 38,
    4: 14,
    9: 31,
    21: 42,
    28: 84,
    36: 44,
    51: 67,
    71: 91,
    80: 100
}

class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.position = 0
        self.won = False

    def move(self, steps):
        if self.position + steps <= 100:
            self.position += steps

            # Check if landed on a snake
            if self.position in SNAKES:
                self.position = SNAKES[self.position]
                return f"{self.name} got bitten by a snake! Moved from {self.position + steps} to {self.position}"

            # Check if landed on a ladder
            if self.position in LADDERS:
                old_pos = self.position
                self.position = LADDERS[self.position]
                return f"{self.name} climbed a ladder! Moved from {old_pos} to {self.position}"

            # Check if won
            if self.position == 100:
                self.won = True
                return f"{self.name} won the game!"

            return f"{self.name} moved to {self.position}"
        return f"{self.name} needs {100 - self.position} or fewer to finish"

class Game:
    def __init__(self):
        self.players = [
            Player("Player 1", PURPLE),
            Player("Player 2", ORANGE)
        ]
        self.current_player = 0
        self.dice_value = 0
        self.game_over = False
        self.message = "Roll the dice to start!"
        self.rolling = False
        self.roll_time = 0
        self.board_image = self.create_board()

        # Animation variables
        self.moving = False
        self.move_start_time = 0
        self.move_from = 0
        self.move_to = 0
        self.move_steps = 0
        self.current_step = 0
        self.step_delay = 500  # milliseconds between steps
        self.snake_ladder_message = ""

    def create_board(self):
        # Create a surface for the board
        board = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
        board.fill(WHITE)

        # Draw grid
        for i in range(GRID_SIZE + 1):
            # Horizontal lines
            pygame.draw.line(board, BLACK, (0, i * CELL_SIZE), (BOARD_SIZE, i * CELL_SIZE), 2)
            # Vertical lines
            pygame.draw.line(board, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, BOARD_SIZE), 2)

        # Add numbers to cells
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                # Calculate row from bottom (0 is bottom row, 9 is top row)
                actual_row = GRID_SIZE - 1 - row

                # Snake pattern numbering (alternating direction)
                if actual_row % 2 == 0:  # Even rows from bottom (0, 2, 4...) - left to right
                    num = actual_row * GRID_SIZE + col + 1
                else:  # Odd rows from bottom (1, 3, 5...) - right to left
                    num = (actual_row + 1) * GRID_SIZE - col

                # Position for the number
                x = col * CELL_SIZE + CELL_SIZE // 2
                y = row * CELL_SIZE + CELL_SIZE // 2

                # Draw the number
                text = FONT.render(str(num), True, BLACK)
                text_rect = text.get_rect(center=(x, y))
                board.blit(text, text_rect)

                # Color the cell if it's a snake or ladder
                if num in SNAKES:
                    pygame.draw.rect(board, (255, 200, 200),
                                    (col * CELL_SIZE + 2, row * CELL_SIZE + 2,
                                     CELL_SIZE - 4, CELL_SIZE - 4), 3)
                elif num in LADDERS:
                    pygame.draw.rect(board, (200, 255, 200),
                                    (col * CELL_SIZE + 2, row * CELL_SIZE + 2,
                                     CELL_SIZE - 4, CELL_SIZE - 4), 3)

        # Draw snakes
        for start, end in SNAKES.items():
            start_pos = self.get_position_coordinates(start)
            end_pos = self.get_position_coordinates(end)
            pygame.draw.line(board, RED, start_pos, end_pos, 5)
            # Draw snake head
            pygame.draw.circle(board, RED, end_pos, 10)

        # Draw ladders
        for start, end in LADDERS.items():
            start_pos = self.get_position_coordinates(start)
            end_pos = self.get_position_coordinates(end)
            pygame.draw.line(board, GREEN, start_pos, end_pos, 5)
            # Draw ladder rungs
            distance = ((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)**0.5
            num_rungs = int(distance / 40)
            for i in range(1, num_rungs + 1):
                t = i / (num_rungs + 1)
                x = start_pos[0] + t * (end_pos[0] - start_pos[0])
                y = start_pos[1] + t * (end_pos[1] - start_pos[1])

                # Calculate perpendicular direction for the rung
                dx = end_pos[0] - start_pos[0]
                dy = end_pos[1] - start_pos[1]
                length = 20

                # Perpendicular vector
                px = -dy / ((dx**2 + dy**2)**0.5) * length
                py = dx / ((dx**2 + dy**2)**0.5) * length

                pygame.draw.line(board, BROWN, (x - px/2, y - py/2), (x + px/2, y + py/2), 3)

        return board

    def get_position_coordinates(self, position):
        if position == 0:  # Starting position
            return (CELL_SIZE // 2, HEIGHT - CELL_SIZE // 2)

        position -= 1  # Convert to 0-indexed

        # Calculate row from bottom (0 is bottom row, 9 is top row)
        row = GRID_SIZE - 1 - (position // GRID_SIZE)
        actual_row = GRID_SIZE - 1 - row  # Row from bottom

        # Calculate column based on snake pattern
        if actual_row % 2 == 0:  # Even rows from bottom - left to right
            col = position % GRID_SIZE
        else:  # Odd rows from bottom - right to left
            col = GRID_SIZE - 1 - (position % GRID_SIZE)

        x = col * CELL_SIZE + CELL_SIZE // 2
        y = row * CELL_SIZE + CELL_SIZE // 2

        return (x, y)

    def roll_dice(self):
        if not self.rolling and not self.game_over:
            self.rolling = True
            self.roll_time = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()

        # Handle dice rolling animation
        if self.rolling:
            if current_time - self.roll_time > 1000:  # Roll for 1 second
                self.rolling = False
                self.dice_value = random.randint(1, 6)

                # Start movement animation
                player = self.players[self.current_player]
                self.move_from = player.position
                self.move_to = min(player.position + self.dice_value, 100)
                self.move_steps = self.dice_value
                self.current_step = 0
                self.moving = True
                self.move_start_time = current_time
                self.message = f"{player.name} rolled a {self.dice_value}!"
            else:
                # Show random dice values during rolling
                self.dice_value = random.randint(1, 6)

        # Handle player movement animation
        elif self.moving:
            player = self.players[self.current_player]

            # Time to move to next step?
            if current_time - self.move_start_time > self.step_delay:
                self.current_step += 1
                self.move_start_time = current_time

                # Update player position for this step
                if self.current_step <= self.move_steps:
                    player.position = self.move_from + self.current_step
                    self.message = f"{player.name} moving... ({player.position})"

                # Finished moving all steps
                if self.current_step >= self.move_steps:
                    self.moving = False

                    # Check if landed on a snake
                    if player.position in SNAKES:
                        old_pos = player.position
                        player.position = SNAKES[player.position]
                        self.snake_ladder_message = f"{player.name} got bitten by a snake! Moved from {old_pos} to {player.position}"
                        self.message = self.snake_ladder_message

                    # Check if landed on a ladder
                    elif player.position in LADDERS:
                        old_pos = player.position
                        player.position = LADDERS[player.position]
                        self.snake_ladder_message = f"{player.name} climbed a ladder! Moved from {old_pos} to {player.position}"
                        self.message = self.snake_ladder_message

                    # Check if won
                    elif player.position == 100:
                        player.won = True
                        self.game_over = True
                        self.message = f"{player.name} won the game!"
                    else:
                        self.message = f"{player.name} moved to {player.position}"

                    # Switch to next player if game not over
                    if not self.game_over:
                        self.current_player = (self.current_player + 1) % len(self.players)

    def draw(self):
        # Fill the screen with white
        SCREEN.fill(WHITE)

        # Draw the board
        SCREEN.blit(self.board_image, (0, 0))

        # Draw sidebar background
        sidebar_rect = pygame.Rect(BOARD_SIZE, 0, SIDEBAR_WIDTH, HEIGHT)
        pygame.draw.rect(SCREEN, LIGHT_GRAY, sidebar_rect)
        pygame.draw.line(SCREEN, BLACK, (BOARD_SIZE, 0), (BOARD_SIZE, HEIGHT), 3)

        # 1. Draw current player indicator at the top
        if not self.game_over:
            player = self.players[self.current_player]

            # Create a background for the player turn indicator
            indicator_rect = pygame.Rect(BOARD_SIZE + 20, 40, SIDEBAR_WIDTH - 40, 60)
            pygame.draw.rect(SCREEN, MEDIUM_GRAY, indicator_rect)
            pygame.draw.rect(SCREEN, player.color, indicator_rect, 4)

            # Draw player name with their color
            player_text = TITLE_FONT.render(f"{player.name}'s turn", True, player.color)
            text_rect = player_text.get_rect(center=indicator_rect.center)
            SCREEN.blit(player_text, text_rect)

        # 2. Draw player positions below player turn
        pos_title = FONT.render("Player Positions", True, BLACK)
        pos_title_rect = pos_title.get_rect(center=(BOARD_SIZE + SIDEBAR_WIDTH//2, 140))
        SCREEN.blit(pos_title, pos_title_rect)

        pos_box = pygame.Rect(BOARD_SIZE + 20, 170, SIDEBAR_WIDTH - 40, 120)
        pygame.draw.rect(SCREEN, WHITE, pos_box)
        pygame.draw.rect(SCREEN, BLACK, pos_box, 2)

        for i, player in enumerate(self.players):
            # Player position info
            y_pos = pos_box.y + 25 + i * 40

            # Player color indicator
            pygame.draw.circle(SCREEN, player.color, (pos_box.x + 25, y_pos), 12)

            # Player name and position - use smaller font if needed
            player_info = f"{player.name}: Position {player.position}"
            info_text = FONT.render(player_info, True, BLACK)
            # Check if text is too wide for the box
            if info_text.get_width() > pos_box.width - 70:  # 70 = left margin + circle + padding
                info_text = SMALL_FONT.render(player_info, True, BLACK)
            SCREEN.blit(info_text, (pos_box.x + 50, y_pos - 12))

        # 3. Draw game messages (moved up from bottom)
        message_y = 330
        message_box = pygame.Rect(BOARD_SIZE + 20, message_y, SIDEBAR_WIDTH - 40, 160)
        pygame.draw.rect(SCREEN, WHITE, message_box)
        pygame.draw.rect(SCREEN, BLACK, message_box, 2)

        # Message box title
        msg_title = FONT.render("Game Messages:", True, BLACK)
        SCREEN.blit(msg_title, (message_box.x + 10, message_box.y + 10))

        # Wrap message text to fit in the box
        message_lines = self._wrap_text(self.message, SMALL_FONT, SIDEBAR_WIDTH - 60)
        for i, line in enumerate(message_lines):
            message_text = SMALL_FONT.render(line, True, BLACK)
            SCREEN.blit(message_text, (message_box.x + 10, message_box.y + 40 + i * 20))

        # 4. Draw dice and roll button at the bottom (moved down from middle)
        dice_y = HEIGHT - 220  # Moved up from HEIGHT - 180
        dice_size = 120  # Larger dice
        dice_pos = (BOARD_SIZE + (SIDEBAR_WIDTH - dice_size) // 2, dice_y)
        pygame.draw.rect(SCREEN, WHITE, (*dice_pos, dice_size, dice_size))
        pygame.draw.rect(SCREEN, BLACK, (*dice_pos, dice_size, dice_size), 3)

        # Draw dice value
        if self.dice_value > 0:
            dice_text = DICE_FONT.render(str(self.dice_value), True, BLACK)
            dice_rect = dice_text.get_rect(center=(dice_pos[0] + dice_size//2, dice_pos[1] + dice_size//2))
            SCREEN.blit(dice_text, dice_rect)

        # Draw "Roll Dice" button
        roll_rect = pygame.Rect(BOARD_SIZE + 40, dice_y + dice_size + 20, SIDEBAR_WIDTH - 80, 50)
        pygame.draw.rect(SCREEN, MEDIUM_GRAY, roll_rect)
        pygame.draw.rect(SCREEN, BLACK, roll_rect, 2)
        roll_text = FONT.render("ROLL DICE", True, BLACK)
        roll_text_rect = roll_text.get_rect(center=roll_rect.center)
        SCREEN.blit(roll_text, roll_text_rect)

        # Draw players on the board
        for player in self.players:
            if player.position > 0:
                pos = self.get_position_coordinates(player.position)
                # Offset slightly to avoid overlap
                if player == self.players[0]:
                    pos = (pos[0] - 10, pos[1])
                else:
                    pos = (pos[0] + 10, pos[1])
                pygame.draw.circle(SCREEN, player.color, pos, PLAYER_RADIUS)

                # Add pulsing highlight for current player
                if player == self.players[self.current_player] and not self.game_over:
                    pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) * 3 + 2  # Pulsing effect
                    pygame.draw.circle(SCREEN, player.color, pos, PLAYER_RADIUS + pulse, 2)

        # Draw game over message
        if self.game_over:
            overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 180))  # Semi-transparent white
            SCREEN.blit(overlay, (0, 0))

            game_over_text = TITLE_FONT.render("Game Over!", True, BLACK)
            text_rect = game_over_text.get_rect(center=(BOARD_SIZE//2, BOARD_SIZE//2 - 50))
            SCREEN.blit(game_over_text, text_rect)

            winner = next(player for player in self.players if player.won)
            winner_text = TITLE_FONT.render(f"{winner.name} Wins!", True, winner.color)
            winner_rect = winner_text.get_rect(center=(BOARD_SIZE//2, BOARD_SIZE//2))
            SCREEN.blit(winner_text, winner_rect)

            restart_text = FONT.render("Press R to restart", True, BLACK)
            restart_rect = restart_text.get_rect(center=(BOARD_SIZE//2, BOARD_SIZE//2 + 50))
            SCREEN.blit(restart_text, restart_rect)

    def _wrap_text(self, text, font, max_width):
        """Helper function to wrap text to fit within a certain width"""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            # If adding this word would make the line too long, start a new line
            if font.size(test_line)[0] > max_width:
                if current_line:  # Only add a line if there's text to add
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # If a single word is too long, just add it anyway
                    lines.append(word)
                    current_line = []
            else:
                current_line.append(word)

        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))

        return lines

def main():
    game = Game()
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                # Check if dice or roll button was clicked
                dice_y = HEIGHT - 220  # Updated to match the new position
                dice_size = 120
                dice_pos = (BOARD_SIZE + (SIDEBAR_WIDTH - dice_size) // 2, dice_y)

                # Dice area
                if (dice_pos[0] <= mouse_pos[0] <= dice_pos[0] + dice_size and
                    dice_pos[1] <= mouse_pos[1] <= dice_pos[1] + dice_size):
                    game.roll_dice()

                # Roll button area
                roll_rect = pygame.Rect(BOARD_SIZE + 40, dice_y + dice_size + 20, SIDEBAR_WIDTH - 80, 50)
                if roll_rect.collidepoint(mouse_pos):
                    game.roll_dice()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.game_over:
                    game = Game()  # Restart the game
                elif event.key == pygame.K_SPACE:  # Space bar to roll dice
                    if not game.rolling and not game.moving and not game.game_over:
                        game.roll_dice()

        game.update()

        # Draw everything
        game.draw()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()