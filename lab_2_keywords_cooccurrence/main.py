"""
Lab 2
Extract keywords based on co-occurrence frequency
"""
import json
from pathlib import Path
from typing import Optional, Sequence, Mapping, Any
import re
from itertools import chain
from lab_1_keywords_tfidf.main import clean_and_tokenize, calculate_frequencies

KeyPhrase = tuple[str, ...]
KeyPhrases = Sequence[KeyPhrase]


def check_type_and_not_empty(some_object: Any, some_type: type) -> bool:
    """
    Checks object type and whether it contains something
    """
    return bool(some_object and isinstance(some_object, some_type))


def extract_phrases(text: str) -> Optional[Sequence[str]]:
    """
    Splits the text into separate phrases using phrase delimiters
    :param text: an original text
    :return: a list of phrases

    In case of corrupt input arguments, None is returned
    """
    if not check_type_and_not_empty(text, str):
        return None
    pattern = re.compile(r'''
    [^\w\s]+        #  matches any non whitespace and non alphanumeric character
    (?:\W|$)+      #  matches any non alphanumeric character and end of string
    |                       #  second pattern (punctuation before word)
    (?:\W|^)+      #  matches any non alphanumeric character and start of string
    [^\w\s]+        #  matches any non whitespace and non alphanumeric character''',
                         re.VERBOSE)
    return [phrase.strip() for phrase in re.split(pattern, text) if phrase]


def extract_candidate_keyword_phrases(phrases: Sequence[str], stop_words: Sequence[str]) -> Optional[KeyPhrases]:
    """
    Creates a list of candidate keyword phrases by splitting the given phrases by the stop words
    :param phrases: a list of the phrases
    :param stop_words: a list of the stop words
    :return: the candidate keyword phrases for the text

    In case of corrupt input arguments, None is returned
    """
    if not check_type_and_not_empty(phrases, list) or not check_type_and_not_empty(stop_words, list):
        return None
    modified_phrases = []
    for sentence in phrases:
        modified_sentence = ' '.join([word if word not in stop_words else '?' for word in sentence.lower().split()])
        modified_phrases.append(modified_sentence)
    return [tuple(phrase.split()) for phrase in extract_phrases('? '.join(modified_phrases))]


def calculate_frequencies_for_content_words(candidate_keyword_phrases: KeyPhrases) -> Optional[Mapping[str, int]]:
    """
    Extracts the content words from the candidate keyword phrases list and computes their frequencies
    :param candidate_keyword_phrases: a list of the candidate keyword phrases
    :return: a dictionary with the content words and corresponding frequencies

    In case of corrupt input arguments, None is returned
    """
    if not check_type_and_not_empty(candidate_keyword_phrases, list):
        return None
    words = list(chain(*candidate_keyword_phrases))
    return {word: words.count(word) for word in words}


def calculate_word_degrees(candidate_keyword_phrases: KeyPhrases,
                           content_words: Sequence[str]) -> Optional[Mapping[str, int]]:
    """
    Calculates the word degrees based on the candidate keyword phrases list
    Degree of a word is equal to the total length of all keyword phrases the word is found in

    :param content_words: the content words from the candidate keywords
    :param candidate_keyword_phrases: the candidate keyword phrases for the text
    :return: the words and their degrees

    In case of corrupt input arguments, None is returned
    """
    if (not check_type_and_not_empty(candidate_keyword_phrases, list)
            or not check_type_and_not_empty(content_words, list)):
        return None
    word_degree = dict.fromkeys(content_words, 0)
    for word in content_words:
        for phrase in candidate_keyword_phrases:
            if word in phrase:
                word_degree[word] += len(phrase)
    return word_degree


def calculate_word_scores(word_degrees: Mapping[str, int],
                          word_frequencies: Mapping[str, int]) -> Optional[Mapping[str, float]]:
    """
    Calculate the word score based on the word degree and word frequency metrics

    :param word_degrees: a mapping between the word and the degree
    :param word_frequencies: a mapping between the word and the frequency
    :return: a dictionary with {word: word_score}

    In case of corrupt input arguments, None is returned
    """
    if (not check_type_and_not_empty(word_degrees, dict)
            or not check_type_and_not_empty(word_frequencies, dict)
            or word_degrees.keys() != word_frequencies.keys()):
        return None
    word_score = {word: word_degrees[word] / word_frequencies[word] for word in word_degrees}
    return word_score


def calculate_cumulative_score_for_candidates(candidate_keyword_phrases: KeyPhrases,
                                              word_scores: Mapping[str, float]) -> Optional[Mapping[KeyPhrase, float]]:
    """
    Calculate cumulative score for each candidate keyword phrase. Cumulative score for a keyword phrase equals to
    the sum of the word scores of each keyword phrase's constituent

    :param candidate_keyword_phrases: a list of candidate keyword phrases
    :param word_scores: word scores
    :return: a dictionary containing the mapping between the candidate keyword phrases and respective cumulative scores

    In case of corrupt input arguments, None is returned
    """
    if (not check_type_and_not_empty(candidate_keyword_phrases, list)
            or not check_type_and_not_empty(word_scores, dict)):
        return None
    cumulative = {}
    for phrase in candidate_keyword_phrases:
        try:
            cumulative[phrase] = sum([word_scores[word] for word in phrase])
        except KeyError:
            return None
    return cumulative


