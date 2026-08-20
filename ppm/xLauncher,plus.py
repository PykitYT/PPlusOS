program_command = "xLauncher"

class Main(Program):
    def main(self):
        import pygame as pg

        try:
            XC = XClient
        except NameError:
            self.io.write("XClient not found\n")
            return 1

        W, H = 480, 520
        xc = XC(self.syskernel, "xLauncher", W, H)
        try:
            xc.connect()
        except Exception:
            self.io.write("xPPUi not running\n")
            return 1

        fs = self.syskernel.fs
        sel = 0
        scroll = 0
        VIS = 14
        status = "Enter:run  A:add  R:refresh  Del:remove from list"
        mode = "list"
        buf = ""
        extra = []  # ручные имена

        def is_x_ui(name: str) -> bool:
            # x + заглавная: xConsole, xPPM, xNan...
            if len(name) < 2:
                return False
            return name[0] == "x" and name[1].isupper()

        def scan():
            found = []
            try:
                for n in fs.listfiles("/bin"):
                    pure = n.rstrip("/*")
                    if is_x_ui(pure):
                        found.append(pure)
            except Exception:
                pass
            for e in extra:
                if e not in found:
                    found.append(e)
            return sorted(set(found), key=str.lower)

        def run_cmd(name):
            nonlocal status
            if fs.exists_program("/bin/" + name):
                fs.run_program("/bin/" + name)
                status = "started " + name
            else:
                status = "not in /bin: " + name

        def redraw(apps):
            xc.fill(18, 20, 28)
            xc.rect(0, 0, W, 40, (40, 48, 70))
            xc.text(14, 10, "xLauncher — UI apps", (160, 210, 255))
            y = 56
            for i in range(VIS):
                idx = scroll + i
                if idx >= len(apps):
                    break
                name = apps[idx]
                col = (255, 255, 140) if idx == sel else (210, 210, 220)
                pre = ">" if idx == sel else " "
                xc.rect(20, y - 2, W - 40, 26, (35, 40, 55) if idx == sel else (25, 28, 36))
                xc.text(30, y + 2, pre + "  " + name, col)
                y += 30
            if mode == "add":
                xc.rect(40, 200, W - 80, 90, (50, 55, 75))
                xc.text(55, 215, "Add program name:", (255, 255, 255))
                xc.text(55, 245, buf + "█", (180, 255, 180))
            xc.rect(0, H - 28, W, 28, (30, 32, 42))
            xc.text(12, H - 22, status[:60], (150, 160, 170))
            xc.flip()

        while True:
            apps = scan()
            if sel >= len(apps):
                sel = max(0, len(apps) - 1)
            if sel < scroll:
                scroll = sel
            if sel >= scroll + VIS:
                scroll = sel - VIS + 1

            for e in xc.poll():
                t = e.get("t")
                if t in ("quit", "close"):
                    xc.close()
                    return 0

                if mode == "add":
                    if t == "text":
                        ch = e.get("s", "")
                        if ch.isprintable() and ch not in "/\\":
                            buf += ch
                    if t == "key":
                        k = e.get("key")
                        if k == pg.K_BACKSPACE:
                            buf = buf[:-1]
                        elif k == pg.K_ESCAPE:
                            mode = "list"
                            buf = ""
                        elif k in (pg.K_RETURN, pg.K_KP_ENTER) and buf.strip():
                            extra.append(buf.strip())
                            status = "added " + buf.strip()
                            mode = "list"
                            buf = ""
                    continue

                if t == "key":
                    k = e.get("key")
                    if k == pg.K_UP:
                        sel = max(0, sel - 1)
                    elif k == pg.K_DOWN:
                        sel = min(len(apps) - 1, sel + 1)
                    elif k in (pg.K_RETURN, pg.K_KP_ENTER) and apps:
                        run_cmd(apps[sel])
                    elif k == pg.K_DELETE and apps:
                        name = apps[sel]
                        if name in extra:
                            extra.remove(name)
                            status = "removed from list " + name
                        else:
                            status = "auto app — use ppm remove"

                if t == "text":
                    ch = (e.get("s") or "").lower()
                    if ch == "a":
                        mode = "add"
                        buf = ""
                    elif ch == "r":
                        status = "refreshed"

            redraw(apps)
            yield
