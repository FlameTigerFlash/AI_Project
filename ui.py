from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class Keyboards:
    @staticmethod
    async def get_start_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="В меню команд", callback_data="team_menu"),
             InlineKeyboardButton(text="В меню задач", callback_data="task_menu")],
            [InlineKeyboardButton(text="Отчёт ИИ по прошедшим задачам.", callback_data="ai_review")],
            [InlineKeyboardButton(text="Справка", callback_data="help")]
        ])


    @staticmethod
    async def get_helper_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="В меню команд", callback_data="team_menu"),
            InlineKeyboardButton(text="В меню задач", callback_data="task_menu")]
        ])


    @staticmethod
    async def get_task_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Все задания", callback_data="get_tasks"),
             InlineKeyboardButton(text="Создать задачу", callback_data="add_tasks")],
            [InlineKeyboardButton(text="Написать отзыв", callback_data="write_review")],
            [InlineKeyboardButton(text="Редактировать задание", callback_data="task_editor_menu")],
            [InlineKeyboardButton(text="В главное меню", callback_data="main_menu")]
        ])


    @staticmethod
    async def get_team_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Создать команду", callback_data="create_team"),
             InlineKeyboardButton(text="Присоединиться к команде", callback_data="join_team")],
            [InlineKeyboardButton(text="В главное меню", callback_data="main_menu")]
        ])


    @staticmethod
    async def get_task_editor_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Изменить статус исполнителя", callback_data="alter_worker_status"),
             InlineKeyboardButton(text="Изменить статус задачи", callback_data="alter_task_status")],
            [InlineKeyboardButton(text="Список трудящихся", callback_data="get_workers"),
             InlineKeyboardButton(text="Изменить описание задачи", callback_data="change_task_description")],
            [InlineKeyboardButton(text="В меню задач", callback_data="task_menu")]
        ])

    @staticmethod
    async def get_task_completion_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Задача выполнена", callback_data="task_completed")],
             [InlineKeyboardButton(text="Задача провалена", callback_data="task_failed")],
            [InlineKeyboardButton(text="Обратно в меню управления задачей", callback_data="back")]
        ])

    @staticmethod
    async def get_worker_status_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Менеджер", callback_data="set_manager")],
            [InlineKeyboardButton(text="Исполнитель", callback_data="set_executor")],
            [InlineKeyboardButton(text="Обратно в меню управления задачей", callback_data="back")]
        ])


class TextBlocks:
    @staticmethod
    async def get_main_menu():
        return ("\tВы находитесь в главном меню.\n"
                "\tВыберите, пожалуйста, интересующую Вас опцию.")


    @staticmethod
    async def get_task_menu():
        return ("\tВы находитесь в меню заданий.\n"
                "\tПри создании задачи укажите команду, к которой она относится (не забыв предварительно её создать),"
                "названия поручений, а также список участников. Разделителем служит знак \';\'\n"
                "Только руководитель (ADMIN) команды может создавать задачи."
                "\tПри показе задач отображаются как созданные лично Вами (даже без личного участия в них),"
                "так и те, сотрудником которых Вы являетесь.")


    @staticmethod
    async def get_team_menu():
        return ("\tВы находитесь в меню управления командой.\n"
                "\tПри создании команды укажите её название и пароль. Вы автоматически становитесь её администратором.\n"
                "\tПри присоединении к одной из существующих команд также укажите её название и пароль.")


    @staticmethod
    async def get_task_editor_menu():
        return ("\tВы находитесь в меню управления задачей.\n"
                "\tВы можете изменить статус участников, завершить задание и назначить роли.")