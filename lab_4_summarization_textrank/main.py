"""
Lab 4
Summarize text using TextRank algorithm
"""
from typing import Union, Any, Type

from lab_3_keywords_textrank.main import TextEncoder, \
    TextPreprocessor, TFIDFAdapter

PreprocessedSentence = tuple[str, ...]
EncodedSentence = tuple[int, ...]


def check_type(variable: Any, possible_type: Type) -> None:
    """
    Checks type of variable and raise ValueError if incorrect
    """
    if not isinstance(variable, possible_type) \
            or (possible_type is int and isinstance(variable, bool)):
        raise ValueError


def check_iterable(
        container: Any, container_type: Type, elements_type: Type) -> None:
    """
    Checks type of variables in iterable and raise ValueError if incorrect
    """
    check_type(container, container_type)
    for i in container:
        check_type(i, elements_type)


class Sentence:
    """
    An abstraction over the real-world sentences
    """

    _preprocessed: tuple[str, ...]
    _encoded: tuple[int, ...]

    def __init__(self, text: str, position: int) -> None:
        """
        Constructs all the necessary attributes
        """
        check_type(text, str)
        check_type(position, int)
        self._text = text
        self._position = position
        self._preprocessed = ()
        self._encoded = ()

    def get_position(self) -> int:
        """
        Returns the attribute
        :return: the position of the sentence in the text
        """
        return self._position

    def set_text(self, text: str) -> None:
        """
        Sets the attribute
        :param text: the text
        :return: None
        """
        check_type(text, str)
        self._text = text

    def get_text(self) -> str:
        """
        Returns the attribute
        :return: the text
        """
        return self._text

    def set_preprocessed(self, preprocessed_sentence: PreprocessedSentence) -> None:
        """
        Sets the attribute
        :param preprocessed_sentence: the preprocessed sentence (a sequence of tokens)
        :return: None
        """
        check_iterable(preprocessed_sentence, tuple, str)
        self._preprocessed = preprocessed_sentence

    def get_preprocessed(self) -> PreprocessedSentence:
        """
        Returns the attribute
        :return: the preprocessed sentence (a sequence of tokens)
        """
        return self._preprocessed

    def set_encoded(self, encoded_sentence: EncodedSentence) -> None:
        """
        Sets the attribute
        :param encoded_sentence: the encoded sentence (a sequence of numbers)
        :return: None
        """
        check_iterable(encoded_sentence, tuple, int)
        self._encoded = encoded_sentence

    def get_encoded(self) -> EncodedSentence:
        """
        Returns the attribute
        :return: the encoded sentence (a sequence of numbers)
        """
        return self._encoded


class SentencePreprocessor(TextPreprocessor):
    """
    Class for sentence preprocessing
    """

    def __init__(self, stop_words: tuple[str, ...], punctuation: tuple[str, ...]) -> None:
        """
        Constructs all the necessary attributes
        """
        super().__init__(stop_words, punctuation)
        check_iterable(stop_words, tuple, str)
        self._stop_words = stop_words
        check_iterable(punctuation, tuple, str)
        self._punctuation = punctuation

    def _split_by_sentence(self, text: str) -> tuple[Sentence, ...]:
        """
        Splits the provided text by sentence
        :param text: the raw text
        :return: a sequence of sentences
        """
        check_type(text, str)
        text = text.replace('\n', ' ').replace('  ', ' ')
        sentences = []
        count = 0
        start = 0
        punctuation_index = 0
        space_flag = False
        for index, elem in enumerate(text):
            if elem in '.!?':
                punctuation_index = index
            elif elem.isspace():
                space_flag = True
            elif elem.isupper() and space_flag and punctuation_index:
                sentences.append(Sentence(text[start: punctuation_index + 1], count))
                start = index
                count += 1
            if not elem.isspace():
                space_flag = False
                if elem not in '.!?':
                    punctuation_index = 0
        sentences.append(Sentence(text[start:], count))
        return tuple(sentences)

    def _preprocess_sentences(self, sentences: tuple[Sentence, ...]) -> None:
        """
        Enriches the instances of sentences with their preprocessed versions
        :param sentences: a list of sentences
        :return:
        """
        check_iterable(sentences, tuple, Sentence)
        for sentence in sentences:
            preprocessed = self.preprocess_text(sentence.get_text())
            sentence.set_preprocessed(preprocessed)

    def get_sentences(self, text: str) -> tuple[Sentence, ...]:
        """
        Extracts the sentences from the given text & preprocesses them
        :param text: the raw text
        :return:
        """
        sentences = self._split_by_sentence(text)
        self._preprocess_sentences(sentences)
        return sentences


