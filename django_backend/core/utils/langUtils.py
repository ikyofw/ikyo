import string, random, re
import json5

EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

def isNullBlank(s) -> bool:
    return s is None or type(s) == str and s.strip() == ''

def isNotNullBlank(s) -> bool:
    return not isNullBlank(s)

def randonStr(length) -> str:
    s = ''
    for c in random.sample(string.ascii_lowercase + string.digits + string.ascii_uppercase, length):
        s += c
    return s


def convertStr2Json(jsonStr, defaultKey=None) -> dict:
    ''' 
        {text: 'capton abc', value:3, style: "color: red", "tooltip": 'help url', formula: "function(data){var sum=0; for(var i=0;i<len(data); i++{sum+=data[i];})return \\\"total=\\\" + sum;}"}
        {"text": "caption abc", "style": "color: red", "tooltip": "help url"}

        defaultKey: e.g. text, used for "jsonStr" is only a dict value. E.g. jsonStr="1234", defaultKey="value", then convert to {'value': '1234'}
    '''
    if isNullBlank(jsonStr):
        return None
    elif type(jsonStr) == dict:
        return jsonStr
    if type(jsonStr) != str:
        raise Exception('convertStr2Json unsupport data type %s: %s' % (type(jsonStr), jsonStr))
    testStr = jsonStr
    if testStr[0] != '{':
        testStr = '{' + testStr
    if testStr[-1] != '}':
        testStr += '}'
    try:
        return json5.loads(testStr)
    except:
        if defaultKey is not None:
            try:
                testStr = "{\"%s\":\"%s\"}" % (defaultKey, jsonStr)
                return json5.loads(testStr)
            except:
                pass
    raise Exception('Covnert string [%s] to json failed.' % jsonStr)


def validateEmail(email) -> bool:
    return re.fullmatch(EMAIL_REGEX, email)