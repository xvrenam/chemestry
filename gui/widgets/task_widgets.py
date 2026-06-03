# gui/widgets/task_widgets.py (полностью)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QRadioButton, QButtonGroup,
    QCheckBox, QLineEdit, QPushButton, QHBoxLayout, QComboBox,
    QListWidget, QListWidgetItem, QTextEdit, QSpinBox, QGridLayout,
    QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QTimer
import json

class BaseTaskWidget(QWidget):
    answer_submitted = pyqtSignal(dict)

    def __init__(self, task, variant, parent=None):
        super().__init__(parent)
        self.task = task
        self.variant = variant
        self.variant_data = variant.variant_data or {}
        if isinstance(self.variant_data, str):
            self.variant_data = json.loads(self.variant_data)
        self.init_ui()

    def init_ui(self):
        pass

    def get_answer(self) -> dict:
        raise NotImplementedError

    def emit_answer(self):
        self.answer_submitted.emit(self.get_answer())


# ---------- Простые типы ----------
class ChoiceTaskWidget(BaseTaskWidget):
    def init_ui(self):
        layout = QVBoxLayout()
        self.label = QLabel(self.variant_data.get('question_text', self.task.question_text))
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        self.group = QButtonGroup(self)
        self.radio_buttons = []
        options = self.variant_data.get('options', [])
        for i, opt in enumerate(options):
            rb = QRadioButton(opt)
            self.group.addButton(rb, i)
            layout.addWidget(rb)
            self.radio_buttons.append(rb)

        btn = QPushButton("Ответить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        return {'answer': self.group.checkedId() if self.group.checkedId() != -1 else None}


class TrueFalseTaskWidget(BaseTaskWidget):
    def init_ui(self):
        layout = QVBoxLayout()
        self.label = QLabel(self.variant_data.get('question_text', self.task.question_text))
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        self.group = QButtonGroup(self)
        self.true_rb = QRadioButton("Верно")
        self.false_rb = QRadioButton("Неверно")
        self.group.addButton(self.true_rb, 1)
        self.group.addButton(self.false_rb, 0)
        layout.addWidget(self.true_rb)
        layout.addWidget(self.false_rb)

        btn = QPushButton("Ответить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        return {'answer': self.true_rb.isChecked()}


class MatchTaskWidget(BaseTaskWidget):
    def init_ui(self):
        import random
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Сопоставьте элементы из левой колонки с правой:"))

        grid = QGridLayout()
        
        # Сохраняем исходное соответствие индексов перед перемешиванием
        left_items = self.variant_data.get('left_items', [])
        right_items = self.variant_data.get('right_items', [])
        
        # Формируем пары (исходный_индекс, значение) и перемешиваем
        left_pairs = list(enumerate(left_items))
        right_pairs = list(enumerate(right_items))
        random.shuffle(left_pairs)
        random.shuffle(right_pairs)
        
        # Извлекаем тексты и исходные индексы
        self.left_original_indices = [orig for orig, _ in left_pairs]
        self.left_texts = [text for _, text in left_pairs]
        
        self.right_original_indices = [orig for orig, _ in right_pairs]
        self.right_texts = [text for _, text in right_pairs]
        
        self.combos = []

        for i, left_text in enumerate(self.left_texts):
            label = QLabel(left_text)
            combo = QComboBox()
            combo.addItem("Выберите...", None)
            for j, right_text in enumerate(self.right_texts):
                # В userData храним исходный индекс правого элемента
                combo.addItem(right_text, self.right_original_indices[j])
            grid.addWidget(label, i, 0)
            grid.addWidget(combo, i, 1)
            self.combos.append(combo)

        layout.addLayout(grid)

        btn = QPushButton("Ответить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        matches = {}
        for i, combo in enumerate(self.combos):
            orig_left_idx = self.left_original_indices[i]
            orig_right_idx = combo.currentData()  # исходный индекс правого элемента
            if orig_right_idx is not None:
                matches[str(orig_left_idx)] = orig_right_idx
        return {'matches': matches}


class FillBlankTaskWidget(BaseTaskWidget):
    def init_ui(self):
        layout = QVBoxLayout()
        self.label = QLabel(self.variant_data.get('text', ''))
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Введите пропущенное слово/формулу")
        layout.addWidget(self.input)

        btn = QPushButton("Ответить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        return {'answer': self.input.text().strip()}


# ---------- Химические типы ----------
class BalanceEquationWidget(BaseTaskWidget):
    def init_ui(self):
        layout = QVBoxLayout()
        reactants = ' + '.join(self.variant_data.get('reactants', []))
        products = ' + '.join(self.variant_data.get('products', []))
        self.equation_label = QLabel(f"{reactants} → {products}")
        layout.addWidget(self.equation_label)

        layout.addWidget(QLabel("Введите коэффициенты (через пробел):"))
        self.coeff_input = QLineEdit()
        layout.addWidget(self.coeff_input)

        btn = QPushButton("Проверить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        coeffs = self.coeff_input.text().strip().split()
        return {'coefficients': [int(c) for c in coeffs] if coeffs else []}


class PredictProductWidget(BaseTaskWidget):
    def init_ui(self):
        layout = QVBoxLayout()
        reactants = ' + '.join(self.variant_data.get('reactants', []))
        layout.addWidget(QLabel(f"Реагенты: {reactants}"))
        layout.addWidget(QLabel("Предскажите продукты реакции:"))
        self.input = QLineEdit()
        self.input.setPlaceholderText("Например: NaCl, H2O")
        layout.addWidget(self.input)

        btn = QPushButton("Ответить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        text = self.input.text().strip()
        # Разделяем по '+' или ',' и удаляем пустые строки/пробелы
        products = [p.strip() for p in text.replace('+', ',').split(',') if p.strip()]
        return {'products': products}


class ClassifyTaskWidget(BaseTaskWidget):
    def init_ui(self):
        layout = QVBoxLayout()
        self.label = QLabel(f"К какому классу относится: {self.variant_data.get('item_name', '')}?")
        layout.addWidget(self.label)

        self.combo = QComboBox()
        self.options = self.variant_data.get('options', [])
        self.combo.addItems(self.options)
        layout.addWidget(self.combo)

        btn = QPushButton("Ответить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        return {'class': self.combo.currentText()}


class CalculationTaskWidget(BaseTaskWidget):
    def init_ui(self):
        layout = QVBoxLayout()
        self.label = QLabel(self.variant_data.get('question', ''))
        layout.addWidget(self.label)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Введите число (например, 0.5 или 0,5)")
        layout.addWidget(self.input)

        btn = QPushButton("Ответить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        text = self.input.text().strip()
        # Заменяем запятую на точку для корректного преобразования
        text = text.replace(',', '.')
        try:
            val = float(text)
            return {'value': val}
        except ValueError:
            return {'value': None}
        


class ChainTransformWidget(BaseTaskWidget):
    def init_ui(self):
        layout = QVBoxLayout()
        start = self.variant_data.get('starting_material', '')
        steps = self.variant_data.get('steps', [])
        layout.addWidget(QLabel(f"Исходное вещество: {start}"))
        layout.addWidget(QLabel("Запишите продукты каждой стадии:"))

        self.inputs = []
        for i, step in enumerate(steps, 1):
            lbl = QLabel(f"Стадия {i} ({step.get('reagent', '')}): ")
            inp = QLineEdit()
            layout.addWidget(lbl)
            layout.addWidget(inp)
            self.inputs.append(inp)

        btn = QPushButton("Ответить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        products = list()
        for inp in self.inputs:
            text = inp.text().strip()
            prods = [p.strip() for p in text.replace('+', ',').split(',') if p.strip()]
            products.append(prods)
        return {'products': products}


# ---------- Интерактивные / продвинутые ----------
class VirtualLabWidget(BaseTaskWidget):
    """Упрощённая версия: выбор действий и наблюдение результата."""
    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Эксперимент: {self.variant_data.get('name', '')}"))
        layout.addWidget(QLabel("Реагенты: " + ', '.join(self.variant_data.get('reagents', []))))
        layout.addWidget(QLabel("Процедура: " + self.variant_data.get('procedure', '')))

        layout.addWidget(QLabel("Что наблюдаете?"))
        self.observation_combo = QComboBox()
        self.observations = self.variant_data.get('observations', ["Выделение газа", "Изменение цвета", "Осадок", "Ничего"])
        self.observation_combo.addItems(self.observations)
        layout.addWidget(self.observation_combo)

        btn = QPushButton("Проверить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        return {'observation': self.observation_combo.currentText()}


class PuzzleTaskWidget(BaseTaskWidget):
    """Кроссворд / химический ребус."""
    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Разгадайте:"))
        for clue in self.variant_data.get('clues', []):
            layout.addWidget(QLabel(f"• {clue}"))
        self.input = QLineEdit()
        layout.addWidget(self.input)

        btn = QPushButton("Ответить")
        btn.clicked.connect(self.emit_answer)
        layout.addWidget(btn)
        self.setLayout(layout)

    def get_answer(self):
        return {'answer': self.input.text().strip()}


class TimedTaskWidget(BaseTaskWidget):
    """Задание с таймером."""
    answer_submitted = pyqtSignal(dict)

    def init_ui(self):
        layout = QVBoxLayout()
        self.time_left = self.variant_data.get('time_limit', 30)
        self.timer_label = QLabel(f"Осталось: {self.time_left} сек")
        layout.addWidget(self.timer_label)

        layout.addWidget(QLabel(self.variant_data.get('text', '')))

        self.input = QLineEdit()
        layout.addWidget(self.input)

        self.btn = QPushButton("Ответить")
        self.btn.clicked.connect(self.emit_answer)
        layout.addWidget(self.btn)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        self.setLayout(layout)

    def update_timer(self):
        self.time_left -= 1
        self.timer_label.setText(f"Осталось: {self.time_left} сек")
        if self.time_left <= 0:
            self.timer.stop()
            self.btn.setEnabled(False)
            QMessageBox.information(self, "Время вышло", "Время истекло!")
            self.answer_submitted.emit({'answer': None, 'timed_out': True})

    def get_answer(self):
        self.timer.stop()
        return {'answer': self.input.text(), 'timed_out': False}


# ---------- Фабрика ----------
def create_task_widget(task, variant) -> BaseTaskWidget:
    mapping = {
        'choice': ChoiceTaskWidget,
        'true_false': TrueFalseTaskWidget,
        'match': MatchTaskWidget,
        'fill_blank': FillBlankTaskWidget,
        'balance_equation': BalanceEquationWidget,
        'predict_product': PredictProductWidget,
        'classify': ClassifyTaskWidget,
        'calculation': CalculationTaskWidget,
        'chain_transform': ChainTransformWidget,
        'virtual_lab': VirtualLabWidget,
        'puzzle': PuzzleTaskWidget,
        'timed': TimedTaskWidget,
    }
    widget_class = mapping.get(task.type, ChoiceTaskWidget)
    return widget_class(task, variant)