class SentenceEncoder(TextEncoder):
    """
    A class to encode string sequence into matching integer sequence
    """

    def __init__(self) -> None:
        """
        Constructs all the necessary attributes
        """
        super().__init__()
        self.max_id = 1000

    def _learn_indices(self, tokens: tuple[str, ...]) -> None:
        """
        Fills attributes mapping words and integer equivalents to each other
        :param tokens: a sequence of string tokens
        :return:
        """
        check_iterable(tokens, tuple, str)
        new_tokens = (i for i in tokens if i not in self._word2id)
        for index, token in enumerate(new_tokens, start=self.max_id):
            self._word2id[token] = index
            self._id2word[index] = token
            self.max_id += 1

    def encode_sentences(self, sentences: tuple[Sentence, ...]) -> None:
        """
        Enriches the instances of sentences with their encoded versions
        :param sentences: a sequence of sentences
        :return: a list of sentences with their preprocessed versions
        """
        check_iterable(sentences, tuple, Sentence)
        for sentence in sentences:
            self._learn_indices(sentence.get_preprocessed())
            sentence.set_encoded(tuple(self._word2id[word] for word in sentence.get_preprocessed()))


def calculate_similarity(sequence: Union[list, tuple], other_sequence: Union[list, tuple]) -> float:
    """
    Calculates similarity between two sequences using Jaccard index
    :param sequence: a sequence of items
    :param other_sequence: a sequence of items
    :return: similarity score
    """
    for seq in sequence, other_sequence:
        try:
            check_type(seq, list)
        except ValueError:
            check_type(seq, tuple)
        if not seq:
            return 0
    sequence_set, other_sequence_set = set(sequence), set(other_sequence)
    return len(sequence_set & other_sequence_set) / len(sequence_set | other_sequence_set)


class SimilarityMatrix:
    """
    A class to represent relations between sentences
    """

    _matrix: list[list[float]]

    def __init__(self) -> None:
        """
        Constructs necessary attributes
        """
        self._matrix = []
        self._vertices_list = []

    def get_vertices(self) -> tuple[Sentence, ...]:
        """
        Returns a sequence of all vertices present in the graph
        :return: a sequence of vertices
        """
        return tuple(self._vertices_list)

    def calculate_inout_score(self, vertex: Sentence) -> int:
        """
        Retrieves a number of vertices that are similar (i.e. have similarity score > 0) to the input one
        :param vertex
        :return:
        """
        check_type(vertex, Sentence)
        return sum(i > 0 for i in self._matrix[self._vertices_list.index(vertex)]) - 1

    def add_edge(self, vertex1: Sentence, vertex2: Sentence) -> None:
        """
        Adds or overwrites an edge in the graph between the specified vertices
        :param vertex1:
        :param vertex2:
        :return:
        """
        if vertex1 == vertex2:
            raise ValueError
        for vertex in vertex1, vertex2:
            check_type(vertex, Sentence)
            if vertex not in self._vertices_list:
                self._vertices_list.append(vertex)
                new_row = [calculate_similarity(vertex.get_encoded(), other.get_encoded())
                           for other in self._vertices_list]
                self._matrix.append(new_row)
                for i in range(len(self._matrix) - 1):
                    self._matrix[i].append(self._matrix[-1][i])

    def get_similarity_score(self, sentence: Sentence, other_sentence: Sentence) -> float:
        """
        Gets the similarity score for two sentences from the matrix
        :param sentence
        :param other_sentence
        :return: the similarity score
        """
        check_type(sentence, Sentence)
        check_type(other_sentence, Sentence)
        if sentence not in self._vertices_list or other_sentence not in self._vertices_list:
            raise ValueError
        ind1, ind2 = self._vertices_list.index(sentence), self._vertices_list.index(other_sentence)
        return self._matrix[ind1][ind2]

    def fill_from_sentences(self, sentences: tuple[Sentence, ...]) -> None:
        """
        Updates graph instance with vertices and edges extracted from sentences
        :param sentences
        :return:
        """
        check_iterable(sentences, tuple, Sentence)
        if not sentences:
            raise ValueError
        check_type(sentences, tuple)
        for ind1, one_sent in enumerate(sentences):
            for ind2, another_sent in enumerate(sentences):
                if ind2 == ind1:
                    break
                self.add_edge(one_sent, another_sent)


