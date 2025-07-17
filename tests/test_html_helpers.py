from auto.html_helpers import count_link_states


def test_count_link_states():
    html = """
    <div>
      <a href='/pr1'><span class='text-green-500'>+1</span></a>
      <span>Merged</span>
    </div>
    <div>
      <a href='/pr2'><span class='text-green-500'>+2</span></a>
    </div>
    <div>
      <a href='/pr3'><span class='text-green-500'>+3</span></a>
    </div>
    """
    merged, active = count_link_states(html)
    assert merged == 1
    assert active == 2
