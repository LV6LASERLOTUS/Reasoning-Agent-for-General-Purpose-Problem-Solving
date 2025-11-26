from wikipedia import WikipediaPage
from ddgs import DDGS


class ToolBox():
    def __init__(self):
        ...
    def search_wiki(self, input:str)->str:
        try:
            result = WikipediaPage(input)
            return result.summary
        except Exception as e:
            print(e)
            return 'Unable to retrieve information right now'
        
    def search_browser(self,input):
        search = DDGS()
        try:
            result = search.text(input,max_result=2)
            return result
        
        except Exception as e:
            print(e)
            return

    def execute_python(self):
        ...


if __name__ =='__main__':

    test=ToolBox()
    input='First for Women'
    print(test.search_browser(input))