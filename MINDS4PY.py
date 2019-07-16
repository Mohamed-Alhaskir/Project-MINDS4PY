import os
import requests
import json
import copy


class MINDS():
    """
    A brief summary of its purpose and behavior
    Any public methods, along with a brief description
    Any class properties (attributes)
    Anything related to the interface for subclassers, if the class is intended to be subclassed

    ...

    Attributes
    ----------
    new_minds_collection
    uniminds_blocks
    __dict__[schema['label']]

    Methods
    -------
    create_block(self, blocktemp, **kwargs)
    ave_minds_collection(self, overwrite= None)


    """
    def __init__(self, name, path=os.getcwd()):
        """
        Class method docstrings go here.

        A brief description of what the method is and what it’s used for
        Any arguments (both required and optional) that are passed including keyword arguments
        Label any arguments that are considered optional or have a default value
        Any side effects that occur when executing the method
        Any exceptions that are raised
        Any restrictions on when the method can be called
        Parameters
        ----------
        name : str
            The name of the file to be created
        path:  str, optional
                default is set to the current working directory
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
                        self.__dict__[schema['label']]['@type'] = "https://schema.hbp.eu/uniminds/core/%s/v1.0.0" % schema['label']
                        self.__dict__[schema['label']].pop('id', None)
                        self.__dict__[schema['label']].pop('type', None)
                        self.__dict__[schema['label']].pop('relative_url', None)
                        self.__dict__[schema['label']].pop('cellular_target', None)






                # TODO: add properties as dict if more value info is available (e.g., value type}
            else:
                continue

    def __check_kwargs4block(self, blocktemp, **kwargs):
        """
        A hiddend class method that checks kwargs according t their block

        Parameters
        ----------
        sound : str, optional
            The sound the animal makes (default is None)

        Raises
        ------
        NotImplementedError
            If no sound is set for the animal or passed in as a
            parameter.

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
                    if bkey in ['__block_label','@type', '__block_id']:
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
        This Class method will check
        if all entered kewargs are part of
        the to be created block or if important keys are missing
        It will also automatically add the @type with rest of kewargs .

        Parameters
        ----------
        blocktemp : An attribute of the MINDS class,
            It should be one of the blocks listed in the MINDS.uniminds.blocks

        Raises
        ------
        Append the newly created block to the new_minds_collection['minds_blocks']
        """
        if id.split('.')[-1] != "json":
            id = id.split('.')[0] + ".json"
        self.__check_kwargs4block(blocktemp, **kwargs)
        if len(self.error) > 0:
            print(self.error)
        # if everything is fine with the entries then create a new_block as dict accord to Trello
        else:
            new_block = {
                '__block_label': blocktemp['__block_label'],
                '__block_id': blocktemp['__block_id'],
                '@type': blocktemp['@type'],
                '@id': id}
            for key in blocktemp.keys():
                if key not in ['__block_label','@type', '__block_id'] :
                    try:
                        new_block[key] = kwargs[key]
                    except:
                        new_block[key] = None
        self.new_minds_collection['minds_blocks'].append(new_block)

    def __save_block(self, block, filepath):
        d2json = copy.deepcopy(block)
        d2json.pop('__block_id', None)
        d2json.pop('__block_label', None)
        with open(filepath, 'w') as fp:
            json.dump(d2json, fp, indent=4)

    def save_minds_collection(self, overwrite=False):
        """
        This Class method creates the dirctory structure according to MINDS
        then saves the blocks in the new_minds_collection['minds_blocks']
        as jsons in to their according block directory
        Raises
        ------
        blocks are saved in their according directory
        """
        minds_repo = self.new_minds_collection['path'] + '/' + self.new_minds_collection['name']
        if not os.path.exists(minds_repo):
            os.makedirs(minds_repo)
        for block in self.new_minds_collection['minds_blocks']:
            # please write paths according to python not specific for windows OS
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


