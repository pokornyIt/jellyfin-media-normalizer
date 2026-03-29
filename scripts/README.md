
# README - Script Utilities

This folder contains helper scripts for exporting a filesystem structure and recreating it elsewhere.

## 1. nas_scan.sh

Scans the current directory recursively and generates:
- folders.txt: all folders as relative paths
- files.txt: all files as relative paths

The script ignores Synology metadata paths starting with @.

### Usage

```bash
cd /volume1/my-data
bash /path/to/nas_scan.sh
```

### Behavior Summary

| Situation                  | Behavior             |
| -------------------------- | -------------------- |
| Folder is found            | Added to folders.txt |
| File is found              | Added to files.txt   |
| Path starts with @         | Ignored              |
| Output files already exist | Overwritten          |

### Example Terminal Output

```text
================================================
  NAS Scan - 2026-03-21 18:30:00
  Scan root: /volume1/my-data
================================================
Folders saved to: /volume1/my-data/folders.txt
Files saved to: /volume1/my-data/files.txt

Done!
```

## 2. create_structure.sh

Reads folders.txt and files.txt and recreates the directory tree with empty files in the current working directory.
This is useful for test environment setup, dry-run planning, or project structure bootstrapping.

### Usage

```bash
cd /target/where/you/want/the/structure
bash /path/to/create_structure.sh
```

### Behavior Summary

| Situation                            | Behavior                                     |
| ------------------------------------ | -------------------------------------------- |
| Folder does not exist                | Creates it, including parent path (mkdir -p) |
| Folder already exists                | Skips it without failing                     |
| File does not exist                  | Creates an empty file (touch)                |
| File already exists                  | Skips it without failing                     |
| Parent folder of a file is missing   | Creates parent folder automatically          |
| Empty lines or lines starting with # | Ignored                                      |

### Example Terminal Output

```text
[ 1/2 ] Creating folders...
  Created:       Movies/Action
  Already exists: Movies/Drama
  ...

[ 2/2 ] Creating files...
  Created:       Movies/Action/some_movie.mkv
  ...

================================================
  Summary
================================================
  Folders - created: 42  |  skipped: 5
  Files   - created: 198 |  skipped: 2
================================================
```
