program_command = "explorer"

class Main(Program):
    def main(self):
        io = self.io
        fs = self.syskernel.fs
        cwd = "/"

        def clear():
            io.write("\033[2J\033[H")

        def norm(path):
            path = (path or "").strip()
            if not path:
                return cwd
            if not path.startswith("/"):
                path = (cwd.rstrip("/") + "/" + path) if cwd != "/" else "/" + path
            parts = []
            for p in path.split("/"):
                if not p or p == ".":
                    continue
                if p == "..":
                    if parts:
                        parts.pop()
                    continue
                parts.append(p)
            return "/" + "/".join(parts) if parts else "/"

        def join_cwd(name):
            return (cwd.rstrip("/") + "/" + name) if cwd != "/" else "/" + name

        def list_dir(path):
            try:
                if path == "/":
                    folder = fs.root
                else:
                    parent, name = fs._resolve(path)
                    folder = None
                    for item in parent.files:
                        if isinstance(item, Folder) and item.name == name:
                            folder = item
                            break
                    if folder is None:
                        return None
                entries = []
                for item in folder.files:
                    if isinstance(item, Folder):
                        entries.append((item.name, "dir"))
                    elif hasattr(item, "program_class"):
                        entries.append((item.name, "prog"))
                    else:
                        entries.append((item.name, "file"))
                entries.sort(
                    key=lambda x: (
                        0 if x[1] == "dir" else 1 if x[1] == "prog" else 2,
                        x[0].lower(),
                    )
                )
                return entries
            except Exception:
                return None

        def find_entry(num):
            entries = list_dir(cwd) or []
            if num < 1 or num > len(entries):
                return None
            return entries[num - 1]

        def draw():
            clear()
            io.write("=== PPlus Explorer ===\n")
            io.write("cwd: " + cwd + "\n")
            io.write("-" * 42 + "\n")
            entries = list_dir(cwd)
            if entries is None:
                io.write("(cannot list)\n")
            elif not entries:
                io.write("(empty)\n")
            else:
                for i, (name, kind) in enumerate(entries, 1):
                    if kind == "dir":
                        mark = "/"
                    elif kind == "prog":
                        mark = "*"
                    elif name.endswith(".py"):
                        mark = "#"
                    else:
                        mark = " "
                    io.write(f"  {i:3}  {name}{mark}\n")
            io.write("-" * 42 + "\n")
            io.write("n# open   x# run prog/py   e# edit nan\n")
            io.write("u up   g path   s text   f dir   t file\n")
            io.write("r refresh   q quit   |  Ctrl→_u _r _n…\n")

        def wait_child(program_io):
            while True:
                process = None
                for p in self.syskernel.processes:
                    if p.io is program_io:
                        process = p
                        break
                if process is None or process.finished:
                    break
                if program_io.is_reading():
                    data = yield from io.read_line()
                    program_io.send(data)
                else:
                    yield

        def run_dotpy(path):
            if not fs.exists_program("/bin/dotpy"):
                io.write("dotpy not installed\n")
                yield from io.read_line()
                return
            program_io = fs.run_program("/bin/dotpy")
            while True:
                process = None
                for p in self.syskernel.processes:
                    if p.io is program_io:
                        process = p
                        break
                if process is None or process.finished:
                    return
                if program_io.is_reading():
                    program_io.send(path)
                    break
                yield
            yield from wait_child(program_io)

        def run_prog(path):
            try:
                parent, nm = fs._resolve(path)
                cls = None
                for item in parent.files:
                    if getattr(item, "name", None) == nm and hasattr(item, "program_class"):
                        cls = item.program_class
                        break
                if cls is None:
                    io.write("program not found\n")
                    yield from io.read_line()
                    return
                p = self.syskernel.create_process(cls, capture_input=False)
                yield from wait_child(p.io)
            except Exception as e:
                io.write("run error: " + str(e) + "\n")
                yield from io.read_line()

        def run_nan(path):
            if not fs.exists_program("/bin/nan"):
                io.write("nan not installed\n")
                yield from io.read_line()
                return
            program_io = fs.run_program("/bin/nan")
            while True:
                process = None
                for p in self.syskernel.processes:
                    if p.io is program_io:
                        process = p
                        break
                if process is None or process.finished:
                    return
                if program_io.is_reading():
                    program_io.send(path)
                    break
                yield
            yield from wait_child(program_io)

        def apply_hotkey(line):
            """_u / _3 / _n → обычная команда"""
            if not (line.startswith("_") and len(line) >= 2):
                return line
            key = line[1:].strip()
            kl = key.lower()
            if kl == "u":
                return "u"
            if kl == "r":
                return "r"
            if kl == "q":
                return "q"
            if kl == "g":
                io.write("path = ")
                t = yield from io.read_line()
                return "g " + t.strip()
            if kl == "s":
                io.write("search = ")
                t = yield from io.read_line()
                return "s " + t.strip()
            if kl == "f":
                io.write("folder = ")
                t = yield from io.read_line()
                return "f " + t.strip()
            if kl == "t":
                io.write("file = ")
                t = yield from io.read_line()
                return "t " + t.strip()
            if kl == "n":
                io.write("n = ")
                t = yield from io.read_line()
                return "n " + t.strip()
            if kl == "e":
                io.write("e = ")
                t = yield from io.read_line()
                return "e " + t.strip()
            if kl == "x":
                io.write("x = ")
                t = yield from io.read_line()
                return "x " + t.strip()
            if key.isdigit():
                return "n " + key
            io.write("unknown hotkey\n")
            return ""

        draw()
        while True:
            io.write("> ")
            line = yield from io.read_line()
            line = line.strip()
            if not line:
                draw()
                continue

            line = yield from apply_hotkey(line)
            if not line:
                continue

            if line in ("q", "quit", "exit"):
                clear()
                return 0

            if line in ("r", "refresh"):
                draw()
                continue

            if line in ("u", "up", ".."):
                cwd = norm("..")
                draw()
                continue

            if line.startswith("g ") or line.startswith("cd "):
                np = norm(line.split(None, 1)[1])
                if list_dir(np) is not None:
                    cwd = np
                else:
                    io.write("not a directory\n")
                    yield from io.read_line()
                draw()
                continue

            if line.startswith("n "):
                try:
                    num = int(line.split(None, 1)[1])
                except Exception:
                    io.write("bad number\n")
                    continue
                ent = find_entry(num)
                if not ent:
                    io.write("bad index\n")
                    continue
                name, kind = ent
                path = join_cwd(name)
                if kind == "dir":
                    cwd = norm(name)
                    draw()
                    continue
                if kind == "file" and name.endswith(".py"):
                    io.write("run with dotpy? (y/n) = ")
                    ans = (yield from io.read_line()).strip().lower()
                    if ans == "y":
                        yield from run_dotpy(path)
                    draw()
                    continue
                if kind == "file":
                    try:
                        data = fs.open_file(path, "r").read()
                        clear()
                        io.write("=== " + path + " ===\n")
                        io.write(data + ("\n" if not data.endswith("\n") else ""))
                        io.write("-- enter --\n")
                        yield from io.read_line()
                    except Exception as e:
                        io.write(str(e) + "\n")
                        yield from io.read_line()
                    draw()
                    continue
                if kind == "prog":
                    io.write("use x " + str(num) + " to run\n")
                    continue

            if line.startswith("x "):
                try:
                    num = int(line.split(None, 1)[1])
                except Exception:
                    io.write("bad number\n")
                    continue
                ent = find_entry(num)
                if not ent:
                    io.write("bad index\n")
                    continue
                name, kind = ent
                path = join_cwd(name)
                if kind == "prog":
                    yield from run_prog(path)
                    draw()
                    continue
                if kind == "file" and name.endswith(".py"):
                    yield from run_dotpy(path)
                    draw()
                    continue
                io.write("not a program or .py\n")
                continue

            if line.startswith("e "):
                try:
                    num = int(line.split(None, 1)[1])
                except Exception:
                    io.write("bad number\n")
                    continue
                ent = find_entry(num)
                if not ent or ent[1] == "dir":
                    io.write("pick a file\n")
                    continue
                yield from run_nan(join_cwd(ent[0]))
                draw()
                continue

            if line.startswith("s "):
                q = line.split(None, 1)[1].lower()
                clear()
                io.write("search '" + q + "' in " + cwd + "\n")
                found = False
                for i, (name, kind) in enumerate(list_dir(cwd) or [], 1):
                    if q in name.lower():
                        mark = "/" if kind == "dir" else "*" if kind == "prog" else "#" if name.endswith(".py") else " "
                        io.write(f"  {i:3}  {name}{mark}\n")
                        found = True
                if not found:
                    io.write("(no matches)\n")
                io.write("-- enter --\n")
                yield from io.read_line()
                draw()
                continue

            if line.startswith("f "):
                try:
                    fs.create_folder(norm(line.split(None, 1)[1]))
                    io.write("ok\n")
                except Exception as e:
                    io.write(str(e) + "\n")
                yield from io.read_line()
                draw()
                continue

            if line.startswith("t "):
                yield from run_nan(norm(line.split(None, 1)[1]))
                draw()
                continue

            io.write("unknown command\n")
