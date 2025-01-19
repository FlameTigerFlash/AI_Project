from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class Keyboards:
    @staticmethod
    async def get_start_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="В личный кабинет", callback_data="cabinet_menu")],
            [InlineKeyboardButton(text="В меню команд", callback_data="team_menu"),
             InlineKeyboardButton(text="В меню задач", callback_data="task_menu")],
            [InlineKeyboardButton(text="Справка", callback_data="help")]
        ])


    @staticmethod
    async def get_task_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Все задания", callback_data="get_tasks"),
             InlineKeyboardButton(text="Создать задачу", callback_data="add_tasks")],
            [InlineKeyboardButton(text="Написать отзыв", callback_data="write_review")],
            [InlineKeyboardButton(text="Редактировать задание", callback_data="task_editor_menu")],
            [InlineKeyboardButton(text="Отчёт ИИ по прошедшим задачам.", callback_data="ai_review")],
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
            [InlineKeyboardButton(text="Отправить запрос менеджерам", callback_data="send_request")],
            [InlineKeyboardButton(text="Отзывы о задаче", callback_data="get_reviews"),
             InlineKeyboardButton(text="Комментировать работу участника", callback_data="estimate_member")],
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


    @staticmethod
    async def get_cabinet_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Заполнить анкету", callback_data="fill_out_form")],
            [InlineKeyboardButton(text="Моя статистика", callback_data="get_stats"),
             InlineKeyboardButton(text="Уведомления", callback_data="get_notifications")],
            [InlineKeyboardButton(text="Текущие задачи", callback_data="get_current_tasks"),
             InlineKeyboardButton(text="Отчёт ИИ", callback_data="get_ai_self_review")],
            [InlineKeyboardButton(text="В главное меню", callback_data="main_menu")]
        ])


    @staticmethod
    async def get_notifications_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Прочитать все", callback_data="read_all_notifications"),
             InlineKeyboardButton(text="Ответить", callback_data="answer_notification")],
            [InlineKeyboardButton(text="Вернуться в личный кабинет", callback_data="cabinet_menu")]
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
                "/back - вернуться в текущее меню, прервав ввод параметров. В случае возникновения зависаний/"
                "непредвиденных затруднений всегда стоит вернуться в меню.\n"
                "/help - получить справку (на случай, если она ещё раз или два Вам понадобится).\n"
                "Для удобства участники разделены по группам. В меню команд вы можете создать собственную команду "
                "или присоединиться к уже существующей, введя корректный пароль.\n"
                "Будучи руководителем команды, Вы можете создавать задачи. Для этого следует ввести команду (организацию), "
                "к которой будет относиться данная задача, задать её название и назначить участников. Вы по умолчанию "
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


    @staticmethod
    async def get_cabinet_menu():
        return ("Добро пожаловать в личный кабинет! Здесь Вы можете получить статистику, прочесть уведомления, ответить на запрос, "
                "если являетесь менеджером задания, а также провести компьютерный анализ.")


    @staticmethod
    async def get_notifications_menu():
        return ("Вы можете прочитать уведомления от менеджеров (все сразу), "
                "ответить на запрос директора, если являетесь менеджером, или вернуться в меню личного кабинета.")