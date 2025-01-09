class Task:
    def __init__(self, name, params, error=None):
        self.name = name
        self.error = error
        self.params = params


class TaskResult(Task):
    pass
