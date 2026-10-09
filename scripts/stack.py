"""Shared helper: read the deployed stack's outputs."""

import boto3

STACK_NAME = "neeru"


def outputs(stack_name: str = STACK_NAME, region: str = "ap-south-1") -> dict:
    cfn = boto3.client("cloudformation", region_name=region)
    stack = cfn.describe_stacks(StackName=stack_name)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}
