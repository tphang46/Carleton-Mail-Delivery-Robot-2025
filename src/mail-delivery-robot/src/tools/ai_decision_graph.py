from langgraph.graph import StateGraph, END
import ollama

class NavState(dict):
    current_beacon: str
    destination: str
    direction: str | None


# Key: (current_beacon, destination)
# Value: direction
NAV_DECISION_CACHE = {}


def build_nav_graph(node):

    graph = StateGraph(NavState)

    def decide_direction(state: NavState):
        cache_key = (state["current_beacon"], state["destination"])

        if cache_key in NAV_DECISION_CACHE:
            cached_direction = NAV_DECISION_CACHE[cache_key]
            node.get_logger().info(
                f"Cache hit for {cache_key}, using cached direction: {cached_direction}"
            )
            state["direction"] = cached_direction
            return state

        # CACHE MISS
        prompt = f"""
        Robot at {state["current_beacon"]}, destination {state["destination"]}.
        Give a ONE word answer from the options: NAV_LEFT, NAV_RIGHT, NAV_PASS, NAV_U-TURN, NAV_DOCK.
        
        """

        node.get_logger().info(f"Prompt to LLM: {prompt}")

        response = ollama.generate(
            model="qwen2:0.5b",
            prompt=prompt
        )

        node.get_logger().info(f"Raw LLM Response: {response}")

        result = response["response"].strip().split()[0]
        node.get_logger().info(f"LLM Response: {result}")

        # Store in cache
        NAV_DECISION_CACHE[cache_key] = result
        node.get_logger().info(f"Cached decision for {cache_key}: {result}")

        state["direction"] = result
        return state

    graph.add_node("Decide Direction", decide_direction)
    graph.set_entry_point("Decide Direction")
    graph.add_edge("Decide Direction", END)

    return graph.compile()
