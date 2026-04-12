from src.search import uniform_cost_search, astar_search, greedy_search, depth_limited_search


def test_uniform_cost_aveiro_faro():
    result = uniform_cost_search('Aveiro', 'Faro')
    assert result['success'] is True
    assert result['path'] == ['Aveiro', 'Leiria', 'Santarém', 'Évora', 'Beja', 'Faro']
    assert result['cost'] == 532


def test_astar_matches_optimal_for_faro():
    ucs = uniform_cost_search('Aveiro', 'Faro')
    astar = astar_search('Aveiro', 'Faro')
    assert astar['success'] is True
    assert astar['cost'] == ucs['cost']
    assert astar['path'] == ucs['path']


def test_greedy_reaches_goal_for_faro():
    result = greedy_search('Braga', 'Faro')
    assert result['success'] is True
    assert result['path'][0] == 'Braga'
    assert result['path'][-1] == 'Faro'


def test_dls_finds_solution_with_enough_depth():
    result = depth_limited_search('Aveiro', 'Faro', depth_limit=10)
    assert result['success'] is True
    assert result['path'][0] == 'Aveiro'
    assert result['path'][-1] == 'Faro'
