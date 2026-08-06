from graph.workflow import MAX_TOOL_ERRORS, echec_node, route_after_tools


def test_route_after_tools_continues_when_under_threshold():
    state = {"tool_error_count": MAX_TOOL_ERRORS - 1}
    assert route_after_tools(state) == "agent"


def test_route_after_tools_routes_to_echec_when_threshold_reached():
    state = {"tool_error_count": MAX_TOOL_ERRORS}
    assert route_after_tools(state) == "echec"


def test_route_after_tools_defaults_to_zero_errors_when_missing():
    assert route_after_tools({}) == "agent"


def test_echec_node_reports_error_count_in_message():
    state = {"tool_error_count": 3}
    result = echec_node(state)
    message = result["messages"][0]
    assert "3" in message.content
    assert "interrompue" in message.content.lower()
