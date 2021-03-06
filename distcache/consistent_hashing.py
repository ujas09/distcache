"""
Consistent Hashing

Consistent hashing is scheme which does not depend on the number of servers.
Each server is assigned a position on a abstract circle or a hash ring.

So you have a list of servers [a, b, c]
You make k copies of them. It makes the consistent hashing better.
servers = [a1, a2, ak, b1, b2, bk, c1, c2, ck]
Of course, you can have weighted servers so that better servers have higher chances of landing a keys

Now we assign them a position in the 32bit ring.
[...ak....b2....c1....c2....a2.....b1....bk....a1.....ck..........]
[...10....19k...1M...28M....54.2M..60M...67M...100M...124M..23^32-1]
So we need to sort the servers according to their position.

Now when user says which server to send a particular key "apple".
We hash the key: apple-> 16M.
What's larger than 16M and has a server? 28M.
Great, we send the key to c2. c2 is c, remember?

What happens when a server is down?
There is no response and the query has to be queried against a database
or any other function. And, it has to be stored again in the server.

If the server c went down. Our key ring would be updated to something like this.
[...ak....b2...........a2.....b1....bk....a1.................]
[...10....19k..........54.2M..60M...67M...100M........23^32-1]
We hash the key: apple-> 16M.
What's larger than 16M and has a server? 54.2M.
Great, we send the key to a2.

Similarly, we can add servers in the same way.
There will be cache misses first because the server next to the new server on the ring has the key.
Then those keys will expire out or will be LRU invalidated.
Similarly, there is cache miss when a server goes down. All the queries that were to be handed by that
server are sent to the next server.

Notes: We compute position for servers until there is no collision.

Example usage:
    servers = ['192.168.0.246:11212', '192.168.0.247:11212', '192.168.0.249:11212']
    weights = [3, 3, 3]
    ring = ConsistentHashing(servers, weights)
    server = ring.get_node('my_key')

TODO: Allow users to specify both number of replicas and weight of servers
TODO: Use a better hashing technique. Something that distributes more uniformly among the keys.
"""
from bisect import bisect_right, insort


class ConsistentHashing:
    """
    Implements consistent hashing
    """

    def __init__(self, nodes=None, weights=None):
        """
        Initially we will make as may replicas as weight
        :param nodes: list of servers
        :param weights[int]: the servers with higher usable capacity should have weights.
        """
        self.ring = []  # (position, server) in sorted order
        self.occupied = set()
        self.weight = 5
        if nodes and not weights:
            weights = [self.weight] * len(nodes)
        # The user can keep adding servers as the user discovers servers
        if nodes and len(nodes):
            self._generate_ring(nodes, weights)

    def _generate_ring(self, nodes, weights):
        for id, node in enumerate(nodes):
            for i in range(weights[id]):
                key = "{}_{}".format(node, i)
                position = hash(key)
                # If the position already exists hash again.
                while position in self.occupied:
                    key = "{}_{}".format(key, i)
                    position = hash(key)
                self.occupied.add(position)
                insort(self.ring, (position, node))

    def add_node(self, node, weight=5):
        self._generate_ring([node], [weight])

    def remove_node(self, node):
        """
        Remove node from the ring because it is dead or unavailable.
        """
        temp = []
        for position, server in self.ring:
            if server != node:
                temp.append((position, server))
                self.occupied.remove(position)
        self.ring = temp.copy()
        del temp

    def get_node(self, key):
        """
        Get the node/server where the key is or should be.
        :param key:
        :return: node
        """
        position = bisect_right(self.ring, (hash(key), None))
        if position == len(self.ring):
            position = 0
        return self.ring[position][1]


if __name__ == '__main__':
    servers = ['192.168.0.246:11212',
               '192.168.0.247:11212',
               '192.168.0.249:11212']
    weights = [5, 3, 1]
    ring = ConsistentHashing(servers, weights)
    server = ring.get_node('my_key')
    print(server)

    ring.remove_node(server)

    server = ring.get_node('my_key')
    print(server)
