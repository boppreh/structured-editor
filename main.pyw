import sys
from libeditor import MainWindow, Document
from language import read_language

class CodeDocument(Document):
    def __init__(self, contents_text='', path=None):
        super(CodeDocument, self).__init__(contents_text, path)
        self.contents = json.parse(contents_text)

main_window = MainWindow('Example Application', CodeDocument)
json = read_language('json')

files = sys.argv[1:] or ["test_files/1.json"]
if files:
    for path in files:
        main_window.openDocument(path)

main_window.run()
