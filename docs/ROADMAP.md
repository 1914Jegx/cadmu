# CADMU Roadmap

## Near Term (0.2.x)
- **Package export formats**: JSON/Markdown exports for diagnostics and audits.
- **Plugin interface**: Lightweight hooks so distributions can register modules
  without modifying core files.
- **Interactive cleanups**: Optional prompt mode (choose which actions to run).

## Mid Term (0.3.x)
- **Additional distro support**: Debian/Ubuntu (`apt`), Fedora (`dnf`), and
  openSUSE (`zypper`) specific heuristics similar to the Arch pacman module.
- **Configuration file support**: YAML/JSON config to customise command sets,
  thresholds, and output directories.
- **HTML reporting**: Generate fully formatted HTML diagnostics for easier
  sharing.

## Long Term
- **Daemonised monitoring**: Optional timer/service that runs selected audits
  automatically and publishes notifications.
- **Remote orchestration**: Ability to dispatch commands to remote hosts via
  SSH, aggregating results into a single report.
- **Extensible UI**: Text-based dashboard (e.g. Textual) for browsing history of
  diagnostics and audit findings.
