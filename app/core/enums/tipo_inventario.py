from enum import Enum

class InventoryFilterType(str, Enum):
    bajo = "bajo"       # Inventario menor o igual al mínimo
    bueno = "bueno"     # Inventario por encima del mínimo
    todos = "todos"     # Todos los productos
