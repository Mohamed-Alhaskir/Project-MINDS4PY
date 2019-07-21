"""
Created on 01 August 2019
@author: Mohamed Alhaskir
"""
import os, copy, json, requests


class MINDS:
    """
    This class will extract MINDS block from the MINDS schema Version v1.0.0
    """

    def __init__(self, name, path=os.getcwd()):
        """

        :param name: The name of the MINDS dataset
        :type name; str
        :param path: path to the dataset
        :type path: str
        """

        url = "https://kg.humanbrainproject.org/api/structure?withLinks=true"
        response = requests.get(url)
        self.new_minds_collection = {'name': name, "path": path, "minds_blocks": []}
        self.uniminds_blocks = []
        for schema in response.json()['schemas']:
            if schema['id'].startswith('uniminds/core/'):
                self.uniminds_blocks.append(schema['label'])
                properties = {}
                for prop in schema['properties']:
                    att = prop['attribute']
                    if 'w3' in att:
                        continue
                    elif 'inference' in att:
                        continue
                    elif 'provenance' in att:
                        continue
                    else:
                        if "canBe" in prop.keys():
                            vtype = "link"
                            vexp = "%s" % prop['canBe']
                        else:
                            vtype = "metadata-entry"
                            vexp = ["str", "int", "float", "bool"]
                        properties[prop['label'].lower().replace(' ', '_')] = {'value_type': vtype, 'value_exp': vexp}
                        self.__dict__[schema['label']] = properties
                        self.__dict__[schema['label']]['__block_label'] = schema['label']
                        self.__dict__[schema['label']]['__block_id'] = schema['id']
                        self.__dict__[schema['label']]['@type'] = "https://schema.hbp.eu/uniminds/core/%s/v1.0.0" % \
                                                                  schema['label']
                        self.__dict__[schema['label']].pop('id', None)
                        self.__dict__[schema['label']].pop('type', None)
                        self.__dict__[schema['label']].pop('relative_url', None)
                        self.__dict__[schema['label']].pop('cellular_target', None)
            else:
                continue

    def __check_kwargs4block(self, blocktemp, **kwargs):
        """
        this method check if block blongs to schema or if key is part of block and  value  type
        :param blocktemp: The block type
        :type blocktemp: att
        :param kwargs: keys and values of the according block
        :return: a list or errors
        if the provided block does not blong to schema or key is not part of block or value wrong type
        """
        self.error = []
        d = {}
        if isinstance(blocktemp, (str, float, int)):
            self.error.append((1, "blocktemp must be an attribute of MINDS"))
        else:
            for key, value in kwargs.items():
                d[key] = value
                if key not in blocktemp.keys():
                    self.error.append((2, "key is not a block key "))
                for bkey, bvalue in blocktemp.items():
                    if bkey in ['__block_label', '@type', '__block_id']:
                        pass
                    else:
                        for val in bvalue.items():
                            for v in val:
                                if v == 'link':
                                    if key == bkey:
                                        if not isinstance(d[key], list):
                                            self.error.append((3, "wrong input type of value"))
                                        else:
                                            for v in d[key]:
                                                if not isinstance(v, dict):
                                                    self.error.append((4, "wrong input type of value"))
                                                else:
                                                    if len(v.keys()) > 1:
                                                        self.error.append((5, "too many keys"))
                                                    else:
                                                        if "@id" not in v.keys():
                                                            self.error.append((6, "key is not @id"))
                                elif v == 'metadata-entry':
                                    if key == bkey:
                                        if not isinstance(d[key], (str, int, float)):
                                            self.error.append((7, "wrong value type"))
        return self.error

    def create_block(self, blocktemp, id, **kwargs):
        """
        this methed will call __check_kwargs4block function and create MINDS block with according keys
        :param blocktemp: att
        :param id: id of the block
        :param kwargs: key and values of the according block;  keys with value = none will be
        created if they are not provided
        :return: a list or error if the
        provided block does not blong to schema or key is not part of block or value wrong typ

        """

        if id.split('.')[-1] != "json":
            id = id.split('.')[0] + ".json"
        self.__check_kwargs4block(blocktemp, **kwargs)
        if len(self.error) > 0:
            print(self.error)
        else:
            new_block = {
                '__block_label': blocktemp['__block_label'],
                '__block_id': blocktemp['__block_id'],
                '@type': blocktemp['@type'],
                '@id': id}
            for key in blocktemp.keys():
                if key not in ['__block_label', '@type', '__block_id']:
                    try:
                        new_block[key] = kwargs[key]
                    except:
                        new_block[key] = None
        self.new_minds_collection['minds_blocks'].append(new_block)

    def __save_block(self, block, filepath):
        """
        the method will make a copy of the created block and delete "__block_id" and "__block_label" from block keys
        :param block: the created block
        :param filepath: dict
        """
        d2json = copy.deepcopy(block)
        d2json.pop('__block_id', None)
        d2json.pop('__block_label', None)
        with open(filepath, 'w') as fp:
            json.dump(d2json, fp, indent=4)

    def save_minds_collection(self, overwrite=False):
        """
        this method will save the collection of created blocks in the new_minds_collection list as JSON-LD repository
        :param overwrite: to overwrite already created MINDS repository
        :return: if overwrite = False and block already exists method will return a string saying: block already exists
        and no new block will be saved
        """
        minds_repo = self.new_minds_collection['path'] + '/' + self.new_minds_collection['name']
        if not os.path.exists(minds_repo):
            os.makedirs(minds_repo)
        for block in self.new_minds_collection['minds_blocks']:
            sub_core_path = minds_repo + '/%s' % block['__block_id']
            if not os.path.exists(sub_core_path):
                os.makedirs(sub_core_path)
            filepath = sub_core_path + '/%s' % block['@id']
            if overwrite:
                self.__save_block(block, filepath)
            else:
                if os.path.isfile(filepath):
                    print("NOTE: block %s already exists and is not overwritten." % block['@id'])
                else:
                    self.__save_block(block, filepath)
