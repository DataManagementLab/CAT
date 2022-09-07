import os
from abc import ABC, abstractmethod
import json
import argparse
import re
from collections import defaultdict


import requests
import logging
from html import unescape as htmlue
from nltk.translate.bleu_score import sentence_bleu
from cat.simulation.nlg import common

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AbstractParaphraser(ABC):
    ESCAPE_SYM = '#'
    ESCAPE_PATTERN = re.compile(f'{ESCAPE_SYM}([a-zA-Z_]*)')

    def __init__(self, name):
        self.name = name

    def paraphrase_file(self, input_path: str, output_path: str, compute_bleu=True):
        out_data = []
        with open(input_path, mode='r', encoding='utf-8') as sents_file:
            for line in sents_file.readlines():
                sent = line.strip('\n').strip()
                logger.info(f'Input: {sent}')
                paraphrased = self.paraphrase_sentence(sent=sent)
                logger.info(f'Output: {paraphrased}')
                bleu = sentence_bleu([self._sent_to_tokens(paraphrased)],
                                     self._sent_to_tokens(sent)) if compute_bleu else None
                out_data.append({'input': sent, 'output': paraphrased, 'bleu': bleu})
        with open(output_path, mode='w', encoding='utf-8') as out_file:
            json.dump(out_data, out_file, indent=2)

    def _sent_to_tokens(self, sent, split_sym=' '):
        return sent.split(split_sym)

    def _escape_placeholders(self, sent: str) -> str:
        placeholders = common.get_template_placeholders(sent)
        escaped_placedholders = dict([(placeholder, f'{self.ESCAPE_SYM}{placeholder}') for placeholder in placeholders])
        return sent.format(**escaped_placedholders)

    def _unescape_placeholders(self, original: str, escaped: str) -> str:
        unescaped = self.ESCAPE_PATTERN.sub(r'{\1}', escaped)
        tokenized = self._sent_to_tokens(unescaped)
        for i, token in enumerate(tokenized):
            if re.findall('{(.+?)}', token):
                lower_placeholder = token.lower()
                tokenized[i] = lower_placeholder
        unescaped = ' '.join(tokenized)
        original_ph = common.get_template_placeholders(original)
        new_ph = common.get_template_placeholders(unescaped)
        unknown_placeholders = set(new_ph) - set(original_ph)
        if len(unknown_placeholders) > 0:
            logger.error(f'Unknown placeholders {unknown_placeholders}')
            return None
        for ph in original_ph:
            if f'{{{ph}}}' not in unescaped:
                logger.error(f'Missing placeholder {{{ph}}} in back translation {unescaped}')
                return None
        return unescaped

    @abstractmethod
    def paraphrase_sentence(self, sent: str):
        pass

    @abstractmethod
    def paraphrase_word(self, token: str):
        pass


class PPDBParaphraser(AbstractParaphraser):
    PPDB_RAW = 'ppdb'
    PPDB_JSON = 'ppdb.json'

    def __init__(self):
        current_path = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(current_path, self.PPDB_JSON)
        if not os.path.exists(json_path):
            self._preprocess()
        with open(json_path, 'r') as f:
            self.paraphrases = json.load(f)
        AbstractParaphraser.__init__(self, 'ppdb')

    def _preprocess(self):
        current_path = os.path.dirname(os.path.realpath(__file__))
        raw_path = os.path.join(current_path, self.PPDB_RAW)
        ppdb_dict = defaultdict(list)
        with open(raw_path, 'r') as pp_file:
            for line in pp_file:
                columns = line.strip().split(' ||| ')
                if len(columns) < 6:
                    continue
                if columns[5] != 'Equivalence':
                    continue
                word = columns[1]
                paraphrase = columns[2]
                if paraphrase not in ppdb_dict[word]:
                    ppdb_dict[word].append(paraphrase)
        dump_path = os.path.join(current_path, self.PPDB_JSON)
        with open(self.PPDB_JSON, 'w') as out_file:
            json.dump(ppdb_dict, out_file, sort_keys=True)

    def paraphrase_sentence(self, sent: str):
        paraphrased = []
        for word in self._sent_to_tokens(sent):
            paraphrase = self.paraphrase_word(word)
            paraphrased.append(paraphrase)
        return ' '.join(paraphrased)

    def paraphrase_word(self, token: str):
        possibilities = self.paraphrases.get(token, [])
        if len(possibilities) == 0:
            return token
        return possibilities[0] # random.choice(possibilities)


