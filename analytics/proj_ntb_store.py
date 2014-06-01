"""
Enables storage of project and their notebooks for different backends (Git,
Mongo, etc). For now we'll support mongoDB.
"""

import bson
import pymongo


class NotebookStore(object):
    """
    Store based on the MongoDB.
    """
    # TODO: export using GIT URL?
    # TODO: work with IDs and name in meta!

    def __init__(self, uri, uid):
        client = pymongo.MongoClient(uri)
        self.database = client[uid]

    def list_projects(self, uid, token):
        """
        list available projects.

        :param uid: User id.
        :param token: Token for this user.
        """
        self.database.authenticate(uid, token)
        tmp = self.database.collection_names(include_system_collections=False)
        res = []
        # bit of a hack but each db in suricate is also used for data storage.
        for item in tmp:
            if item.find('data_') == -1:
                res.append(item)
        return res

    def retrieve_project(self, project, uid, token):
        """
        Retrieve notebooks part of the project.

        :param project: name of the project.
        :param uid: User id.
        :param token: Token for this user.
        """
        self.database.authenticate(uid, token)
        res = []
        tmp = self.database[project].find(fields={'_id': True, 'meta': True})
        for item in tmp:
            res.append((str(item['_id']), item['meta']))
        return res

    def delete_project(self, project, uid, token):
        """
        Delete a project.

        :param project: name of the project.
        :param uid: User id.
        :param token: Token for this user.
        """
        self.database.authenticate(uid, token)
        self.database[project].drop()

    def retrieve_notebook(self, project, ntb_id, uid, token):
        """
        Retrieve a single notebook from a project.

        :param project: name of the project.
        :param ntb_id: Identifier for the notebook.
        :param uid: User id.
        :param token: Token for this user.
        """
        self.database.authenticate(uid, token)
        tmp = self.database[project].find_one({"_id": bson.ObjectId(ntb_id)})
        tmp.pop('_id')
        return tmp

    def update_notebook(self, project, ntb_id, content, uid, token):
        """
        Update a single notebook in a project.

        :param project: name of the project.
        :param ntb_id: Identifier for the notebook.
        :param content: The new notebook as dict.
        :param uid: User id.
        :param token: Token for this user.
        """
        self.database.authenticate(uid, token)
        coll = self.database[project]
        if ntb_id is None:
            ntb_id = coll.insert(content)
        else:
            coll.update({'_id': bson.ObjectId(ntb_id)},
                        {"$set": content}, upsert=True)
        return str(ntb_id)

    def delete_notebook(self, project, ntb_id, uid, token):
        """
        Delete a single notebook from a project.

        :param project: name of the project.
        :param ntb_id: Identifier for the notebook.
        :param uid: User id.
        :param token: Token for this user.
        """
        self.database.authenticate(uid, token)
        self.database[project].remove({'_id': bson.ObjectId(ntb_id)})
