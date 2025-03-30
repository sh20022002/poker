# Texas Hold’em Probability Project

This project is a **Pygame** application that displays a Texas Hold’em table with:

- A **background image** stretched to fill the window.
- A **sorted deck** of playing cards placed in rows and columns.
- **Placeholders** for the hero’s (player’s) hole cards (2) and community cards (5).
- A **Monte Carlo**-based probability calculator that shows the hero’s approximate chance to win against a chosen number of opponents, given the known cards on the table.

---

## Screenshot

Below is a screenshot of the running application showing the background image, placeholders (in white and yellow boxes at the top), UI buttons (Players +, -, Reset), and the deck layout below:

![Texas Hold’em Probability in Action]('Screenshot 2025-03-30 174559.png')

1. **Players**: 2 → The current number of players in the game.  
2. **+ / -**: Increase or decrease the total number of players (2–10).  
3. **Reset**: Clears all selections and returns the deck to its initial state.  
4. **White Placeholders**: Slots for hero hole cards (2).  
5. **Yellow Placeholders**: Slots for community cards (up to 5).  
6. **Win%**: Shows the hero’s approximate probability of eventually winning against the other players.

---

## How It Works

1. **Deck Sorting**  
   - All `.png` (or `.svg`) card images are stored in a folder.
   - The code parses each filename to extract its suit (clubs, diamonds, hearts, spades) and rank (2,3,4,5,6,7,8,9,10,jack,queen,king,ace).
   - Cards are sorted in ascending order of suits (rows) and ranks (columns).

2. **Card Placement & Selection**  
   - By default, all cards are displayed in the deck region (bottom).
   - Click a card from the deck:
     1. If the hero has fewer than 2 hole cards, the card goes there.
     2. Otherwise, if the community has fewer than 5 cards, the card goes into the next free community slot.
   - To **unselect** a card (return it to the deck), click on the placeholder containing that card.

3. **Opponents & Probability**  
   - Use the **+** or **-** button to set the total number of players (including the hero).
   - The script runs a **Monte Carlo** simulation (`hero_win_probability`) each time cards are added/removed. It deals random hole cards to opponents and random unknown community cards, then evaluates how often the hero’s final 5-card hand is best.

4. **Reset**  
   - Clicking **Reset** clears all selections: hero hole cards, community cards, and unmarks any deck picks, returning the entire deck to the main layout.

---

## Installation

1. **Clone** or download this repository.
2. **Install Python** (3.7+ recommended).
3. **Install Pygame**:
   ```bash
   pip install pygame
