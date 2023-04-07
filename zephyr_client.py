import zephyr
from constants import *

# Zephyr client

class Zephyr:
    """
    Simple Zephyr client that remembers its subscriptions
    with a format similar to .zephyr.subs
    """

    # Which classes are we subscribed to all their instances?
    _entire_class_subscriptions: set[str]
    _subscriptions: zephyr.Subscriptions

    def _subscribe(self, triplet):
        """
        Subscribe (without saving into disk)
        """
        cls,instance,recipient = triplet
        if instance == '*':
            self._entire_class_subscriptions.add(cls)
        assert recipient == '*', 'Non-wildcard recipients are not supported by this bridge'
        self._subscriptions.add(triplet)
        

    def __init__(self):
        self._entire_class_subscriptions = set()
        zephyr.init()
        self._subscriptions = zephyr.Subscriptions()
        with open(ZEPHYR_SUBSCRIPTIONS_FILE, 'r') as f:
            subscriptions = [tuple(line.split(',')) for line in f.read().split('\n') if line != '']
        for triplet in subscriptions:
            self._subscribe(triplet)
        

    def all_instances_subscribed(self, cls):
        """
        Are we subscribed to all instances of `cls`?
        """
        return cls in self._entire_class_subscriptions
    
    
    def subscribe(self, cls, instance=None):
        """
        Subscribe to the given Zephyr class and instance
        (equivalent to `zctl add`, in that it persists)

        If instance is not given, assume all instances
        """ 
        triplet = (cls, instance if instance else '*', '*')
        with open(ZEPHYR_SUBSCRIPTIONS_FILE, 'a') as f:
            f.write(','.join(triplet) + '\n')
        self._subscribe(triplet)
    

    def send_message(self, message, cls=DEFAULT_CLASS, instance=DEFAULT_INSTANCE, opcode=DEFAULT_OPCODE, sender=None, display_name=None):
        """
        Send a Zephyr message to the given class and instance
        """
        # Set signature to sender if not given
        if display_name is None:
            display_name = sender
        
        notice = zephyr.ZNotice(
            cls=cls,
            instance=instance,
            sender=sender,
            opcode=opcode,
            format='Config error: see http://mit.edu/df', # URL actually leads somewhere (what BarnOwl uses)
            fields=[display_name, message],

            # otherwise tickets will expire and someone or something needs to kinit (the keytab) again
            # (TODO: is there any use to authenticating?)
            # http://kb.mit.edu/confluence/pages/viewpage.action?pageId=3907535
            auth=False,
        )
        notice.send()






