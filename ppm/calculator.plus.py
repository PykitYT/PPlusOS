program_command = "pcalc"
class CalcCommand(Program):
    def main(self):
        io = self.io
        io.write("welcome to pcalc! send empty line or 'exit' to quit\n")
        io.write("examples: 2+2  10/3  2**8  (1+2)*3  5+5\n")

        while True:
            io.write("calc> ")
            expr = yield from io.read_line()
            expr = expr.strip()

            if not expr or expr.lower() in ("exit", "quit", "q"):
                return 0

            # только безопасные символы
            allowed = set("0123456789+-*/().% eE")
            # для ** и пробелов
            cleaned = expr.replace("**", "").replace(" ", "")
            if any(c not in allowed and c != "*" for c in expr.replace(" ", "")):
                # чуть мягче: разрешаем * и **
                bad = False
                for c in expr:
                    if c not in "0123456789+-*/().% eE \t":
                        bad = True
                        break
                if bad:
                    io.write("only numbers and + - * / ** ( ) %\n")
                    continue

            try:
                # без доступа к именам/builtins
                result = eval(expr, {"__builtins__": {}}, {})
                io.write(str(result) + "\n")
            except ZeroDivisionError:
                io.write("error: division by zero\n")
            except Exception as e:
                io.write(f"error: {e}\n")