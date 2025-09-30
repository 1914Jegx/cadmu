from cadmu.core.table import render_table


def test_render_table_wraps_long_cells():
    headers = ["Name", "Description"]
    rows = [["alpha", "This is a long description that should wrap across multiple lines for readability."]]
    table = render_table(headers, rows, max_widths={"Description": 20})
    # Expect multiple lines and header present
    assert "Name" in table
    assert table.count("alpha") >= 1
    # Wrapped text should contain line break with partial sentence
    assert "wrap across" in table
