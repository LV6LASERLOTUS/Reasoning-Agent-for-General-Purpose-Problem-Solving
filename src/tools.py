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

        if suggestion:

            suggestions = result.append(suggestion)
            return f"Page not found do you wanna try searching {suggestions} instead"

        return f"Page not found do you wanna try searching one of {result} instead"
    
def search_browser(input):
    search = DDGS()
    try:
        result = search.text(input,max_result=2)
    
    except Exception as e:
        print(e)
        return

def execute_python():
    ...


if __name__ =='__main__':

    input="1 + 1"
    output=search_wiki(input)
    print(output)