"""Definición de los juegos: columnas, rangos y alias aceptados en los CSV."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Group:
    """Grupo de valores del sorteo (p. ej. números principales o estrellas)."""
    name: str
    count: int
    low: int
    high: int
    unique: bool = True  # sin repetidos dentro del grupo
    aliases: tuple = ()  # nombres de columna aceptados (sin el sufijo numérico)

    def columns(self):
        if self.count == 1:
            return [self.name]
        return [f"{self.name}_{i}" for i in range(1, self.count + 1)]


@dataclass(frozen=True)
class Game:
    key: str
    label: str
    groups: tuple = field(default_factory=tuple)
    date_aliases: tuple = ("fecha", "date", "draw_date")

    def all_columns(self):
        return [c for g in self.groups for c in g.columns()]


EUROMILLIONS = Game(
    key="euromillions",
    label="EuroMillions",
    groups=(
        Group("n", 5, 1, 50, aliases=("n", "num", "numero", "number", "ball", "bola")),
        Group("star", 2, 1, 12, aliases=("star", "estrella", "e", "lucky_star")),
    ),
)

BONOLOTO = Game(
    key="bonoloto",
    label="Bonoloto",
    groups=(
        Group("n", 6, 1, 49, aliases=("n", "num", "numero", "number", "ball", "bola")),
        Group("complementario", 1, 1, 49, aliases=("complementario", "c", "comp", "bonus")),
        # El reintegro puede coincidir con un número principal: es otro rango (0-9).
        Group("reintegro", 1, 0, 9, aliases=("reintegro", "r", "refund")),
    ),
)

GAMES = {g.key: g for g in (EUROMILLIONS, BONOLOTO)}


def get_game(key: str) -> Game:
    try:
        return GAMES[key.lower()]
    except KeyError:
        raise ValueError(f"Juego desconocido: {key!r}. Opciones: {sorted(GAMES)}")
