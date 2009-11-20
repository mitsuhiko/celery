import time
import socket
import threading
from UserDict import UserDict

from celery.messaging import EventPublisher, EventConsumer


def Event(type, **fields):
    return dict(fields, type=type, timestamp=time.time())


class EventDispatcher(object):
    """

    dispatcher.send("event-name", arg1=1, arg2=2, arg3=3)

    """
    def __init__(self, connection, hostname=None):
        self.connection = connection
        self.publisher = EventPublisher(self.connection)
        self.hostname = hostname or socket.gethostname()
        self._lock = threading.Lock()

    def send(self, type, **fields):
        self._lock.acquire()
        try:
            fields["timestamp"] = time.time()
            fields["hostname"] = self.hostname
            self.publisher.send(Event(type, **fields))
        finally:
            self._lock.release()

    def close(self):
        self._lock.locked() and self._lock.release()
        self.publisher and self.publisher.close()


class EventReceiver(object):
    handlers = {}

    def __init__(self, connection, handlers=None):
        self.connection = connection
        if handlers is not None:
            self.handlers = handlers

    def process(self, type, event):
        print("Received event: %s" % event)
        handler = self.handlers.get(type) or self.handlers.get("*")
        handler and handler(event)

    def _receive(self, message_data, message):
        type = message_data.pop("type").lower()
        self.process(type, Event(type, **message_data))

    def consume(self, limit=None):
        consumer = EventConsumer(self.connection)
        consumer.register_callback(self._receive)
        it = consumer.iterconsume(limit=limit)
        while True:
            it.next()
