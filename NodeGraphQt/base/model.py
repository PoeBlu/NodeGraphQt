#!/usr/bin/python
import json
from collections import defaultdict

from NodeGraphQt.constants import (NODE_PROP,
                                   NODE_PROP_QLABEL,
                                   NODE_PROP_QLINEEDIT,
                                   NODE_PROP_QCHECKBOX,
                                   NODE_PROP_COLORPICKER)
from NodeGraphQt.errors import NodePropertyError


class PortModel(object):

    def __init__(self, node):
        self.node = node
        self.type_ = ''
        self.name = 'port'
        self.display_name = True
        self.multi_connection = False
        self.visible = True
        self.connected_ports = defaultdict(list)

    def __repr__(self):
        return f"<{self.__class__.__name__}(\'{self.name}\') @ {hex(id(self))}>"

    @property
    def to_dict(self):
        """
        serialize model information to a dictionary.

        Returns:
            dict: node port dictionary eg.
                {
                    'type': 'in',
                    'name': 'port',
                    'display_name': True,
                    'multi_connection': False,
                    'connected_ports': {<node_id>: [<port_name>, <port_name>]}
                }
        """
        props = self.__dict__.copy()
        props.pop('node')
        props['connected_ports'] = dict(props.pop('connected_ports'))
        return props


class NodeModel(object):

    def __init__(self):
        self.type_ = None
        self.id = hex(id(self))
        self.icon = None
        self.name = 'node'
        self.color = (13, 18, 23, 255)
        self.border_color = (74, 84, 85, 255)
        self.text_color = (255, 255, 255, 180)
        self.disabled = False
        self.selected = False
        self.width = 100.0
        self.height = 80.0
        self.pos = [0.0, 0.0]
        self.inputs = {}
        self.outputs = {}
        self._custom_prop = {}

        # node graph model set at node added time.
        self._graph_model = None

        # store the property attributes.
        # (deleted when node is added to the graph)
        self._TEMP_property_attrs = {}

        # temp store the property widget types.
        # (deleted when node is added to the graph)
        self._TEMP_property_widget_types = {
            'type_': NODE_PROP_QLABEL,
            'id': NODE_PROP_QLABEL,
            'icon': NODE_PROP,
            'name': NODE_PROP_QLINEEDIT,
            'color': NODE_PROP_COLORPICKER,
            'border_color': NODE_PROP,
            'text_color': NODE_PROP_COLORPICKER,
            'disabled': NODE_PROP_QCHECKBOX,
            'selected': NODE_PROP,
            'width': NODE_PROP,
            'height': NODE_PROP,
            'pos': NODE_PROP,
            'inputs': NODE_PROP,
            'outputs': NODE_PROP,
        }

    def add_property(self, name, value, items=None, range=None,
                     widget_type=NODE_PROP, tab='Properties'):
        """
        add custom property.

        Args:
            name (str): name of the property.
            value (object): data.
            items (list[str]): items used by widget type NODE_PROP_QCOMBO.
            range (tuple)): min, max values used by NODE_PROP_SLIDER.
            widget_type (int): widget type flag.
            tab (str): widget tab name.
        """
        tab = tab or 'Properties'

        if name in self.properties.keys():
            raise NodePropertyError(f'"{name}" reserved for default property.')
        if name in self._custom_prop.keys():
            raise NodePropertyError(f'"{name}" property already exists.')

        self._custom_prop[name] = value

        if self._graph_model is None:
            self._TEMP_property_widget_types[name] = widget_type
            self._TEMP_property_attrs[name] = {'tab': tab}
            if items:
                self._TEMP_property_attrs[name]['items'] = items
            if range:
                self._TEMP_property_attrs[name]['range'] = range
        else:
            attrs = {self.type_: {name: {
                'widget_type': widget_type,
                'tab': tab
            }}}
            if items:
                attrs[self.type_][name]['items'] = items
            if range:
                attrs[self.type_][name]['range'] = range
            self._graph_model.set_node_common_properties(attrs)

    def set_property(self, name, value):
        if name in self.properties.keys():
            setattr(self, name, value)
        elif name in self._custom_prop.keys():
            self._custom_prop[name] = value
        else:
            raise NodePropertyError(f'No property "{name}"')

    def get_property(self, name):
        if name in self.properties.keys():
            return self.properties[name]
        return self._custom_prop.get(name)

    def get_widget_type(self, name):
        model = self._graph_model
        if model is None:
            return self._TEMP_property_widget_types.get(name)
        return model.get_node_common_properties(self.type_)[name]['widget_type']

    def get_tab_name(self, name):
        model = self._graph_model
        if model is None:
            if attrs := self._TEMP_property_attrs.get(name):
                return attrs[name].get('tab')
            return
        return model.get_node_common_properties(self.type_)[name]['tab']

    @property
    def properties(self):
        """
        return all default node properties.

        Returns:
            dict: default node properties.
        """
        props = self.__dict__.copy()
        exclude = ['_custom_prop',
                   '_graph_model',
                   '_TEMP_property_attrs',
                   '_TEMP_property_widget_types']
        [props.pop(i) for i in exclude if i in props.keys()]
        return props

    @property
    def custom_properties(self):
        """
        return all custom properties specified by the user.

        Returns:
            dict: user defined properties.
        """
        return self._custom_prop

    @property
    def to_dict(self):
        """
        serialize model information to a dictionary.

        Returns:
            dict: node id as the key and properties as the values eg.
                {'0x106cf75a8': {
                    'name': 'foo node',
                    'color': (48, 58, 69, 255),
                    'border_color': (85, 100, 100, 255),
                    'text_color': (255, 255, 255, 180),
                    'type': 'com.chantasticvfx.FooNode',
                    'selected': False,
                    'disabled': False,
                    'inputs': {
                        <port_name>: {<node_id>: [<port_name>, <port_name>]}},
                    'outputs': {
                        <port_name>: {<node_id>: [<port_name>, <port_name>]}},
                    'width': 0.0,
                    'height: 0.0,
                    'pos': (0.0, 0.0),
                    'custom': {},
                    }
                }
        """
        node_dict = self.__dict__.copy()
        node_id = node_dict.pop('id')

        inputs = {}
        outputs = {}
        for name, model in node_dict.pop('inputs').items():
            if connected_ports := model.to_dict['connected_ports']:
                inputs[name] = connected_ports
        for name, model in node_dict.pop('outputs').items():
            if connected_ports := model.to_dict['connected_ports']:
                outputs[name] = connected_ports
        if inputs:
            node_dict['inputs'] = inputs
        if outputs:
            node_dict['outputs'] = outputs

        if custom_props := node_dict.pop('_custom_prop', {}):
            node_dict['custom'] = custom_props

        exclude = ['_graph_model',
                   '_TEMP_property_attrs',
                   '_TEMP_property_widget_types']
        [node_dict.pop(i) for i in exclude if i in node_dict.keys()]

        return {node_id: node_dict}

    @property
    def serial(self):
        """
        Serialize model information to a string.

        Returns:
            str: serialized JSON string.
        """
        model_dict = self.to_dict
        return json.dumps(model_dict)


