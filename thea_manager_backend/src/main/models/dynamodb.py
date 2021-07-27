#!/usr/bin/env python

# ---------------------------------------------------------------
#                           Imports
# ---------------------------------------------------------------

# General Imports
import logging
logger = logging.getLogger(__name__)

from os import getenv
from typeguard import check_argument_types

# Boto3 Imports
from boto3 import resource
from boto3.dynamodb.conditions import Key

# Utils imports 
from .utils import exception_handler

# ---------------------------------------------------------------
#                           DynamoDB
# ---------------------------------------------------------------


class Dynamo():
    """
        This class to programtically interact with the boto3 DynamoDB API.

        Attributes
        ----------

        _resource: class 'botocore.client.DynamoDB', required

        Methods
        -------
        create_item(table_name, item)
            Puts item into dynamo table

        read_single_item(table_name, key, projection_expression, expression_attribute_names, expression_attribute_values)
            Retrives item from dynamo table

        read_multiple_items(table_name, key, projection_expression, last_evaluated_key, limit)
            Retrieves multiple items from dynamo table

        update_item(table_name, key, update_expression, expression_attribute_names, expression_attribute_values, condition_expression, return_values)
            Updates item on dynamo table

        delete_item(table_name, key)
            Deletes item from dynamo table
    """

    def __init__(self) -> None:
        self._resource = resource("dynamodb", region_name = getenv("REGION"))

    # Create
    @exception_handler
    def create_item(self, table_name: str, item: dict):
        """
            Adds item to DynamoDB table

            Parameters
            ----------

                table_name: str [required]
                    DynamoDB table name to add object to

                item: dict [required]
                    Object to be added to DynamoDB

            Returns
            -------

                response: str | None
                    server response data

                http_staus_code: int
                    HTTP server response

            Raises
            ------

                ClientError
                    Boto3 client service related error when making API request

                ParamValidationError
                    Error is raised when incorrect parameters provided to boto3
                    API method
        """

        # Type guarding
        assert check_argument_types()

        # Target DynamoDB table
        table = self._resource.Table(table_name)

        # Push to DynamoDB
        logger.info(f"Putting new item into database: {item}")
        response = table.put_item(Item = item)

        logger.info(f"None {response['ResponseMetadata']['HTTPStatusCode']}")
        return None, response['ResponseMetadata']['HTTPStatusCode']

    # Retrieve
    @exception_handler
    def read_single_item(self, table_name: str, key: dict, projection_expression: str, expression_attribute_names: dict = None, expression_attribute_values: dict = None):
        """
            Read single item from Dynamo table.

            Parameters
            ----------

                table_name: str [required]
                    DynamoDB table name to be queried

                key: dict [required]
                    Dictonary based object containing the filters to query DynamoDB

                projection_expression: str [required]
                    Filter expression indicating keys to query from database. If none, then all keys of object are returned

            Returns
            -------

                response: str | list
                    server response data

                http_staus_code: int
                    HTTP server response

            Raises
            ------

                ClientError
                    Boto3 client service related error when making API request

                ParamValidationError
                    Error is raised when incorrect parameters provided to boto3
                    API method
        """

        # Type guarding
        assert check_argument_types()
        
        # Target DynamoDB table
        table = self._resource.Table(table_name)

        # kwargs
        kwargs = {
            "Key": key,
            "ProjectionExpression": projection_expression,
            "ExpressionAttributeNames": expression_attribute_names,
            "ExpressionAttributeValues": expression_attribute_values,
            "ConsistentRead": True    
        }

        kwargs = {k:v for k,v in kwargs.items() if v}

        logger.info(f"Querying Dynamo table for key: {key}")
        return table.get_item(**kwargs).get("Item"), 200

    # Retrieve
    @exception_handler
    def read_multiple_items(self, table_name: str, key: dict, projection_expression: str, expression_attribute_names: dict = None, last_evaluated_key: dict = None, limit = 1000):
        """
            Read multiple DynamoDB NoSQL object

            Parameters:
            -----------

                table_name: str [required]
                    DynamoDB table name to be queried

                key: dict [required]
                    Dictionary based object containing the filters to query DynamoDB

                projection_expression: str [required]
                    Filter expression indicating keys to query from database. If none, then all keys of object are returned.

                last_evaluated_key: str [optional]
                    Is used during pagination, is the key of the last item evaluated to continue from.

                limit: int [optional]
                    The number of items to return during a single query request

            Returns:

                response: str | list
                    server response data

                http_staus_code: int
                    HTTP server response

            Raises
            ------

                ClientError
                    Boto3 client service related error when making API request

                ParamValidationError
                    Error is raised when incorrect parameters provided to boto3
                    API method
        """

        # Type guarding
        assert check_argument_types()
        
        # Target DynamoDB table
        table = self._resource.Table(table_name)

        # Create kwargs
        kwargs = {
            "Limit": limit,
            "IndexName": key["index_name"],
            "ProjectionExpression": projection_expression,
            "ExpressionAttributeNames": expression_attribute_names,
            "KeyConditionExpression": Key(key["index_name"]).eq(key["index_val"])
        }

        kwargs = {k:v for k,v in kwargs.items() if v}

        logger.info(f"Querying Dynamo table for index: {key['index_name']}, val: {key['index_val']}")
        return table.query(**kwargs).get("Items"), 200

    @exception_handler
    def read_entire_table(self, table_name: str, projection_expression: str = ""):
        """
            Scans and retrieves an entire data table.

            Parameters
            ----------

                table_name: str [required]
                    name of data table to be scanned

                projection_expression: str [required]
                    Filter expression indicating keys to query from database. If none, then all keys of object are returned.

            Returns
            -------

                table: list
                    list of objects containing data table entries           
        """

        # Type guarding
        assert check_argument_types()

        # Target DynamoDB table
        table = self._resource.Table(table_name)

        # Define kwargs
        kwargs = {
            "ProjectionExpression": projection_expression
        }

        # Remove empty keys
        kwargs = {k:v for k,v in kwargs.items() if v}

        # Scan table
        response = table.scan(**kwargs)

        # Return response
        logger.info(f"null {response['ResponseMetadata']['HTTPStatusCode']}")
        return response.get("Items", []), response['ResponseMetadata']['HTTPStatusCode']

    # Update
    @exception_handler
    def update_item(self, table_name: str, key: dict, update_expression: str, expression_attribute_names: dict = None, expression_attribute_values: dict = None, condition_expression = None, return_values: str = None):
        """
            Update an object on a Dynamo table.

            Parameters
            ----------

                table_name: str [required]
                    DynamoDB table name.

                key: dict [required]
                    Dictonary based object containing the filters to query DynamoDB.

                update_expression: str [required]
                    String instructing how to update DynamoDB object.

                expression_attribute_names: dict [optional]
                    Placeholder used in a Dynamo expression as an alternative to actual attribute 
                    name. An expression attribute name must begin with a pound sign ( # ), and be 
                    followed by one or more alphanumeric characters.

                expression_attribute_values: dict [optional]
                    Used with update expressions, are substitutes for the actual values that you 
                    want to replace in your update statement. Must start with a colon (":") rather 
                    than a pound sign.

                condition_expression: str [optional]
                    Parameter that you can use on write-based operations. If you include a Condition Expression
                    in your write operation, it will be evaluated prior to executing the write. If the Condition 
                    expression evaluates to false, the write will be aborted.

                return_values: str [optional]
                    parameter specifying what the API should return as part of it's response payload. Valid values are:
                        * NONE If ReturnValues is not specified, or if its value is NONE, then nothing is returned. (This setting is the default for ReturnValues.)
                        * ALL_OLD Returns all of the attributes of the item, as they appeared before the UpdateItem operation.
                        * UPDATED_OLD Returns only the updated attributes, as they appeared before the UpdateItem operation.
                        * ALL_NEW Returns all of the attributes of the item, as they appear after the UpdateItem operation.
                        * UPDATED_NEW Returns only the updated attributes, as they appear after the UpdateItem operation.

            Returns
            -------

                response:
                    type: str | list
                        server response data

                http_staus_code: int
                    HTTP server response

            Raises
            ------

                ClientError
                    Boto3 client service related error when making API request

                ParamValidationError
                    Error is raised when incorrect parameters provided to boto3
                    API method
        """

        # Type guarding
        assert check_argument_types()
        
        # Target DynamoDB table
        table = self._resource.Table(table_name)

        # Define kwargs
        kwargs = {
            "Key": key,
            "UpdateExpression": update_expression,
            "ExpressionAttributeNames": expression_attribute_names,
            "ExpressionAttributeValues": expression_attribute_values,
            "ConditionExpression": condition_expression,
            "ReturnValues": return_values
        }

        # Remove empty keys
        kwargs = {k: v for k, v in kwargs.items() if v}

        # Update DynamoDB item
        response = table.update_item(**kwargs)
        logger.info(f"Updating dynamo object with key: {key}")

        logger.info(f"null {response['ResponseMetadata']['HTTPStatusCode']}")
        return None, response['ResponseMetadata']['HTTPStatusCode']

    # Delete
    @exception_handler
    def delete_item(self, table_name: str, key: dict):
        """
            Deletes object from Dynamo table

            Parameters
            ----------

                table_name: str [required]
                    DynamoDB table name

                key: dict [required]
                    Dictonary based object containing the filters to query DynamoDB

            Returns
            -------
                
                response: str | list
                    server response data

                http_staus_code: int
                    HTTP server response

            Raises
            ------

                ClientError
                    Boto3 client service related error when making API request

                ParamValidationError
                    Error is raised when incorrect parameters provided to boto3
                    API method
        """

        # Type guarding
        assert check_argument_types()
        
        # Target DynamoDB table
        table = self._resource.Table(table_name)

        # Delete DynamoDB item
        response = table.delete_item(Key = key)
        logger.info(f"Deleting item from DynamoDB: {key}")

        logger.info(f"{response} response['ResponseMetadata']['HTTPStatusCode']")
        return response, response['ResponseMetadata']['HTTPStatusCode']


if __name__ == "__main__":
    dynamo_db = Dynamo()