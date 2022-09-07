"""
UNUSED
"""
from flask import request
from flask_restplus import Resource, Namespace, fields
from flask_restplus.inputs import boolean
from flask_jwt_extended import jwt_required
import os
import yaml
import re

# allow disabling JWT by overriding default
if not boolean(os.getenv('JWT_ON', False)):
    jwt_required = lambda fn: fn

api = Namespace('rasa', description='Bot related operations.')

# login_data = api.model('Login_data', {
#     'passphrase': fields.String('Passphrase', required=True),
# })

BOT_BASE_DIR = 'data/bots'


@api.route('/bots')
class Bots(Resource):
    @api.doc('list_bots')
    @jwt_required
    def get(self):
        if not os.path.exists(BOT_BASE_DIR):
            return [], 200
        bot_dirs = [bot for bot in os.listdir(BOT_BASE_DIR)]
        bots = []
        for bot in bot_dirs:
            delimiter = bot.rfind('_')
            bots.append({
                'path': bot,
                'name': bot[:delimiter],
                'created': int(bot[delimiter + 1:])
            })
        return bots, 200


config_data = api.model('Config_data', {
    'language': fields.String(description='The language of the training embeddings.')
})


@api.route('/bots/<string:path>/config')
class BotConfig(Resource):
    @api.doc('bot_config')
    @jwt_required
    def get(self, path):
        bot_dir = os.path.abspath(f'{BOT_BASE_DIR}/{path}')
        if not os.path.exists(bot_dir):
            api.abort(404, f'Could not find config for bot {path}')
        try:
            config_path = os.path.join(bot_dir, 'config.yml')
            with open(config_path, 'r', encoding='utf-8') as config_stream:
                config = yaml.load(config_stream, yaml.FullLoader)
                return transform_config(config), 200
        except Exception as e:
            api.abort(400, e)

    @api.doc('update_bot_config')
    @api.expect(config_data)
    # @jwt_required
    def post(self, path):
        data = request.json
        print(data)
        return True, 200


def transform_config(config):
    transformed_config = {
        'language': config['language'],
        'pipeline': config['pipeline'],
        'policies': [transform_policy(policy) for policy in config['policies']]
    }
    return transformed_config


def transform_policy(policy):
    transformed_policy = {}
    if policy['name'] == 'EmbeddingPolicy':
        transformed_policy = {
            'name': 'EmbeddingPolicy',
            'priority': 1,
            'hiddenLayersSizesPreDial': policy[
                'hidden_layers_sizes_pre_dial'] if 'hidden_layers_sizes_pre_dial' in policy.keys() else [],
            'hiddenLayersSizesBot': policy[
                'hidden_layers_sizes_bot'] if 'hidden_layers_sizes_bot' in policy.keys() else [],
            'transformerSize': policy['transformer_size'] if 'transformer_size' in policy.keys() else 128,
            'numTransformerLayers': policy[
                'num_transformer_layers'] if 'num_transformer_layers' in policy.keys() else 1,
            'posEncoding': policy['pos_encoding'] if 'pos_encoding' in policy.keys() else 'timing',
            'maxSeqLength': policy['max_seq_length'] if 'max_seq_length' in policy.keys() else 256,
            'numHeads': policy['num_heads'] if 'num_heads' in policy.keys() else 4,
            'batchSize': policy['batch_size'] if 'batch_size' in policy.keys() else [8, 32],
            'batchStrategy': policy['batch_strategy'] if 'batch_strategy' in policy.keys() else 'balanced',
            'epochs': policy['epochs'] if 'epochs' in policy.keys() else 1,
            'randomSeed': policy['random_seed'] if 'random_seed' in policy.keys() else None,
            'embedDim': policy['embed_dim'] if 'embed_dim' in policy.keys() else 20,
            'numNeg': policy['num_neg'] if 'num_neg' in policy.keys() else 20,
            'similarityType': policy['similarity_type'] if 'similarity_type' in policy.keys() else 'auto',
            'lossType': policy['loss_type'] if 'loss_type' in policy.keys() else 'softmax',
            'muPos': policy['mu_pos'] if 'mu_pos' in policy.keys() else 0.8,
            'muNeg': policy['mu_neg'] if 'mu_neg' in policy.keys() else -0.2,
            'useMaxSimNeg': policy['use_max_sim_neg'] if 'use_max_sim_neg' in policy.keys() else True,
            'scaleLoss': policy['scale_loss'] if 'scale_loss' in policy.keys() else True,
            'c2': policy['C2'] if 'C2' in policy.keys() else 0.001,
            'cEmb': policy['C_emb'] if 'C_emb' in policy.keys() else 0.8,
            'dropoutRateA': policy['droprate_a'] if 'droprate_a' in policy.keys() else 0.1,
            'dropoutRateB': policy['droprate_b'] if 'droprate_b' in policy.keys() else 0.0,
            'evaluateEveryNumEpochs': policy[
                'evaluate_every_num_epochs'] if 'evaluate_every_num_epochs' in policy.keys() else 20,
            'evaluateOnNumExamples': policy[
                'evaluate_on_num_examples'] if 'evaluate_on_num_examples' in policy.keys() else 0
        }
    elif policy['name'] == 'KerasPolicy':
        transformed_policy = {
            'name': 'KerasPolicy',
            'priority': 1,
            'rnnSize': policy['rnn_size'] if 'rnn_size' in policy.keys() else 32,
            'epochs': policy['epochs'] if 'epochs' in policy.keys() else 100,
            'batchSize': policy['batch_size'] if 'batch_size' in policy.keys() else 32,
            'validationSplit': policy['validation_split'] if 'validation_split' in policy.keys() else 0.1,
            'randomSeed': policy['random_seed'] if 'random_seed' in policy.keys() else None,
        }
    elif policy['name'] == 'MappingPolicy':
        transformed_policy = {
            'name': 'MappingPolicy',
            'priority': 2
        }
    elif policy['name'] == 'MemoizationPolicy':
        transformed_policy = {
            'name': 'MemoizationPolicy',
            'priority': 3
        }
    elif policy['name'] == 'FallbackPolicy':
        transformed_policy = {
            'name': 'FallbackPolicy',
            'priority': 4
        }
    elif policy['name'] == 'FormPolicy':
        transformed_policy = {
            'name': 'FormPolicy',
            'priority': 5
        }
    return transformed_policy


