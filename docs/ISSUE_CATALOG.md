# Issue Catalog

Seed ideas for future GitHub issues. Split by theme with suggested difficulty
and acceptance criteria.

## Diagnostics
- **Add HTML diagnostic output** *(medium)* – Generate HTML report mirroring the
  text layout. Include CSS for readability.
- **JSON export for diagnostics** *(medium)* – Emit structured JSON summarising
  each section for downstream tooling.
- **Configurable command sets** *(hard)* – Allow users to define YAML/JSON files
  that override default diagnostics.

## Audit
- **Add Debian/Ubuntu heuristics** *(medium)* – Inspect `apt-mark showmanual` and
  `dpkg -l` for stale packages, services, etc.
- **Alert thresholds in config** *(easy)* – Let users configure disk/memory
  thresholds for warnings vs. critical findings.

## Cleaning
- **Interactive cleanup prompt** *(medium)* – Provide `cadmu clean --interactive`
  to choose which actions run.
- **Cache usage summariser** *(easy)* – Show total reclaimed space after
  executing actions.

## Maintenance
- **SMART long test scheduler** *(easy)* – Add optional long SMART test task.
- **Systemd timer template** *(medium)* – Ship sample timer + service file to run
  `cadmu maintain --execute` weekly.

## Updating
- **Add zypper-specific recommendations** *(medium)* – Provide heuristics similar
  to Arch for openSUSE.
- **Update dry-run mode** *(easy)* – Display approximate download sizes if the
  package manager supports it.

## Arch Toolkit
- **AUR helper comparison** *(medium)* – Compare foreign packages between `paru`
  and `yay` to highlight duplicates.
- **Vulnerability feed integration** *(hard)* – Cross-reference CVE data (e.g.
  via Arch Security Tracker) with explicit packages.

## Documentation
- **Render docs with MkDocs** *(medium)* – Publish docs site to GitHub Pages.
- **Video walkthrough** *(easy)* – Record quick screencast demonstrating each
  CLI command.

## Automation
- **Add Dependabot** *(easy)* – Configure for Python and GitHub Actions updates.
- **Coverage upload** *(easy)* – Integrate Codecov and add badge to README.

When creating actual issues, link back to this catalog and move items to the
Roadmap once scheduled.
