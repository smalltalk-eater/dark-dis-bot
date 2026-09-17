from dataclasses import dataclass


@dataclass(frozen=True)
class BloomDefinition:
    key: str
    name: str
    description: str
    rarity: str
    weight: int


BLOOMS: dict[str, BloomDefinition] = {
    "pale_bloom": BloomDefinition(
        key="pale_bloom",
        name="Бледный цветок",
        description="Тихий след тех, кто впервые услышал Сад.",
        rarity="RARE",
        weight=45,
    ),
    "thorn_bloom": BloomDefinition(
        key="thorn_bloom",
        name="Шип Эдема",
        description="Цветок, выросший там, где путь пришлось отвоевать.",
        rarity="RARE",
        weight=30,
    ),
    "moon_bloom": BloomDefinition(
        key="moon_bloom",
        name="Лунный цветок",
        description="Раскрывается только в редкие тихие ночи Сада.",
        rarity="EPIC",
        weight=15,
    ),
    "glass_bloom": BloomDefinition(
        key="glass_bloom",
        name="Стеклянный цветок",
        description="Хрупкая память о том, что уже невозможно вернуть.",
        rarity="LEGENDARY",
        weight=8,
    ),
    "lost_bloom": BloomDefinition(
        key="lost_bloom",
        name="Потерянный цветок",
        description="Редчайший росток из той части Эдема, которой больше нет.",
        rarity="MYTHIC",
        weight=2,
    ),
}


# Bloom является бонусной находкой и не заменяет обычную награду EDEN CASE.
BLOOM_CASE_DROP_CHANCE = 0.08
