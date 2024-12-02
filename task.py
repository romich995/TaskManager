import datetime
import os
import json

from pydantic import BaseModel
from enum import Enum
from pydantic import TypeAdapter

TASKS_JSON_FILENAME = "tasks.json"
FIRST_ID = 0
JSON_INDENT = 4

class PriorityEnum(str, Enum):
    high = 'Высокий'
    middle = 'Средний'
    low = 'Низкий'

class StatusEnum(str, Enum):
    executed = 'Выполнено'
    not_executed = 'Не выполнено'

class Task(BaseModel):
    id: str|None = None
    title: str
    description: str
    category: str
    due_date: datetime.date
    priority: PriorityEnum
    status: StatusEnum = StatusEnum.not_executed
    class Config:
        validate_assignment = True

Tasks = TypeAdapter(list[Task])

class TaskManager:
    tasks_json_full_path: str
    next_id: str | None
    def __init__(self,
                 task_json_filename: str = TASKS_JSON_FILENAME):
        self.tasks_json_full_path = task_json_filename
        self.next_id = None
    def read(self) -> list[Task]:
        """
        Считывает файл с задачами, если он существует

        :return:
        """
        if os.path.isfile(self.tasks_json_full_path):
            with open(self.tasks_json_full_path, "r") as json_file:
                tasks_json = json.load(json_file)
            tasks = Tasks.validate_python(tasks_json)
            return tasks
        else:
            return []

    def write(self, tasks: list[Task]):
       """
       Записывает данные в файл
       :return:
       """
       with open(self.tasks_json_full_path, "wb") as json_file:
           json_file.write(Tasks.dump_json(tasks, indent=JSON_INDENT))

    def get_next_id(self, tasks: list) -> str:
        """

        :param tasks:
        :return:
        """
        if tasks:
            next_id = max(int(task.id) for task in tasks) + 1
        else:
            next_id = FIRST_ID
        return str(next_id)

    def append(self, task: Task):
        """

        :param task:
        :return:
        """
        tasks = self.read()
        next_id = self.get_next_id(tasks)
        task.id = next_id
        tasks.append(task)
        self.write(tasks)

    def search_by_id(self, identificator: str, tasks: list[Task]) -> Task:
        for task in tasks:
            if task.id == identificator:
                return task

    def show(self, category: str = None):
        tasks = self.read()
        if category is not None:
            tasks = [task for task in tasks if task.category == category]
        return Tasks.dump_json(tasks, indent=JSON_INDENT).decode()
    def main(self):
        while True:
            print(
                """1. Для просмотра задач введите '1' и нажмите Enter.\n"""
                """2. Для добавления задачи введите '2' и нажмите Enter.\n"""
                """3. Для изменения задачи введите '3' и нажмите Enter.\n"""
                """4. Для удаления задачи введите '4' и нажмите Enter.\n"""
                """5. Для поиска задачи введите '5' и нажмите Enter.\n"""
                """6. Для завершения работы введите '6' и нажмите Enter.\n"""
                )
            execution_code = input()
            if execution_code == '1':
                self.show_cli()
            elif execution_code == '2':
                self.append_cli()
            elif execution_code == '3':
                self.update_cli()
            elif execution_code == '4':
                self.delete_cli()
            elif execution_code == '5':
                self.search_cli()
            elif execution_code == '6':
                break

    def search_cli(self):
        category, status, keywords = None, None, None
        print("""Будете осуществлять поиск по полю категория - введите 'Да'""")
        answer = input()
        if answer == 'Да':
            print("""Введите категорию""")
            category = input()

        print("""Будете осуществлять поиск по полю статус(Выполнено/Не выполнено) - введите 'Да'""")
        answer = input()
        if answer == 'Да':
            print("""Введите статус""")
            status = input()

        print("""Будете осуществлять поиск по словам в описании - введите 'Да'""")
        answer = input()
        if answer == 'Да':
            print("""Введите слова через пробел в нижнем регистре""")
            keywords = set(input().lower().split())
        tasks = self.read()
        searched_tasks = self.search(tasks=tasks, category=category,
                    status=status, keywords=keywords)

        print(Tasks.dump_json(searched_tasks, indent=JSON_INDENT).decode())

    def delete_cli(self):
        print("""Удалить задачу по идентификатороу - введите '1'""")
        print("""Удалить задачу по категории - введите '2'""")

        execution_code = input()

        if execution_code == '1':
            print('Введите идентификатор')
            identificator = input()
            tasks = self.read()
            task = self.search_by_id(identificator, tasks)

            if task is None:
                print("""Задачи с данным идентификатором не существует""")
            else:
                tasks.remove(task)
                self.write(tasks)
                print("""Задача успешно удалена""")

        elif execution_code == '2':
            print('Введите категорию')
            category = input()
            tasks = self.read()
            tasks = [task for task in tasks if task.category != category]
            self.write(tasks)
            print("""Задачи успешно удалены""")

    def search(self,
               tasks: list[Task],
               category: str = None,
               status: StatusEnum = None,
               keywords: set[str] = None) -> list[Task]:
        searched_tasks = tasks
        if category is not None:
            searched_tasks = [task for task in searched_tasks if task.category == category]

        if status is not None:
            searched_tasks = [task for task in searched_tasks if task.status == status]

        if keywords is not None:
            searched_tasks = [task for task in searched_tasks if set(task.description.lower().split()) & keywords == keywords]

        return searched_tasks
    def update_cli(self):
        print("""Хотите отредактировать задачу - введите '1'""")
        print("""Хотите отметить задачу как выполненная - введите '2'""")
        execution_code = input()
        if execution_code == '1':
            self.update_task_cli()
        elif execution_code == '2':
            print("""Введите идентификатор задачи""")
            identificator = input()
            tasks = self.read()
            task = self.search_by_id(identificator, tasks)
            task.status = StatusEnum.executed
            self.write(tasks)


    def update_task_cli(self):
        print("""Введите идентификатор задачи:""")
        identificator = input()
        tasks = self.read()
        task = self.search_by_id(identificator, tasks)
        if task is None:
            print("""Задачи с данным идентификатором не существует""")
        else:
            print(task.model_dump_json(indent=JSON_INDENT))
            print("""Введите новое название задачи""")
            task.title = input()
            print("""Введите новое описание задачи""")
            task.description = input()
            print("""Введите новую категорию задачи""")
            task.category = input()
            print("""Введите новый срок выполнения задачи""")
            task.due_date = input()
            print("""Введите новый приоритет задачи""")
            task.priority = input()
            self.write(tasks)

    def append_cli(self):
        print("""Введите название задачи""")
        title = input()
        print("""Введите описание задачи""")
        description = input()
        print("""Введите категорию задачи""")
        category = input()
        print("""Введите срок выполнения задачи""")
        due_date = input()
        print("""Введите приоритет задачи""")
        priority = input()
        task = Task(title=title,
                    description=description,
                    category=category,
                    due_date=due_date,
                    priority=priority)
        self.append(task)

    def show_cli(self):
        print("""1. Для просмотра всех текущих задач введите '1' и нажмите Enter.""")
        print("""2. Для просмотра задач по категориям введите '2' и нажмите Enter.""")
        execution_code = input()
        if execution_code == '1':
            data = self.show()
            print(data)
        elif execution_code == '2':
            print("""Введите категорию и нажмите Enter:""")
            category = input()
            data = self.show(category)
            print(data)


if __name__ == "__main__":
    task_manager = TaskManager()
    task_manager.main()


