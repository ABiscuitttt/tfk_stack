#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Stacks 统一启停入口（替代原 Makefile）。

用法示例：
    ./stacks.py up                       全量按序启
    ./stacks.py up services/hermes       单起
    ./stacks.py down services/hermes services/trilium
    ./stacks.py ps infra/traefik
    ./stacks.py logs infra/traefik
"""
from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRAEFIK = "infra/traefik"
COMPOSE_FILE = "docker-compose.yml"


def discover_services() -> list[str]:
    """按启动顺序返回所有服务相对路径。

    顺序：infra 里 `*-net` 结尾的网络 stack → traefik → 其他 infra → services（排除 _template）。
    down 时由调用方反转，网络 stack 最后停。
    """

    def compose_dirs(parent: str) -> list[str]:
        base = ROOT / parent
        if not base.is_dir():
            return []
        return sorted(
            f"{parent}/{d.name}"
            for d in base.iterdir()
            if d.is_dir() and (d / COMPOSE_FILE).is_file()
        )

    infra_all = compose_dirs("infra")
    services_all = [s for s in compose_dirs("services") if not s.endswith("/_template")]

    nets = [s for s in infra_all if s.endswith("-net")]
    other_infra = [s for s in infra_all if s not in nets and s != TRAEFIK]

    ordered: list[str] = []
    ordered.extend(nets)
    if TRAEFIK in infra_all:
        ordered.append(TRAEFIK)
    ordered.extend(other_infra)
    ordered.extend(services_all)
    return ordered


def normalize(path: str) -> str:
    return path.strip().lstrip("./").rstrip("/")


def resolve_targets(given: list[str], all_services: list[str], reverse: bool) -> list[str]:
    """无参 → 全量（按 reverse 决定方向）；有参 → 校验并按用户给定顺序返回。"""
    if not given:
        return list(reversed(all_services)) if reverse else list(all_services)

    known = set(all_services)
    resolved: list[str] = []
    for raw in given:
        svc = normalize(raw)
        if svc not in known:
            print(f"错误：未知服务 {svc!r}", file=sys.stderr)
            print("可用服务：", file=sys.stderr)
            for s in all_services:
                print(f"  - {s}", file=sys.stderr)
            sys.exit(2)
        resolved.append(svc)
    return resolved


def run_compose(svc: str, sub: list[str]) -> int:
    cmd = ["docker", "compose", "-f", f"{svc}/{COMPOSE_FILE}", *sub]
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def batch(action_label: str, targets: list[str], sub: list[str]) -> int:
    """遍历执行，遇错继续，返回最大非零码。"""
    worst = 0
    for svc in targets:
        print(f">> {action_label} {svc}")
        rc = run_compose(svc, sub)
        if rc != 0 and rc > worst:
            worst = rc
    return worst


def cmd_up(args: argparse.Namespace) -> int:
    targets = resolve_targets(args.services, discover_services(), reverse=False)
    return batch("up", targets, ["up", "-d"])


def cmd_down(args: argparse.Namespace) -> int:
    targets = resolve_targets(args.services, discover_services(), reverse=True)
    return batch("down", targets, ["down"])


def cmd_pull(args: argparse.Namespace) -> int:
    targets = resolve_targets(args.services, discover_services(), reverse=False)
    return batch("pull", targets, ["pull"])


def cmd_restart(args: argparse.Namespace) -> int:
    rc_down = cmd_down(args)
    rc_up = cmd_up(args)
    return max(rc_down, rc_up)


def cmd_ps(args: argparse.Namespace) -> int:
    (svc,) = resolve_targets([args.service], discover_services(), reverse=False)
    return run_compose(svc, ["ps"])


def cmd_logs(args: argparse.Namespace) -> int:
    (svc,) = resolve_targets([args.service], discover_services(), reverse=False)
    return run_compose(svc, ["logs", "-f", "--tail=200"])


def _check(label: str, ok: bool, detail: str = "") -> bool:
    mark = "✓" if ok else "✗"
    line = f"  {mark} {label}"
    if detail:
        line += f" — {detail}"
    print(line)
    return ok


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.returncode, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return 127, f"{cmd[0]} not found"
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def _port_free(port: int) -> tuple[bool, str]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.bind(("0.0.0.0", port))
            return True, "空闲"
        except OSError as e:
            return False, f"已占用（{e.strerror}）"


def _docker_network_exists(name: str) -> bool:
    rc, out = _run(["docker", "network", "inspect", name, "--format", "{{.Name}}"])
    return rc == 0 and out == name


def cmd_doctor(_: argparse.Namespace) -> int:
    print("== docker / compose ==")
    rc_d, out_d = _run(["docker", "version", "--format", "{{.Server.Version}}"])
    ok_docker = _check("docker daemon", rc_d == 0, out_d if rc_d == 0 else out_d or "无法连接 daemon")
    rc_c, out_c = _run(["docker", "compose", "version", "--short"])
    _check("docker compose v2", rc_c == 0, out_c)

    print("== 端口 ==")
    ok80, detail80 = _port_free(80)
    # traefik 已经起在 80 属于正常场景，做个区分
    if not ok80:
        rc_ps, out_ps = _run(["docker", "ps", "--filter", "name=^traefik$", "--format", "{{.Names}}"])
        if rc_ps == 0 and out_ps.strip() == "traefik":
            detail80 = "被 traefik 容器占用（正常）"
            ok80 = True
    _check("宿主 80 端口", ok80, detail80)

    print("== *.localhost 解析 ==")
    ok_dns = True
    for host in ("traefik.localhost", "portainer.localhost"):
        try:
            addr = socket.gethostbyname(host)
            _check(host, True, addr)
        except socket.gaierror as e:
            ok_dns = False
            _check(host, False, str(e))

    print("== Docker 网络 ==")
    for net in ("traefik-net", "sandbox-net"):
        _check(net, _docker_network_exists(net))

    print("== 已发现 stack ==")
    for svc in discover_services():
        print(f"  - {svc}")

    ok_all = ok_docker and rc_c == 0 and ok80 and ok_dns
    return 0 if ok_all else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stacks.py",
        description="Stacks 统一启停入口：对 infra/* 与 services/* 下的 docker compose 编排做遍历。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  ./stacks.py up\n"
               "  ./stacks.py up services/hermes\n"
               "  ./stacks.py down services/hermes services/trilium\n"
               "  ./stacks.py logs infra/traefik",
    )
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    def add_multi(name: str, help_text: str, func):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("services", nargs="*", metavar="SVC", help="服务路径，如 services/hermes；省略即全量")
        p.set_defaults(func=func)

    add_multi("up", "启动服务（无参=全量按序，traefik 优先）", cmd_up)
    add_multi("down", "停止服务（无参=全量反序，traefik 最后停）", cmd_down)
    add_multi("restart", "先 down 再 up（参数透传）", cmd_restart)
    add_multi("pull", "拉取镜像", cmd_pull)

    p_ps = sub.add_parser("ps", help="查看单服务状态")
    p_ps.add_argument("service", metavar="SVC")
    p_ps.set_defaults(func=cmd_ps)

    p_logs = sub.add_parser("logs", help="跟随单服务日志（--tail 200）")
    p_logs.add_argument("service", metavar="SVC")
    p_logs.set_defaults(func=cmd_logs)

    p_doc = sub.add_parser("doctor", help="环境自检：docker/compose/端口/DNS/网络/stack 清单")
    p_doc.set_defaults(func=cmd_doctor)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
