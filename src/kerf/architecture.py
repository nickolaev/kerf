# Copyright 2026 Multikernel Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Architecture-specific Linux ABI and CPU identifier helpers."""

from dataclasses import dataclass
import os
import platform
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class Architecture:
    name: str
    cpu_id_label: str
    kexec_file_load_syscall: int
    reboot_syscall: int
    cpuinfo_id_keys: Tuple[str, ...]


_ARCHITECTURES: Dict[str, Architecture] = {
    "x86_64": Architecture("x86_64", "APIC ID", 320, 169, ("apicid",)),
    "x86": Architecture("x86", "APIC ID", 320, 88, ("apicid",)),
    "aarch64": Architecture("aarch64", "CPU ID", 294, 142, ("processor",)),
    "arm": Architecture("arm", "CPU ID", 382, 88, ("processor",)),
    "riscv64": Architecture("riscv64", "hart ID", 294, 142, ("hart", "processor")),
}

_ALIASES = {
    "amd64": "x86_64",
    "i386": "x86",
    "i686": "x86",
    "arm64": "aarch64",
    "riscv": "riscv64",
}


def architecture(machine: str = "") -> Architecture:
    """Return ABI data for *machine* or the running kernel."""
    machine = (machine or platform.machine()).lower()
    canonical = _ALIASES.get(machine, machine)
    if canonical.startswith("arm") and canonical not in _ARCHITECTURES:
        canonical = "arm"
    try:
        return _ARCHITECTURES[canonical]
    except KeyError as error:
        raise RuntimeError(f"Unsupported architecture: {machine}") from error


def get_kexec_file_load_syscall(machine: str = "") -> int:
    return architecture(machine).kexec_file_load_syscall


def get_reboot_syscall(machine: str = "") -> int:
    return architecture(machine).reboot_syscall


def cpu_id_label(machine: str = "") -> str:
    return architecture(machine).cpu_id_label


def _parse_cpuinfo_ids(lines: Iterable[str], key_name: str) -> set[int]:
    ids = set()
    for line in lines:
        key, separator, value = line.partition(":")
        if separator and key.strip().lower() == key_name:
            try:
                ids.add(int(value.strip(), 0))
            except ValueError:
                continue
    return ids


def get_system_cpu_ids(cpuinfo_path: str = "/proc/cpuinfo", machine: str = "") -> set[int]:
    """Read physical APIC IDs or RISC-V hart IDs from procfs."""
    arch = architecture(machine)
    try:
        with open(cpuinfo_path, "r", encoding="utf-8") as cpuinfo:
            lines = cpuinfo.readlines()
        ids = set()
        for key_name in arch.cpuinfo_id_keys:
            ids = _parse_cpuinfo_ids(lines, key_name)
            if ids:
                break
    except OSError:
        ids = set()
    if ids:
        return ids
    if arch.name in ("x86_64", "x86"):
        return set()
    return set(range(os.cpu_count() or 0))
