from core.drawing.lighting import _lighting_grid_dimensions, _lighting_positions


def test_four_lighting_points_use_balanced_two_by_two_grid():
    assert _lighting_grid_dimensions(4, width=6.0, length=3.0) == (2, 2)


def test_three_lighting_points_use_horizontal_line_in_extremely_wide_room():
    assert _lighting_grid_dimensions(3, width=9.0, length=3.0) == (3, 1)


def test_four_lighting_points_stay_in_grid_in_extremely_wide_room():
    assert _lighting_grid_dimensions(4, width=9.0, length=3.0) == (2, 2)


def test_four_lighting_points_stay_in_grid_in_extremely_tall_room():
    assert _lighting_grid_dimensions(4, width=2.0, length=8.0) == (2, 2)


def test_eight_lighting_points_follow_tall_room_shape():
    assert _lighting_grid_dimensions(8, width=3.8, length=9.9) == (2, 4)


def test_four_lighting_positions_have_two_columns_and_two_rows():
    positions = _lighting_positions((0.0, 0.0), width=6.0, length=3.0, count=4)

    xs = sorted({round(x, 8) for x, _ in positions})
    ys = sorted({round(y, 8) for _, y in positions})

    assert len(positions) == 4
    assert len(xs) == 2
    assert len(ys) == 2


def test_two_lighting_points_follow_tall_room_direction():
    assert _lighting_grid_dimensions(2, width=2.0, length=5.0) == (1, 2)


def test_eight_lighting_positions_have_two_columns_and_four_rows():
    positions = _lighting_positions((0.0, 0.0), width=4.1, length=10.2, count=8)

    xs = sorted({round(x, 8) for x, _ in positions})
    ys = sorted({round(y, 8) for _, y in positions})

    assert len(positions) == 8
    assert len(xs) == 2
    assert len(ys) == 4
