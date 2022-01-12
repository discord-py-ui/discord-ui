# Discord UI

## 5.2.0

### Breaking changes

- `delete_unused` keyword for `Slash` class and `Slash.commands.sync`.

### Changed

- `Slash.commands.sync` should be way faster now since it uses bulk requests now.
Note that these will automatically overwrite all commands. This method should take about 1 to 2 seconds now (if no ratelimit occurs)

- Improved `Slash.commands.nuke`. This method should take about under 1 seconds (if no ratelimit occurs)

## 5.1.6
### Fixed

- guild permissions not being applied due to an comparison issue with the api permissions and the local guild permissions