@api.route('/bots/<string:path>/domain')
class BotDomain(Resource):
    @api.doc('bot_domain')
    # @jwt_required
    def get(self, path):
        bot_dir = os.path.abspath(f'{BOT_BASE_DIR}/{path}')
        if not os.path.exists(bot_dir):
            api.abort(404, f'Could not find domain for bot {path}')
        try:
            domain_path = os.path.join(bot_dir, 'domain.yml')
            with open(domain_path, 'r', encoding='utf-8') as domain_stream:
                domain = yaml.load(domain_stream, yaml.FullLoader)
                return transform_domain(domain), 200
        except Exception as e:
            api.abort(400, e)


def transform_domain(domain):
    transformed_domain = {
        'actions': domain['actions'] if 'actions' in domain.keys() else [],
        'slots': transform_slots(domain['slots']) if 'slots' in domain.keys() else [],
        'entities': domain['entities'] if 'entities' in domain.keys() else [],
        'intents': transform_intents(domain['intents']) if 'intents' in domain.keys() else [],
        'templates': transform_templates(domain['templates']) if 'templates' in domain.keys() else []
    }
    return transformed_domain


def transform_slots(slots):
    transformed_slots = [{
        'name': slotKey,
        'type': slots[slotKey]['type'] if 'type' in slots[slotKey].keys() else 'unfeaturized'
    } for slotKey in slots.keys()]
    return transformed_slots


def transform_templates(templates):
    transformed_templates = [{
        'actionName': actionKey,
        'templates': [
            {
                'text': template['text']
            }
            for template in templates[actionKey] if 'text' in template.keys()]
    } for actionKey in templates.keys()]
    return transformed_templates


def transform_intents(intents):
    transformed_intents = [{
        'name': intent,
        'triggers': intent['triggers'] if isinstance(intent, dict) else None
    } for intent in intents]

    return transformed_intents


story_re = re.compile('##.*\n')


@api.route('/bots/<string:path>/stories')
class BotStories(Resource):
    @api.doc('bot_stories')
    @api.expect(config_data)
    # @jwt_required
    def get(self, path):
        bot_dir = os.path.abspath(f'{BOT_BASE_DIR}/{path}')
        if not os.path.exists(bot_dir):
            api.abort(404, f'Could not find stories for bot {path}')
        try:
            stories_path = os.path.join(bot_dir, 'data/stories.md')
            with open(stories_path, 'r', encoding='utf-8') as stories_stream:
                stories = [s for s in story_re.split(stories_stream.read()) if len(s) > 0]
                return stories, 200
        except Exception as e:
            api.abort(400, e)
