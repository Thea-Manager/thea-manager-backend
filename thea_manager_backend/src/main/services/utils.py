# Native imports
from re import sub
from os import getenv
from time import time
from requests import get

# jwt imports
from jose import jwt, jwk
from jose.utils import base64url_decode

# Logging Imports
import logging

# General imports
from hashlib import md5
from decimal import Decimal
from math import floor, log, pow
from collections.abc import MutableMapping

# ---------------------------------------------------------------
#                           Global Variables
# ---------------------------------------------------------------

logger = logging.getLogger(__name__)
accepted_file_extensions = [".txt", ".pdf", ".doc", ".docx", ".jpeg", ".jpg", ".png", ".csv", ".xls", ".xlsx"]

# ---------------------------------------------------------------
#                           Methods
# ---------------------------------------------------------------

def generate_differences_message(dict_a, dict_b):
    """
        Finds the differences between two dictionaries (for intersecting keys)
        and generates a list of strings highlighting the changes from dict_a to
        dict_b

        Parameters
        ----------
            dict_a: dict [required]
            dict_b: dict [required]

        Returns
        --------
            messages:
                list of unique difference messages
    """
    keys = get_common_keys(dict_a, dict_b)
    news = get_dict_vals(dict_b, keys)
    olds = get_dict_vals(dict_a, keys)

    # Generate message
    message = []
    for k, old, new in zip(keys, olds, news):

        if k in ["scopeId", "issueId", "projectId", "milestoneId"]:
            continue

        if old == new:
            continue

        # convert camel case to normal
        if not isinstance(dict_a[k], str) or not isinstance(dict_b[k], str):
            k = sub(r'(?<!^)(?=[A-Z])', ' ', k).lower()
            message.append(f"Updated '{k}'")
        else:
            k = sub(r'(?<!^)(?=[A-Z])', ' ', k).lower()
            message.append(f"Updated '{k}' from '{old}' to '{new}'")

    return list(set(message))


def get_dict_vals(mydict: dict, keys: list):
    """
        Gets list of values in dictionary for specific keys

        Parameters
        ----------
            mydict: dict [required]
                dictionary to extract target values from

            keys: list [required]
                list of target keys to extract informatio from

        Returns
        -------
            list of values for specific keys
    """
    return [mydict[x] for x in keys]


def get_common_keys(dict_a: dict, dict_b: dict):
    """
        Gets intersecting keys between two dictionaries

        Parameters
        ----------
            dict_a: dict [required]
            dict_b: dict [required]

        Returns
        -------
            list of intersecting dict keys
    """
    return list(set(dict_a.keys()) & set(dict_b.keys()))


def convert_size(size_bytes: int):
    """
        Converts bytes into appropriate size category label

        Parameters
        ----------       
            size_bytes: int [required]
                size in bytes

        Returns
        --------
            response: str
                size along with category
    """
    if size_bytes == 0: 
        return "0B" 
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB") 
    i = int(floor(log(size_bytes, 1024)))
    power = pow(1024, i) 
    size = round(size_bytes / power, 2) 
    return "{} {}".format(size, size_name[i])


def calculate_s3_etag(file_path, chunk_size=8*1024*1024):
    """
        Locally calculates file etag using default 8mb S3 chuncksize

        Parameters
        ----------
            file_path: str [required]
                file path
            
            chunk_size: int [required]
                8mb chunk size

        Returns
        --------
            local_etag: str
                multi-part etag checksum
    """
    md5s = []

    with open(file_path, 'rb') as fp:
        while True:
            data = fp.read(chunk_size)
            if not data:
                break
            md5s.append(md5(data))

    if len(md5s) < 1:
        return '"{}"'.format(md5().hexdigest())

    if len(md5s) == 1:
        return '"{}"'.format(md5s[0].hexdigest())

    digests = b''.join(m.digest() for m in md5s)
    digests_md5 = md5(digests)
    return '"{}-{}"'.format(digests_md5.hexdigest(), len(md5s))


def increment_alphanum(s):
    """
        Serially increments alphanumeric string
        
        Parameters
        ----------
            s: str [required]
                alphanumeric string
                
        Returns
        --------
            new_st: str
                serially incremented alphanumeric string
    """

    # Local global
    alphanum = "0123456789abcdefghijklmnopqrstuvwxyz"

    # vars
    new_s, continue_change = [], True
    
    # increment alphanum count
    for c in s[::-1].lower():
        if continue_change:
            if c == "z":
                new_s.insert(0, "0")
            else:
                new_s.insert(0, alphanum[alphanum.index(c) + 1])
                continue_change = False
        else:
            new_s.insert(0, c)

    return "".join(new_s)


def flatten_nested_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
        Flattens nested dictionaries into 1 degree dicts

        Parameters
        ----------
            d: dict [requried]
                dictionary object to flatten

            parent_key:  str [optional]
                parent key

            sep:  str [optional]
                separator item separating parent keys from nested keys

        Returns
        --------
            flattened: dict
                flattened dictionary item
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_nested_dict(v, new_key, sep = sep).items())
        else:
            items.append((new_key, v))

    return dict(items)


