# Download News In Slow French Flashcards to Anki

Lovely little script to pull the latest ["News In Slow French"](newsinslowfrench.com) flashcards into [Anki]().

## Getting started

Bootstrap:
```bash
poetry install
playwright install
```

Configure:
```
# settings.toml
[anki]
deck_name = "Français"
collection_fp = "path/to/your/collection.anki2"

# .secrets.toml
[nisf]
username = "your@email.com"
password = "password123"
```

Run it:
```bash
poetry run pull_flashcards
```
