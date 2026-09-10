import os
import pwd
import sys
from pathlib import Path


APP_USER = "appuser"
WRITABLE_PATHS = (Path("/app/var"),)


def main() -> None:
    command = sys.argv[1:]
    if not command:
        raise SystemExit("missing command")

    if os.geteuid() == 0:
        user = pwd.getpwnam(APP_USER)
        for path in WRITABLE_PATHS:
            path.mkdir(parents=True, exist_ok=True)
            _chown_tree(path, user.pw_uid, user.pw_gid)

        os.setgroups([])
        os.setgid(user.pw_gid)
        os.setuid(user.pw_uid)

    os.execvp(command[0], command)


def _chown_tree(path: Path, uid: int, gid: int) -> None:
    os.chown(path, uid, gid)
    for child in path.rglob("*"):
        os.chown(child, uid, gid)


if __name__ == "__main__":
    main()
