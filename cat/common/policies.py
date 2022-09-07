from typing import Optional, Any
from copy import deepcopy
from rasa.core.constants import DEFAULT_POLICY_PRIORITY
from rasa.core.featurizers import TrackerFeaturizer
from rasa.core.policies.ted_policy import TEDPolicy
from rasa.utils.tensorflow.models import RasaModel
from sympy.printing.tests.test_tensorflow import tf
from tensorflow.python.keras.callbacks import EarlyStopping


class TEDEarlyStoppingPolicy(TEDPolicy):
    es_defaults = {
        'monitor': 'acc',
        'mode': 'max',
        'min_delta': 0.005,
        'patience': 5,
        'verbose': 0
    }

    def __init__(self,
                 featurizer: Optional[TrackerFeaturizer] = None,
                 priority: int = DEFAULT_POLICY_PRIORITY,
                 max_history: Optional[int] = None,
                 model: Optional[RasaModel] = None,
                 **kwargs: Any
                 ):
        callback_args = deepcopy(self.es_defaults)
        es_args = kwargs.get('early_stopping', self.es_defaults)
        callback_args.update(es_args)
        add_args = {
            'callbacks': [
                EarlyStopping(monitor=callback_args['monitor'], mode=callback_args['mode'],
                              min_delta=callback_args['min_delta'],
                              patience=callback_args['patience'], verbose=callback_args['verbose'])
            ]
        }
        kwargs.update(add_args)
        TEDPolicy.__init__(self, featurizer, priority, max_history, model, **kwargs)
