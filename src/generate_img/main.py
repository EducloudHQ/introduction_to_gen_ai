from aws_lambda_powertools.event_handler.appsync import Router
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit
import json

from botocore.exceptions import ClientError
import boto3

tracer = Tracer()

metrics = Metrics(namespace="Powertools")

logger = Logger(child=True)
router = Router()


@router.resolver(type_name="Query", field_name="generateImage")
@tracer.capture_method
def generate_image(prompt: str):
    metrics.add_metric(name="GenerativeAIInvocations", unit=MetricUnit.Count, value=1)
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
    )

    body = json.dumps({
        "text_prompts": [{"text": prompt}],
        "cfg_scale": 10,
        "seed": 0,
        "steps": 50,

    })
    modelId = 'stability.stable-diffusion-xl-v0'
    accept = 'application/json'
    contentType = 'application/json'
    outputText = "\n"
    logger.debug(f"input: we in here")

    try:

        response = bedrock_runtime.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)

        response_body = json.loads(response.get('body').read())
        logger.debug(f"response body: {response_body}")

        outputText = response_body.get('artifacts')[0].get('base64')



    except ClientError as error:

        if error.response['Error']['Code'] == 'AccessDeniedException':
            logger.debug(f"\x1b[41m{error.response['Error']['Message']}\
                    \nTo troubleshoot this issue please refer to the following resources.\
                     \nhttps://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html\
                     \nhttps://docs.aws.amazon.com/bedrock/latest/userguide/security-iam.html\x1b[0m\n")

        else:
            raise error

    return outputText
