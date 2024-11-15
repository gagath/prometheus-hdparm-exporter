<!--
SPDX-FileCopyrightText: 2024 Agathe Porte <microjoe@microjoe.org>

SPDX-License-Identifier: GPL-3.0-only
-->

# prometheus-hdparm-exporter

prometheus-hdparm-exporter is a zero-dependency Python program that will export
the power state of the SATA disks found on the host and expose them to an HTTP
endpoint for consumption by [Prometheus](https://prometheus.io/).

It mon+tors if the disks are correctly shut down according to scheduled time in
the disk or manual calls to `hdparm -y`. It calls `hdparm -C` on every request
and parses the status of each SATA disk `/dev/sd*` reported by `lsblk`.

![Example grafana output graph](./docs/granafa_hdparm.png)

This way we can ensure that power consumption is reduced when the disks are
shut down while not in use.


## Usage

```text
prometheus-hdparm-exoprter HOST PORT
```

## Example

```console
$ sudo prometheus-hdparm-exporter localhost 8000 &
$ curl localhost:8000/metrics
hdparm_disk_power_status{disk="/dev/sda",status="standby"}
hdparm_disk_power_status{disk="/dev/sdb",status="standby"}
hdparm_disk_power_status{disk="/dev/sdc",status="standby"}
hdparm_disk_power_status{disk="/dev/sdd",status="active/idle"}
127.0.0.1 - - [14/Nov/2024 21:38:42] "GET / HTTP/1.1" 200 236
```

Status values:

- `active/idle` means the disk is spinning
- `standby` means the disk is not spinning

The last line is the log line coming from the server’s stdout in the
background; it is not present in the HTTP response.

## Deployment

This repository is a full Python package. It will create the
`prometheus-hdparm-exporter` binary in the PATH upon install.

## Manual deployment

Alternatively, if you do not want to use a Python package manager, the code
fits a single file `./src/prometheus_hdparm_exporter/main.py` and can easily be
distributed on hosts manually after renaming it to
`prometheus_hdparm_exporter.py` for example.

## Grafana configuration

You will need to do a bit of transformations of the `hdparm_disk_power_status`
field in Granafa to obtain this *State timeline* output:

![Grafana transform data configuration: first grouping to matrix on disk
column, then convert field type Time\\disk to Time](./docs/granafa_hdparm.png)

## Known limitations

The server will reply for any URL, not only `/metrics`. This is because this is
the only thing the server do and there is no point in parsing the query url to
match it.

## License

GPL-3.0-only.
