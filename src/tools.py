from wikipedia import WikipediaPage,wikipedia
from wikipedia.exceptions import DisambiguationError,PageError
from ddgs import DDGS



def search_wiki(input:str)->str:
    try:
        page = WikipediaPage(input)
        content=page.summary
        return content
    
    except (PageError,DisambiguationError):

        result, suggestion=wikipedia.search(input,suggestion=True)
        
        #merge suggestion with actual result inside the wiki

        if suggestion and result is not None:
            result.append(suggestion)
            return f"Page not found do you wanna try searching {result} instead"

        return f"Page not found"
    
def search_browser(input):
    search = DDGS()
    try:
        results = search.text(input,max_result=2)
        content = {result['title']:result['body'] for result in results}
        return content
    except Exception as e:
        print(e)
        return None


if __name__ =='__main__':

    input="755161"
    output=search_wiki(input)
    print(output)