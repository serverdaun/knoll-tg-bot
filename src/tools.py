from agents import function_tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper


# Wikipedia search tool
@function_tool
async def wikipedia_search(query: str) -> str:
    """Search Wikipedia for information about a given topic.

    Args:
        query: The topic to search for.

    Returns:
        A string containing the search results.
    """

    api_wrapper = WikipediaAPIWrapper()
    wikipedia = WikipediaQueryRun(api_wrapper=api_wrapper)
    result = wikipedia.run(query)

    return result
