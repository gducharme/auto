from auto.html_utils import extract_links_with_green_span


def test_extract_links_with_green_span():
    html = """
    <div><a href='/task1'><span class='text-green-500'>+1</span></a></div>
    <div><a href='/task2'><span class='text-red-500'>-1</span></a></div>
    <div><a href='/task3'><span class='text-green-500'>+2</span></a></div>
    """
    links = extract_links_with_green_span(html)
    assert links == ['/task1', '/task3']


def test_extract_links_skips_merged_items():
    html = """
    <div>
      <a href='/task1'><span class='text-green-500'>+1</span></a>
      <button><svg></svg>Merged</button>
    </div>
    <div>
      <a href='/task2'><span class='text-green-500'>+2</span></a>
    </div>
    """
    links = extract_links_with_green_span(html)
    assert links == ['/task2']
