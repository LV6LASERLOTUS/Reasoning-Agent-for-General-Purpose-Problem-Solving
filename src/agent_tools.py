from wikipedia import WikipediaPage, wikipedia
from wikipedia.exceptions import DisambiguationError, PageError
from ddgs import DDGS


def search_wiki(query: str) -> str:
    """Searches wikipedia for the query

    This method searches wikipedia and returns the corresponding page's summary,
    otherwise returns search result and a possible suggestion.

    Args:
        query (str): The query you want to search

    Returns:
        str: The corresponding article's summary,
             or the search result and possible suggestion,
             or Page not found
    """

    try:
        # Attempt to fetch the wikipedia
        page = WikipediaPage(query)
        content = page.summary
        return content

    except (PageError, DisambiguationError):
        # If page is not found search for alternatives
        search_results, suggestion = wikipedia.search(query, suggestion=True)

        # if there is suggeston and search results merge them
        if suggestion and search_results is not None:
            search_results.append(suggestion)
            return f"Page not found do you wanna try searching one of  these: {search_results}"

        return "Page not found"


def search_browser(query):
    """Search the web and return the top results.

    This method searches the web using available backend from
    (bing, brave, duckduckgo, google, mojeek, yandex, yahoo, wikipedia)

    Args:
        query (str): The search query string.

    Returns:
        dict or None: A dictionary mapping result titles to their content
                      for the top 2 search results. Returns None if an error occurs.
    """
    search = DDGS()
    try:
        # Search and returns the top 2 result
        results = search.text(query, max_result=5)

        # Create a dictionary of titles and bodies from the result
        content = {result["title"]: result["body"] for result in results}
        return content
    except Exception as e:
        print(e)
        return None


if __name__ == "__main__":
    query = "755161"
    output = search_wiki(query)
    print(output)
