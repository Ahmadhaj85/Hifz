# مكتبة الحفظ (Hifz Library)

Offline PWA for daily spaced-repetition review of books and topics. Hosted on GitHub Pages.

## Adding a book (for Claude or by hand)
1. Put the deck file in `decks/<id>.json`:
   `{"id","v","title","author","ch":[{"t","secs":[{"t","b":[bullets, "§subheading"],"c":[card indices]}]}],"cards":[[cardId,question,answer]]}`
2. Add an entry to `decks/index.json` → `decks[]`: `{"id","v","title","author","file","cards"}`.
3. To update an existing deck, keep `id` and increase `v`. Keep card ids stable so progress is kept.
4. Commit to `main`. The app fetches `decks/index.json` on every launch and installs new or updated decks.

Plain-text decks can also be imported from the app (Library → Import):
```
% Title
# Chapter
## Section
- summary point
? question || answer
```
Progress lives on the device (localStorage); decks in IndexedDB. Library → Backup exports both.
