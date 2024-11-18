# SPDX-FileCopyrightText: 2024 Agathe Porte <microjoe@microjoe.org>
#
# SPDX-License-Identifier: GPL-3.0-only

from datetime import datetime

from prometheus_hdparm_exporter import main


def test_is_sata_disk():
    assert main.is_sata_disk("/dev/sda")
    assert not main.is_sata_disk("/dev/nvme0n1")


def test_parse_hdparm_output():
    text = """
/dev/sda:
 drive state is:  standby

/dev/sdb:
 SG_IO: bad/missing sense data, sb[]: xx yy
 drive state is:  active/idle
"""

    expected = [
        ("/dev/sda", "standby"),
        ("/dev/sdb", "active/idle"),
    ]

    assert main.parse_hdparm_output(text) == expected


def test_format_prometheus_disk_power_status():
    epoch = datetime.fromtimestamp(42, None)

    assert (
        main.format_prometheus_disk_power_status(
            ("/dev/sda", "standby"),
            epoch,
        )
        == 'hdparm_disk_power_status{disk="/dev/sda",status="standby"} 1 42'
    )

    assert (
        main.format_prometheus_disk_power_status(
            ("/dev/sda", "active/idle"),
            epoch,
        )
        == 'hdparm_disk_power_status{disk="/dev/sda",status="active/idle"} 1 42'
    )
