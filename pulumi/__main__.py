"""An AWS Python Pulumi program"""

import os
import mimetypes
from pulumi_aws import s3, route53
from pulumi import FileAsset, Output, ResourceOptions, Config

config = Config()
content_dir = "out"
domain_name = f"cv.{os.environ.get('DOMAIN_NAME')}"
bucket = s3.Bucket(
    domain_name,
    website=s3.BucketWebsiteArgs(
        index_document="index.html"
        )
    )

public_access_block = s3.BucketPublicAccessBlock(
    'public-access-block', 
    bucket=bucket.id, 
    block_public_acls=False)

for file in os.listdir(content_dir):
    filepath = os.path.join(content_dir, file)
    mime_type, _ = mimetypes.guess_type(filepath)
    obj = s3.BucketObject(file,
        bucket=bucket.id,
        source=FileAsset(filepath),
        content_type=mime_type)
    
def public_read_policy_for_bucket(bucket_name):
    return Output.json_dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                Output.format("arn:aws:s3:::{0}/*", bucket_name),
            ]
        }]
    })

bucket_policy = s3.BucketPolicy("bucket-policy",
    bucket=bucket.id,
    policy=public_read_policy_for_bucket(bucket.id), 
    opts=ResourceOptions(depends_on=[public_access_block]))

zone = route53.get_zone(name=f"{os.environ.get('DOMAIN_NAME')}.",
    private_zone=False)

assigned_record = route53.Record("cv",
    zone_id=zone.zone_id,
    name=domain_name,
    type="CNAME",
    ttl=300,
    records=[bucket.website_endpoint]
)
