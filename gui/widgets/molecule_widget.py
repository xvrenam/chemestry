from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem
from PyQt6.QtCore import Qt, QPointF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPen, QBrush, QColor, QRadialGradient
import math

class AtomItem(QGraphicsEllipseItem):
    def __init__(self, element, x, y, radius=20):
        super().__init__(-radius, -radius, 2*radius, 2*radius)
        self.element = element
        self.setPos(x, y)
        self.setBrush(self._color_for_element(element))
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setAcceptHoverEvents(True)

    def _color_for_element(self, el):
        colors = {
            'H': QColor(255,255,255),
            'O': QColor(255,0,0),
            'C': QColor(50,50,50),
            'N': QColor(0,0,255),
            'Na': QColor(171,92,219),
            'Cl': QColor(0,255,0),
        }
        return QBrush(colors.get(el, QColor(200,200,200)))

class BondItem(QGraphicsLineItem):
    def __init__(self, atom1, atom2, bond_order=1):
        super().__init__()
        self.atom1 = atom1
        self.atom2 = atom2
        self.bond_order = bond_order
        self.update_position()
        pen = QPen(Qt.GlobalColor.darkGray, 3)
        self.setPen(pen)

    def update_position(self):
        p1 = self.atom1.pos()
        p2 = self.atom2.pos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())

class MoleculeWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(self.renderHints())
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.atoms = []
        self.bonds = []

    def load_from_data(self, data: dict):
        """data содержит списки atoms и bonds.
        atoms: [{'element': 'H', 'x': 0, 'y': 0}, ...]
        bonds: [{'from': 0, 'to': 1, 'order': 1}, ...]
        """
        self.scene.clear()
        self.atoms = []
        self.bonds = []
        for a in data['atoms']:
            atom = AtomItem(a['element'], a['x'], a['y'])
            self.scene.addItem(atom)
            self.atoms.append(atom)
        for b in data['bonds']:
            bond = BondItem(self.atoms[b['from']], self.atoms[b['to']], b.get('order', 1))
            self.scene.addItem(bond)
            self.bonds.append(bond)

    def animate_reaction(self, products_data, old_bond_indices_to_break, new_bonds_to_form):
        """Пример анимации разрыва и образования связей."""
        # Упрощённо: скрываем старые связи, меняем позиции атомов, показываем новые связи.
        # Для реальной анимации можно использовать QPropertyAnimation на позиции атомов.
        pass