class TextRankSummarizer:
    """
    TextRank for summarization
    """

    _scores: dict[Sentence, float]
    _graph: SimilarityMatrix

    def __init__(self, graph: SimilarityMatrix) -> None:
        """
        Constructs all the necessary attributes
        :param graph: the filled instance of the similarity matrix
        """
        check_type(graph, SimilarityMatrix)
        self._graph = graph
        self._damping_factor = 0.85
        self._convergence_threshold = 0.0001
        self._max_iter = 50
        self._scores = {}

    def update_vertex_score(
            self, vertex: Sentence, incidental_vertices: list[Sentence], scores: dict[Sentence, float]
    ) -> None:
        """
        Changes vertex significance score using algorithm-specific formula
        :param vertex: a sentence
        :param incidental_vertices: vertices with similarity score > 0 for vertex
        :param scores: current vertices scores
        :return:
        """
        check_type(vertex, Sentence)
        check_type(scores, dict)
        sum_ = sum((1 / (1 + self._graph.calculate_inout_score(inc))) * scores[inc] for inc in incidental_vertices)
        self._scores[vertex] = self._damping_factor * (sum_ - 1) + 1

    def train(self) -> None:
        """
        Iteratively computes significance scores for vertices
        """
        vertices = self._graph.get_vertices()
        for vertex in vertices:
            self._scores[vertex] = 1.0

        for iteration in range(self._max_iter):
            prev_score = self._scores.copy()
            for scored_vertex in vertices:
                similar_vertices = [vertex for vertex in vertices
                                    if self._graph.get_similarity_score(scored_vertex, vertex) > 0]
                self.update_vertex_score(scored_vertex, similar_vertices, prev_score)
            abs_score_diff = [abs(i - j) for i, j in zip(prev_score.values(), self._scores.values())]

            if sum(abs_score_diff) <= self._convergence_threshold:  # convergence condition
                print("Converging at iteration " + str(iteration) + "...")
                break

    def get_top_sentences(self, n_sentences: int) -> tuple[Sentence, ...]:
        """
        Retrieves top n most important sentences in the encoded text
        :param n_sentences: number of sentence to retrieve
        :return: a sequence of sentences
        """
        check_type(n_sentences, int)
        return tuple(sorted(self._scores, key=lambda x: self._scores[x], reverse=True)[:n_sentences])

    def make_summary(self, n_sentences: int) -> str:
        """
        Constructs summary from the most important sentences
        :param n_sentences: number of sentences to include in the summary
        :return: summary
        """
        check_type(n_sentences, int)
        top_sentences = sorted(self.get_top_sentences(n_sentences), key=lambda x: x.get_position())
        return '\n'.join([i.get_text() for i in top_sentences])


