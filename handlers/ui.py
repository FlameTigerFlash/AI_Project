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
            [InlineKeyboardButton(text="Список команд", callback_data="teams_list"),
             InlineKeyboardButton(text="Состав команды", callback_data="team_members")],
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
    async def get_helper_menu():
        return ("Вас приветствует бот TaskScheduler (Powered by GigaChat), "
                "специально разработанный Матвеем Сергеевым (@CentralOverheating) и Андреем Щепотьевым (@Catfish270).\n"
                "Я был разработан для организации рабочего процесса и анализа выполненных и проваленных задач "
                "с целью повышения эффективности дальнейших действий.\n"
                "Немного о моих командах.\n"
                "/start - зарегистрироваться и начать использование бота.\n"
                "/back - вернуться в текущее меню, прервав ввод параметров.\n"
                "/help - получить справку (на случай, если она ещё раз или два Вам понадобится).\n"
                "Для удобства участники разделены по группам. В меню команд вы можете создать собственную команду "
                "или присоединиться к уже существующей, введя корректный пароль.\n"
                "Будучи руководителем команды, Вы можете создавать задачи. Для этого следует ввести команду (организацию), "
                "к которой будет относиться данная задача, задать её название и назначить участников. Вы по умолчанию"
                "участвуете в задаче с неизменяемой ролью  директора.\n"
                "Для более тонкой настройки следует перейти в меню редактирования задачи, выбрав номер интересующего Вас таска."
                "Здесь Вы можете изменить описание задачи и роли исполнителей, посмотреть список трудящихся или "
                "завершить задание.")


    @staticmethod
    async def get_task_menu():
        return ("Вы находитесь в меню заданий.\n"
                "При создании задачи укажите команду, к которой она относится (не забыв предварительно её создать),"
                "названия поручений, а также список участников. Разделителем служит знак \';\'\n"
                "Только руководитель (ADMIN) команды может создавать задачи."
                "При показе задач отображаются как созданные лично Вами (даже без личного участия в них),"
                "так и те, сотрудником которых Вы являетесь.")


    @staticmethod
    async def get_team_menu():
        return ("Вы находитесь в меню управления командой.\n"
                "При создании команды укажите её название и пароль. Вы автоматически становитесь её администратором.\n"
                "При присоединении к одной из существующих команд также укажите её название и пароль.")


    @staticmethod
    async def get_task_editor_menu():
        return ("Вы находитесь в меню управления задачей.\n"
                "Вы можете изменить статус участников, завершить задание и назначить роли.")