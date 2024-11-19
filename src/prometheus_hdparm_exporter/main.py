# SPDX-FileCopyrightText: 2024 Agathe Porte <microjoe@microjoe.org>
#
# SPDX-License-Identifier: GPL-3.0-only

import re
import subprocess
import sys
from datetime import datetime
from typing import Optional, Tuple
from wsgiref.simple_server import make_server

TEXT_HEADERS = [("Content-Type", "text/plain; charset=utf-8")]


# Utility functions


def utf8(*lines: str) -> list[bytes]:
    return [line.encode("utf-8") + b"\n" for line in lines]


def parse_hdparm_output(text: str) -> list[Tuple[str, str]]:
    """Parse the output of ``hdparm -C`` command.

    Example output that this command can parse::

        dev/sda:
         drive state is:  standby

        /dev/sdb:
         drive state is:  active/idle

    Returns:
      List of tuples (disk, state).

    """
    out = []
    for chunck in text.split("\n\n"):
        rgx = re.compile("(.*):\n.* drive state is:\\s+(.*)", re.MULTILINE | re.DOTALL)
        rgx_match = rgx.match(chunck)
        if rgx_match:
            out.append((rgx_match.group(1).strip(), rgx_match.group(2).strip()))

    return out


def format_prometheus_disk_power_status(
    power_status: Tuple[str, str], time: Optional[datetime] = None
) -> str:
    """Format disk status to Prometheus line."""
    disk, status = power_status

    if time is None:
        time = datetime.now()

    timestamp = int(time.timestamp() * 1000.0)
    return (
        "hdparm_disk_power_status{"
        f'disk="{disk}",'
        f'status="{status}"'
        "} "
        "1 "  # Default value, this metric uses labels
        f"{timestamp}"
    )


# Error handling functions


def print_failed_process(process):
    print("Error running process", process.args)
    print("=== stdout ===")
    print(process.stdout.decode("utf-8"))
    print("=== stderr ===")
    print(process.stderr.decode("utf-8"))


def send_internal_error(start_response, e):
    """Send an HTTP 500 Internal Server Error to the user."""
    print(e)
    start_response("500 Internal Server Error", TEXT_HEADERS)
    return utf8(str(e), "See server logs for additional details.")


# Disk functions


def disks() -> list[str]:
    """Returns all disks found of the system according to lsblk."""
    process = subprocess.run(
        [
            "lsblk",
            "--list",
            "--nodeps",
            "--noheadings",
            "--output",
            "path",
        ],
        capture_output=True,
        check=True,
    )

    if process.returncode != 0:
        print_failed_process(process)
        raise RuntimeError(f"process lsblk returned value {process.returncode}")

    return process.stdout.decode("utf-8").split("\n")


def is_sata_disk(disk: str) -> bool:
    """Checks if a disk is a SATA disk."""
    return disk.startswith("/dev/sd")


def sata_disks() -> list[str]:
    """Returns all SATA disks found of the system according to lsblk."""
    return [d for d in disks() if is_sata_disk(d)]


def disks_status(disks: list[str]) -> list[Tuple[str, str]]:
    """Query disks status using hdparm (requires root)."""
    process = subprocess.run(["hdparm", "-C", *disks], capture_output=True)

    if process.returncode != 0:
        print_failed_process(process)
        raise RuntimeError(f"process hdparm returned value {process.returncode}")

    status_text = process.stdout.decode("utf-8")

    return parse_hdparm_output(status_text)


# Main WSGI function


def application(_, start_response) -> list[bytes]:
    response = ""

    try:
        status = disks_status(sata_disks())
    except RuntimeError as e:
        return send_internal_error(start_response, e)

    response = "\n".join([format_prometheus_disk_power_status(s) for s in status])

    start_response("200 OK", TEXT_HEADERS)

    return utf8(response)


# If run as main, start the builtin Python WSGI server to serve the app.


def main():
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} HOST PORT", file=sys.stderr)
        sys.exit(2)

    host, port = (sys.argv[1], int(sys.argv[2]))

    with make_server(host, port, application) as httpd:
        print("Serving HTTP on port 8000...")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
