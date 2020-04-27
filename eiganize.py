#!/usr/bin/python3
import sys
import regex as re
from itertools import tee
import functools
import sqlite3
import urllib.parse
import config

katakana_chart = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヽヾ"
hiragana_chart = "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞ"
hir2kat = str.maketrans(hiragana_chart, katakana_chart)
kat2hir  =str.maketrans(katakana_chart, hiragana_chart)

def kata2hira(s):
    return s.translate(kat2hir)

def open_db(dbFile):
    conn = sqlite3.connect(dbFile)
    cur = conn.cursor()
    cur.execute("attach '%s' as mia"%config.miaDicLocation);
    return conn


def mia_definition(cur, w, pronun='*'):

    if pronun != "*":
        query = cur.execute('''
select term, altterm, pronunciation, pos, definition, frequency, starCount
from %s
where
  (term = ? or term = (? || 'い')) and (pronunciation = ?)
   and instr(pos, 'obsc') = 0
   and frequency < 999999
order by frequency
'''%config.miaDictionary, (w, w, pronun))
    else:
        query = cur.execute('''
select term, altterm, pronunciation, pos, definition, frequency, starCount
from %s
where
  (term = ? or term = (? || 'い'))
   and instr(pos, 'obsc') = 0
   and frequency < 999999
order by frequency
'''%config.miaDictionary, (w, w))

    colnames = [ d[0] for d in query.description ]

    resultList = [ dict(zip(colnames, r)) for r in query.fetchall() ]

    return resultList

def known_word(cur, w):

    try:
        query = cur.execute('select norm, base, inflected, reading, pos, subpos from known where inflected = ?', (w,))
    except:
        print("failed query with word [%s]"%w)
        raise

    colnames = [ d[0] for d in query.description ]

    resultList = [ dict(zip(colnames, r)) for r in query.fetchall() ]

    return resultList



def split_at_EOS(l, i):
    if not (type(l) is list):
        # i hate python. why I can't simply create a list of an empty list in one statement?
        # or am I doing something wrong?
        t = []
        t.append([])
        return split_at_EOS(split_at_EOS(t, l), i)

    assert(type(l) is list)
    if i[0] == 'EOS':
        l.append([])
        return (l)

    l[-1].append(i)
    return l


def linesplit(l):
    lineMain = l.rstrip().split('\t',1)
    fields = lineMain[1].split(',') if (len(lineMain) > 1 ) else []
    return(lineMain[0], fields)

japWord = re.compile(r'[\p{IsHan}\p{IsKatakana}\p{IsHiragana}]', re.UNICODE)

def isJapanese(w):
    return japWord.search(w)

japKanji = re.compile(r'\p{IsHan}', re.UNICODE)

def hasKanji(w):
    return japKanji.search(w)


def get_type_word(w):
    if w == 'EOS':
        return 'EOS'
    elif re.search("^[0-9]+$", w):
        return 'NUMBER'
    elif not isJapanese(w):
        return 'NOTJAP'
    else:
        return 'OTHER'

chopRe = re.compile(r'^([^.,;\(]+)')

def chop_def(w):
    m = chopRe.search(w)
    if m:
        return m.group(1)
    return (w)


###############################################3

if len(sys.argv) != 4:
    print ('''Usage:

Eigana:

Add furigana and definitions based on a morph dictionary.

%s mecabFile originalFile morphsDatabase


mecabFile: output of mecab Unidict for the corresponding original file

originalFile: original text file to convert

morphsDatabase: sqlite3 database created from Morphman (see readme.org
for details)

The output will be an HTML file sent to standard output
'''%sys.argv[0])
    exit(1)

mecabFile = sys.argv[1]
originalFile = sys.argv[2]
knownDb = sys.argv[3]
#showKnowns = int(sys.argv[4])

with open(mecabFile) as f:
    mecabLines = f.readlines()

with open(originalFile) as f:
    original = f.readlines()


mecabSentences = functools.reduce(split_at_EOS, map(linesplit, mecabLines))


#for a in mecabSentences[0:5]:
#    print("---")
# print(a)

#mecabSentences = mecabSentences[0:9]


conn = open_db(knownDb)
cur = conn.cursor()
cur2 = conn.cursor()

print ('''
<html><head>
<style type="text/css" >
body {
    margin-left: 150px;
}
a:link {
  color: green;
}

/* visited link */
a:visited {
  color: green;
}

/* mouse over link */
a:hover {
  color: green;
}

/* selected link */
a:active {
  color: green;
}
/* Add style rules here */
</style></head>
<body>
<div
''')

def doWord(morph):

        thisWord = morph[0]

        if not isJapanese(thisWord):
            print (thisWord, end="")
            return

        typeWord = morph[1][0] if len(morph)> 0 else "*"
        pronunKata = morph[1][9] if (len(morph)> 0) and (len(morph[1]) > 9) else "*"
        pronun = kata2hira(pronunKata)
        root = morph[1][7] if (len(morph)> 0) and (len(morph[1]) > 7) else "*"
        rootPronKata = morph[1][6] if (len(morph)> 0) and (len(morph[1]) > 6) else "*"
        rootPron= kata2hira(rootPronKata)
#        print(morph)

        known = known_word(cur2, thisWord)
        if not known:
            # search for root
            known = known_word(cur2, root)

#        if (not known) or (known and showKnowns):
#            print ("   [%s] %s type [%s] root [%s][%s]"%(thisWord,(pronun if hasKanji(thisWord) else ""), typeWord, root, rootPron))

        if (known):
#            if (showKnowns):
#               print ("     known")
            print(thisWord, end="")
#            print (morph[1])
        else:

            defs = mia_definition(cur, thisWord, pronun)
            if not defs:
                defs = mia_definition(cur, root, rootPron)
            if not defs:
                defs = mia_definition(cur, thisWord)
            if not defs:
                defs = mia_definition(cur, root)

            if (defs):
                print("<span style='color:blue;'><ruby>%s<rt><ruby>%s<rt><span style='font-size:8px'>%s</span></rt></ruby</tr></ruby></span>"%(thisWord,pronun,chop_def(defs[0]['definition'])))
 #              print("\t" + "\n\t".join(map(str,defs)))
            else:
                if hasKanji(thisWord):
                    print("<span style='color:red;'><ruby>%s<rt>%s</tr></ruby></span>"%(thisWord,pronun))
                else:
                    print("<span style='color:red;'>%s</span>"%(thisWord))



for (line, sentence) in zip(original, mecabSentences):
    print ("</p><!--%s--><p>"%line.strip())
#    print (line)
#    print ("")
    for morph in sentence:
        doWord(morph)

#    queryStr = urllib.parse.quote(str(sentence), safe='')


    if isJapanese(line):
        queryStr = urllib.parse.quote(line, safe='')
#https://translate.google.com/#view=home&op=translate&sl=ja&tl=en&text=%E6%9D%A5%E3%81%AA%E3%81%84

#https://www.deepl.com/en/translator#en/de/this%20is%20the%20end%20of%20the%20world

        print("<span class='translate'>&nbsp;(<a href='https://translate.google.com/#view=home&op=translate&sl=ja&tl=en&text=%s'>Goo</a>)</span>"%queryStr)
        print("&nbsp;<span class='translate'>&nbsp;(<a href='https://www.deepl.com/en/translator#jp/en/%s'>Deep</a>)</span>"%queryStr)

    #print (sentence)
print ("</body></html>")
