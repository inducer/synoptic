

# {{{ logic that preserves NotImplemented

def not_ni(a):
    if a == NotImplemented:
        return NotImplemented
    else:
        return not a


def and_ni(a, b):
    if a == NotImplemented or b == NotImplemented:
        return NotImplemented
    else:
        return a and b


def or_ni(a, b):
    if a == NotImplemented or b == NotImplemented:
        return NotImplemented
    else:
        return a or b

# }}}


# {{{ query objects

class Query(object):
    def __str__(self):
        return self.visit(StringifyVisitor())

    def __repr__(self):
        return self.visit(ReprVisitor())

    # deriving classes need only implement __lt__ and __eq__
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


class IdQuery(Query):
    def __init__(self, id):
        self.id = id

    def visit(self, visitor, *args):
        return visitor.visit_id_query(self, *args)

    def __eq__(self, other):
        return isinstance(other, IdQuery) and self.id == other.id

    def __lt__(self, other):
        if not isinstance(other, TagQuery):
            return type(self).__name__ < type(other).__name__
        else:
            return self.id < other.id


class TagQuery(Query):
    def __init__(self, name):
        self.name = name

    def visit(self, visitor, *args):
        return visitor.visit_tag_query(self, *args)

    def __eq__(self, other):
        return isinstance(other, TagQuery) and self.name == other.name

    def __lt__(self, other):
        if not isinstance(other, TagQuery):
            return type(self).__name__ < type(other).__name__
        else:
            return self.name < other.name


class TagWildcardQuery(Query):
    def __init__(self, name):
        self.name = name

    def visit(self, visitor, *args):
        return visitor.visit_tag_wildcard_query(self, *args)

    def __eq__(self, other):
        return isinstance(other, TagWildcardQuery) and self.name == other.name

    def __lt__(self, other):
        if not isinstance(other, TagWildcardQuery):
            return type(self).__name__ < type(other).__name__
        else:
            return self.name < other.name


class FulltextQuery(Query):
    def __init__(self, substr):
        self.substr = substr

    def visit(self, visitor, *args):
        return visitor.visit_fulltext_query(self, *args)

    def __eq__(self, other):
        return isinstance(other, FulltextQuery) and self.substr == other.substr

    def __lt__(self, other):
        if not isinstance(other, FulltextQuery):
            return type(self).__name__ < type(other).__name__
        else:
            return self.substr < other.substr


class NotQuery(Query):
    def __init__(self, child):
        self.child = child

    def visit(self, visitor, *args):
        return visitor.visit_not_query(self, *args)

    def __eq__(self, other):
        return isinstance(other, NotQuery) and self.child == other.child

    def __lt__(self, other):
        if not isinstance(other, NotQuery):
            return type(self).__name__ < type(other).__name__
        else:
            return self.child < other.child


class AndQuery(Query):
    def __init__(self, children):
        self.children = children[:]
        self.children.sort()

    def visit(self, visitor, *args):
        return visitor.visit_and_query(self, *args)

    def __eq__(self, other):
        return isinstance(other, AndQuery) and self.children == other.children

    def __lt__(self, other):
        if not isinstance(other, AndQuery):
            return type(self).__name__ < type(other).__name__
        else:
            return self.children < other.children


class OrQuery(Query):
    def __init__(self, children):
        self.children = children[:]
        self.children.sort()

    def visit(self, visitor, *args):
        return visitor.visit_or_query(self, *args)

    def __eq__(self, other):
        return (isinstance(other, OrQuery)
                and self.children == other.children)

    def __lt__(self, other):
        if not isinstance(other, OrQuery):
            return type(self).__name__ < type(other).__name__
        else:
            return self.children < other.children


class DateQuery(Query):
    def __init__(self, is_before, timestamp):
        self.is_before = is_before
        self.timestamp = timestamp

    def visit(self, visitor, *args):
        return visitor.visit_date_query(self, *args)

    def __eq__(self, other):
        return (
                isinstance(other, DateQuery)
                and self.is_before == other.is_before
                and self.timestamp == other.timestamp)

    def __lt__(self, other):
        if not isinstance(other, OrQuery):
            return type(self).__name__ < type(other).__name__
        else:
            return ((self.is_before, self.timestamp)
                    <
                    (other.is_before, other.timestamp))


