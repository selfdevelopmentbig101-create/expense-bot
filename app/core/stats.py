"""Small statistics helpers. Pure logic."""


def percentages(values: list[int]) -> list[int]:
    """Whole-number shares that add up to exactly 100 (largest remainder method).

    [1, 1, 1] -> [34, 33, 33]; all zeros -> all zeros. Order is preserved.
    """
    total = sum(values)
    if total <= 0:
        return [0] * len(values)

    floors = [value * 100 // total for value in values]
    remainders = [value * 100 % total for value in values]
    missing = 100 - sum(floors)
    # Biggest remainders get the extra points; ties go to the earlier (bigger) item.
    order = sorted(range(len(values)), key=lambda i: (-remainders[i], i))
    for index in order[:missing]:
        floors[index] += 1
    return floors
