# logic that preserves NotImplemented -----------------------------------------
def not_ni(a):
    if a == NotImplemented:
        return NotImplemented
    else:
        return not a

def and_ni(a):
    if a == NotImplemented or b == NotImplemented:
        return NotImplemented
    else:
        return a and b

def or_ni(a):
    if a == NotImplemented or b == NotImplemented:
        return NotImplemented
    else:
        return a or b




# query objects ---------------------------------------------------------------
class Query(object):
    def __str__(self):
        return self.visit(StringifyVisitor())

    def __repr__(self):
        return self.visit(ReprVisitor())

    # deriving classes need only implement __le__ and __eq__
    def __ne__(self, other):
        return not_ni(self.__eq__(other))

    def __gt__(self, other):
        return not_ni(self.__le__(other))

    def __le__(self, other):
        return or_ni(
                self.__lt__(other),
                self.__eq__(other))

    def __ge__(self, other):
        return not_ni(self.__lt__(other))




class TagQuery(Query):
    def __init__(self, name):
        self.name = name

    def visit(self, visitor, *args):
        return visitor.visit_tag_query(self, *args)

    def __eq__(self, other):
        if not isinstance(other, TagQuery):
            return False
        else:
            return self.name == other.name
    
    def __lt__(self, other):
        if not isinstance(other, TagQuery):
            return True
        else:
            return self.name < other.name

class FulltextQuery(Query):
    def __init__(self, substr):
        self.substr = substr

    def visit(self, visitor, *args):
        return visitor.visit_fulltext_query(self, *args)

    def __eq__(self, other):
        if not isinstance(other, FulltextQuery):
            return False
        else:
            return self.substr == other.substr

    def __lt__(self, other):
        if not isinstance(other, FulltextQuery):
            return not isinstance(other, TagQuery)
        else:
            return self.substr < other.substr

class NotQuery(Query):
    def __init__(self, child):
        self.child = child

    def visit(self, visitor, *args):
        return visitor.visit_not_query(self, *args)

    def __eq__(self, other):
        if not isinstance(other, NotQuery):
            return False
        else:
            return self.child == other.child

    def __lt__(self, other):
        if not isinstance(other, NotQuery):
            return not isinstance(other, (TagQuery, FulltextQuery))
        else:
            return self.child < other.child

class AndQuery(Query):
    def __init__(self, children):
        self.children = children[:]
        self.children.sort()

    def visit(self, visitor, *args):
        return visitor.visit_and_query(self, *args)

    def __eq__(self, other):
        if not isinstance(other, AndQuery):
            return False
        else:
            return self.children == other.children

    def __lt__(self, other):
        if not isinstance(other, AndQuery):
            return not isinstance(other, (TagQuery, FulltextQuery, NotQuery))
        else:
            return self.children < other.children

class OrQuery(Query):
    def __init__(self, children):
        self.children = children[:]
        self.children.sort()

    def visit(self, visitor, *args):
        return visitor.visit_or_query(self, *args)

    def __eq__(self, other):
        if not isinstance(other, OrQuery):
            return False
        else:
            return self.children == other.children

    def __lt__(self, other):
        if not isinstance(other, OrQuery):
            return not isinstance(other, (TagQuery, FulltextQuery, NotQuery, AndQuery))
        else:
            return self.children < other.children





# normalizing query constructors ----------------------------------------------
def make_not_query(child):
    if isinstance(child, NotQuery):
        return child.child
    else:
        return NotQuery(child)

def _make_flattened_children_query(klass, children):
    new_children = []
    for ch in children:
        if isinstance(ch, klass):
            new_children.extend(ch.children)
        else:
            new_children.append(ch)

    return klass(new_children)

def make_and_query(children):
    return _make_flattened_children_query(AndQuery, children)

def make_or_query(children):
    return _make_flattened_children_query(OrQuery, children)




# operator precedence ---------------------------------------------------------
_PREC_OR = 10
_PREC_AND = 20
_PREC_NOT = 30




