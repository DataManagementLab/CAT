import json
import logging
import os
from argparse import ArgumentParser

from typing import List

from cat.simulation.nlg.paraphrasing import AbstractParaphraser, PPDBParaphraser, GooglePivotParaphraser

logger = logging.getLogger('nlg-paraphraser')
logger.setLevel(level=logging.DEBUG)


class NLUParaphraser:

    def __init__(self, template_path: str, out_path: str, paraphraser_names: List[str], pivot_languages=['en', 'de']):
        self.template_path = template_path
        self.templates = {}
        self.out_path = out_path
        self.paraphrasers: List[AbstractParaphraser] = [p for p in [self._get_paraphraser(n, pivot_languages) for n in
                                                                    paraphraser_names] if p]

    def _get_paraphraser(self, name, languages=[]):
        if name == 'p':
            return PPDBParaphraser()
        if name == 'g':
            if len(set(languages)) < 2:
                logger.error(f'Expected at least 2 langauges for pivot paraphrasing but got {languages}')
                return None
            if languages[0] != languages[-1]:
                languages.append(languages[0])
            return GooglePivotParaphraser(languages=languages)
        return None

    def paraphrase_templates(self):
        with open(self.template_path) as t_file:
            self.templates = json.load(t_file)
        for intent_dict in self.templates.get('intents', []):
            key = intent_dict['id']
            templates = intent_dict['templates']
            paraphrased = []
            for template in templates:
                for p in self.paraphrasers:
                    paraphrase = p.paraphrase_sentence(template)
                    if paraphrase and paraphrase not in templates and paraphrase not in paraphrased:
                        paraphrased.append(paraphrase)
            logger.info(f'Generated {len(paraphrased)} paraphrases for intent {key}')
            intent_dict['templates'] += paraphrased
        with open(self.out_path, 'w') as out_file:
            json.dump(self.templates, out_file)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-t', '--templates', type=str, help='The path to the intent templates')
    parser.add_argument('-p', '--paraphrasers', type=str, nargs='*', default=['g'],
                        help='Type of paraphraser to use for the templates')
    parser.add_argument('-l', '--languages', type=str, nargs='*', default=['en', 'de', 'fr'],
                        help='Languages to use for pivot paraphrasing')
    parser.add_argument('-o', '--out_path', type=str, help='Where to dump the paraphrased training data')

    args = parser.parse_args()

    languages = args.languages
    template_path = args.templates
    out_path = args.out_path
    out_prefix, out_ext = os.path.splitext(out_path)
    # use each as a single paraphraser
    for paraphraser in args.paraphrasers:
        out_path = f'{out_prefix}_{paraphraser}{out_ext}'
        paraphraser = NLUParaphraser(template_path, out_path, paraphraser_names=[paraphraser],
                                     pivot_languages=languages)
        paraphraser.paraphrase_templates()
    # combine all
    out_path = f'{out_prefix}_{"_".join(args.paraphrasers)}{out_ext}'
    paraphraser = NLUParaphraser(template_path, out_path, paraphraser_names=args.paraphrasers, pivot_languages=languages)
    paraphraser.paraphrase_templates()