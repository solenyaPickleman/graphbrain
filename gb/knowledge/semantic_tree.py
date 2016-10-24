#   Copyright (c) 2016 CNRS - Centre national de la recherche scientifique.
#   All rights reserved.
#
#   Written by Telmo Menezes <telmo@telmomenezes.com>
#
#   This file is part of GraphBrain.
#
#   GraphBrain is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   GraphBrain is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with GraphBrain.  If not, see <http://www.gnu.org/licenses/>.


LEAF = 0
NODE = 1


class Position(object):
    LEFT, RIGHT = range(2)


class Tree(object):
    def __init__(self):
        self.root_id = None
        self.cur_id = 0
        self.table = {}

    def get(self, elem_id):
        if elem_id is None:
            return None
        return self.table[elem_id]

    def set(self, elem_id, elem):
        elem.id = elem_id
        self.table[elem_id] = elem

    def add(self, elem):
        self.set(self.cur_id, elem)
        self.cur_id += 1

    def root(self):
        assert(self.root_id is not None)
        return self.get(self.root_id)

    def create_leaf(self, token):
        leaf = Leaf(token)
        leaf.tree = self
        self.add(leaf)
        return leaf.id

    def create_node(self, children=None):
        node = Node(children)
        node.tree = self
        self.add(node)
        return node.id

    def enclose(self, entity):
        node_id = entity.id
        self.add(entity)
        node = self.get(self.create_node([entity.id]))
        self.set(node_id, node)
        return node

    def disenclose(self, node):
        assert(node.is_node())
        assert(len(node.children_ids) > 0)
        entity_id = node.id
        inner_entity = self.get(node.children_ids[0])
        self.set(entity_id, inner_entity)

    def remove_redundant_nesting(self):
        self.root().remove_redundant_nesting()

    def __str__(self):
        return str(self.get(self.root_id))


class Element(object):
    def __init__(self):
        self.type = None
        self.id = None
        self.tree = None
        self.namespace = None

    def is_leaf(self):
        return self.type == LEAF

    def is_node(self):
        return self.type == NODE

    def is_compound(self):
        return True

    def apply_layers(self):
        # if not implemented, do nothing.
        pass

    def remove_redundant_nesting(self):
        # if not implemented, do nothing.
        pass

    def add_child(self, elem_id):
        # throw exception
        pass

    def add_to_first_child(self, elem_id, pos):
        # throw exception
        pass

    def nest(self, elem_id):
        # throw exception
        pass

    def has_pos(self, pos):
        # throw exception
        pass


class Leaf(Element):
    def __init__(self, token):
        super(Leaf, self).__init__()
        self.type = LEAF
        self.pivot = token
        self.left = []
        self.right = []

    # override
    def add_child(self, elem_id):
        node = self.tree.enclose(self)
        node.add_child(elem_id)

    # override
    def add_to_first_child(self, elem_id, pos):
        node = self.tree.enclose(self)
        return node.add_to_first_child(elem_id, pos)

    # override
    def nest(self, elem_id):
        node = self.tree.enclose(self)
        return node.nest(elem_id)

    # override
    def has_pos(self, pos):
        if self.pivot.pos == pos:
            return True
        for token in self.left:
            if token.pos == pos:
                return True
        for token in self.right:
            if token.pos == pos:
                return True
        return False

    def __str__(self):
        words = [token.word for token in self.left]
        words.append(self.pivot.word)
        words += [token.word for token in self.right]
        return '_'.join(words)


class Node(Element):
    def __init__(self, children_ids=None):
        super(Node, self).__init__()
        self.type = NODE
        if children_ids is None:
            self.children_ids = []
        else:
            self.children_ids = children_ids
        self.layer_ids = []
        self.layer_id = -1
        self.compound = False

    def get_child(self, i):
        return self.tree.get(self.children_ids[i])

    def children(self):
        return [self.tree.get(child_id) for child_id in self.children_ids]

    def set_child(self, i, elem_id):
        self.children_ids[i] = elem_id

    def new_layer(self):
        if self.layer_id >= 0:
            self.layer_ids.append(self.layer_id)
            self.layer_id = -1

    def apply_layer(self, entity, layer):
        if layer.is_node():
            for i in range(len(layer.children_ids)):
                if layer.children_ids[i] < 0:
                    child_id = self.tree.create_node(entity.children_ids)
                    child = self.tree.get(child_id)
                    if child.is_singleton():
                        child_id = child.children_ids[0]
                    layer.set_child(i, child_id)
                    return True
                if self.apply_layer(entity, layer.get_child(i)):
                    return True
        return False

    def apply_layers(self):
        self.layer_ids.reverse()
        prev_layer = self
        for layer_id in self.layer_ids:
            layer = self.tree.get(layer_id)
            self.apply_layer(prev_layer, layer)
            prev_layer = layer
        self.children_ids = prev_layer.children_ids
        self.layer_ids = []

    def is_singleton(self):
        return len(self.children_ids) == 1

    def is_node_singleton(self):
        if not self.is_singleton():
            return False
        child = self.tree.get(self.children_ids[0])
        return child.is_node()

    # override
    def is_compound(self):
        return self.compound

    # override
    def add_child(self, elem_id):
        self.children_ids.append(elem_id)

    # override
    def add_to_first_child(self, elem_id, pos):
        if len(self.children_ids) > 0:
            if self.get_child(0).is_leaf():
                self.set_child(0, self.tree.enclose(self.get_child(0)).id)
            if pos == Position.RIGHT:
                self.tree.get(elem_id).parent = self
                self.get_child(0).children_ids.append(elem_id)
            else:
                self.tree.get(elem_id).parent = self
                self.get_child(0).children_ids.insert(0, elem_id)
        else:
            raise IndexError('Requesting root on an empty Node')
        return self

    # override
    def nest(self, elem_id):
        elem = self.tree.get(elem_id)
        if elem.is_leaf():
            rel = elem_id
            rest = []
        else:
            rel = elem.children_ids[0]
            rest = elem.children_ids[1:]
        self.layer_id = self.tree.create_node([rel, -1] + rest)
        return self

    # override
    def remove_redundant_nesting(self):
        for child_id in self.children_ids:
            child = self.tree.get(child_id)
            child.remove_redundant_nesting()
        if self.is_node_singleton():
            self.tree.disenclose(self)

    # override
    def has_pos(self, pos):
        for child in self.children():
            if child.has_pos(pos):
                return True
        return False

    def __str__(self):
        strs = [str(self.tree.get(child_id)) for child_id in self.children_ids]
        return '(%s)' % ' '.join(strs)