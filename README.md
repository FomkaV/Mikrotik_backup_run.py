# MikroTik Backup Script

This project contains a Python script to automatically back up MikroTik router configurations over SSH.

It uses the [`paramiko`](https://www.paramiko.org/) library to connect, run backup/export commands, and save the resulting files locally.

---

## Features

- Connects to MikroTik routers via SSH
- Executes backup commands (`/system backup save` and `/export`)
- Saves backups in a specified directory with timestamped filenames
- Easy to extend for multiple routers

---

## Requirements

- Python 3.x
- `paramiko` library

Install dependencies:

```bash
pip install paramiko


## Useage
```bash
./mikrotik_backup.py \
  --ip 192.168.88.1 \
  --port 22 \
  --user admin \
  --passwd secret123 \
  --days 14 \
  --dir /opt/mikrotik_backup/
