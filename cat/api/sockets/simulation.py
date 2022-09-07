"""
UNUSED
"""
import os
from flask_jwt_extended import jwt_required
from flask_socketio import Namespace, emit
from flask_restplus.inputs import boolean
from cat.simulation.simulator import Generator
import threading

# allow disabling JWT by overriding default
if not boolean(os.getenv('JWT_ON', False)):
    jwt_required = lambda fn: fn


class KillableThread(threading.Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        self.killed = False
        super(KillableThread, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs,
                                             daemon=daemon)

    def kill(self):
        self.killed = True


class SimulationNamespace(Namespace):

    def __init__(self, namespace=None):
        self.simulator: Generator = None
        self.simulator_thread: KillableThread = None
        super(SimulationNamespace, self).__init__(namespace=namespace)

    @jwt_required
    def on_connect(self):
        print('Client connected')
        pass

    @jwt_required
    def on_disconnect(self):
        print('Client disconnected')
        pass

    @jwt_required
    def on_start_simulation(self, simulation, schema_config):
        bot_name = simulation['botName']
        num_dialogs = simulation['dialogs']
        tasks = simulation['tasks']
        tasks = Generator.transform_tasks(tasks)
        schema_config = Generator.transform_config(schema_config)
        self.simulator = Generator(bot_name=bot_name,
                                   tasks=tasks,
                                   schema=schema_config,
                                   num_dialogs_per_task=num_dialogs,
                                   socket=self)
        self.simulator_thread = KillableThread(target=self.simulator.run, name='simulator')
        self.simulator_thread.start()

    @jwt_required
    def on_stop_simulation(self):
        if self.simulator:
            self.simulator.stop()
        if self.simulator_thread:
            self.simulator_thread.kill()
        else:
            emit('simulation_stopped', {
                'message': 'No simulation running'
            })

    def start_background_task(self, target):
        self.socketio.start_background_task(target)