# query visitors --------------------------------------------------------------
class StringifyVisitor(object):
    def visit_tag_query(self, q, enclosing_prec=0):
        return q.name

    def visit_fulltext_query(self, q, enclosing_prec=0):
        return '"%s"' % q.substr

    def visit_not_query(self, q, enclosing_prec=0):
        if isinstance(q.child, TagQuery):
            return '-%s' % q.child.name
        else:
            if enclosing_prec > _PREC_NOT:
                return "(not %s)" % q.child.visit(self, _PREC_NOT)
            else:
                return "not %s" % q.child.visit(self, _PREC_NOT)

    def visit_and_query(self, q, enclosing_prec=0):
        me = " ".join(child.visit(self, _PREC_AND) 
                for child in q.children)
        
        if enclosing_prec > _PREC_AND:
            return "(%s)" % me
        else:
            return me

    def visit_or_query(self, q, enclosing_prec=0):
        me = " or ".join(child.visit(self, _PREC_OR) 
                for child in q.children)
        
        if enclosing_prec > _PREC_OR:
            return "(%s)" % me
        else:
            return me




class ReprVisitor(object):
    def visit_tag_query(self, q, enclosing_prec=0):
        return "%s(%s)" % (q.__class__.__name__, repr(q.name))

    def visit_fulltext_query(self, q, enclosing_prec=0):
        return "%s(%s)" % (q.__class__.__name__, repr(q.substr))

    def visit_not_query(self, q, enclosing_prec=0):
        return "%s(%s)" % (q.__class__.__name__, repr(q.child))

    def visit_and_query(self, q, enclosing_prec=0):
        return "%s(%s)" % (q.__class__.__name__, repr(q.children))

    def visit_or_query(self, q, enclosing_prec=0):
        return "%s(%s)" % (q.__class__.__name__, repr(q.children))




# lexer data ------------------------------------------------------------------
_and = intern("and")
_or = intern("or")
_not = intern("not")
_openpar = intern("openpar")
_closepar = intern("closepar")
_tag = intern("tag")
_negtag = intern("negtag")
_fulltext = intern("fulltext")
_whitespace = intern("whitespace")




from synoptic.lex import RE
_LEX_TABLE = [
    (_and, RE(r"and")),
    (_or, RE(r"or")),
    (_not, RE(r"not")),
    (_openpar, RE(r"\(")),
    (_closepar, RE(r"\)")),
    (_tag, RE(r"[.a-zA-Z][.a-zA-Z0-9]*")),
    (_negtag, RE(r"-[.a-zA-Z][.a-zA-Z0-9]*")),
    (_fulltext, RE(r'".*(?!\\\\)"')),
    (_whitespace, RE("[ \t]+")),
    ]




_TERMINALS = [_tag, _negtag, _fulltext]




# parser ----------------------------------------------------------------------
def parse(expr_str):
    def parse_terminal(pstate):
        next_tag = pstate.next_tag()
        if next_tag is _tag:
            return TagQuery(pstate.next_str_and_advance())
        elif next_tag is _negtag:
            return NotQuery(TagQuery(pstate.next_str_and_advance()[1:]))
        elif next_tag is _fulltext:
            return FulltextQuery(pstate.next_str_and_advance()[1:-1])
        else:
            pstate.expected("terminal")

    def parse_query(pstate, min_precedence=0):
        pstate.expect_not_end()

        if pstate.is_next(_not):
            pstate.advance()
            left_query = NotQuery(parse_query(pstate, _PREC_NOT))
        elif pstate.is_next(_openpar):
            pstate.advance()
            left_query = parse_query(pstate)
            pstate.expect(_closepar)
            pstate.advance()
        else:
            left_query = parse_terminal(pstate)

        did_something = True
        while did_something:
            did_something = False
            if pstate.is_at_end():
                return left_query
            
            next_tag = pstate.next_tag()

            if next_tag is _and and _PREC_AND > min_precedence:
                pstate.advance()
                left_query = make_and_query([left_query, parse_query(pstate, _PREC_AND)])
                did_something = True
            elif next_tag is _or and _PREC_OR > min_precedence:
                pstate.advance()
                left_query = make_or_query([left_query, parse_query(pstate, _PREC_OR)])
                did_something = True
            elif next_tag in _TERMINALS + [_not, _openpar] and _PREC_AND > min_precedence:
                left_query = make_and_query([left_query, parse_query(pstate, _PREC_AND)])
                did_something = True

        return left_query

        
    from synoptic.lex import LexIterator, lex
    pstate = LexIterator(
        [(tag, s, idx) 
         for (tag, s, idx) in lex(_LEX_TABLE, expr_str)
         if tag is not _whitespace], expr_str)

    result = parse_query(pstate)
    if not pstate.is_at_end():
        pstate.raise_parse_error("leftover input after completed parse")

    return result




if __name__ == "__main__":
    v = parse('not (yuck "yy!" and (not (not them or me) and you))')
    print v
    v2 = parse(str(v))
    print v2
    v3 = parse(str(v2))
    print v3
