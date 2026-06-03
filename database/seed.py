# database/seed.py
import json
from database.db import SessionLocal
from database.models.content import (
    Track, Lesson, LessonVersion, Theory, LessonTheory,
    TaskGenerator, Task, TaskVariant, LessonTask
)
from database.models.user import User, UserCurrency, UserInventory, UserShowcase, ItemType, ShopItem
from database.models.gamification import Achievement, UserAchievement, LeaderboardCategory
from database.models.progress import UserTrackProgress, UserLessonProgress
from services.auth_service import AuthService
from services.leaderboard_service import LeaderboardService
from services.statistics_service import StatisticsService
from sqlalchemy import text
import random
import datetime

def seed_shop_data(db):
    """Заполняет типы предметов и товары магазина."""
    # Проверяем, есть ли уже предметы
    if db.query(ItemType).count() > 0:
        return  # уже есть

    # ---- Аватары ----
    avatars = [
        ("Атом", "avatar", "Аватар с изображением атома", "assets/shop/avatar_atom.png", 1),
        ("Колба", "avatar", "Аватар с колбой", "assets/shop/avatar_flask.png", 1),
        ("Мензурка", "avatar", "Аватар с мензуркой", "assets/shop/avatar_beaker.png", 1),
        ("Кристалл", "avatar", "Аватар с кристаллом", "assets/shop/avatar_crystal.png", 1),
        ("Пламя", "avatar", "Аватар с огнём", "assets/shop/avatar_flame.png", 1),
    ]
    for name, cat, desc, icon, stack in avatars:
        item_type = ItemType(name=name, category=cat, description=desc, icon_url=icon, max_stack=stack)
        db.add(item_type)
        db.flush()
        db.add(ShopItem(item_type_id=item_type.id, price_coins=50, price_crystals=0, is_active=True))

    # ---- Темы профиля ----
    themes = [
        ("Классическая", "profile_theme", "Стандартная тема оформления", "assets/shop/theme_classic.png", False),
        ("Кислотный жёлтый", "profile_theme", "Яркая жёлтая тема", "assets/shop/theme_yellow.png", True),
        ("Неоновый синий", "profile_theme", "Тема в синих тонах", "assets/shop/theme_blue.png", True),
        ("Тёмный реактив", "profile_theme", "Тёмная тема с зелёными акцентами", "assets/shop/theme_dark.png", True),
    ]
    for name, cat, desc, icon, purchasable in themes:
        item_type = ItemType(name=name, category=cat, description=desc, icon_url=icon, max_stack=1)
        db.add(item_type)
        db.flush()
        if purchasable:
            db.add(ShopItem(item_type_id=item_type.id, price_coins=100, price_crystals=0, is_active=True))
        else:
            # Классическая тема не появляется в магазине, но тип предмета существует
            pass
        
    # ---- Витрины ----
    showcases = [
        ("Простая полка", "showcase", "Деревянная полка на 2 предмета", "assets/shop/showcase_simple.png", 2),
        ("Стеклянный шкаф", "showcase", "Стеклянная витрина на 3 предмета", "assets/shop/showcase_glass.png", 3),
        ("Золотая витрина", "showcase", "Роскошная витрина на 5 предметов", "assets/shop/showcase_gold.png", 5),
    ]
    for name, cat, desc, icon, cap in showcases:
        item_type = ItemType(name=name, category=cat, description=desc, icon_url=icon, max_stack=1, capacity=cap)
        db.add(item_type)
        db.flush()
        db.add(ShopItem(item_type_id=item_type.id, price_coins=200, price_crystals=10, is_active=True))

    # ---- Артефакты ----
    artifacts = [
        ("Колба Эрленмейера", "artifact", "Коническая колба для титрования", "assets/shop/artifact_erlenmeyer.png"),
        ("Мерный цилиндр", "artifact", "Точный измерительный прибор", "assets/shop/artifact_cylinder.png"),
        ("Кристалл меди", "artifact", "Красивый синий кристалл", "assets/shop/artifact_crystal_cu.png"),
        ("Модель ДНК", "artifact", "Двойная спираль", "assets/shop/artifact_dna.png"),
        ("Пробирка с газом", "artifact", "Пробирка с дымящимся газом", "assets/shop/artifact_testtube.png"),
        ("Весы", "artifact", "Аналитические весы", "assets/shop/artifact_scales.png"),
        ("Горелка Бунзена", "artifact", "Спиртовка для нагрева", "assets/shop/artifact_burner.png"),
        ("Термометр", "artifact", "Измеряет температуру", "assets/shop/artifact_thermometer.png"),
        ("Реторта", "artifact", "Старинный перегонный аппарат", "assets/shop/artifact_retort.png"),
    ]
    for name, cat, desc, icon in artifacts:
        item_type = ItemType(name=name, category=cat, description=desc, icon_url=icon, max_stack=1)
        db.add(item_type)
        db.flush()
        db.add(ShopItem(item_type_id=item_type.id, price_coins=75, price_crystals=5, is_active=True))
    db.commit()
    print("Магазин заполнен.")