class NodeGraphModel(object):

    def __init__(self):
        self.nodes = {}
        self.session = ''
        self.acyclic = True
        self.__common_node_props = {}

    def common_properties(self):
        return self.__common_node_props

    def set_node_common_properties(self, attrs):
        """
        store common node properties.

        Args:
            attrs (dict): common node properties.
                eg.
                     {'nodeGraphQt.nodes.FooNode': {
                        'my_property':{
                            'widget_type': 0,
                            'tab': 'Properties',
                            'items': ['foo', 'bar', 'test'],
                            'range': (0, 100)
                            }
                        }
                    }
        """
        for node_type in attrs.keys():
            node_props = attrs[node_type]

            if node_type not in self.__common_node_props.keys():
                self.__common_node_props[node_type] = node_props
                continue

            for prop_name, prop_attrs in node_props.items():
                common_props = self.__common_node_props[node_type]
                if prop_name not in common_props.keys():
                    common_props[prop_name] = prop_attrs
                    continue
                common_props[prop_name].update(prop_attrs)

    def get_node_common_properties(self, node_type):
        """
        Args:
            node_type (str): node type.

        Returns:
            dict: node common properties.
        """
        return self.__common_node_props.get(node_type)


if __name__ == '__main__':
    p = PortModel(None)
    # print(p.to_dict)

    n = NodeModel()
    n.inputs[p.name] = p
    n.add_property('foo', 'bar')

    print('-'*100)
    print('property keys\n')
    print(list(n.properties.keys()))
    print('-'*100)
    print('to_dict\n')
    for k, v in n.to_dict[n.id].items():
        print(k, v)
