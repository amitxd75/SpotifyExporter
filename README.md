# 🎵 SpotifyExporter

so Spotify held my entire music history hostage in like 47 JSON files and I had to write a whole tool to get it out. you're welcome.

this thing takes your Spotify data dump, cleans it up, deduplicates it, and spits out CSV files ready to import into **MetroList**. that's literally it. it does one job and it does it well.

---

## 🤔 why does this exist

because Spotify gives you your data as a pile of JSONs that look like this:

```json
{
  "ts": "2021-03-04T14:22:00Z",
  "master_metadata_track_name": "Blinding Lights",
  "master_metadata_album_artist_name": "The Weeknd",
  ...
}
```

...across like 10 separate files. for every song you've ever played. since the beginning of time. cool format bro.

MetroList does not accept "a pile of JSONs." MetroList accepts CSVs. hence: this tool.

---

## 📦 get your data from Spotify first

Spotify has two export options and one of them is a trap:

**"Account Data" (the fast one)**
takes 1–5 days. only has your last year of history. basically useless if you've been on Spotify for more than 12 months.

**"Extended Streaming History" (the real one)**
takes up to 30 days. has your ENTIRE lifetime history. every song since you made your account. yes, including that phase.

👉 go to [Spotify Privacy Settings](https://www.spotify.com/account/privacy/), scroll to **"Download your data"**, and request the extended one. then wait. and wait. go touch grass. it'll email you eventually.

extract the ZIP and you'll get a folder with files named `StreamingHistory0.json`, `StreamingHistory1.json`, etc. that's your input.

---

## ⚡ setup

```bash
# clone it
git clone https://github.com/amitxd75/SpotifyExporter
cd SpotifyExporter

# install deps (uv is faster, use it)
uv sync

# or if you're a pip person
pip install -r requirements.txt
```

---

## 🚀 usage

drop your Spotify data folder in the root (name it `SpotifyData`) and run:

```bash
python main.py
```

that's the whole thing. it'll print what it's doing, deduplicate everything, and dump the CSVs into `spotify_export/`.

### want more control?

```bash
python main.py \
  --input ./MySpotifyData \
  --output ./ready_for_metrolist \
  --chunk-size 1000 \
  --top-n 50 \
  --format csv
```

### all the flags:

| flag | short | env var | default | what it does |
|------|-------|---------|---------|--------------|
| `--input` | `-i` | `SPOTIFY_INPUT_FOLDER` | `SpotifyData` | where your Spotify JSONs live |
| `--output` | `-o` | `SPOTIFY_OUTPUT_DIR` | `spotify_export` | where the CSVs go |
| `--chunk-size` | `-s` | `SPOTIFY_CHUNK_SIZE` | `2000` | rows per file (MetroList has import limits) |
| `--top-n` | | | `50` | how big your top playlist is |
| `--format` | `-f` | | `csv` | `csv`, `json`, or `both` |

---

## ⚙️ .env file

if you're tired of typing the same flags every time, make a `.env`:

```env
SPOTIFY_INPUT_FOLDER=SpotifyData
SPOTIFY_OUTPUT_DIR=spotify_export
SPOTIFY_CHUNK_SIZE=2000
```

---

## 📂 what you get

after running, your output folder looks like this:

```
spotify_export/
├── all_unique_1.csv   ← your full library, deduped, chunk 1
├── all_unique_2.csv   ← chunk 2, etc.
├── top50_1.csv        ← your top 50 most played (with play counts)
└── top100_1.csv       ← top 100
```

`all_unique_*.csv` is what you import into MetroList. the top playlists are a bonus — good for flex purposes or actually building playlists.

each track has: `Title`, `Artist`, `Album`, `PlayedAt`, `MsPlayed`, `Type` (track vs podcast).

---

## ✨ features

- **deduplication** — if you played Blinding Lights 847 times, it still only shows up once in your library export. the play count is tracked separately in the top playlists.
- **chunking** — splits output into files of N rows so MetroList doesn't choke on a 12,000-row import
- **top playlists** — ranked by actual play count, not vibes
- **podcast support** — yes it handles those too, they just go in with `Type: podcast`
- **both export schemas** — works with the old Spotify format AND the new extended history format

---

## 🐛 something broke?

**"No StreamingHistory*.json files found"**
your input folder is wrong. double-check `--input` points to the extracted Spotify ZIP contents, not the ZIP itself.

**files are empty**
Spotify's extended export sometimes has entries with 0ms played (you skipped the song after 1 second). they're still included because technically you played it. deal with it.

**MetroList still complaining about the CSV**
try dropping `--chunk-size` to something smaller like `500`. some import wizards just can't handle big files.

---

made this because i switched to MetroList and wasn't about to lose 4 years of listening history. if it helps you too, nice.