def seed_test_user(db):
    """Создаёт тестового пользователя со всем открытым контентом, валютой и достижениями."""
    test_username = "0"
    test_password = "0"
    existing = db.query(User).filter(User.username == test_username).first()
    if existing:
        db.delete(existing)
        db.commit()
        print("Удалён старый тестовый пользователь.")

    # Хешируем пароль
    hashed_pw = AuthService.hash_password(test_password)
    user = User(
        username=test_username,
        email="0@example.com",
        password_hash=hashed_pw,
        current_streak=15,
        longest_streak=30,
        last_active=datetime.datetime.now()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id

    # Кошелёк с кучей валют
    wallet = UserCurrency(user_id=user_id, coins=99999, crystals=9999)
    db.add(wallet)
    db.commit()

    # Проходим все треки и все уроки
    tracks = db.query(Track).filter(Track.is_published == True).all()
    for track in tracks:
        lesson_count = len(track.lessons)
        tp = UserTrackProgress(
            user_id=user_id,
            track_id=track.id,
            status='completed',
            started_at=datetime.datetime.now() - datetime.timedelta(days=30),
            completed_at=datetime.datetime.now(),
            is_repeating=False,
            total_xp=lesson_count * 50,
            current_lesson_index=lesson_count - 1
        )
        db.add(tp)
        db.flush()  # чтобы получить tp.id

        for lesson in track.lessons:
            version = lesson.versions[0] if lesson.versions else None
            lp = UserLessonProgress(
                user_track_progress_id=tp.id,
                lesson_id=lesson.id,
                version_id=version.id if version else None,
                status='completed',
                theory_viewed=True,
                theory_viewed_at=datetime.datetime.now() - datetime.timedelta(days=10),
                tasks_completed=len(lesson.task_links),
                tasks_total=len(lesson.task_links),
                score_earned=len(lesson.task_links),
                score_total=len(lesson.task_links),
                started_at=datetime.datetime.now() - datetime.timedelta(days=10),
                completed_at=datetime.datetime.now() - datetime.timedelta(days=9),
                is_skipped=False
            )
            db.add(lp)
    db.commit()

    # Все достижения
    achievements = db.query(Achievement).all()
    for ach in achievements:
        ua = UserAchievement(
            user_id=user_id,
            achievement_id=ach.id,
            unlocked_at=datetime.datetime.now(),
            shown_to_user=True,
            is_displayed=True
        )
        db.add(ua)
    db.commit()

    lb = LeaderboardService(db)
    # Имитируем накопленный XP по периодам
    lb.update_entry(user.id, 'xp_total', 1500)
    lb.update_entry(user.id, 'xp_weekly', 300)
    lb.update_entry(user.id, 'xp_daily', 50)
    lb.update_entry(user.id, 'xp_monthly', 800)
    lb.update_entry(user.id, 'tasks_completed', 44)
    lb.update_entry(user.id, 'accuracy_rate', 87.5)
    # Стрик
    user.current_streak = 15
    user.longest_streak = 30
    lb.update_entry(user.id, 'current_streak', user.current_streak)

    print(f"Тестовый пользователь '{test_username}' (пароль '{test_password}') создан со всеми разблокировками.")
    db.commit()

def seed_achievements(db):
    """Создаёт базовый набор достижений."""
    if db.query(Achievement).count() > 0:
        return
    achievements_data = [
        {"code": "first_lesson", "name": "Первая реакция", "desc": "Завершите один урок.",
         "icon": "assets/achievements/first_lesson.png", "cond_type": "complete_lesson", "cond_data": {"count": 1},
         "xp": 50, "coins": 30, "crystals": 0},
        {"code": "five_lessons", "name": "Начинающий алхимик", "desc": "Завершите 5 уроков.",
         "icon": "assets/achievements/five_lessons.png", "cond_type": "complete_lesson", "cond_data": {"count": 5},
         "xp": 100, "coins": 50, "crystals": 5},
        {"code": "balance_master", "name": "Мастер уравнений", "desc": "Решите 10 задач на балансировку уравнений.",
         "icon": "assets/achievements/balance_master.png", "cond_type": "count_tasks_by_type", "cond_data": {"type": "balance_equation", "count": 10},
         "xp": 150, "coins": 100, "crystals": 10},
        {"code": "accuracy_90", "name": "С точностью до молекулы", "desc": "Достигните точности >90% после 20 заданий.",
         "icon": "assets/achievements/accuracy_90.png", "cond_type": "accuracy", "cond_data": {"threshold": 0.9, "min_attempts": 20},
         "xp": 200, "coins": 150, "crystals": 15},
        {"code": "streak_7", "name": "Железная воля", "desc": "Заходите в приложение 7 дней подряд.",
         "icon": "assets/achievements/streak_7.png", "cond_type": "streak", "cond_data": {"days": 7},
         "xp": 100, "coins": 50, "crystals": 5},
        {"code": "collector_5", "name": "Коллекционер", "desc": "Купите 5 предметов в магазине.",
         "icon": "assets/achievements/collector_5.png", "cond_type": "collect_items", "cond_data": {"count": 5},
         "xp": 80, "coins": 40, "crystals": 0},
        {"code": "showcase_decor", "name": "Витринных дел мастер", "desc": "Разместите 3 артефакта в витрине.",
         "icon": "assets/achievements/showcase_decor.png", "cond_type": "showcase_artifacts", "cond_data": {"count": 3},
         "xp": 120, "coins": 80, "crystals": 8},
        {"code": "speed_solver", "name": "Быстрый ум", "desc": "Решите задание менее чем за 10 секунд.",
         "icon": "assets/achievements/speed_solver.png", "cond_type": "speed", "cond_data": {"max_seconds": 10},
         "xp": 150, "coins": 100, "crystals": 10},
    ]
    for a in achievements_data:
        ach = Achievement(
            code=a["code"], name=a["name"], description=a["desc"],
            icon_url=a["icon"], condition_type=a["cond_type"], condition_data=a["cond_data"],
            xp_reward=a["xp"], coins_reward=a["coins"], crystals_reward=a["crystals"]
        )
        db.add(ach)
    db.commit()
    print("Достижения созданы.")

def seed_data():
    db = SessionLocal()

    if db.query(Track).count() > 0:
        print("Данные уже существуют. Заполнение пропущено.")
        db.close()
        return

    # ======================= ТРЕКИ =======================
    track8 = Track(name="Химия. 8 класс", description="Базовый курс химии для 8 класса", is_published=True)
    track9 = Track(name="Химия. 9 класс", description="Продвинутый курс для 9 класса", is_published=True)
    db.add_all([track8, track9])
    db.commit()

    # ======================= ГЕНЕРАТОРЫ ЗАДАНИЙ =======================
    # Generator for 'choice'
    gen_choice_8 = TaskGenerator(
        type='choice',
        template_data={
            "questions": [
                {"text": "Какая частица является наименьшей частицей вещества?", "options": ["Атом", "Молекула", "Электрон", "Ядро"], "correct_index": 1},
                {"text": "Что такое валентность?", "options": ["Число связей", "Масса атома", "Заряд ядра", "Число протонов"], "correct_index": 0},
                {"text": "Какое из перечисленных веществ является простым?", "options": ["Вода", "Углекислый газ", "Кислород", "Поваренная соль"], "correct_index": 2},
            ]
        },
        difficulty=2,
        topic_tags=["вещество", "атомы"]
    )
    db.add(gen_choice_8)

    gen_choice_9 = TaskGenerator(
        type='choice',
        template_data={
            "questions": [
                {"text": "Какой металл является самым лёгким?", "options": ["Алюминий", "Литий", "Натрий", "Калий"], "correct_index": 1},
                {"text": "Какая кислота содержится в желудочном соке?", "options": ["Серная", "Соляная", "Азотная", "Уксусная"], "correct_index": 1},
                {"text": "Какой элемент имеет символ 'Fe'?", "options": ["Фтор", "Фосфор", "Железо", "Франций"], "correct_index": 2},
            ]
        },
        difficulty=2,
        topic_tags=["металлы", "элементы"]
    )
    db.add(gen_choice_9)

    gen_balance = TaskGenerator(
        type='balance_equation',
        template_data={
            "equations": [
                {"reactants": ["H2", "O2"], "products": ["H2O"], "coefficients": [2, 1, 2]},
                {"reactants": ["Na", "Cl2"], "products": ["NaCl"], "coefficients": [2, 1, 2]},
                {"reactants": ["Ca", "O2"], "products": ["CaO"], "coefficients": [2, 1, 2]},
                {"reactants": ["HCl", "NaOH"], "products": ["NaCl", "H2O"], "coefficients": [1, 1, 1, 1]},
                {"reactants": ["Fe", "S"], "products": ["FeS"], "coefficients": [1, 1, 1]},
            ]
        },
        difficulty=3,
        topic_tags=["уравнения", "реакции"]
    )
    db.add(gen_balance)

    gen_calc = TaskGenerator(
        type='calculation',
        template_data={
            "formulas": [
                {
                    "params": {"mass": [10, 100], "molar_mass": [18, 100]},
                    "question_template": "Вычислите количество вещества (моль), если масса вещества {mass} г, молярная масса {molar_mass} г/моль.",
                    "expression": "mass / molar_mass",
                    "tolerance": 0.01
                },
                {
                    "params": {"mass_solute": [5, 50], "mass_solution": [100, 500]},
                    "question_template": "В растворе массой {mass_solution} г содержится {mass_solute} г соли. Найдите массовую долю соли (в процентах).",
                    "expression": "(mass_solute / mass_solution) * 100",
                    "tolerance": 0.1
                }
            ]
        },
        difficulty=4,
        topic_tags=["расчеты"]
    )
    db.add(gen_calc)
    db.commit()

    def seed_leaderboard_categories(db):
        if db.query(LeaderboardCategory).count() > 0:
            return
        categories = [
            ("xp_daily", "XP за день", "xp_daily", "global", "daily"),
            ("xp_weekly", "XP за неделю", "xp_weekly", "global", "weekly"),
            ("xp_monthly", "XP за месяц", "xp_monthly", "global", "monthly"),
            ("xp_total", "Общий XP", "xp_total", "global", "never"),
            ("tasks_completed", "Выполнено заданий", "tasks_completed", "global", "daily"),
            ("accuracy_rate", "Точность решений", "accuracy_rate", "global", "daily"),
            ("current_streak", "Текущий стрик", "current_streak", "global", "daily"),
            # при желании можно добавить те же метрики с scope='friends'
            ("xp_weekly_friends", "XP за неделю (друзья)", "xp_weekly", "friends", "weekly"),
            ("tasks_completed_friends", "Заданий за день (друзья)", "tasks_completed", "friends", "daily"),
        ]
        for code, name, metric, scope, period in categories:
            db.add(LeaderboardCategory(
                code=code, name=name, metric_type=metric,
                scope=scope, reset_period=period, is_active=True
            ))
        db.commit()

    # ======================= УРОКИ И ТЕОРИЯ =======================
    # Вспомогательная функция для создания полного урока
    def create_lesson(track, order, title, theory_blocks=None, tasks_data=None, xp=50, est_time=30, is_test=False):
        lesson = Lesson(track_id=track.id, order_index=order)
        db.add(lesson)
        db.flush()

        version = LessonVersion(
            version_of=lesson.id,
            title=title,
            estimated_time=est_time,
            xp_reward=xp,
            version_number=1,
            is_active=True
        )
        db.add(version)
        db.flush()

        # Теория, если не тест
        if not is_test and theory_blocks:
            # Создаём одну запись Theory, содержащую все блоки
            theory = Theory(
                data=json.dumps({"blocks": theory_blocks}),
                topic_tags=[title],
                estimated_time=15
            )
            db.add(theory)
            db.flush()
            lt = LessonTheory(lesson_id=lesson.id, theory_id=theory.id, order_index=1, is_required=True)
            db.add(lt)

        # Задания
        if tasks_data:
            for idx, td in enumerate(tasks_data):
                # Задание может быть создано заранее или создаём сейчас
                if 'task' in td:
                    task = td['task']
                else:
                    task = create_task_from_data(td)
                # Связываем с уроком
                lt = LessonTask(
                    lesson_id=lesson.id,
                    task_id=task.id,
                    order_index=idx + 1,
                    is_required=td.get('is_required', True)
                )
                db.add(lt)
        db.commit()
        return lesson

    def create_task_from_data(td):
        """Создаёт Task и, если нужно, варианты, на основе словаря td"""
        task = Task(
            type=td['type'],
            source_type=td.get('source_type', 'static'),
            generator_id=td.get('generator_id'),
            question_text=td.get('question_text', f'Задание типа {td["type"]}'),
            data=td.get('data', {}),
            correct_answers=td.get('correct_answers', {}),
            scoring_type=td.get('scoring_type', 'binary'),
            max_score=td.get('max_score', 1),
            topic_tags=td.get('topic_tags', [])
        )
        db.add(task)
        db.flush()

        if 'variants' in td:
            for var in td['variants']:
                variant = TaskVariant(
                    base_task_id=task.id,
                    variant_data=var.get('variant_data', {}),
                    correct_answer=var.get('correct_answer', {}),
                    usage_count=0
                )
                db.add(variant)
        db.commit()
        return task

    # ========================= ТЕОРИЯ И ЗАДАНИЯ ДЛЯ УРОКОВ =========================
    # Для сокращения дублирования блоки теории и данные заданий будем описывать в структурах

    # 8 КЛАСС
    # Урок 1
    create_lesson(track8, 0, "Предмет химии. Вещества",
        theory_blocks=[
            {"type": "text", "content": "Химия — это наука о веществах, их свойствах, строении и взаимных превращениях. Вещества — это то, из чего состоят физические тела. Например, вода, сахар, железо — это вещества, а капля воды, кусочек сахара — это тела."},
            {"type": "text", "content": "Вещества делятся на простые и сложные. Простые вещества состоят из атомов одного химического элемента (например, кислород O₂, железо Fe). Сложные вещества — из атомов разных элементов (вода H₂O, углекислый газ CO₂). Химия изучает превращения одних веществ в другие."},
            {"type": "molecule", "data": {"atoms": [{"element": "H", "x": 0, "y": 0}, {"element": "O", "x": 100, "y": 0}, {"element": "H", "x": 50, "y": 86}], "bonds": [{"from": 0, "to": 1, "order": 1}, {"from": 1, "to": 2, "order": 1}]}, "caption": "Молекула воды"}
        ],
        tasks_data=[
            {'type': 'choice', 'source_type': 'generated', 'generator_id': gen_choice_8.id, 'scoring_type': 'binary', 'topic_tags': ['вещество']},
            {'type': 'true_false', 'variants': [
                {"variant_data": {"question_text": "Вода — простое вещество."}, "correct_answer": {"answer": False}},
                {"variant_data": {"question_text": "Кислород — простое вещество."}, "correct_answer": {"answer": True}},
            ], 'topic_tags': ['вещество']},
            {'type': 'fill_blank', 'variants': [
                {"variant_data": {"text": "Химическая формула поваренной соли — ______."}, "correct_answer": {"answer": "NaCl"}},
            ], 'topic_tags': ['формулы']}
        ]
    )

    # Урок 2
    create_lesson(track8, 1, "Строение атома",
        theory_blocks=[
            {"type": "text", "content": "Атом — мельчайшая химически неделимая частица вещества. Атом состоит из ядра и электронной оболочки. Ядро содержит протоны (положительный заряд) и нейтроны (без заряда). Вокруг ядра движутся электроны (отрицательный заряд). Число протонов определяет химический элемент."},
            {"type": "image", "src": "assets/images/atom_model.png", "caption": "Планетарная модель атома"},
            {"type": "text", "content": "Порядковый номер элемента в таблице Менделеева равен заряду ядра и числу протонов. Например, углерод имеет 6 протонов, значит, его порядковый номер — 6. Массовое число равно сумме протонов и нейтронов."}
        ],
        tasks_data=[
            {'type': 'choice', 'source_type': 'generated', 'generator_id': gen_choice_8.id},
            {'type': 'fill_blank', 'variants': [
                {"variant_data": {"text": "Атом углерода имеет 6 протонов, значит его порядковый номер — ______."}, "correct_answer": {"answer": "6"}},
            ]},
            {'type': 'calculation', 'source_type': 'generated', 'generator_id': gen_calc.id, 'scoring_type': 'binary'}
        ]
    )

    # Урок 3
    create_lesson(track8, 2, "Ионная химическая связь",
        theory_blocks=[
            {"type": "text", "content": "Ионная связь образуется между металлами и неметаллами за счёт передачи электронов от металла к неметаллу. При этом образуются положительные и отрицательные ионы, которые притягиваются. Например, в хлориде натрия (NaCl) атом натрия отдаёт один электрон атому хлора."},
            {"type": "image", "src": "assets/images/ionic_bond.png", "caption": "Схема образования ионной связи в NaCl"},
            {"type": "text", "content": "Ионные вещества твёрдые, имеют высокие температуры плавления, часто растворимы в воде и проводят ток в растворах и расплавах."}
        ],
        tasks_data=[
            {'type': 'true_false', 'variants': [
                {"variant_data": {"question_text": "Ионная связь характерна для пары Na и Cl."}, "correct_answer": {"answer": True}},
                {"variant_data": {"question_text": "Связь в молекуле H₂O — ионная."}, "correct_answer": {"answer": False}},
            ]},
            {'type': 'match', 'variants': [
                {"variant_data": {
                    "left_items": ["NaCl", "MgO", "KBr"],
                    "right_items": ["хлорид натрия", "оксид магния", "бромид калия"]
                 }, "correct_answer": {"matches": {"0": 0, "1": 1, "2": 2}}}
            ]},
            {'type': 'fill_blank', 'variants': [
                {"variant_data": {"text": "При образовании ионной связи металл ______ электроны."}, "correct_answer": {"answer": "отдаёт"}},
            ]}
        ]
    )

    # Урок 4 (ковалентная связь)
    create_lesson(track8, 3, "Ковалентная химическая связь",
        theory_blocks=[
            {"type": "text", "content": "Ковалентная связь образуется за счёт общих электронных пар между двумя неметаллами. Если электронные пары смещены к одному из атомов, связь полярная (например, HCl, H₂O). Если не смещены — неполярная (H₂, O₂, N₂)."},
            {"type": "image", "src": "assets/images/covalent_bond.png", "caption": "Перекрывание орбиталей в H₂"},
        ],
        tasks_data=[
            {'type': 'choice', 'source_type': 'generated', 'generator_id': gen_choice_8.id},
            {'type': 'classify', 'variants': [
                {"variant_data": {"item_name": "HCl", "options": ["ионная", "ковалентная полярная", "ковалентная неполярная", "металлическая"]}, "correct_answer": {"class": "ковалентная полярная"}},
                {"variant_data": {"item_name": "NaF", "options": ["ионная", "ковалентная полярная", "ковалентная неполярная", "металлическая"]}, "correct_answer": {"class": "ионная"}},
            ]},
        ]
    )

    # Урок 5 (оксиды)
    create_lesson(track8, 4, "Классы неорганических веществ: оксиды",
        theory_blocks=[
            {"type": "text", "content": "Оксиды — это сложные вещества, состоящие из двух элементов, один из которых кислород в степени окисления –2. Оксиды делятся на основные (металл + кислород, например CaO), кислотные (неметалл + кислород, CO₂, SO₃) и амфотерные (Al₂O₃, ZnO)."},
            {"type": "text", "content": "Основные оксиды реагируют с кислотами, кислотные — со щелочами, амфотерные — и с кислотами, и со щелочами."}
        ],
        tasks_data=[
            {'type': 'classify', 'variants': [
                {"variant_data": {"item_name": "CO₂", "options": ["основный", "кислотный", "амфотерный", "несолеобразующий"]}, "correct_answer": {"class": "кислотный"}},
                {"variant_data": {"item_name": "MgO", "options": ["основный", "кислотный", "амфотерный", "несолеобразующий"]}, "correct_answer": {"class": "основный"}},
            ]},
            {'type': 'choice', 'variants': [
                {"variant_data": {"question_text": "Выберите кислотный оксид:", "options": ["CaO", "SO₂", "Na₂O", "K₂O"]}, "correct_answer": {"answer": 1}},
            ]},
        ]
    )

    # Урок 6 (кислоты и основания)
    create_lesson(track8, 5, "Кислоты и основания",
        theory_blocks=[
            {"type": "text", "content": "Кислоты — это электролиты, которые при диссоциации образуют катионы водорода и анионы кислотного остатка. Примеры: HCl, H₂SO₄, HNO₃. Основания — электролиты, образующие гидроксид-анионы OH⁻: NaOH, Ca(OH)₂."},
            {"type": "image", "src": "assets/images/acid_base_reaction.png", "caption": "Реакция нейтрализации"}
        ],
        tasks_data=[
            {'type': 'match', 'variants': [
                {"variant_data": {"left_items": ["HCl", "NaOH", "H₂SO₄"], "right_items": ["соляная кислота", "гидроксид натрия", "серная кислота"]}, "correct_answer": {"matches": {"0": 0, "1": 1, "2": 2}}}
            ]},
            {'type': 'true_false', 'variants': [
                {"variant_data": {"question_text": "NaOH — это кислота."}, "correct_answer": {"answer": False}},
            ]},
        ]
    )

    # Урок 7 (соли)
    create_lesson(track8, 6, "Соли: состав и номенклатура",
        theory_blocks=[
            {"type": "text", "content": "Соли — продукты замещения водорода в кислоте на металл. Название соли складывается из названия кислотного остатка и металла. Например, NaCl — хлорид натрия, CaSO₄ — сульфат кальция."}
        ],
        tasks_data=[
            {'type': 'fill_blank', 'variants': [
                {"variant_data": {"text": "Формула сульфата меди(II) — ______."}, "correct_answer": {"answer": "CuSO₄"}},
                {"variant_data": {"text": "KCl называется хлорид ______."}, "correct_answer": {"answer": "калия"}},
            ]},
            {'type': 'choice', 'variants': [
                {"variant_data": {"question_text": "Какая соль является хлоридом?", "options": ["Na₂SO₄", "KCl", "CaCO₃", "Mg(NO₃)₂"]}, "correct_answer": {"answer": 1}},
            ]},
        ]
    )

    # Урок 8 — тест (только задания)
    create_lesson(track8, 7, "Тест по классам неорганических веществ",
        is_test=True, xp=80, est_time=20,
        tasks_data=[
            {'type': 'classify', 'variants': [
                {"variant_data": {"item_name": "CaO", "options": ["оксид", "кислота", "основание", "соль"]}, "correct_answer": {"class": "оксид"}},
                {"variant_data": {"item_name": "HNO₃", "options": ["оксид", "кислота", "основание", "соль"]}, "correct_answer": {"class": "кислота"}},
            ]},
            {'type': 'choice', 'variants': [
                {"variant_data": {"question_text": "Какое вещество является основанием?", "options": ["HCl", "NaOH", "NaCl", "CO₂"]}, "correct_answer": {"answer": 1}},
            ]},
            {'type': 'match', 'variants': [
                {"variant_data": {"left_items": ["CO₂", "NaOH", "NaCl"], "right_items": ["кислотный оксид", "основание", "соль"]}, "correct_answer": {"matches": {"0": 0, "1": 1, "2": 2}}}
            ]},
            {'type': 'fill_blank', 'variants': [
                {"variant_data": {"text": "Na₂SO₄ — это ______ натрия."}, "correct_answer": {"answer": "сульфат"}},
            ]},
        ]
    )

    # Урок 9 (реакции и закон сохранения)
    create_lesson(track8, 8, "Химические реакции. Закон сохранения массы",
        theory_blocks=[
            {"type": "text", "content": "Химическая реакция — превращение одних веществ (реагентов) в другие (продукты). Реакции записываются уравнениями, где отражается закон сохранения массы: число атомов каждого элемента до и после реакции одинаково."},
            {"type": "image", "src": "assets/images/periodic_table_mini.png", "caption": "Фрагмент таблицы Менделеева"}
        ],
        tasks_data=[
            {'type': 'balance_equation', 'source_type': 'generated', 'generator_id': gen_balance.id, 'scoring_type': 'binary'},
            {'type': 'true_false', 'variants': [
                {"variant_data": {"question_text": "При химической реакции масса веществ увеличивается."}, "correct_answer": {"answer": False}},
            ]},
        ]
    )

    # Урок 10 (типы реакций)
    create_lesson(track8, 9, "Типы химических реакций",
        theory_blocks=[
            {"type": "text", "content": "Реакции бывают соединения (A+B→AB), разложения (AB→A+B), замещения (A+BC→AC+B) и обмена (AB+CD→AD+CB)."},
        ],
        tasks_data=[
            {'type': 'classify', 'variants': [
                {"variant_data": {"item_name": "2H₂ + O₂ → 2H₂O", "options": ["соединение", "разложение", "замещение", "обмен"]}, "correct_answer": {"class": "соединение"}},
            ]},
        ]
    )

    # Урок 11 (растворы, массовая доля)
    create_lesson(track8, 10, "Растворы. Массовая доля",
        theory_blocks=[
            {"type": "text", "content": "Раствор — однородная система, состоящая из растворителя и растворённого вещества. Массовая доля w = m(вещества) / m(раствора). Выражается в процентах."},
        ],
        tasks_data=[
            {'type': 'calculation', 'source_type': 'generated', 'generator_id': gen_calc.id},
        ]
    )

    # Тест по реакциям и растворам (12)
    create_lesson(track8, 11, "Тест по реакциям и растворам",
        is_test=True, xp=80, est_time=20,
        tasks_data=[
            {'type': 'balance_equation', 'source_type': 'generated', 'generator_id': gen_balance.id},
            {'type': 'calculation', 'source_type': 'generated', 'generator_id': gen_calc.id},
        ]
    )

    # ОВР (13)
    create_lesson(track8, 12, "Окислительно-восстановительные реакции",
        theory_blocks=[
            {"type": "text", "content": "ОВР — реакции с изменением степеней окисления. Окислитель принимает электроны, восстановитель отдаёт."},
        ],
        tasks_data=[
            {'type': 'true_false', 'variants': [
                {"variant_data": {"question_text": "В реакции Zn + 2HCl → ZnCl₂ + H₂ цинк — окислитель."}, "correct_answer": {"answer": False}},
            ]},
        ]
    )

    # Обзор металлов и неметаллов (14)
    create_lesson(track8, 13, "Основные металлы и неметаллы",
        theory_blocks=[
            {"type": "text", "content": "Металлы расположены в левой и нижней части таблицы, неметаллы — в правой верхней. Водород — неметалл."},
            {"type": "image", "src": "assets/images/crystal_lattice.png", "caption": "Кристаллическая решетка"}
        ],
        tasks_data=[
            {'type': 'classify', 'variants': [
                {"variant_data": {"item_name": "Cu", "options": ["металл", "неметалл", "амфотерный элемент"]}, "correct_answer": {"class": "металл"}},
            ]},
        ]
    )

    # Итоговый тест 8 класса (15)
    create_lesson(track8, 14, "Итоговый тест за 8 класс",
        is_test=True, xp=200, est_time=40,
        tasks_data=[
            {'type': 'choice', 'source_type': 'generated', 'generator_id': gen_choice_8.id},
            {'type': 'balance_equation', 'source_type': 'generated', 'generator_id': gen_balance.id},
            {'type': 'calculation', 'source_type': 'generated', 'generator_id': gen_calc.id},
            {'type': 'match', 'variants': [
                {"variant_data": {"left_items": ["H₂O", "NaCl", "CO₂", "CaO"], "right_items": ["вода", "поваренная соль", "углекислый газ", "негашеная известь"]}, "correct_answer": {"matches": {"0": 0, "1": 1, "2": 2, "3": 3}}}
            ]},
        ]
    )

    # Продолжим с 9 классом (также подробно)
    # Урок 1 (9 класс) Периодический закон
    create_lesson(track9, 0, "Периодический закон и таблица Менделеева",
        theory_blocks=[
            {"type": "text", "content": "Периодический закон, открытый Д.И. Менделеевым, гласит: свойства химических элементов и их соединений находятся в периодической зависимости от заряда ядра атома. Таблица Менделеева — графическое отображение закона."},
            {"type": "image", "src": "assets/images/periodic_table_mini.png", "caption": "Периодическая система"}
        ],
        tasks_data=[
            {'type': 'choice', 'source_type': 'generated', 'generator_id': gen_choice_9.id},
            {'type': 'fill_blank', 'variants': [
                {"variant_data": {"text": "Элемент с порядковым номером 11 — это ______."}, "correct_answer": {"answer": "натрий"}},
            ]},
        ]
    )

    # Урок 2 (металлы)
    create_lesson(track9, 1, "Металлы: общая характеристика",
        theory_blocks=[
            {"type": "text", "content": "Металлы — элементы, обладающие металлическим блеском, ковкостью, тепло- и электропроводностью. В реакциях они отдают электроны, выступая восстановителями."},
            {"type": "image", "src": "assets/images/metallic_bond.png", "caption": "Металлическая кристаллическая решетка"}
        ],
        tasks_data=[
            {'type': 'true_false', 'variants': [
                {"variant_data": {"question_text": "Металлы в реакциях являются окислителями."}, "correct_answer": {"answer": False}},
            ]},
            {'type': 'choice', 'variants': [
                {"variant_data": {"question_text": "Какой из перечисленных металлов самый пластичный?", "options": ["Железо", "Алюминий", "Золото", "Свинец"]}, "correct_answer": {"answer": 2}},
            ]},
        ]
    )

    # Урок 3 (щелочные металлы)
    create_lesson(track9, 2, "Щелочные металлы",
        theory_blocks=[
            {"type": "text", "content": "Щелочные металлы (Li, Na, K, Rb, Cs) — мягкие, очень активные, на воздухе быстро окисляются. Энергично реагируют с водой с выделением водорода."}
        ],
        tasks_data=[
            {'type': 'balance_equation', 'variants': [
                {"variant_data": {"reactants": ["Na", "H₂O"], "products": ["NaOH", "H₂"]}, "correct_answer": {"coefficients": [2, 2, 2, 1]}},
            ]},
        ]
    )

    # Урок 4 (железо)
    create_lesson(track9, 3, "Железо и его соединения",
        theory_blocks=[
            {"type": "text", "content": "Железо — металл средней активности, притягивается магнитом. Образует два ряда соединений: Fe²⁺ (соли железа(II)) и Fe³⁺ (соли железа(III))."}
        ],
        tasks_data=[
            {'type': 'classify', 'variants': [
                {"variant_data": {"item_name": "FeCl₃", "options": ["Fe(II)", "Fe(III)", "Fe(VI)", "Fe(0)"]}, "correct_answer": {"class": "Fe(III)"}},
            ]},
        ]
    )

    # Тест по металлам (5)
    create_lesson(track9, 4, "Тест по металлам",
        is_test=True, xp=100, est_time=25,
        tasks_data=[
            {'type': 'choice', 'source_type': 'generated', 'generator_id': gen_choice_9.id},
            {'type': 'match', 'variants': [
                {"variant_data": {"left_items": ["Na", "Fe", "Cu", "Zn"], "right_items": ["щелочной металл", "ферромагнетик", "красный металл", "алюминиевая группа"]}, "correct_answer": {"matches": {"0": 0, "1": 1, "2": 2, "3": 3}}}
            ]},
            {'type': 'balance_equation', 'variants': [
                {"variant_data": {"reactants": ["Fe", "Cl₂"], "products": ["FeCl₃"]}, "correct_answer": {"coefficients": [2, 3, 2]}},
            ]},
        ]
    )

    # Урок 6 (неметаллы общая хар-ка)
    create_lesson(track9, 5, "Неметаллы: общая характеристика",
        theory_blocks=[
            {"type": "text", "content": "Неметаллы — элементы, которые могут принимать электроны, завершая внешний уровень. Они образуют кислотные оксиды, летучие водородные соединения. Типичные неметаллы: O, N, S, Cl, C, P."}
        ],
        tasks_data=[
            {'type': 'choice', 'variants': [
                {"variant_data": {"question_text": "Какой из элементов образует простое вещество — газ при н.у.?", "options": ["Сера", "Углерод", "Кислород", "Фосфор"]}, "correct_answer": {"answer": 2}},
            ]},
        ]
    )

    # Урок 7 (водород и кислород)
    create_lesson(track9, 6, "Водород и кислород",
        theory_blocks=[
            {"type": "text", "content": "Водород — самый легкий газ, горит, образует взрывчатую смесь с кислородом. Кислород поддерживает горение. Реакция 2H₂ + O₂ → 2H₂O выделяет много энергии."},
            {"type": "image", "src": "assets/images/gas_collection.png", "caption": "Сбор газов"}
        ],
        tasks_data=[
            {'type': 'balance_equation', 'source_type': 'generated', 'generator_id': gen_balance.id},
        ]
    )

    # Урок 8 (галогены)
    create_lesson(track9, 7, "Галогены",
        theory_blocks=[
            {"type": "text", "content": "Галогены (F, Cl, Br, I) — сильные окислители. Фтор — самый активный. Хлор используется для обеззараживания воды, бром — в медицине."}
        ],
        tasks_data=[
            {'type': 'true_false', 'variants': [
                {"variant_data": {"question_text": "Фтор является сильным восстановителем."}, "correct_answer": {"answer": False}},
            ]},
        ]
    )

    # Урок 9 (скорость реакций)
    create_lesson(track9, 8, "Скорость химических реакций",
        theory_blocks=[
            {"type": "text", "content": "Скорость реакции зависит от природы веществ, концентрации, температуры, катализатора и площади поверхности (для твердых веществ). Повышение температуры на 10°C увеличивает скорость в 2-4 раза (правило Вант-Гоффа)."}
        ],
        tasks_data=[
            {'type': 'calculation', 'variants': [
                {"variant_data": {"question": "Температурный коэффициент равен 2. На сколько градусов нужно повысить температуру, чтобы скорость увеличилась в 8 раз?"}, "correct_answer": {"value": 30, "tolerance": 0.5}},
            ]},
        ]
    )

    # Урок 10 (равновесие)
    create_lesson(track9, 9, "Химическое равновесие",
        theory_blocks=[
            {"type": "text", "content": "Химическое равновесие — состояние, когда скорости прямой и обратной реакций равны. Принцип Ле-Шателье: если на систему оказать воздействие, равновесие смещается в сторону, ослабляющую это воздействие."},
            {"type": "image", "src": "assets/images/equilibrium_graph.png", "caption": "График установления равновесия"}
        ],
        tasks_data=[
            {'type': 'choice', 'variants': [
                {"variant_data": {"question_text": "Куда сместится равновесие N₂ + 3H₂ ⇌ 2NH₃ + Q при повышении давления?", "options": ["Вправо", "Влево", "Не изменится"]}, "correct_answer": {"answer": 0}},
            ]},
        ]
    )

    # Тест по неметаллам и кинетике (11)
    create_lesson(track9, 10, "Тест по неметаллам и кинетике",
        is_test=True, xp=100, est_time=25,
        tasks_data=[
            {'type': 'balance_equation', 'source_type': 'generated', 'generator_id': gen_balance.id},
            {'type': 'choice', 'source_type': 'generated', 'generator_id': gen_choice_9.id},
            {'type': 'match', 'variants': [
                {"variant_data": {"left_items": ["Cl₂", "H₂", "N₂", "O₂"], "right_items": ["желто-зеленый газ", "бесцветный горючий газ", "инертный газ", "поддерживает горение"]}, "correct_answer": {"matches": {"0": 0, "1": 1, "2": 2, "3": 3}}}
            ]},
        ]
    )

    # Урок 12 (электролитическая диссоциация)
    create_lesson(track9, 11, "Электролитическая диссоциация",
        theory_blocks=[
            {"type": "text", "content": "Электролиты — вещества, растворы или расплавы которых проводят электрический ток. При растворении в воде ионные соединения и многие кислоты распадаются на ионы."},
            {"type": "image", "src": "assets/images/electrolysis.png", "caption": "Схема электролиза"}
        ],
        tasks_data=[
            {'type': 'fill_blank', 'variants': [
                {"variant_data": {"text": "HCl → H+ + ______."}, "correct_answer": {"answer": "Cl-"}},
            ]},
        ]
    )

    # Урок 13 (ионные реакции)
    create_lesson(track9, 12, "Реакции ионного обмена",
        theory_blocks=[
            {"type": "text", "content": "Реакции ионного обмена идут до конца, если образуется осадок, газ или малодиссоциирующее вещество (вода). Например, AgNO₃ + NaCl → AgCl↓ + NaNO₃."}
        ],
        tasks_data=[
            {'type': 'balance_equation', 'variants': [
                {"variant_data": {"reactants": ["AgNO₃", "NaCl"], "products": ["AgCl", "NaNO₃"]}, "correct_answer": {"coefficients": [1, 1, 1, 1]}},
            ]},
        ]
    )

    # Урок 14 (введение в органику)
    create_lesson(track9, 13, "Введение в органическую химию",
        theory_blocks=[
            {"type": "text", "content": "Органическая химия изучает соединения углерода (кроме оксидов, карбидов, угольной кислоты и ее солей). Основные классы: алканы, алкены, спирты, карбоновые кислоты."},
            {"type": "image", "src": "assets/images/organic_molecule.png", "caption": "Модель метана CH₄"}
        ],
        tasks_data=[
            {'type': 'choice', 'variants': [
                {"variant_data": {"question_text": "Какая формула соответствует метану?", "options": ["CH₄", "C₂H₆", "C₃H₈", "C₄H₁₀"]}, "correct_answer": {"answer": 0}},
            ]},
        ]
    )

    # Итоговый тест 9 класса
    create_lesson(track9, 14, "Итоговый тест за 9 класс",
        is_test=True, xp=200, est_time=40,
        tasks_data=[
            {'type': 'choice', 'source_type': 'generated', 'generator_id': gen_choice_9.id},
            {'type': 'balance_equation', 'source_type': 'generated', 'generator_id': gen_balance.id},
            {'type': 'calculation', 'source_type': 'generated', 'generator_id': gen_calc.id},
            {'type': 'match', 'variants': [
                {"variant_data": {"left_items": ["Fe", "Cl₂", "NaOH", "H₂SO₄"], "right_items": ["металл", "неметалл", "щелочь", "кислота"]}, "correct_answer": {"matches": {"0": 0, "1": 1, "2": 2, "3": 3}}}
            ]},
            {'type': 'classify', 'variants': [
                {"variant_data": {"item_name": "CaCO₃", "options": ["оксид", "кислота", "основание", "соль"]}, "correct_answer": {"class": "соль"}},
            ]},
        ]
    )

    seed_shop_data(db)
    seed_achievements(db)
    seed_leaderboard_categories(db)
    seed_test_user(db)

    print("Реальный контент успешно добавлен.")

if __name__ == "__main__":
    seed_data()