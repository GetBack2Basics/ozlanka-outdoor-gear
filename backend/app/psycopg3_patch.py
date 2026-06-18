# psycopg3 bytes compatibility patch — MUST be first import
import re as _re

_orig_re_match = _re.match
_orig_re_search = _re.search
_orig_re_sub = _re.sub


def _decode_bytes(s):
    return s.decode("utf-8") if isinstance(s, bytes) else s


def _patched_re_match(pattern, string, flags=0):
    return _orig_re_match(pattern, _decode_bytes(string), flags)


def _patched_re_search(pattern, string, flags=0):
    return _orig_re_search(pattern, _decode_bytes(string), flags)


def _patched_re_sub(pattern, repl, string, count=0, flags=0):
    return _orig_re_sub(pattern, repl, _decode_bytes(string), count, flags)


_re.match = _patched_re_match
_re.search = _patched_re_search
_re.sub = _patched_re_sub

# Now import SQLAlchemy
import sqlalchemy.dialects.postgresql.base as _pg_base

# Patch compiled pattern class attributes to handle bytes
def _wrap_pattern(p):
    orig_search = p.search
    orig_match = p.match
    orig_sub = p.sub
    orig_findall = p.findall
    orig_finditer = p.finditer

    def _decoded_search(string, *a, **kw):
        return orig_search(_decode_bytes(string), *a, **kw)
    def _decoded_match(string, *a, **kw):
        return orig_match(_decode_bytes(string), *a, **kw)
    def _decoded_sub(repl, string, *a, **kw):
        return orig_sub(repl, _decode_bytes(string), *a, **kw)
    def _decoded_findall(string, *a, **kw):
        return orig_findall(_decode_bytes(string), *a, **kw)
    def _decoded_finditer(string, *a, **kw):
        return orig_finditer(_decode_bytes(string), *a, **kw)

    p.search = _decoded_search
    p.match = _decoded_match
    p.sub = _decoded_sub
    p.findall = _decoded_findall
    p.finditer = _decoded_finditer
    return p

# Wrap all compiled patterns on the PGDialect class
for _attr_name in dir(_pg_base.PGDialect):
    _attr = getattr(_pg_base.PGDialect, _attr_name)
    if isinstance(_attr, _re.Pattern):
        _wrap_pattern(_attr)

# Also wrap on the psycopg dialect subclass
import sqlalchemy.dialects.postgresql.psycopg as _psycopg_mod
for _attr_name in dir(_psycopg_mod.PGDialect):
    _attr = getattr(_psycopg_mod.PGDialect, _attr_name)
    if isinstance(_attr, _re.Pattern) and not hasattr(_attr, '_patched'):
        _wrap_pattern(_attr)
        _attr._patched = True
