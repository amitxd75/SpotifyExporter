"""
main.py
-----------------
Converts a Spotify data export (JSON) into clean, deduplicated CSV/JSON packs.

Spotify export structure expected:
    SpotifyData/
        StreamingHistory0.json
        StreamingHistory1.json
        ...

Each file is a JSON array of objects with either:
  - trackName / artistName  (music)
  - episodeName / podcastName  (podcasts)

Usage:
    python spotify_export.py --input SpotifyData --output spotify_export
"""

import json
import os
from collections import Counter
from glob import glob
from typing import List, Literal

import pandas as pd
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

load_dotenv()

app = typer.Typer(
    help="Spotify Export Processor: Convert Spotify data exports to CSV/JSON packs."
)
console = Console()

# Supported output formats
OutputFormat = Literal["csv", "json", "both"]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────


def save_chunks(
    tracks: List[dict],
    base_name: str,
    output_dir: str,
    chunk_size: int,
    fmt: OutputFormat = "csv",
) -> int:
    """
    Split `tracks` into chunks of `chunk_size` and save each chunk to disk.

    Args:
        tracks:     Full list of track dicts.
        base_name:  File name prefix (e.g. "all_unique", "top50").
        output_dir: Destination directory (created if absent).
        chunk_size: Max records per file.
        fmt:        "csv", "json", or "both".

    Returns:
        Number of files written.
    """
    os.makedirs(output_dir, exist_ok=True)
    files_written = 0

    for i in range(0, len(tracks), chunk_size):
        chunk = tracks[i : i + chunk_size]
        chunk_index = i // chunk_size + 1
        df = pd.DataFrame(chunk)

        if fmt in ("csv", "both"):
            path = os.path.join(output_dir, f"{base_name}_{chunk_index}.csv")
            df.to_csv(path, index=False)
            console.print(f"  [dim]💾 Saved:[/dim] [green]{path}[/green]")
            files_written += 1

        if fmt in ("json", "both"):
            path = os.path.join(output_dir, f"{base_name}_{chunk_index}.json")
            df.to_json(path, orient="records", indent=2, force_ascii=False)
            console.print(f"  [dim]💾 Saved:[/dim] [green]{path}[/green]")
            files_written += 1

    return files_written


def normalize(track: dict) -> tuple:
    """Return a lowercase (title, artist) key used for deduplication."""
    return (track["Title"].strip().lower(), track["Artist"].strip().lower())


def deduplicate(tracks: List[dict]) -> List[dict]:
    """
    Remove duplicate tracks by (Title, Artist), keeping the first occurrence.
    Preserves original ordering.
    """
    seen: set = set()
    unique: List[dict] = []

    for track in tracks:
        key = normalize(track)
        if key not in seen:
            seen.add(key)
            unique.append(track)

    return unique


# ─────────────────────────────────────────────
# PARSING
# ─────────────────────────────────────────────


def parse_streaming_history(input_folder: str) -> List[dict]:
    """
    Load and parse all StreamingHistory*.json files in `input_folder`.

    Handles two Spotify export schemas:
      - Legacy:   { "trackName", "artistName", "endTime", "msPlayed" }
      - Extended: { "master_metadata_track_name", "master_metadata_album_artist_name",
                    "master_metadata_album_album_name", "ts", "ms_played" }

    Podcast entries (episodeName / episode_name) are included as well.

    Returns:
        List of normalised track dicts:
        { Title, Artist, Album, PlayedAt, MsPlayed, Type }
    """
    files = sorted(glob(os.path.join(input_folder, "StreamingHistory*.json")))

    if not files:
        console.print(
            f"[bold red]Error:[/bold red] No StreamingHistory*.json files found in '{input_folder}'"
        )
        raise typer.Exit(code=1)

    tracks: List[dict] = []

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            # ── Extended music schema ──────────────────────────────────────
            if item.get("master_metadata_track_name"):
                tracks.append(
                    {
                        "Title": item["master_metadata_track_name"],
                        "Artist": item.get("master_metadata_album_artist_name", ""),
                        "Album": item.get("master_metadata_album_album_name", ""),
                        "PlayedAt": item.get("ts", ""),
                        "MsPlayed": item.get("ms_played", 0),
                        "Type": "track",
                    }
                )

            # ── Legacy music schema ────────────────────────────────────────
            elif item.get("trackName"):
                tracks.append(
                    {
                        "Title": item["trackName"],
                        "Artist": item.get("artistName", ""),
                        "Album": "",
                        "PlayedAt": item.get("endTime", ""),
                        "MsPlayed": item.get("msPlayed", 0),
                        "Type": "track",
                    }
                )

            # ── Extended podcast schema ────────────────────────────────────
            elif item.get("episode_name"):
                tracks.append(
                    {
                        "Title": item["episode_name"],
                        "Artist": item.get("podcast_name", ""),
                        "Album": "",
                        "PlayedAt": item.get("ts", ""),
                        "MsPlayed": item.get("ms_played", 0),
                        "Type": "podcast",
                    }
                )

            # ── Legacy podcast schema ──────────────────────────────────────
            elif item.get("episodeName"):
                tracks.append(
                    {
                        "Title": item["episodeName"],
                        "Artist": item.get("podcastName", ""),
                        "Album": "",
                        "PlayedAt": item.get("endTime", ""),
                        "MsPlayed": item.get("msPlayed", 0),
                        "Type": "podcast",
                    }
                )

    return tracks


