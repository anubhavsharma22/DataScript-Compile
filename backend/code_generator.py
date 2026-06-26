class CodeGenerator:
    def __init__(self, commands):
        self.commands = commands

    def generate_code(self):
        imports = "import io\nimport pandas as pd\nresult = None\noutput_filename = None\n"
        code = "\n".join(self.commands)
        return f"{imports}\n{code}"
