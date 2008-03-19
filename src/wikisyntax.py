from docutils.nodes import Inline, TextElement

class strikeout(Inline, TextElement): pass

import docutils.writers.html4css1 

class MyHTMLWriter(docutils.writers.html4css1.Writer):
    def __init__(self):
        docutils.writers.html4css1.Writer.__init__(self)
        self.translator_class = MyHTMLTranslator

class MyHTMLTranslator(docutils.writers.html4css1.HTMLTranslator):
    def visit_strikeout(self, node):
        self.body.append(self.starttag(node, 'strike', ''))

    def depart_strikeout(self, node):
        self.body.append('</strike>')

from docutils.parsers.rst.roles import register_generic_role

register_generic_role('strike', strikeout)
