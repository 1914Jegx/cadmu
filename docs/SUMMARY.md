# CADMU in Plain Language

CADMU keeps Linux machines tidy and healthy. It gives you one command with a few
subcommands. Each subcommand either prints a report or offers optional fixes—you
always stay in control.

## How It Works

- **Diagnostics (`cadmu diag`)** gather facts about the machine. Think of it as a
  medical check-up: OS version, hardware, services, network, caches, logs.
- **Audit (`cadmu audit`)** reads the numbers and highlights problems (disk space
  pressure, RAM shortages, failed services, outdated packages on Arch).
- **Clean (`cadmu clean`)** lists cache-purge actions by risk level. Run it with
  `--execute` to actually remove artefacts.
- **Maintain (`cadmu maintain`)** describes routine chores (journal vacuuming,
  SMART tests, Btrfs balance). Execute them when you are ready.
- **Update (`cadmu update`)** knows which package managers are installed and
  prints the correct upgrade order.
- **Arch (`cadmu arch`)** dives deep into pacman data. Use
  `cadmu arch --pacman --explicit-installed --recommendations` to see a table of
  explicitly installed packages with tailored guidance.

Under the hood CADMU shells out to familiar tools (`pacman`, `journalctl`,
`systemctl`, etc.). Every command is wrapped so the program records what was
run and whether it succeeded. If a tool is missing, CADMU tells you instead of
crashing.

## Key Ideas Simplified

- **Command Runner**: a smart `subprocess.run`. It knows when to add `sudo` and
  how to skip optional features politely.
- **Reports**: plain text files with clear sections. Easy to read and easy to
  share.
- **Recommendations**: simple heuristics derived from package metadata:
  repository → stability, dependency count → difficulty, install date → age.

## When to Use What

- Running upgrades? Start with `cadmu diag --no-optional` to get a quick status,
  follow with `cadmu audit`, then run `cadmu update --execute --sudo`.
- Disk space concerns? `cadmu clean` shows safe cache removals. If you need more
  detail, `cadmu arch ...` tells you which explicit packages are old or risky.
- Teaching a teammate? Point them to `docs/STUDY_GUIDE.md` for a slow walk-through.

## Takeaways

CADMU’s job is to surface information in a predictable format and give you
confidence about next steps. You choose when to act. The CLI never hides what it
is doing, and every change-oriented command has a preview mode.