# ─────────────────────────────────────────────
# TOP TRACKS
# ─────────────────────────────────────────────


def build_top_tracks(tracks: List[dict], top_n: int) -> List[dict]:
    """
    Count how many times each (Title, Artist) pair appears and return
    the top `top_n` entries, sorted by play count descending.

    The returned dicts include a `PlayCount` field so the caller can see
    popularity at a glance.
    """
    counter: Counter = Counter((t["Title"], t["Artist"]) for t in tracks)
    sorted_tracks = counter.most_common(top_n)  # already sorted descending

    return [
        {
            "Title": title,
            "Artist": artist,
            "Album": "",  # Not available from play-count aggregation
            "PlayCount": count,
        }
        for (title, artist), count in sorted_tracks
    ]


# ─────────────────────────────────────────────
# SUMMARY TABLE
# ─────────────────────────────────────────────


def print_summary(
    history: List[dict], unique_tracks: List[dict], files_written: int
) -> None:
    """Render a Rich summary table after processing completes."""
    total_ms = sum(t.get("MsPlayed", 0) for t in history)
    total_hours = total_ms / 3_600_000

    track_entries = [t for t in history if t.get("Type") == "track"]
    podcast_entries = [t for t in history if t.get("Type") == "podcast"]

    table = Table(title="📊 Export Summary", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim", width=28)
    table.add_column("Value", justify="right")

    table.add_row("Total play events", str(len(history)))
    table.add_row("  ↳ Music", str(len(track_entries)))
    table.add_row("  ↳ Podcasts", str(len(podcast_entries)))
    table.add_row("Unique tracks/episodes", str(len(unique_tracks)))
    table.add_row("Total listening time", f"{total_hours:,.1f} hours")
    table.add_row("Files written", str(files_written))

    console.print()
    console.print(table)


# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────


@app.command()
def main(
    input_folder: str = typer.Option(
        os.getenv("SPOTIFY_INPUT_FOLDER", "SpotifyData"),
        "--input",
        "-i",
        help="Folder containing Spotify JSON export files.",
    ),
    output_dir: str = typer.Option(
        os.getenv("SPOTIFY_OUTPUT_DIR", "spotify_export"),
        "--output",
        "-o",
        help="Directory where output files will be saved.",
    ),
    chunk_size: int = typer.Option(
        int(os.getenv("SPOTIFY_CHUNK_SIZE", 2000)),
        "--chunk-size",
        "-s",
        help="Number of tracks per output file.",
    ),
    top_n: int = typer.Option(
        50,
        "--top-n",
        help="Size of the 'top tracks' playlist (e.g. 50 → Top 50).",
    ),
    fmt: str = typer.Option(
        "csv",
        "--format",
        "-f",
        help="Output format: csv | json | both",
    ),
) -> None:
    """
    Process a Spotify data export into clean, deduplicated output files.

    Steps:
      1. Parse all StreamingHistory*.json files.
      2. Deduplicate by (Title, Artist).
      3. Save the full unique library in chunks.
      4. Build and save top-N (and top-100) playlists with play counts.
      5. Print a summary.
    """
    # Validate format option early so the user gets a clear error
    if fmt not in ("csv", "json", "both"):
        console.print(
            "[bold red]Error:[/bold red] --format must be one of: csv, json, both"
        )
        raise typer.Exit(code=1)

    console.print("[bold green]🚀 Spotify Export Processor[/bold green]\n")
    files_written = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,  # clears progress bar after completion
    ) as progress:
        # ── Step 1: Parse ──────────────────────────────────────────────────
        task = progress.add_task("📥 Parsing streaming history…", total=None)
        history = parse_streaming_history(input_folder)
        progress.update(task, completed=True)

    # Print parse results outside the progress context so they aren't erased
    console.print(f"  [blue]Total play events:[/blue] {len(history)}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        # ── Step 2: Deduplicate ────────────────────────────────────────────
        task = progress.add_task("🧹 Removing duplicates…", total=None)
        unique_tracks = deduplicate(history)
        progress.update(task, completed=True)

    console.print(f"  [blue]Unique tracks/episodes:[/blue] {len(unique_tracks)}")

    # ── Step 3: Full library chunks ────────────────────────────────────────
    console.print(f"\n[bold]📦 Saving full library (chunks of {chunk_size})…[/bold]")
    files_written += save_chunks(
        unique_tracks, "all_unique", output_dir, chunk_size, fmt
    )

    # ── Step 4: Top-N playlists ────────────────────────────────────────────
    console.print("\n[bold]🔥 Building Top Playlists…[/bold]")

    # Always produce top-100; also produce top-N if it differs from 100
    playlist_sizes = sorted({top_n, 100})
    for n in playlist_sizes:
        top_tracks = build_top_tracks(history, n)
        console.print(f"  Top {n} ({len(top_tracks)} tracks)")
        files_written += save_chunks(top_tracks, f"top{n}", output_dir, chunk_size, fmt)

    # ── Step 5: Summary ───────────────────────────────────────────────────
    print_summary(history, unique_tracks, files_written)
    console.print("[bold green]✅ Done![/bold green]")


if __name__ == "__main__":
    app()
