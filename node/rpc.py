from jsonrpc.backend.flask import api

from node import server

server.register_blueprint(api.as_blueprint())


@api.dispatcher.add_method(name='service.echo')
def echo(*args, **kwargs):
    """
    Echoes you back.

    :param args: args to echo back
    :type args: Set[]
    :param kwargs: key word args to echo back
    :type kwargs: Mapping[]
    :return: [args, {{kwargs}}]
    :rtype: Set[Set[], Mapping[]]
    """

    return args, kwargs


