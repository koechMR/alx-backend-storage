#!/usr/bin/env python3
""" MongoDB Operations with pymongo """


def list_all(mongo_collection):
    """ List documents in Python """
    documents = mongo_collection.find()

    if documents.count() == 0:
        return []

    return documents
