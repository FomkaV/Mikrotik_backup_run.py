#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import paramiko
import time
import datetime
import subprocess
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="MikroTik backup script via SSH/SFTP"
    )
    parser.add_argument("--ip", dest="ip_address", required=True, help="MikroTik IP address")
    parser.add_argument("--port", dest="ssh_port", type=int, default=22, help="SSH port (default: 22)")
    parser.add_argument("--user", dest="ssh_user", required=True, help="SSH username")
    parser.add_argument("--passwd", dest="ssh_passwd", required=True, help="SSH password")
    parser.add_argument("--days", dest="days_to_del", type=int, default=7,
                        help="Delete backups older than N days (default: 7)")
    parser.add_argument("--dir", dest="backup_dir", default="/opt/mikrotik_backup/",
                        help="Local backup directory (default: /opt/mikrotik_backup/)")
    return parser.parse_args()


def del_old(bak_dir, day_to_del, dev_name):
    """
    Delete old MikroTik backups matching pattern {dev_name}* older than {day_to_del} days in {bak_dir}.
    """
    pattern = f"{dev_name}*"
    try:
        print(f"[~] Deleting old files in {bak_dir} older than {day_to_del} days matching: {pattern}")
        subprocess.run(
            ["find", bak_dir, "-name", pattern, "-mtime", f"+{day_to_del}", "-exec", "rm", "-f", "{}", ";"],
            check=True
        )
        print("[✓] Old files deleted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[!] Error while deleting old files: {e}")


def main():
    args = parse_args()

    # Ensure backup directory exists
    os.makedirs(args.backup_dir, exist_ok=True)

    # Date
    now = datetime.datetime.now()
    Date = now.strftime("%d%m%y")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"[+] Connecting to MikroTik {args.ip_address}:{args.ssh_port} ...")
        ssh.connect(
            hostname=args.ip_address,
            port=args.ssh_port,
            username=args.ssh_user,
            password=args.ssh_passwd,
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )
        print("[+] Connected via SSH.")

        # Get MikroTik identity
        stdin, stdout, stderr = ssh.exec_command("/system identity print")
        Mikrotik_NAME = stdout.read().decode()

        identity = None
        for line in Mikrotik_NAME.splitlines():
            if "name:" in line:
                identity = line.split("name:")[1].strip()
                print("[+] MikroTik identity: " + identity)
                break
        else:
            raise Exception("[-] Could not find 'name:' in identity output.")
        Mikrotik_NAME = identity.replace(" ", "_")

        # File names
        REMOTE_BACKUP_FILE = f"{Mikrotik_NAME}.backup"
        LOCAL_SAVE_PATH = os.path.join(args.backup_dir, f"{REMOTE_BACKUP_FILE}{Date}")
        print("[+] Save file to: " + LOCAL_SAVE_PATH)

        # Make backup
        print("[+] Sending backup command...")
        stdin, stdout, stderr = ssh.exec_command(f"/system backup save name={Mikrotik_NAME}")
        time.sleep(3)

        error = stderr.read().decode()
        if error:
            raise Exception(f"[!] Error from MikroTik: {error.strip()}")

        print("[+] Backup command executed successfully.")

        # Download with SFTP
        print("[+] Opening SFTP session...")
        sftp = ssh.open_sftp()
        remote_path = f"/{REMOTE_BACKUP_FILE}"
        print(f"[+] Downloading {remote_path} → {LOCAL_SAVE_PATH}")
        sftp.get(remote_path, LOCAL_SAVE_PATH)
        sftp.close()

        print(f"[✓] Backup downloaded successfully to: {LOCAL_SAVE_PATH}")

        # Delete old backups
        del_old(args.backup_dir, args.days_to_del, Mikrotik_NAME)

    except Exception as e:
        print(f"[!] ERROR: {e}")

    finally:
        ssh.close()
        print("[+] SSH connection closed.")


if __name__ == "__main__":
    main()