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

"""Tests for architecture-specific ABI and CPU identifier handling."""

import pytest

from kerf.architecture import (
    architecture,
    get_kexec_file_load_syscall,
    get_reboot_syscall,
    get_system_cpu_ids,
)


@pytest.mark.parametrize(
    ("machine", "kexec_syscall", "reboot_syscall", "label"),
    [
        ("x86_64", 320, 169, "APIC ID"),
        ("aarch64", 294, 142, "CPU ID"),
        ("riscv64", 294, 142, "hart ID"),
    ],
)
def test_architecture_abi(machine, kexec_syscall, reboot_syscall, label):
    assert get_kexec_file_load_syscall(machine) == kexec_syscall
    assert get_reboot_syscall(machine) == reboot_syscall
    assert architecture(machine).cpu_id_label == label


def test_riscv_cpuinfo_hart_ids(tmp_path):
    cpuinfo = tmp_path / "cpuinfo"
    cpuinfo.write_text(
        "processor\t: 0\nhart\t\t: 0\n\nprocessor\t: 1\nhart\t\t: 5\n",
        encoding="utf-8",
    )

    assert get_system_cpu_ids(str(cpuinfo), "riscv64") == {0, 5}


def test_unknown_architecture_is_rejected():
    with pytest.raises(RuntimeError, match="Unsupported architecture"):
        architecture("mips64")
