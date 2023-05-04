import extract_kinship_terms
import pytest


# To run these tests from the commandline, navigate to the directory
# this file is stored in, and run the command "pytest".

terms = extract_kinship_terms.get_terms("../terms.csv")


def test_extract_from_comment_one_kinship_term_singular_my():
    sentence = "my sister loves that book"
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    expected = [{
        "text": sentence,
        "kinship_term": "sister",
        "singular": True,
        "specific": "specific",
        "index": 3,
        "determiner": "my"
    }]
    assert actual == expected


def test_extract_from_comment_one_kinship_term_singular_not_my():
    sentence = "she's a mom, you know -- she's psychic"
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    expected = [{
        "text": sentence,
        "kinship_term": "mom",
        "singular": True,
        "specific": "generic",
        "index": 8,
        "determiner": "a"
    }]
    assert actual == expected


def test_extract_from_comment_one_kinship_term_plural_not_my():
    sentence = "it's important to get along well with your siblings"
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    expected = [{
        "text": sentence,
        "kinship_term": "sibling",
        "singular": False,
        "specific": "mixed",
        "index": 43,
        "determiner": "your"
    }]
    assert actual == expected


def test_extract_from_comment_one_kinship_term_plural_my():
    sentence = "I never really got along well wtih my siblings"
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    expected = [{
        "text": sentence,
        "kinship_term": "sibling",
        "singular": False,
        "specific": "specific",
        "index": 38,
        "determiner": "my"
    }]
    assert actual == expected


def test_extract_from_comment_nonstandard_plural():
    sentence = "I don't have any children"
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    expected = [{
        "text": sentence,
        "kinship_term": "child",
        "singular": False,
        "specific": "generic",
        "index": 17,
        "determiner": ""  # "any" is not considered a determiner in our GENERIC_DETERMINERS
    }]
    assert actual == expected


def test_extract_from_comment_multiple_kinship_terms():
    sentence = "are you close with your mom and dad?"
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    expected = [{
        "text": sentence,
        "kinship_term": "mom",
        "singular": True,
        "specific": "mixed",
        "index": 24,
        "determiner": "your"
    },
    {
        "text": sentence,
        "kinship_term": "dad",
        "singular": True,
        "specific": "generic",
        "index": 32,
        "determiner": ""   # "mom and" is betwen "your" and "dad", so regex would not count it as a det
    }]
    assert actual == expected


def test_extract_from_comment_same_kinship_term_different_contexts():
    sentence = "are you close with your mom? my mom and i are really close"
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    expected = [{
        "text": sentence,
        "kinship_term": "mom",
        "singular": True,
        "specific": "mixed",
        "index": 24,
        "determiner": "your"
    },
    {
        "text": sentence,
        "kinship_term": "mom",
        "singular": True,
        "specific": "specific",
        "index": 32,
        "determiner": "my"
    }]
    assert actual == expected


def test_extract_from_comment_same_kinship_term_same_context():
    sentence = "have you met my brother? my brother loves that book"
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    expected = [{
        "text": sentence,
        "kinship_term": "brother",
        "singular": True,
        "specific": "specific",
        "index": 16,
        "determiner": "my"
    },
    {
        "text": sentence,
        "kinship_term": "brother",
        "singular": True,
        "specific": "specific",
        "index": 28,
        "determiner": "my"
    }]
    assert actual == expected


def test_extract_from_comment_adjacent_word():
    sentence = 'they\'ve got a smarmy brother'
    expected = [{
        "text": sentence,
        "kinship_term": "brother",
        "singular": True,
        "specific": "generic",
        "index": 21,
        "determiner": ""  # word between "a" and "brother"; regex would not capture
    }]
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    assert actual == expected


def test_extract_from_comment_wife():
    sentence = 'they\'ve got a cute wife'
    expected = [{
        "text": sentence,
        "kinship_term": "wife",
        "singular": True,
        "specific": "generic",
        "index": 19,
        "determiner": ""
    }]
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    assert actual == expected


def test_extract_from_comment_wives():
    sentence = 'most wives don\'t sing in the shower'
    expected = [{
        "text": sentence,
        "kinship_term": "wife",
        "singular": False,
        "specific": "generic",
        "index": 5,
        "determiner": ""
    }]
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    assert actual == expected


def test_extract_from_comment_so():
    sentence = 'bob met up w my s/o the other day n they were wearing a flamingo shirt'
    expected = [{
        "text": sentence,
        "kinship_term": "s/o",
        "singular": True,
        "specific": "specific",
        "index": 16,
        "determiner": "my"
    }]
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    assert actual == expected


def test_extract_from_comment_possessive():
    sentence = 'jill\'s gf said that the volcano was gonna explode'
    expected = [{
        "text": sentence,
        "kinship_term": "gf",
        "singular": True,
        "specific": "specific",
        "index": 7,
        "determiner": "\'s"
    }]
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    assert actual == expected


def test_extract_from_comment_other_words():
    sentence = 'springfield was visited for parenting purposes'
    expected = []
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    assert actual == expected


def test_extract_from_comment_new_line():
    sentence = "i had a\r\ntall mom"
    expected = [{
        "text": sentence,
        "kinship_term": "mom",
        "singular": True,
        "specific": "generic",
        "index": 14,
        "determiner": ""
    }]
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    assert actual == expected


def test_extract_from_comment_new_line_two():
    sentence = """I have a
tall mom"""
    expected = [{
        "text": sentence,
        "kinship_term": "mom",
        "singular": True,
        "specific": "generic",
        "index": 14,
        "determiner": ""
    }]
    actual = extract_kinship_terms.extract_from_comment(sentence, terms)
    assert actual == expected


def test_get_terms():
    file = 'terms_test.csv'
    actual = extract_kinship_terms.get_terms(file)
    expected = '|'.join(['(^|\s)(?P<kinship_pl>(?P<kinship_term>sister)s?)($|[\s\.,;:\?!\)])',
                '(^|\s)(?P<kinship_pl>(?P<kinship_term>significant other)s?)($|[\s\.,;:\?!\)])',
                '(^|\s)(?P<kinship_pl>(?P<kinship_term>child)(ren)?)($|[\s\.,;:\?!\)])',
                '(^|\s)(?P<kinship_term>wife)($|[\s\.,;:\?!\)])',
                '(^|\s)(?P<kinship_term>wives)($|[\s\.,;:\?!\)])',
                '(^|\s)(?P<kinship_term>s/o)($|[\s\.,;:\?!\)])'])
    assert actual == expected


def test_get_terms_error():
    file = 'terms_test2.csv'
    with pytest.raises(ValueError):
        extract_kinship_terms.get_terms(file)


if __name__ == '__main__':
    pytest.main(['test_extract_kinship_terms.py', '-v'])