def get_top_n(keyword_phrases_with_scores: Mapping[KeyPhrase, float],
              top_n: int,
              max_length: int) -> Optional[Sequence[str]]:
    """
    Extracts the top N keyword phrases based on their scores and lengths

    :param keyword_phrases_with_scores: a dictionary containing the keyword phrases and their cumulative scores
    :param top_n: the number of the keyword phrases to extract
    :param max_length: maximal length of a keyword phrase to be considered
    :return: a list of keyword phrases sorted by their scores in descending order

    In case of corrupt input arguments, None is returned
    """
    if (not check_type_and_not_empty(top_n, int)
            or not check_type_and_not_empty(max_length, int)
            or max_length < 0
            or not check_type_and_not_empty(keyword_phrases_with_scores, dict)
            or top_n < 0):
        return None
    normal_length_phrases = [phrase for phrase in keyword_phrases_with_scores if len(phrase) <= max_length]
    sorted_phrase = sorted(normal_length_phrases, key=lambda x: keyword_phrases_with_scores[x], reverse=True)
    return [' '.join(words) for words in sorted_phrase[:top_n]]


def extract_candidate_keyword_phrases_with_adjoining(candidate_keyword_phrases: KeyPhrases,
                                                     phrases: Sequence[str]) -> Optional[KeyPhrases]:
    """
    Extracts the adjoining keyword phrases from the candidate keywords Sequence and
    builds new candidate keywords containing stop words

    Adjoining keywords: such pairs that are found at least twice in the candidate keyword phrases list one after another

    To build a new keyword phrase the following is required:
        1. Find the first constituent of the adjoining keyword phrase in the phrases followed by:
            a stop word and the second constituent of the adjoining keyword phrase
        2. Combine these three pieces in the new candidate keyword phrase, i.e.:
            new_candidate_keyword = [first_constituent, stop_word, second_constituent]

    :param candidate_keyword_phrases: a list of candidate keyword phrases
    :param phrases: a list of phrases
    :return: a list containing the pairs of candidate keyword phrases that are found at least twice together

    In case of corrupt input arguments, None is returned
    """
    if not check_type_and_not_empty(candidate_keyword_phrases, list) or not check_type_and_not_empty(phrases, list):
        return None

    neighbours = []
    for i in range(len(candidate_keyword_phrases) - 4):
        if (candidate_keyword_phrases[i] == candidate_keyword_phrases[i + 3]
                and candidate_keyword_phrases[i + 1] == candidate_keyword_phrases[i + 4]):
            neighbours.append((candidate_keyword_phrases[i], candidate_keyword_phrases[i + 1]))

    phrases = [phrase.lower() for phrase in phrases]
    keyword_phrases_with_stop_words = []
    for phrase in phrases:
        for pair in neighbours:
            part1, part2 = ' '.join(pair[0]), ' '.join(pair[1])
            if part1 in phrase and part2 in phrase:
                keyword_phrases_with_stop_words.extend(re.findall(fr'{part1}.*?{part2}', phrase))

    return [tuple(phrase.split()) for phrase in set(keyword_phrases_with_stop_words)
            if keyword_phrases_with_stop_words.count(phrase) > 1]


def calculate_cumulative_score_for_candidates_with_stop_words(candidate_keyword_phrases: KeyPhrases,
                                                              word_scores: Mapping[str, float],
                                                              stop_words: Sequence[str]) \
        -> Optional[Mapping[KeyPhrase, float]]:
    """
    Calculate cumulative score for each candidate keyword phrase. Cumulative score for a keyword phrase equals to
    the sum of the word scores of each keyword phrase's constituent except for the stop words

    :param candidate_keyword_phrases: a list of candidate keyword phrases
    :param word_scores: word scores
    :param stop_words: a list of stop words
    :return: a dictionary containing the mapping between the candidate keyword phrases and respective cumulative scores

    In case of corrupt input arguments, None is returned
    """
    if (not check_type_and_not_empty(candidate_keyword_phrases, list)
            or not check_type_and_not_empty(word_scores, dict)
            or not check_type_and_not_empty(stop_words, list)):
        return None
    cumulative = {}
    for phrase in candidate_keyword_phrases:
        cumulative[phrase] = sum([word_scores[word] for word in phrase if word not in stop_words])
    return cumulative


def generate_stop_words(text: str, max_length: int) -> Optional[Sequence[str]]:
    """
    Generates the list of stop words from the given text

    :param text: the text
    :param max_length: maximum length (in characters) of an individual stop word
    :return: a list of stop words
    """
    if not check_type_and_not_empty(text, str) or not check_type_and_not_empty(max_length, int) or max_length < 0:
        return None
    tokens = clean_and_tokenize(text)
    if tokens:
        frequencies = calculate_frequencies(tokens)
    else:
        return None
    scores = sorted(frequencies.values())
    percentile = scores[round(len(scores) * 0.8) - 1]
    return [phrase for phrase, score in frequencies.items()
            if score >= percentile and len(phrase) <= max_length]


def load_stop_words(path: Path) -> Optional[Mapping[str, Sequence[str]]]:
    """
    Loads stop word lists from the file
    :param path: path to the file with stop word lists
    :return: a dictionary containing the language names and corresponding stop word lists
    """
    if not check_type_and_not_empty(path, Path):
        return None
    file = open(path, encoding='utf-8')
    stop_words = json.load(file)
    if isinstance(stop_words, dict):
        return stop_words
    return None
