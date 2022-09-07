import os
from flask_restplus import Resource, Namespace, fields
from flask_restplus.inputs import boolean
from flask_jwt_extended import jwt_required
import nltk
from nltk.corpus import wordnet

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# allow disabling JWT by overriding default
if not boolean(os.getenv('JWT_ON', False)):
    jwt_required = lambda fn: fn
api = Namespace('nl', description='Natural language related operations')

synonyms_data = api.model('Synonyms_data', {
    'word': fields.String(readonly=True, description='The word to find a synonym for')
})


@api.route('/synonyms/<word>')
class Synonym(Resource):
    @api.doc('list_synonyms')
    @api.expect(synonyms_data)
    @jwt_required
    def get(self, word):
        word = word.strip()
        synonyms = []
        wordnet.ensure_loaded()
        for synset in wordnet.synsets(word):
            lemmas = [clean(lemma) for lemma in synset.lemma_names() if not lemma == word]
            if len(lemmas) > 0:
                synonym = {}
                name, pos_tag, _ = tuple(synset.name().split('.'))
                synonym['meaning'] = name
                definition = synset.definition()
                synonym['definition'] = definition
                pos_type = get_word_type(pos_tag)
                synonym['type'] = pos_type
                synonym['lemmas'] = lemmas
                synonyms.append(synonym)
        return synonyms, 200


def get_word_type(pos_tag):
    if pos_tag == 'n':
        return 'noun'
    elif pos_tag == 'v':
        return 'verb'
    elif pos_tag == 'r':
        return 'adverb'
    elif pos_tag == 's' or pos_tag == 'a':
        return 'adjective'
    else:
        return 'unknown'


def clean(s):
    return s.replace('_', ' ')