class StatelessQueryTerminal(Query):
    def __eq__(self, other):
        return isinstance(other, type(self))

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return type(self).__name__ < type(other).__name__
        else:
            return False


class DatedQuery(StatelessQueryTerminal):
    def visit(self, visitor, *args):
        return visitor.visit_dated_query(self, *args)


class NoHideQuery(StatelessQueryTerminal):
    def visit(self, visitor, *args):
        return visitor.visit_no_hide_query(self, *args)


class SortByDateQuery(StatelessQueryTerminal):
    def visit(self, visitor, *args):
        return visitor.visit_sort_by_date(self, *args)

# }}}


# {{{ normalizing query constructors

def make_tag_query(tag):
    if "?" in tag or "*" in tag:
        return TagWildcardQuery(tag)
    else:
        return TagQuery(tag)


def make_not_query(child):
    if isinstance(child, NotQuery):
        return child.child
    elif isinstance(child, AndQuery):
        return OrQuery([make_not_query(subchild) for subchild in child.children])
    elif isinstance(child, OrQuery):
        return AndQuery([make_not_query(subchild) for subchild in child.children])
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

# }}}


# {{{ operator precedence

_PREC_OR = 10
_PREC_AND = 20
_PREC_NOT = 30

# }}}


# {{{ query visitors

class StringifyVisitor(object):
    def visit_id_query(self, q, enclosing_prec=0):
        return "id(%d)" % q.id

    def visit_tag_query(self, q, enclosing_prec=0):
        return q.name

    def visit_tag_wildcard_query(self, q, enclosing_prec=0):
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

    def visit_date_query(self, q, enclosing_prec=0):
        if q.is_before:
            name = "before"
        else:
            name = "after"

        from datetime import datetime
        return "%s(%s)" % (name,
                datetime.fromtimestamp(q.timestamp).strftime("%d %b %Y %T"))

    def visit_dated_query(self, q, enclosing_prec=0):
        return "dated"

    def visit_no_hide_query(self, q, enclosing_prec=0):
        return "nohide"

    def visit_sort_by_date(self, q, enclosing_prec=0):
        return "sortbydate"


class ReprVisitor(object):
    def visit_tag_query(self, q):
        return "%s(%s)" % (type(q).__name__, repr(q.name))

    def visit_tag_wildcard_query(self, q):
        return "%s(%s)" % (type(q).__name__, repr(q.name))

    def visit_fulltext_query(self, q):
        return "%s(%s)" % (type(q).__name__, repr(q.substr))

    def visit_not_query(self, q):
        return "%s(%s)" % (type(q).__name__, repr(q.child))

    def visit_and_query(self, q):
        return "%s(%s)" % (type(q).__name__, repr(q.children))

    def visit_or_query(self, q):
        return "%s(%s)" % (type(q).__name__, repr(q.children))

    def visit_date_query(self, q):
        return "%s(%s, %s)" % (q.__class__.__name__,
                repr(q.is_before), repr(q.timestamp))

    def visit_dated_query(self, q):
        return "%s()" % type(q).__name__

    visit_no_hide_query = visit_dated_query
    visit_sort_by_date = visit_dated_query


class TagListVisitor(object):
    def visit_id_query(self, q):
        return []

    def visit_tag_query(self, q):
        return [q.name]

    def visit_tag_wildcard_query(self, q):
        return [q.name]

    def visit_fulltext_query(self, q):
        return []

    def visit_not_query(self, q):
        return q.child.visit(self)

    def visit_and_query(self, q):
        result = []
        for ch in q.children:
            result += ch.visit(self)
        return result

    def visit_or_query(self, q):
        result = []
        for ch in q.children:
            result += ch.visit(self)
        return result

    def visit_date_query(self, q):
        return []

    visit_dated_query = visit_date_query
    visit_no_hide_query = visit_date_query
    visit_sort_by_date = visit_date_query

# }}}


# {{{ lexer data

_and = intern("and")
_or = intern("or")
_not = intern("not")
_openpar = intern("openpar")
_closepar = intern("closepar")
_id = intern("id")
_before = intern("before")
_after = intern("after")
_dated = intern("dated")
_nohide = intern("nohide")
_sortbydate = intern("sortbydate")
_tag = intern("tag")
_negtag = intern("negtag")
_fulltext = intern("fulltext")
_whitespace = intern("whitespace")


