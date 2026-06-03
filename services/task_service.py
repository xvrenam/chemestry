import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from database.models.content import Task, TaskVariant, TaskGenerator, LessonTask
from database.models.progress import TaskAttempt
from services.statistics_service import StatisticsService

class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def get_lesson_tasks(self, lesson_id: int):
        """Возвращает список заданий урока с сортировкой."""
        return self.db.query(LessonTask, Task)\
            .join(Task, LessonTask.task_id == Task.id)\
            .filter(LessonTask.lesson_id == lesson_id)\
            .order_by(LessonTask.order_index)\
            .all()

    def get_or_create_variant(self, task: Task) -> TaskVariant:
        """
        Для задания возвращает вариант.
        Если есть генератор — создаёт новый вариант на основе шаблона.
        Если есть готовые варианты — выбирает случайный.
        """
        # Если у задания есть готовые варианты, выбираем случайный
        variants = self.db.query(TaskVariant).filter(TaskVariant.base_task_id == task.id).all()
        if variants:
            import random
            variant = random.choice(variants)
            variant.usage_count += 1
            self.db.commit()
            return variant

        # Если задание генерируемое — создаём новый вариант
        if task.generator_id:
            generator = self.db.query(TaskGenerator).filter(TaskGenerator.id == task.generator_id).first()
            if generator:
                variant = self.generate_variant_from_template(task, generator)
                self.db.add(variant)
                self.db.commit()
                self.db.refresh(variant)
                return variant

        # Если нет вариантов и нет генератора — используем встроенные в task данные
        # Создаём фиктивный вариант на основе данных задания
        variant = TaskVariant(
            base_task_id=task.id,
            variant_data={},
            correct_answer=task.correct_answers,
            usage_count=0
        )
        self.db.add(variant)
        self.db.commit()
        self.db.refresh(variant)
        return variant

    def generate_variant_from_template(self, task: Task, generator: TaskGenerator) -> TaskVariant:
        import random
        template = generator.template_data
        task_type = task.type

        variant_data = {}
        correct_answer = None

        if task_type == 'choice':
            # template: {"questions": [{"text": "...", "options": [...], "correct_index": 0}, ...]}
            q = random.choice(template['questions'])
            variant_data = {'question_text': q['text'], 'options': q['options']}
            correct_answer = {'answer': q['correct_index']}

        elif task_type == 'true_false':
            # template: {"statements": [{"text": "...", "is_true": true}, ...]}
            stmt = random.choice(template['statements'])
            variant_data = {'question_text': stmt['text']}
            correct_answer = {'answer': stmt['is_true']}

        elif task_type == 'match':
            # template: {"pairs": [{"left": [...], "right": [...]}]} (генерируемый набор пар)
            pairs = template['pairs']
            selected = random.choice(pairs)
            variant_data = {'left_items': selected['left'], 'right_items': selected['right']}
            correct_answer = {'matches': selected['matches']}  # список пар индексов или словарь

        elif task_type == 'fill_blank':
            # template: {"texts": [{"text": "... ___ ...", "answer": "..."}]}
            item = random.choice(template['texts'])
            variant_data = {'text': item['text']}
            correct_answer = {'answer': item['answer']}

        elif task_type == 'balance_equation':
            # template: {"equations": [{"reactants": [...], "products": [...], "coefficients": [...]}]}
            eq = random.choice(template['equations'])
            variant_data = {'reactants': eq['reactants'], 'products': eq['products']}
            correct_answer = {'coefficients': eq['coefficients']}

        elif task_type == 'predict_product':
            # template: {"reactions": [{"reactants": [...], "products": [...]}]}
            rxn = random.choice(template['reactions'])
            variant_data = {'reactants': rxn['reactants']}
            correct_answer = {'products': rxn['products']}

        elif task_type == 'classify':
            # template: {"items": [{"name": "...", "options": [...], "correct_class": "..."}]}
            item = random.choice(template['items'])
            variant_data = {'item_name': item['name'], 'options': item['options']}
            correct_answer = {'class': item['correct_class']}

        elif task_type == 'calculation':
            # template: {"formulas": [{"params": {...}, "answer": ...}]}
            formula = random.choice(template['formulas'])
            # генерируем случайные параметры
            params = {k: random.randint(v[0], v[1]) for k, v in formula['params'].items()}
            variant_data = {'question': formula['question_template'].format(**params), 'params': params}
            # вычисляем ответ по формуле
            answer = eval(formula['expression'], {}, params)  # осторожно с eval, но для диплома ОК
            correct_answer = {'value': answer, 'tolerance': formula.get('tolerance', 0.01)}

        elif task_type == 'chain_transform':
            # template: {"chains": [{"steps": [...], "starting_material": "..."}]}
            chain = random.choice(template['chains'])
            variant_data = {'starting_material': chain['starting_material'], 'steps': chain['steps']}
            correct_answer = {'products': [step['product'] for step in chain['steps']]}

        elif task_type == 'virtual_lab':
            # template: {"experiments": [{"name": "...", "reagents": [...], "procedure": "...", "observations": {...}}]}
            exp = random.choice(template['experiments'])
            variant_data = {'name': exp['name'], 'reagents': exp['reagents'], 'procedure': exp['procedure']}
            correct_answer = {'expected_observation': exp['expected_observation']}

        elif task_type == 'find_error':
            # template: {"texts": [{"text": "...", "error_position": ..., "correct_text": "..."}]}
            err = random.choice(template['texts'])
            variant_data = {'text': err['text']}
            correct_answer = {'error_position': err['error_position'], 'correction': err['correct_text']}

        elif task_type == 'open_experiment':
            # template: {"scenarios": [{"description": "...", "expected_answer": "..."}]}
            scen = random.choice(template['scenarios'])
            variant_data = {'description': scen['description']}
            correct_answer = {'keywords': scen['keywords']}  # для проверки открытого ответа по ключевым словам

        elif task_type == 'puzzle':
            # template: {"puzzles": [{"clues": [...], "answer": "..."}]}
            puz = random.choice(template['puzzles'])
            variant_data = {'clues': puz['clues']}
            correct_answer = {'answer': puz['answer']}

        elif task_type == 'timed':
            # template: {"tasks": [{"text": "...", "answer": "...", "time_limit": 30}]}
            t = random.choice(template['tasks'])
            variant_data = {'text': t['text'], 'time_limit': t['time_limit']}
            correct_answer = {'answer': t['answer']}

        else:
            # fallback
            variant_data = {}
            correct_answer = task.correct_answers

        variant = TaskVariant(
            base_task_id=task.id,
            variant_data=variant_data,
            correct_answer=correct_answer,
            usage_count=0
        )
        return variant

    def check_answer(self, variant: TaskVariant, user_answer: dict, scoring_type: str, max_score: int) -> tuple:
        correct = variant.correct_answer
        if isinstance(correct, str):
            correct = json.loads(correct)

        is_correct = False

        # Обработка различных форматов ответов:
        if scoring_type == 'binary':
            if 'answer' in correct:
                is_correct = (user_answer.get('answer') == correct['answer'])
            elif 'coefficients' in correct:
                user_coeff = user_answer.get('coefficients', [])
                is_correct = (user_coeff == correct['coefficients'])
            elif 'products' in correct:
                if correct['products'] and isinstance(correct['products'], list):
                    # chain_transform: список стадий (списки строк)
                    if correct['products'] and isinstance(correct['products'][0], list):
                        user_prods = user_answer.get('products', [])
                        if len(user_prods) != len(correct['products']):
                            is_correct = False
                        else:
                            is_correct = True
                            for u, c in zip(user_prods, correct['products']):
                                if set(u) != set(c):
                                    is_correct = False
                                    break
                    else:
                        # predict_product: плоский список строк
                        user_prods = user_answer.get('products', [])
                        # Нормализуем до плоского списка строк
                        if user_prods and isinstance(user_prods[0], list):
                            user_prods = [item for sublist in user_prods for item in sublist]
                        is_correct = set(user_prods) == set(correct['products'])
            elif 'class' in correct:
                is_correct = (user_answer.get('class') == correct['class'])
            elif 'value' in correct:
                try:
                    uv = float(user_answer.get('value'))
                    cv = float(correct['value'])
                    tolerance = correct.get('tolerance', 0.01)
                    is_correct = abs(uv - cv) <= tolerance
                except:
                    is_correct = False
            elif 'matches' in correct:
                user_matches = user_answer.get('matches', {})
                # user_matches dict: key=index left, value=index right
                is_correct = (user_matches == correct['matches'])
            elif 'observation' in correct:
                is_correct = (user_answer.get('observation') == correct['observation'])
            elif 'error_position' in correct:
                is_correct = (user_answer.get('error_position') == correct['error_position'] and
                            user_answer.get('correction', '').strip() == correct['correction'])
            elif 'keywords' in correct:
                # открытый ответ: проверяем наличие ключевых слов
                text = user_answer.get('answer_text', '').lower()
                keywords = correct.get('keywords', [])
                is_correct = all(kw in text for kw in keywords)
            else:
                is_correct = (user_answer == correct)

            score = max_score if is_correct else 0
            return is_correct, score, max_score

        elif scoring_type == 'partial':
            # Для match или других частичных оценок
            if 'matches' in correct:
                user_matches = user_answer.get('matches', {})
                correct_matches = correct['matches']
                total = len(correct_matches)
                correct_count = sum(1 for k,v in user_matches.items() if correct_matches.get(k) == v)
                score = int(max_score * (correct_count / total))
                is_correct = (score >= max_score // 2)
                return is_correct, score, max_score
            # Для других типов с частичной оценкой можно расширить

        # fallback
        is_correct = (user_answer == correct)
        score = max_score if is_correct else 0
        return is_correct, score, max_score

    def save_attempt(self, user_id: uuid.UUID, task_id: int, variant_id: int,
                     user_answer: dict, lesson_progress_id: int = None) -> TaskAttempt:
        """
        Сохраняет попытку выполнения задания, вычисляя результат.
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        variant = self.db.query(TaskVariant).filter(TaskVariant.id == variant_id).first()
        is_correct, score_earned, score_max = self.check_answer(
            variant, user_answer, task.scoring_type, task.max_score
        )

        attempt = TaskAttempt(
            user_id=user_id,
            task_id=task_id,
            variant_id=variant_id,
            user_answer=user_answer,
            is_correct=is_correct,
            score_earned=score_earned,
            score_max=score_max,
            started_at=datetime.now(),   # упрощённо
            completed_at=datetime.now(),
            time_spent=0,
            hints_used=0,
            hints_cost=0,
            lesson_progress_id=lesson_progress_id,
            attempt_number=1  # позже можно увеличивать
        )
        self.db.add(attempt)
        self.db.commit()
        stats_svc = StatisticsService(self.db)
        stats_svc.update_topic_stats(
            user_id=user_id,
            topic_tags=task.topic_tags,
            is_correct=is_correct,
            task_type=task.type
        )
        return attempt