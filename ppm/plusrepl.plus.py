program_command = "plusrepl"

class Main(Program):
    def main(self):
        def write_arguments(io, args, kernel=None):
            args = list(args)
            while args:
                if kernel is not None:
                    process = None
                    for p in kernel.processes:
                        if p.io is io:
                            process = p
                            break
                    if process is None or process.finished:
                        return
                if io.is_reading():
                    io.send(args.pop(0))
                yield
        io = self.io
        fs = self.syskernel.fs

        io.write("Loading PlusRepl...\n")

        # Важно: local_vars = {}, break вместо return, нормальные отступы
        code = (
            "local_vars = {'print': print, 'input': input}\n"
            "print('PlusRepl on DotPy')\n"
            "print('Type exit to quit')\n"
            "while True:\n"
            "    line = input('>>> ')\n"
            "    line = line.strip()\n"
            "    if not line:\n"
            "        continue\n"
            "    if line in ('exit', 'exit()', 'quit', 'quit()'):\n"
            "        break\n"
            "    try:\n"
            "        try:\n"
            "            result = eval(line, {'__builtins__': __builtins__}, local_vars)\n"
            "            if result is not None:\n"
            "                print(repr(result))\n"
            "        except SyntaxError:\n"
            "            exec(line, {'__builtins__': __builtins__}, local_vars)\n"
            "    except Exception as e:\n"
            "        print(type(e).__name__ + ': ' + str(e))\n"
        )

        try:
            fs.create_folder('/tmp')
        except Exception:
            pass
        fs.open_file('/tmp/repl.py', 'w').write(code)

        if not fs.exists_program('/bin/dotpy'):
            io.write("error: /bin/dotpy not found\n")
            return 1

        program_io = fs.run_program('/bin/dotpy')
        yield from write_arguments(program_io, ['/tmp/repl.py'], self.syskernel)

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

        return 0