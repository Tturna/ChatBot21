def IsStringInList(string_, list_, ignoreCase=False):
    string_ = str.lower(string_) if ignoreCase else string_
    for e in list_:
        e = str.lower(e) if ignoreCase else e
        if string_ == e: return True
    return False

def IsListElementInString(string_, list_, ignoreCase=False):
    string_ = str.lower(string_) if ignoreCase else string_
    for e in list_:
        e = str.lower(e) if ignoreCase else e
        if e in string_: return True
    return False