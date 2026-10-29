# Snake: Relapse Edition

A polished desktop Snake game built with Python and Pygame. It keeps the original
relapse-themed concept while adding a modern arcade UI, menu/pause/game-over
states, score and high-score tracking, safer movement, and optional online music.

## Features

- Dark arcade interface with a dedicated score panel
- Keyboard controls: arrows or WASD
- Pause/resume and restart flow
- Speed increases as the score grows
- Food never spawns inside the snake
- Persistent high score stored in the user's home directory
- Online game-over music fetched into memory (no separate MP3 download required)
- Continues to work if online music is unavailable

## Requirements

- Python 3.10+
- Pygame 2.5+

## Run locally

```bash
python -m pip install -r requirements.txt
python isnik.py
```

## Controls

| Key | Action |
| --- | --- |
| Arrow keys / WASD | Move |
| P | Pause / resume |
| Enter / Space | Start or continue |
| R | Retry after game over |
| Esc | Return to menu; quit from the menu |

## Online music

The game fetches `kanibalismo.mp3` from this repository's raw GitHub URL and
passes the audio bytes to Pygame through an in-memory buffer. It does not save
the audio file to the player's computer. An internet connection is needed for
the music, and playback depends on the audio device and the remote file being
available. The game itself remains playable if audio loading fails.

If you redistribute this project, make sure you have permission to distribute
the music recording and any lyrics included with it.

## Project structure

```text
snake-relapse-professional/
├── isnik.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Troubleshooting

- **Pygame is missing:** run `python -m pip install -r requirements.txt`.
- **No music:** check your internet connection and system audio. The game does
  not require music to run.
- **Window does not open:** run the command from a desktop Python environment
  with graphics support; Pygame windows generally cannot open in a headless shell.