class NoRelevantTextsError(Exception):
    pass


class IncorrectQueryError(Exception):
    pass


class Buddy:
    """
    (Almost) All-knowing entity
    """

    def __init__(
            self,
            paths_to_texts: list[str],
            stop_words: tuple[str, ...],
            punctuation: tuple[str, ...],
            idf_values: dict[str, float],
    ):
        """
        Constructs all the necessary attributes
        :param paths_to_texts: paths to the texts from which to learn
        :param stop_words: a sequence of stop words
        :param punctuation: a sequence of punctuation symbols
        :param idf_values: pre-computed IDF values
        """
        self._stop_words = stop_words
        self._punctuation = punctuation
        self._idf_values = idf_values
        self._text_preprocessor = TextPreprocessor(self._stop_words, self._punctuation)
        self._sentence_encoder = SentenceEncoder()
        self._sentence_preprocessor = SentencePreprocessor(self._stop_words, self._punctuation)
        self._paths_to_texts = paths_to_texts
        self._knowledge_database = {}

        for path in paths_to_texts:
            self.add_text_to_database(path)

    def add_text_to_database(self, path_to_text: str) -> None:
        """
        Adds the given text to the existing database
        :param path_to_text
        :return:
        """
        check_type(path_to_text, str)
        with open(path_to_text, encoding='utf-8') as file:
            text = file.read()
        preprocessor = SentencePreprocessor(self._stop_words, self._punctuation)
        sentences = preprocessor.get_sentences(text)
        self._sentence_encoder.encode_sentences(sentences)
        preprocessed_text = self._text_preprocessor.preprocess_text(text)
        tf_idf = TFIDFAdapter(preprocessed_text, self._idf_values)
        tf_idf.train()
        number_of_keywords = 100
        keywords = tf_idf.get_top_keywords(number_of_keywords)
        similarity_matrix = SimilarityMatrix()
        similarity_matrix.fill_from_sentences(sentences)
        summarizer = TextRankSummarizer(similarity_matrix)
        summarizer.train()
        summary = '\n'.join([i.get_text() for i in sorted(summarizer.get_top_sentences(5),
                                                          key=lambda x: x.get_position())])
        key = {'sentences': sentences, 'keywords': keywords, 'summary': summary}
        self._knowledge_database[path_to_text] = key

    def _find_texts_close_to_keywords(self, keywords: tuple[str, ...], n_texts: int) -> tuple[str, ...]:
        """
        Finds texts that are similar (i.e. contain the same keywords) to the given keywords
        :param keywords: a sequence of keywords
        :param n_texts: number of texts to find
        :return: the texts' ids
        """
        check_iterable(keywords, tuple, str)
        check_type(n_texts, int)
        scores = {}
        for path_to_text, data in self._knowledge_database.items():
            scores[path_to_text] = calculate_similarity(data['keywords'], keywords)
        if not any(scores.values()):
            raise NoRelevantTextsError('Texts that are related to the query were not found. Try another query.')
        return tuple(sorted(scores, key=lambda x: (scores[x], x), reverse=True)[:n_texts])

    def reply(self, query: str, n_summaries: int = 3) -> str:
        """
        Replies to the query
        :param query: the query
        :param n_summaries: the number of summaries to include in the answer
        :return: the answer
        """
        if not query:
            raise IncorrectQueryError('Incorrect query. Use string as input.')
        try:
            check_type(query, str)
        except ValueError as exc:
            raise IncorrectQueryError('Incorrect query. Use string as input.') from exc
        check_type(n_summaries, int)
        if len(self._knowledge_database) < n_summaries:
            raise ValueError
        user_keywords = self._text_preprocessor.preprocess_text(query)
        texts = self._find_texts_close_to_keywords(user_keywords, n_summaries)[:5]
        repl = []
        for text in texts:
            repl.append(self._knowledge_database[text]["summary"])
        return 'Ответ:\n' + '\n\n'.join(repl)
