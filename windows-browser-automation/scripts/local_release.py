"""Yerel policygate wheel derleme ve GitHub Release hazırlığı."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from policygate import ActionRequest, require


WHEEL_PATTERN = re.compile(
    r"^policy_gate-(\d+\.\d+\.\d+)-py3-none-any\.whl$"
)


def find_wheel(policy_root: Path) -> Path:
    def wheel_version(wheel: Path) -> tuple[int, ...]:
        match = WHEEL_PATTERN.fullmatch(wheel.name)
        return tuple(int(part) for part in match.group(1).split("."))

    wheels = sorted(
        (policy_root / "dist").glob("policy_gate-*.whl"),
        key=wheel_version,
    )
    if not wheels:
        raise FileNotFoundError("policy-gate/dist icinde wheel bulunamadi")
    wheel = wheels[-1]
    if WHEEL_PATTERN.fullmatch(wheel.name) is None:
        raise ValueError(f"beklenmeyen wheel adı: {wheel.name}")
    return wheel


def build_wheel(repo_root: Path, policy_root: Path) -> Path:
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", str(policy_root)],
        cwd=repo_root,
        check=True,
    )
    return find_wheel(policy_root)


def release_command(repo_root: Path, wheel: Path, tag: str) -> list[str]:
    version = WHEEL_PATTERN.fullmatch(wheel.name).group(1)
    if tag != f"v{version}":
        raise ValueError(f"tag {tag} wheel surumu v{version} ile eslesmiyor")
    relative_wheel = wheel.relative_to(repo_root).as_posix()
    return [
        "gh",
        "release",
        "create",
        tag,
        relative_wheel,
        "--draft",
        "--title",
        f"policygate {version}",
        "--notes",
        "Local wheel; no PyPI publish. Installation proof for this repository only.",
    ]


def execute_release(repo_root: Path, wheel: Path, tag: str,
                    command: list[str]) -> None:
    require(ActionRequest(
        worker="policygate",
        action="policygate.local_release",
        level="MODIFY",
        summary="GitHub taslak release oluşturulacak.",
        details={"tag": tag, "wheel": wheel.name},
    ))
    subprocess.run(command, cwd=repo_root, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Yerel policygate wheel derleme ve GitHub Release hazirligi."
    )
    parser.add_argument(
        "--policy-gate",
        default=Path(__file__).resolve().parents[2] / "policy-gate",
        help="policy-gate paket kokunun yolu",
    )
    parser.add_argument("--tag", default="v1.1.0", help="GitHub Release etiketi")
    parser.add_argument(
        "--no-build", action="store_true", help="Var olan wheel'i dogrula"
    )
    parser.add_argument(
        "--execute", action="store_true", help="Taslak release komutunu calistir"
    )
    args = parser.parse_args()
    policy_root = Path(args.policy_gate).resolve()
    repo_root = policy_root.parent
    try:
        if args.no_build:
            wheel = find_wheel(policy_root)
        else:
            wheel = build_wheel(repo_root, policy_root)
        command = release_command(repo_root, wheel, args.tag)
        if args.execute:
            execute_release(repo_root, wheel, args.tag, command)
        else:
            print(" ".join(command))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"LOCAL_RELEASE_ERROR {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