class AbstractPivotParaphraser(AbstractParaphraser, ABC):
    def __init__(self, name):
        AbstractParaphraser.__init__(self, name)


class GooglePivotParaphraser(AbstractPivotParaphraser):
    URL = 'https://translation.googleapis.com/language/translate/v2'
    API_KEY = 'AIzaSyA2AhHSZ5qCf-aJEPXczK2n2lMpS3Amlis'

    def __init__(self, languages):
        self.languages = languages
        AbstractPivotParaphraser.__init__(self, 'google')

    def paraphrase_sentence(self, sent: str) -> str:
        translation = self._multi_translation(sent, self.languages)
        return translation

    def paraphrase_word(self, word: str) -> str:
        translation = self._multi_translation(word, self.languages)
        return translation

    def _multi_translation(self, text: str, languages=['en', 'de', 'fr', 'zh-CN', 'en']) -> str:
        if len(set(languages)) < 2:
            raise Exception('Need at least one intermediate language for pivot paraphrasing but got ' + languages)
        base = self._escape_placeholders(text)
        translation = base
        for i in range(len(languages) - 1):
            src_lang = languages[i]
            target_lang = languages[i + 1]
            translation = self._query_translation(text=translation, source=src_lang, target=target_lang)
        return self._unescape_placeholders(text, translation)

    def _query_translation(self, text: str, source: str = 'en', target='de') -> str:
        params = {'q': text, 'source': source, 'target': target, 'key': self.API_KEY}
        r = requests.post(url=self.URL, data=params)
        if r.status_code == 403:
            return self._query_translation(text, source, target)
        response = json.loads(htmlue(r.text))
        translations = response.get('data', {}).get('translations', [])
        return [translation.get('translatedText', text) for translation in translations][0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--query', type=str,
                        help='Input query to paraphrase. Can contain escaped characters in curly brackets')
    parser.add_argument('-i', '--in_file', type=str, help='Line separated list of queries')
    parser.add_argument('-o', '--out_file', type=str, help='Output file to write json to')
    parser.add_argument('-l', '--languages', type=str, nargs='*',
                        help='The languages to use for pivot translation. First languages is appended as target automatically. Language abbreviations are not validated')
    parser.add_argument('-b', '--bleu', type=bool, default=True, help='Wether to compute and log the BLEU score')
    parser.add_argument('-p', '--paraphraser', default='g',
                        help='Type of paraphraser. "g" for Google Translate API, "p" for PPDB paraphraser')
    args = parser.parse_args()

    query = args.query
    in_file = args.in_file
    if query and in_file:
        logger.error('Can either specify query or input file to paraphrase')
        exit(1)
    if not (query or in_file):
        logger.error('Must either specify query or input file to paraphrase')
        exit(1)
    if args.in_file and not args.out_file:
        logger.error(f'Missing argument "-o"/"--out_file" for file paraphrasation')
        exit(1)

    languages = []
    paraphrase_type = args.paraphraser
    if paraphrase_type == 'p':
        p = PPDBParaphraser()
    elif not paraphrase_type == 'g':
        logger.warning(f'Unknown paraphraser type "{paraphrase_type}", using default paraphraser "g"')
        paraphrase_type = 'g'
    if paraphrase_type == 'g':
        languages = args.languages
        if not languages or len(set(languages)) < 2:
            logger.error('At least two languages required for pivot paraphrasing')
            exit(1)
        if not languages[0] == languages[-1]:
            languages.append(languages[0])
        p = GooglePivotParaphraser(languages=languages)

    if query:
        logger.info(f'Input Sentence: {query}')
        paraphrase = p.paraphrase_sentence(query)
        logger.info(f'Output Sentence: {paraphrase}')
    else:
        p.paraphrase_file(input_path=in_file, output_path=args.out_file, compute_bleu=args.bleu)