def clean_nested_dict(d: dict, upload: bool = True):
    """
        Cleans nested dictionary by coverting float to Decimal or vice versa

        Parameters
        ----------
            d: dict [required]
                dict item to clean

            upload: bool [optional]
                flag to specify whether to convert Decimal-> Float or Float-> Decimal
                             this is because DynamoDB doesn't support float but Decimal instead, and
                             when returning to client, only Float objects are jsonifyiable.

        Returns
        --------
            d: dict
                cleaned dictionary object
    """
    d = flatten_nested_dict(d)

    if upload:
        for key, val in d.items():
            if isinstance(val, float):
                d[key] = Decimal(val)
    else:
        for key, val in d.items():
            if isinstance(val, Decimal):
                d[key] = float(val)

    return d

# ---------------------------------------------------------------
#                           JWT Related Methods
# ---------------------------------------------------------------

# Get cognito environment variables
COGNITO_REGION, COGNITO_POOL_ID = getenv("REGION"), getenv("COGNITO_POOL_ID")

# Construct cognito idp url
cognito_idp_base_url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_POOL_ID}"


def get_token_claims(token: str):
    """
        Extracts unverified claims from JWt

        Parameters
        -----------
            token: str [required]

        Returns
        -------
            JWT: dict
                Unverified claims from JWT 
    """

    return jwt.get_unverified_claims(token)


def get_public_key(access_token: str, jwks: dict):
    """
        Retrieves public key and validates if key matches
        local key of access token header

        Parameters
        -----------
            access_token: str [required]
                JWT cognito access token

            jwks: dict [required]
                JWKs retrieved from cognito idp for relevant cognito pool id

        Returns
        -------
            key: dict | None
                extracted public key
    """

    kid = jwt.get_unverified_header(access_token).get("kid")
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key


def verify_jwt_signature(access_token: str, jwks: dict) -> bool:
    """
        Verifies signature of JWT

        Parameters
        ----------

            access_token: str [required]
                JWT token

            jwks: dict [required]
                JWKs from public cognito idp

        Returns:
        --------
            verification: bool
                Singature verified or not

        Raises:
        -------
            ValueError:
                if public key not found, error is raised
    """

    # Retrieve public key
    public_key = get_public_key(access_token, jwks)

    if not public_key:
        raise ValueError("No pubic key found!")

    # Construct hmac key from public key
    hmac_key = jwk.construct(public_key)

    # extract encoded signature
    message, signature = access_token.rsplit(".", 1)
    
    # encode signature & message
    signature, message = signature.encode(), message.encode()
    
    # Verify hmac key
    return hmac_key.verify(message, base64url_decode(signature))


def validate_jwt_claims(access_token):
    """
        Verifies calimes of JWT. Specifically, this method checks if:
            
            1- Token is expired
            2- Token issuer is valid
            3- Token use is for access purposes

        Parameters
        ----------
            token: str [required]
                JWT token

            jwks: dict [required]
                JWKs from public cognito idp

        Returns:
        --------
            Authorization: str
                Authorization message

            https_status_code: int
                Server response code

        Raises:
        -------
            ValueError:
                Token expired, if token is expired
                Invalid token provider, if provider of access token does not match public key issuer
                Invalid token use, if purpose of token is not to provide access
    """

    decoded_token = jwt.get_unverified_claims(access_token)

    # Check if JWT is expired
    if time() >= int(decoded_token["exp"]):
        return "Token expired", 401
    
    # Check if token issuer is valid
    if cognito_idp_base_url!=decoded_token["iss"]:
        return "Invalid token provider", 401

    # Check token use
    if decoded_token["token_use"]!="access":
        return "Invalid token use", 403
    
    return "Authorized", 200


def validate_token(access_token):
    """
        Validates if access token is valid by:

            1- verifying token structure
            2- verifying token signature
            3- verifying token claims

        The steps to validate tokens are outlined in this AWS
        documentation: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html

        Parameters
        ----------
            access_token: str [required]
                cognito access token

        Returns
        -------
            authorization: str
                authorization message from verifciation response
            
            https_status_code: int
                authroziation server response code
    """

    # Check if JWT structure is valid
    if len(access_token.split(".")) != 3:
        return "Invalid token", 403

    # Retrieve JWK
    jwks = get(f"{cognito_idp_base_url}/.well-known/jwks.json").json()
    
    # Verify signature
    if not verify_jwt_signature(access_token, jwks):
        return "Invalid token signature", 403
    
    # Verify claims
    return validate_jwt_claims(access_token)
    

# ---------------------------------------------------------------
#                           Decorators
# ---------------------------------------------------------------

# TODO: need to figure out a way to be more granular with ValueError
# because it can be several kinds of errors
def exception_handler(func):
    """
        Exception handling decorator meant to handle common errors returned
        from AWS and interpret them depending on the intended business logic

        Parameters
        ----------
            func: <method>
                Method to be wrapped and executed within this decorater

        Returns
        -------
            inner_function:
                Output of executed wrapped method
    """
    (func)
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if type(e).__name__ == "ResourceNotFoundException":
                logger.error(e)
                return "Organization ID Not Found", 404
            elif type(e).__name__ == "MessageRejected":
                logger.error(e)
                return "Email message rejected", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "ValidationException":
                logger.error(e)
                return "Invalid path ID", e.response['ResponseMetadata']['HTTPStatusCode']
            elif type(e).__name__ == "ValueError":
                logger.error(e)
                return "Project ID Not found", 404
            else:
                logger.error(e)
                return str(e), 500
    return inner_function
