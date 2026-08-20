program_name = "status"
class Main(Program):
  def main(self):
    self.io.write(f"Kernel Status: {self.syskernel.status}\n")
    return 0
