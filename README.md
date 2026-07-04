# ffxiv-raid-analyzer

CLI tool that logs into FFLogs, pulls fight data for a report, and prints raid-tracking
stats (pulls, clears, deaths, damage downs, mitigation casts) for pasting into a
spreadsheet.

## Setup

1. `uv sync`
2. Create an FFLogs API client at https://www.fflogs.com/api/clients/ with redirect URI
   `http://localhost:8765/callback`.
3. Copy `.env.example` to `.env` and fill in `FFLOGS_CLIENT_ID` / `FFLOGS_CLIENT_SECRET`
   from that client.
4. Edit `raid_analyzer/constants.py` to set the mitigation and damage-down ability IDs you
   want tracked. See "Finding ability IDs" below for how to find them.

## Usage

```
uv run python main.py login
uv run python main.py analyze <report code or fflogs.com URL>
```

`login` opens a browser to authorize with FFLogs and caches the resulting token under
`~/.config/ffxiv-raid-analyzer/` (override the location with `RAID_ANALYZER_CONFIG_DIR`).

`analyze` shows pulls/clears for the report, lets you optionally pick a specific boss to
scope the rest of the stats to, then prints deaths/damage-down and mitigation tables and
copies the same data as TSV to your clipboard for pasting into a spreadsheet.

_Note_: FFLogs archives reports after some time, and pulling fight data from an archived
report requires an active FFLogs subscription.

## Finding ability IDs

`MITIGATION_ABILITIES` and `DAMAGE_DOWN_ABILITIES` in `raid_analyzer/constants.py` are
`label -> FFLogs ability ID` dicts. FFLogs has no built-in concept of "this is a
mitigation" or "this is the damage-down debuff", so these are picked and entered by hand.
Use the `find-ability` command against any report that contains a cast/application of the
ability you're looking for:

```
uv run python main.py find-ability <report code or URL> <search text>
```

For example, `uv run python main.py find-ability 9mtdaRFcMKvV4khn reprisal` prints every
ability with "reprisal" in its name along with its ID, one per line.

Some abilities show up twice under similar names: a lower "cast" ID (the ability itself)
and a higher, `100xxxx`-prefixed "debuff" ID (the effect it applies to whoever it hits).
Use the cast ID for `MITIGATION_ABILITIES` and the debuff's own ID for
`DAMAGE_DOWN_ABILITIES`.
