import json
import os
import uuid

import boto3
from boto3.dynamodb.conditions import Key

table = boto3.resource("dynamodb").Table(os.environ["TABLE"])
STATUSES = {"Saved", "Applied", "Interview", "Offer", "Rejected"}
FIELDS = ("company", "role", "status", "notes")


def reply(code, body=None):
    return {"statusCode": code, "body": json.dumps(body if body is not None else {})}


def handler(event, context):
    # The JWT authorizer has already verified the token. "sub" identifies the user.
    user = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    method = event["requestContext"]["http"]["method"]
    app_id = (event.get("pathParameters") or {}).get("id")
    data = json.loads(event.get("body") or "{}")

    if method == "GET":
        items = table.query(KeyConditionExpression=Key("userId").eq(user))["Items"]
        return reply(200, items)

    if method == "DELETE":
        table.delete_item(Key={"userId": user, "appId": app_id})
        return reply(204)

    if not data.get("company") or not data.get("role"):
        return reply(400, {"error": "company and role are required"})
    if data.get("status", "Saved") not in STATUSES:
        return reply(400, {"error": "invalid status"})

    item = {k: str(data.get(k, ""))[:200] for k in FIELDS}
    item["status"] = item["status"] or "Saved"
    item["userId"] = user
    item["appId"] = app_id if method == "PUT" else str(uuid.uuid4())
    # Key includes userId, so one user can never overwrite another user's record.
    table.put_item(Item=item)
    return reply(200, item)
