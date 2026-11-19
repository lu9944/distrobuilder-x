#!/usr/bin/env python3
"""Assemble the distrobuilder definition used by the image build workflow.

Reads the base definition, sets the Ubuntu release from the RELEASE
environment variable, and appends the packages belonging to the optional
groups that were selected in the workflow UI.

Usage: assemble-image.py <base.yaml> <output.yaml>
"""

import os
import re
import sys

import yaml

PACKAGE_GROUPS = {
    "NET_TOOLS": [
        "bind9-dnsutils",
        "iproute2",
        "iputils-ping",
        "mtr-tiny",
        "net-tools",
        "netcat-openbsd",
        "socat",
        "tcpdump",
        "traceroute",
    ],
    "EDITOR_TOOLS": [
        "htop",
        "less",
        "nano",
        "tmux",
        "vim",
    ],
    "SEARCH_TOOLS": [
        "gawk",
        "jq",
        "ripgrep",
        "tree",
    ],
    "ARCHIVE_TOOLS": [
        "bzip2",
        "unzip",
        "xz-utils",
        "zip",
        "zstd",
    ],
    "DEV_TOOLS": [
        "build-essential",
        "gdb",
        "git",
        "make",
        "python3",
        "python3-pip",
    ],
    "DEBUG_TOOLS": [
        "iotop",
        "lsof",
        "strace",
        "sysstat",
    ],
}

PACKAGE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9+.-]*$")

# Used when a workflow run has no inputs (for example a tag push).
DEFAULT_GROUPS = {
    "NET_TOOLS": True,
    "EDITOR_TOOLS": True,
    "SEARCH_TOOLS": True,
    "ARCHIVE_TOOLS": True,
    "DEV_TOOLS": False,
    "DEBUG_TOOLS": False,
}


def env_flag(name):
    raw = os.environ.get(name, "").strip().lower()
    if raw == "":
        return DEFAULT_GROUPS.get(name, False)

    return raw in ("1", "true", "yes", "on")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <base.yaml> <output.yaml>", file=sys.stderr)
        return 2

    with open(sys.argv[1], encoding="utf-8") as stream:
        definition = yaml.safe_load(stream)

    release = os.environ.get("RELEASE", "").strip()
    if release:
        definition["image"]["release"] = release

    packages = definition["packages"]["sets"][0]["packages"]
    selected = []

    for flag, group in PACKAGE_GROUPS.items():
        if not env_flag(flag):
            continue

        selected.append(flag)
        for package in group:
            if package not in packages:
                packages.append(package)

    raw_extra = os.environ.get("EXTRA_PACKAGES", "")
    extra_packages = [
        value.strip()
        for value in raw_extra.replace("\n", ",").replace(" ", ",").split(",")
        if value.strip()
    ]

    for package in extra_packages:
        if not PACKAGE_NAME_RE.match(package):
            print(f"Invalid package name: {package!r}", file=sys.stderr)
            return 1

        if package not in packages:
            packages.append(package)

    with open(sys.argv[2], "w", encoding="utf-8") as stream:
        yaml.safe_dump(
            definition,
            stream,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )

    print("Release:", release or "(unchanged)")
    print("Groups:", ", ".join(selected) or "none")
    print("Extra packages:", ", ".join(extra_packages) or "none")
    print("Total packages:", len(packages))
    return 0


if __name__ == "__main__":
    sys.exit(main())
