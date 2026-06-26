import subprocess

class Executor:
    def __init__(self, code):
        self.code = code

    def execute(self):
        try:
            exec(self.code)
            return {"status": "success", "message": "Code executed successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