from pytools.lex import RE
_LEX_TABLE = [
    (_and, RE(r"and\b")),
    (_or, RE(r"or\b")),
    (_not, RE(r"not\b")),
    (_openpar, RE(r"\(")),
    (_closepar, RE(r"\)")),
    (_id, RE(r"id\(([0-9]+)\)")),
    (_before, RE(r"before\(([-:, A-Za-z0-9]+)\)")),
    (_after, RE(r"after\(([-:, A-Za-z0-9]+)\)")),
    (_dated, RE(r"dated\b")),
    (_nohide, RE(r"nohide\b")),
    (_sortbydate, RE(r"sortbydate\b")),
    (_tag, RE(r"[.\w?*]+")),
    (_negtag, RE(r"-[.\w?*]+")),
    (_fulltext, RE(r'".*?(?!\\\\)"')),
    (_whitespace, RE("[ \t]+")),
    ]


_STATELESS_TERMINALS = {
        _dated: DatedQuery(),
        _nohide: NoHideQuery(),
        _sortbydate: SortByDateQuery()
        }

_TERMINALS = (
        [_tag, _negtag, _fulltext, _id, _before, _after]
        + list(_STATELESS_TERMINALS.iterkeys()))

# }}}


# {{{parser

def parse_query(expr_str):
    def parse_terminal(pstate):
        next_tag = pstate.next_tag()
        if next_tag is _tag:
            return make_tag_query(pstate.next_str_and_advance())
        elif next_tag is _negtag:
            return NotQuery(make_tag_query(pstate.next_str_and_advance()[1:]))
        elif next_tag is _fulltext:
            return FulltextQuery(pstate.next_str_and_advance()[1:-1])
        elif next_tag is _dated:
            pstate.advance()
            return DatedQuery()
        elif next_tag in _STATELESS_TERMINALS:
            pstate.advance()
            return _STATELESS_TERMINALS[next_tag]
        elif next_tag in [_id]:
            result = IdQuery(int(pstate.next_match_obj().group(1)))
            pstate.advance()
            return result
        elif next_tag in [_before, _after]:
            from parsedatetime.parsedatetime import Calendar
            cal = Calendar()
            timetup = cal.parse(pstate.next_match_obj().group(1))
            pstate.advance()
            import time
            return DateQuery(next_tag == _before, time.mktime(timetup[0]))
        else:
            pstate.expected("terminal")

    def inner_parse(pstate, min_precedence=0):
        pstate.expect_not_end()

        if pstate.is_next(_not):
            pstate.advance()
            left_query = make_not_query(inner_parse(pstate, _PREC_NOT))
        elif pstate.is_next(_openpar):
            pstate.advance()
            left_query = inner_parse(pstate)
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
                left_query = make_and_query(
                        [left_query, inner_parse(pstate, _PREC_AND)])
                did_something = True
            elif next_tag is _or and _PREC_OR > min_precedence:
                pstate.advance()
                left_query = make_or_query(
                        [left_query, inner_parse(pstate, _PREC_OR)])
                did_something = True
            elif (next_tag in _TERMINALS + [_not, _openpar]
                    and _PREC_AND > min_precedence):
                left_query = make_and_query(
                        [left_query, inner_parse(pstate, _PREC_AND)])
                did_something = True

        return left_query

    from pytools.lex import LexIterator, lex
    pstate = LexIterator(
        [(tag, s, idx, matchobj)
         for (tag, s, idx, matchobj) in lex(
             _LEX_TABLE, expr_str, match_objects=True)
         if tag is not _whitespace], expr_str)

    if pstate.is_at_end():
        return TagQuery(u"home")

    result = inner_parse(pstate)
    if not pstate.is_at_end():
        pstate.raise_parse_error("leftover input after completed parse")

    return result

# }}}


# {{{ 'test'

if __name__ == "__main__":
    v = parse_query('not (yuck "yy!" and (not (not them and (yes or me)) and you))')
    print v
    v2 = parse_query(str(v))
    print v2
    v3 = parse_query(str(v2))
    print v3
    print parse_query('yuck bluck')
    print parse_query('')

    v = parse_query('not before(yesterday 5 am)')
    print v
    v2 = parse_query(str(v))
    print v2
    v = parse_query('pic ("test" or "validation")')
    print repr(v)

# }}}

# vim: foldmethod=marker
